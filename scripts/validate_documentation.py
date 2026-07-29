"""Validate public documentation against saved evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKDOWN = {
    "README.md": ["# RAG Foundations", "## Acceptance Matrix", "## Final v2 Metrics", "docs/DATASET_CARD.md"],
    "docs/PROJECT_REQUIREMENTS.md": ["# Project 1: Prompting & RAG Foundations", "## Overview", "## What to Build", "## Milestones", "## Acceptance Criteria", "## Practitioner Resources"],
    "docs/DATASET_CARD.md": ["# Dataset Card", "## Dataset Identity", "## Intended Use", "## Construction Principles", "## Limitations", "## Ethics And Privacy"],
    "docs/PROJECT_PLAN.md": ["# Consolidated Project Plan and Implementation Map", "## Risks And Mitigations", "docs/DATASET_CARD.md"],
    "docs/DESIGN_DECISIONS.md": ["# Design Decisions", "## FAISS IndexFlatIP", "## Candidate A"],
    "docs/ARCHITECTURE.md": ["# Architecture", "## Offline Ingestion And Indexing", "## Query-Time Runtime", "docs/DATASET_CARD.md"],
    "docs/PROMPT_DESIGN.md": ["# Prompt Design", "## Grounded Prompts", "## Tone Prompts"],
    "docs/EXPERIMENTS.md": ["# Experiments", "## Chunking Configurations", "## Granite Vs Mistral Final v2 Comparison"],
    "docs/EVALUATION_METHOD.md": ["# Evaluation Method", "## Dataset", "## Scoring Layers", "docs/DATASET_CARD.md"],
    "docs/FINAL_REPORT.md": ["# Final Report: RAG Foundations Final v2", "## Failure Cases", "## Acceptance Matrix"],
    "docs/EVIDENCE_INDEX.md": ["# Evidence Index", "## Active Runtime Assets", "## Validators And Tests", "docs/DATASET_CARD.md"],
}

ACCEPTANCE_CRITERIA = [
    ">=70% grounded correctness",
    "Document + section citation",
    "Clear unsupported refusal",
    "Three distinct recognizable tones",
    "Structured tone output + few-shot",
    "Malformed-output handling",
    ">=3 documented experiments",
    "Evaluation report with retrieval, >=3 failures, 20 tone inputs, and model comparison",
]

FORBIDDEN = [
    "Codex", "ChatGPT", "AGENTS", "Master Prompt", "Continue from Gate",
    "prompt authorization", "remediation", "handoff", "AI-assisted semantic review",
    "tool-assisted semantic adjudication", "independent owner signoff is not complete",
    "data/faiss/watsonx", "project-01-rag-foundations",
]

SECRET_PATTERNS = [
    re.compile(r"(?im)^watsonx_api_key[ \t]*=[ \t]*\S+"),
    re.compile(r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)project_id\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
]


def read_json(path: str) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_required_docs() -> None:
    for rel, markers in REQUIRED_MARKDOWN.items():
        path = REPO_ROOT / rel
        require(path.is_file(), f"required Markdown file is missing: {rel}")
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            require(marker in text, f"required marker missing from {rel}: {marker}")
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        require(len(headings) >= 3 or rel == "docs/PROJECT_REQUIREMENTS.md", f"doc is too shallow: {rel}")


def validate_original_requirements() -> None:
    text = (REPO_ROOT / "docs/PROJECT_REQUIREMENTS.md").read_text(encoding="utf-8")
    for heading in ["## Overview", "## What to Build", "### Milestone 1", "### Milestone 6", "## Key Concepts to Understand", "## Common Pitfalls to Watch For", "## Stretch Goals", "## Resources", "## Practitioner Resources"]:
        require(heading in text, f"original requirements heading missing: {heading}")
    require(text.count("- [ ]") == 8, "original eight acceptance checklist items must be present")


def validate_acceptance_matrix() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    report = (REPO_ROOT / "docs/FINAL_REPORT.md").read_text(encoding="utf-8")
    for criterion in ACCEPTANCE_CRITERIA:
        require(readme.count(criterion) == 1, f"README criterion must appear once: {criterion}")
        require(report.count(criterion) == 1, f"Final Report criterion must appear once: {criterion}")
    require("Clear unsupported refusal | PARTIAL" in readme, "unsupported refusal must be PARTIAL")
    require("Three distinct recognizable tones | PARTIAL" in readme, "tone distinctness must be PARTIAL")


def validate_metrics() -> None:
    metrics = read_json("data/evaluation/final_v2/scoring/final_metrics.json")
    comparison = read_json("data/evaluation/final_v2/scoring/model_comparison.json")
    public = (REPO_ROOT / "README.md").read_text(encoding="utf-8") + "\n" + (REPO_ROOT / "docs/FINAL_REPORT.md").read_text(encoding="utf-8")
    for value in ["17/20", "16/20", "3/4", "4/4", "8/20", "9/20", "16/20", "20/20", str(metrics["retrieval"]["hit_at_1"]), str(metrics["retrieval"]["mrr"])]:
        require(value in public, f"public docs do not include metric value: {value}")
    require(metrics["scoring_layer"] == "owner_verified_hybrid_final", "metrics scoring layer changed")
    require(comparison["scoring_layer"] == "owner_verified_hybrid_final", "comparison scoring layer changed")
    require(comparison["pricing_evidence"] is None if "pricing_evidence" in comparison else True, "pricing evidence must be null")


def validate_links() -> None:
    docs = list(REQUIRED_MARKDOWN)
    tick = re.compile(r"`((?:data|src|scripts|tests|docs|prompts)/[^`\s,;:)]+)`")
    for rel in docs:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for match in tick.finditer(text):
            candidate = match.group(1).rstrip(".")
            if "*" in candidate:
                continue
            require((REPO_ROOT / candidate).exists(), f"documented path missing in {rel}: {candidate}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            clean = target.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            require((REPO_ROOT / clean).exists(), f"Markdown link missing in {rel}: {clean}")


def validate_public_language() -> None:
    for rel in REQUIRED_MARKDOWN:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for phrase in FORBIDDEN:
            require(phrase.lower() not in text.lower(), f"forbidden phrase in {rel}: {phrase}")
    require((REPO_ROOT / "data/evaluation/final_v2/human_review/owner_adjudication.json").exists(), "owner artifact missing")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    require("synthetic" in readme and "fictional" in readme, "README must disclose synthetic dataset")


def validate_no_secrets() -> None:
    for rel in ["README.md", ".env.example"]:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            require(pattern.search(text) is None, f"possible secret-like value in {rel}")


def validate_documentation() -> dict[str, Any]:
    validate_required_docs()
    validate_original_requirements()
    validate_acceptance_matrix()
    validate_metrics()
    validate_links()
    validate_public_language()
    validate_no_secrets()
    return {"status": "ok", "required_markdown_count": len(REQUIRED_MARKDOWN)}


def main() -> int:
    print(json.dumps(validate_documentation(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
