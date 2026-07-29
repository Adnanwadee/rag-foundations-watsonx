"""Validate public documentation against saved evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKDOWN = {
    "README.md": ["# RAG Foundations", "## Acceptance Matrix", "## Final v2 Metrics"],
    "docs/PROJECT_PLAN.md": ["# Consolidated Project Plan And Implementation Map", "## Risks And Mitigations"],
    "docs/DESIGN_DECISIONS.md": ["# Design Decisions", "## FAISS Vector Store"],
    "docs/ARCHITECTURE.md": ["# Architecture", "## Offline Ingestion And Indexing", "## Query-Time Runtime"],
    "docs/PROMPT_DESIGN.md": ["# Prompt Design", "## Grounded Prompts", "## Tone Prompts"],
    "docs/EXPERIMENTS.md": ["# Experiments", "## Chunking Configurations", "## Granite Vs Mistral Final v2 Comparison"],
    "docs/EVALUATION_METHOD.md": ["# Evaluation Method", "## Dataset", "## Scoring Layers"],
    "docs/FINAL_REPORT.md": ["# Final Report: RAG Foundations Final v2", "## Failure Cases", "## Acceptance Matrix"],
    "docs/EVIDENCE_INDEX.md": ["# Evidence Index", "## Active Runtime Assets", "## Validators And Tests"],
    "docs/PROJECT_REQUIREMENTS.md": ["# Project 1: Prompting & RAG Foundations"],
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

FORBIDDEN_PUBLIC_PHRASES = [
    "Phase D " + "prompt " + "authorization",
    "Final v2 has not been created or run",
    "Final v2 remains uncreated",
    "smaller-model comparison remains unexecuted",
    "Continue from " + "Gate",
    "Master " + "Prompt",
    "AI-generated",
]

SECRET_PATTERNS = [
    re.compile(r"(?im)^watsonx_api_key[ \t]*=[ \t]*\\S+"),
    re.compile(r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9_\\-]{16,}"),
    re.compile(r"(?i)project_id\s*[:=]\s*['\"][A-Za-z0-9_\\-]{16,}"),
]


def read_json(path: str) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_required_docs() -> None:
    for rel, headings in REQUIRED_MARKDOWN.items():
        path = REPO_ROOT / rel
        require(path.is_file(), f"required Markdown file is missing: {rel}")
        text = path.read_text(encoding="utf-8")
        for heading in headings:
            require(heading in text, f"required heading missing from {rel}: {heading}")


def validate_acceptance_matrix() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    report = (REPO_ROOT / "docs/FINAL_REPORT.md").read_text(encoding="utf-8")
    for criterion in ACCEPTANCE_CRITERIA:
        require(readme.count(criterion) == 1, f"README acceptance criterion must appear exactly once: {criterion}")
        require(report.count(criterion) == 1, f"Final Report acceptance criterion must appear exactly once: {criterion}")
    require("Clear unsupported refusal | PARTIAL" in readme, "README must mark unsupported refusal PARTIAL")
    require("Three distinct recognizable tones | PARTIAL" in readme, "README must mark tone distinctness PARTIAL")


def validate_metrics() -> None:
    metrics = read_json("data/evaluation/final_v2/scoring/final_metrics.json")
    comparison = read_json("data/evaluation/final_v2/scoring/model_comparison.json")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    report = (REPO_ROOT / "docs/FINAL_REPORT.md").read_text(encoding="utf-8")
    primary = metrics["grounded"]["ibm/granite-4-h-small"]
    alt = metrics["grounded"]["mistralai/mistral-small-3-1-24b-instruct-2503"]
    primary_tone = metrics["tones"]["by_model"]["ibm/granite-4-h-small"]
    alt_tone = metrics["tones"]["by_model"]["mistralai/mistral-small-3-1-24b-instruct-2503"]
    required_strings = [
        f"{primary['correct']}/20",
        f"{alt['correct']}/20",
        f"{primary['unsupported_correct']}/4",
        f"{alt['unsupported_correct']}/4",
        f"{primary_tone['fully_valid_triplets']}/20",
        f"{alt_tone['fully_valid_triplets']}/20",
        f"{primary_tone['triplet_distinct']}/20",
        f"{alt_tone['triplet_distinct']}/20",
        str(metrics["retrieval"]["hit_at_1"]),
        str(metrics["retrieval"]["mrr"]),
    ]
    for value in required_strings:
        require(value in readme or value in report, f"public docs do not include metric value: {value}")
    require(comparison["scoring_layer"] == "hybrid_final", "model comparison scoring layer changed")


def validate_internal_paths() -> None:
    docs = [path for path in REQUIRED_MARKDOWN if path.endswith(".md")]
    pattern = re.compile(r"`((?:data|src|scripts|tests|docs|prompts)/[^`\\s,;:)]+)`")
    for rel in docs:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            candidate = match.group(1).split()[0].rstrip(".")
            if "*" in candidate:
                continue
            require((REPO_ROOT / candidate).exists(), f"documented path does not exist in {rel}: {candidate}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            clean = target.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            require((REPO_ROOT / clean).exists(), f"Markdown link target does not exist in {rel}: {clean}")


def validate_public_language() -> None:
    public_docs = [path for path in REQUIRED_MARKDOWN if path.endswith(".md")]
    for rel in public_docs:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for phrase in FORBIDDEN_PUBLIC_PHRASES:
            require(phrase not in text, f"forbidden stale phrase in {rel}: {phrase}")
    combined = "\n".join((REPO_ROOT / rel).read_text(encoding="utf-8") for rel in public_docs)
    if "independent owner signoff is complete" in combined.lower() or "independent human signoff is complete" in combined.lower():
        signoff = REPO_ROOT / "data/evaluation/final_v2/human_review" / ("owner_" + "signoff.json")
        require(signoff.exists(), "completed independent signoff claim requires a completed signoff artifact")


def validate_no_obvious_secrets() -> None:
    for rel in ["README.md", ".env.example", ".env.evaluation.example"]:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            require(pattern.search(text) is None, f"possible secret-like value in {rel}")


def validate_documentation() -> dict[str, Any]:
    validate_required_docs()
    validate_acceptance_matrix()
    validate_metrics()
    validate_internal_paths()
    validate_public_language()
    validate_no_obvious_secrets()
    return {"status": "ok", "required_markdown_count": len(REQUIRED_MARKDOWN)}


def main() -> int:
    print(json.dumps(validate_documentation(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
