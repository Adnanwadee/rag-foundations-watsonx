"""Validate repository references, JSON syntax, path portability, and public residue."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

PATH_KEYS = {
    "path",
    "source_path",
    "index_path",
    "metadata_path",
    "index_config_path",
    "dataset_path",
    "prompt_manifest_path",
    "index_manifest_path",
    "owner_adjudication_path",
    "system_prompt_path",
    "user_prompt_path",
    "few_shot_path",
}

ALLOW_MISSING_PREFIXES = {"artifacts/"}

ALLOW_TEXT_PHASE_PATHS = {
    "data/documents_v2_1/",
    "data/indexes/selected/metadata.json",
    "data/evaluation/final_v2/retrieval_results.json",
    "data/evaluation/final_v2/manifests/rendered_requests.json",
}

FORBIDDEN_ALWAYS = [
    "Codex",
    "ChatGPT",
    "AGENTS",
    "Master Prompt",
    "Continue from Gate",
    "prompt authorization",
    "remediation",
    "handoff",
    "AI-assisted semantic review",
    "tool-assisted semantic adjudication",
    "data/faiss/watsonx",
    "project-01-rag-foundations",
]

ABSOLUTE_PATTERNS = [
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"Desktop/"),
]

SECRET_PATTERNS = [
    re.compile(
        r"""(?i)api[_-]?key['"]?\s*[:=]\s*['"]?"""
        r"""(?P<value>[A-Za-z0-9_-]{16,})['"]?"""
    ),
    re.compile(
        r"""(?im)^WATSONX_API_KEY\s*=\s*(?P<value>[^\s#]+)"""
    ),
]

PLACEHOLDER_SECRET_VALUES = {
    "changeme",
    "change-me",
    "change_me",
    "replace-me",
    "replace_me",
    "example",
    "placeholder",
}

SKIP_PARTS = {
    ".git",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
}


def fail(msg: str) -> None:
    raise ValueError(msg)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def should_skip(path: Path) -> bool:
    return path == REPO_ROOT / ".env" or any(
        part in SKIP_PARTS for part in path.parts
    )


def parse_json_files() -> int:
    count = 0

    for path in REPO_ROOT.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue

        relative_path = rel(path)

        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            count += 1

        elif path.suffix == ".jsonl":
            lines = path.read_text(encoding="utf-8").splitlines()

            for line_number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue

                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    fail(
                        f"invalid JSONL "
                        f"{relative_path}:{line_number}: {exc}"
                    )

            count += 1

    return count


def is_allowed_missing(value: str) -> bool:
    return (
        value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("mailto:")
        or any(
            value.startswith(prefix)
            for prefix in ALLOW_MISSING_PREFIXES
        )
        or "://" in value
        or bool(
            re.match(
                r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+",
                value,
            )
        )
    )


def walk_paths(
    obj: Any,
    source: str,
    parent_key: str = "",
) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            walk_paths(value, source, key)

    elif isinstance(obj, list):
        for value in obj:
            walk_paths(value, source, parent_key)

    elif isinstance(obj, str):
        for pattern in ABSOLUTE_PATTERNS:
            if pattern.search(obj):
                fail(
                    f"absolute/personal path in {source}: "
                    f"{obj[:140]}"
                )

        if parent_key in PATH_KEYS or parent_key.endswith("_path"):
            normalized_value = obj.replace("\\", "/")

            repository_prefixes = (
                "data/",
                "docs/",
                "src/",
                "scripts/",
                "tests/",
                "prompts/",
                ".github/",
                ".env",
            )

            if normalized_value.startswith(repository_prefixes):
                if not (REPO_ROOT / normalized_value).exists():
                    fail(
                        f"missing referenced path in {source}: "
                        f"{normalized_value}"
                    )

                return

            if is_allowed_missing(normalized_value):
                return


def validate_json_references() -> None:
    for path in REPO_ROOT.rglob("*.json"):
        if should_skip(path):
            continue

        content = path.read_text(encoding="utf-8")
        walk_paths(json.loads(content), rel(path))

    for path in REPO_ROOT.rglob("*.jsonl"):
        if should_skip(path):
            continue

        lines = path.read_text(encoding="utf-8").splitlines()

        for line in lines:
            if line.strip():
                walk_paths(json.loads(line), rel(path))


def is_placeholder_secret(value: str) -> bool:
    """Return whether a detected value is clearly a safe placeholder."""

    normalized = value.strip().strip("'\"")
    normalized_lower = normalized.lower()

    return (
        not normalized
        or (
            normalized.startswith("<")
            and normalized.endswith(">")
        )
        or (
            normalized.startswith("${")
            and normalized.endswith("}")
        )
        or normalized_lower in PLACEHOLDER_SECRET_VALUES
    )


def validate_text_residue() -> None:
    excluded_suffixes = {
        ".index",
        ".pyc",
    }

    for path in REPO_ROOT.rglob("*"):
        if (
            should_skip(path)
            or not path.is_file()
            or path.suffix.lower() in excluded_suffixes
        ):
            continue

        relative_path = rel(path)
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for secret_pattern in SECRET_PATTERNS:
            for match in secret_pattern.finditer(text):
                value = match.group("value")

                if not is_placeholder_secret(value):
                    fail(
                        f"possible credential in {relative_path}"
                    )


def validate_no_empty_files() -> None:
    allowed_empty_files = {
        "data/evaluation/final_v2/grounded_results.jsonl",
        "data/evaluation/final_v2/tone_results.jsonl",
    }

    for path in REPO_ROOT.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue

        if (
            path.stat().st_size == 0
            and rel(path) not in allowed_empty_files
        ):
            fail(f"empty file: {rel(path)}")


def validate_references() -> dict[str, Any]:
    parsed = parse_json_files()

    validate_json_references()
    validate_text_residue()
    validate_no_empty_files()

    return {
        "status": "ok",
        "json_or_jsonl_files": parsed,
    }


def main() -> int:
    result = validate_references()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())