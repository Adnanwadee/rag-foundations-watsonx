"""Validate repository references, JSON syntax, path portability, and public residue."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PATH_KEYS = {"path", "source_path", "index_path", "metadata_path", "index_config_path", "dataset_path", "prompt_manifest_path", "index_manifest_path", "owner_adjudication_path", "system_prompt_path", "user_prompt_path", "few_shot_path"}
ALLOW_MISSING_PREFIXES = {"artifacts/"}
ALLOW_TEXT_PHASE_PATHS = {
    "data/documents_v2_1/",
    "data/indexes/selected/metadata.json",
    "data/evaluation/final_v2/retrieval_results.json",
    "data/evaluation/final_v2/manifests/rendered_requests.json",
}
FORBIDDEN_ALWAYS = ["Codex", "ChatGPT", "AGENTS", "Master Prompt", "Continue from Gate", "prompt authorization", "remediation", "handoff", "AI-assisted semantic review", "tool-assisted semantic adjudication", "data/faiss/watsonx", "project-01-rag-foundations"]
ABSOLUTE_PATTERNS = [re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"), re.compile(r"/Users/"), re.compile(r"/home/"), re.compile(r"Desktop/")]
VALIDATOR_ALLOWLIST = {"scripts/validate_references.py", "scripts/validate_documentation.py"}
SECRET_PATTERNS = [re.compile(r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"), re.compile(r"(?im)^WATSONX_API_KEY=\S+")]
SKIP_PARTS = {".git", ".ruff_cache", ".pytest_cache", "__pycache__"}


def fail(msg: str) -> None:
    raise ValueError(msg)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def should_skip(path: Path) -> bool:
    return path == REPO_ROOT / ".env" or any(part in SKIP_PARTS for part in path.parts)


def parse_json_files() -> int:
    count = 0
    for path in REPO_ROOT.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        rp = rel(path)
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            count += 1
        elif path.suffix == ".jsonl":
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.strip():
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        fail(f"invalid JSONL {rp}:{line_no}: {exc}")
            count += 1
    return count


def is_allowed_missing(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://") or value.startswith("mailto:") or any(value.startswith(prefix) for prefix in ALLOW_MISSING_PREFIXES) or "://" in value or re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+", value)


def walk_paths(obj: Any, source: str, parent_key: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            walk_paths(value, source, key)
    elif isinstance(obj, list):
        for value in obj:
            walk_paths(value, source, parent_key)
    elif isinstance(obj, str):
        for pat in ABSOLUTE_PATTERNS:
            if pat.search(obj):
                fail(f"absolute/personal path in {source}: {obj[:140]}")
        if parent_key in PATH_KEYS or parent_key.endswith("_path"):
            value = obj.replace("\\", "/")
            if value.startswith(("data/", "docs/", "src/", "scripts/", "tests/", "prompts/", ".github/", ".env")):
                if not (REPO_ROOT / value).exists():
                    fail(f"missing referenced path in {source}: {value}")
                return
            if is_allowed_missing(value):
                return


def validate_json_references() -> None:
    for path in REPO_ROOT.rglob("*.json"):
        if should_skip(path):
            continue
        walk_paths(json.loads(path.read_text(encoding="utf-8")), rel(path))
    for path in REPO_ROOT.rglob("*.jsonl"):
        if should_skip(path):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                walk_paths(json.loads(line), rel(path))


def validate_text_residue() -> None:
    for path in REPO_ROOT.rglob("*"):
        if should_skip(path) or not path.is_file() or path.suffix.lower() in {".index", ".pyc"}:
            continue
        rp = rel(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for secret in SECRET_PATTERNS:
            if secret.search(text):
                fail(f"possible credential in {rp}")
        if rp not in VALIDATOR_ALLOWLIST:
            for phrase in FORBIDDEN_ALWAYS:
                if phrase.lower() in text.lower():
                    fail(f"forbidden phrase in {rp}: {phrase}")
        if rp not in VALIDATOR_ALLOWLIST and ("phase c" in text.lower() or "phase_c" in text.lower()):
            if not any(rp.startswith(prefix) for prefix in ALLOW_TEXT_PHASE_PATHS):
                fail(f"workflow phase residue in {rp}")


def validate_no_empty_files() -> None:
    for path in REPO_ROOT.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        if path.stat().st_size == 0 and rel(path) not in {"data/evaluation/final_v2/grounded_results.jsonl", "data/evaluation/final_v2/tone_results.jsonl"}:
            fail(f"empty file: {rel(path)}")


def validate_references() -> dict[str, Any]:
    parsed = parse_json_files()
    validate_json_references()
    validate_text_residue()
    validate_no_empty_files()
    return {"status": "ok", "json_or_jsonl_files": parsed}


def main() -> int:
    print(json.dumps(validate_references(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
