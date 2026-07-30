"""Validate repository references, JSON syntax, public text, and credential hygiene."""

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

REPOSITORY_PREFIXES = (
    "data/",
    "docs/",
    "src/",
    "scripts/",
    "tests/",
    "prompts/",
    ".github/",
    ".env.example",
)

BACKTICK_PATH_PREFIXES = (
    "src/",
    "scripts/",
    "tests/",
    "docs/",
    "data/",
    "prompts/",
    ".github/",
    ".env.example",
)

FORBIDDEN_PUBLIC_TERMS = [
    "validate_" + "documentation",
    "validate_" + "documentation.py",
    "Continue from Gate",
    "Master Prompt",
    "prompt authorization",
    "AI-assisted semantic review",
    "tool-assisted semantic adjudication",
    "project-" + "01-rag-foundations",
    "Co" + "dex",
    "Chat" + "GPT",
    "AG" + "ENTS.md",
]

ABSOLUTE_PATTERNS = [
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"/Users/[^/\s)]+/"),
    re.compile(r"/home/[^/\s)]+/"),
    re.compile(r"Desk" + r"top/"),
]

SECRET_PATTERNS = [
    re.compile(
        r"""(?i)api[_-]?key['"]?\s*[:=]\s*['"]?"""
        r"""(?P<value>[A-Za-z0-9_${}<>\-]{16,})['"]?"""
    ),
    re.compile(r"""(?im)^WATSONX_API_KEY\s*=\s*(?P<value>[^\s#]+)"""),
]

PLACEHOLDER_SECRET_VALUES = {
    "changeme",
    "change-me",
    "change_me",
    "replace-me",
    "replace_me",
    "placeholder",
}

SKIP_PARTS = {
    ".git",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
}

TEXT_SUFFIXES_FOR_CREDENTIAL_SCAN = {
    "",
    ".cfg",
    ".conf",
    ".env",
    ".example",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")


def fail(msg: str) -> None:
    raise ValueError(msg)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def should_skip(path: Path) -> bool:
    return path == REPO_ROOT / ".env" or any(part in SKIP_PARTS for part in path.parts)


def iter_repository_files() -> list[Path]:
    return [path for path in REPO_ROOT.rglob("*") if not should_skip(path) and path.is_file()]


def is_public_text_file(path: Path) -> bool:
    relative_path = rel(path)
    return (
        relative_path == "README.md"
        or relative_path == "scripts/README.md"
        or relative_path == ".env.example"
        or relative_path == "pyproject.toml"
        or (relative_path.startswith("docs/") and path.suffix.lower() == ".md")
        or (relative_path.startswith(".github/") and path.suffix.lower() in {".yml", ".yaml"})
    )


def is_markdown_file(path: Path) -> bool:
    relative_path = rel(path)
    return (
        relative_path == "README.md"
        or relative_path == "scripts/README.md"
        or (relative_path.startswith("docs/") and path.suffix.lower() == ".md")
    )


def parse_json_files() -> int:
    count = 0

    for path in iter_repository_files():
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
                    fail(f"invalid JSONL {relative_path}:{line_number}: {exc}")

            count += 1

    return count


def is_allowed_missing(value: str) -> bool:
    return (
        value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("mailto:")
        or any(value.startswith(prefix) for prefix in ALLOW_MISSING_PREFIXES)
        or "://" in value
        or bool(re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+", value))
    )


def validate_no_absolute_paths(text: str, source: str) -> None:
    for pattern in ABSOLUTE_PATTERNS:
        match = pattern.search(text)
        if match:
            fail(f"absolute/personal path in {source}: {match.group(0)}")


def walk_paths(obj: Any, source: str, parent_key: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            walk_paths(value, source, key)

    elif isinstance(obj, list):
        for value in obj:
            walk_paths(value, source, parent_key)

    elif isinstance(obj, str):
        validate_no_absolute_paths(obj, source)

        if parent_key in PATH_KEYS or parent_key.endswith("_path"):
            normalized_value = obj.replace("\\", "/")

            if normalized_value.startswith(REPOSITORY_PREFIXES):
                if not (REPO_ROOT / normalized_value).exists():
                    fail(f"missing referenced path in {source}: {normalized_value}")

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
        or (normalized.startswith("<") and normalized.endswith(">"))
        or (normalized.startswith("${") and normalized.endswith("}"))
        or normalized_lower in PLACEHOLDER_SECRET_VALUES
    )


def should_scan_for_credentials(path: Path) -> bool:
    if should_skip(path) or not path.is_file():
        return False
    if path.name == ".env" or path.name == ".env.example":
        return True
    return path.suffix.lower() in TEXT_SUFFIXES_FOR_CREDENTIAL_SCAN


def validate_credential_text(path: Path, text: str) -> None:
    relative_path = rel(path)
    for secret_pattern in SECRET_PATTERNS:
        for match in secret_pattern.finditer(text):
            value = match.group("value")

            if not is_placeholder_secret(value):
                fail(f"possible credential in {relative_path}")


def validate_text_residue() -> dict[str, int]:
    public_text_files_checked = 0
    credential_files_checked = 0

    for path in iter_repository_files():
        text = path.read_text(encoding="utf-8", errors="ignore")

        if should_scan_for_credentials(path):
            credential_files_checked += 1
            validate_credential_text(path, text)

        if not is_public_text_file(path):
            continue

        public_text_files_checked += 1
        relative_path = rel(path)
        validate_no_absolute_paths(text, relative_path)

        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in text:
                fail(f"forbidden public reference in {relative_path}: {term}")

    return {
        "public_text_files_checked": public_text_files_checked,
        "credential_files_checked": credential_files_checked,
    }


def normalize_markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if " " in target:
        target = target.split()[0]
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target


def is_external_or_anchor(target: str) -> bool:
    return (
        target.startswith("#")
        or target.startswith("http://")
        or target.startswith("https://")
        or target.startswith("mailto:")
    )


def strip_query_and_anchor(target: str) -> str:
    return target.split("#", 1)[0].split("?", 1)[0]


def validate_markdown_links() -> dict[str, int]:
    markdown_files_checked = 0
    markdown_links_checked = 0

    for path in iter_repository_files():
        if not is_markdown_file(path):
            continue

        markdown_files_checked += 1
        text = path.read_text(encoding="utf-8")

        for match in MARKDOWN_LINK_RE.finditer(text):
            target = normalize_markdown_target(match.group(1))

            if is_external_or_anchor(target):
                markdown_links_checked += 1
                continue

            target_without_fragment = strip_query_and_anchor(target)
            if not target_without_fragment:
                markdown_links_checked += 1
                continue

            resolved = (path.parent / target_without_fragment).resolve()
            if not resolved.exists():
                fail(f"missing Markdown link target in {rel(path)}: {target}")

            markdown_links_checked += 1

    return {
        "markdown_files_checked": markdown_files_checked,
        "markdown_links_checked": markdown_links_checked,
    }


def looks_like_plain_repository_path(value: str) -> bool:
    if not value.startswith(BACKTICK_PATH_PREFIXES):
        return False
    if any(marker in value for marker in (" ", "*", "://", "<", ">", "$", "|")):
        return False
    return True


def validate_backticked_repository_paths() -> dict[str, int]:
    repository_paths_checked = 0

    for path in iter_repository_files():
        if not is_markdown_file(path):
            continue

        text = path.read_text(encoding="utf-8")
        for match in BACKTICK_RE.finditer(text):
            value = match.group(1).strip()
            if not looks_like_plain_repository_path(value):
                continue

            repository_paths_checked += 1
            normalized = value.rstrip("/") if value.endswith("/") else value
            target = REPO_ROOT / normalized
            if not target.exists():
                fail(f"missing backticked repository path in {rel(path)}: {value}")
            if value.endswith("/") and not target.is_dir():
                fail(f"backticked repository directory is not a directory in {rel(path)}: {value}")

    return {"repository_paths_checked": repository_paths_checked}


def validate_project_requirements_structure() -> None:
    path = REPO_ROOT / "docs/PROJECT_REQUIREMENTS.md"
    text = path.read_text(encoding="utf-8")

    if "preserves the original assignment brief" not in text.splitlines()[0]:
        fail("docs/PROJECT_REQUIREMENTS.md missing preservation banner")

    if text.count("# Project 1: Prompting & RAG Foundations") != 1:
        fail("docs/PROJECT_REQUIREMENTS.md must contain exactly one assignment H1")

    required_literals = [
        "**Stack:**",
        "**Duration:**",
        "**Difficulty:**",
        "## Overview",
        "## What to Build",
        "## Milestones",
        "## Key Concepts to Understand",
        "## Acceptance Criteria",
        "## Common Pitfalls to Watch For",
        "## Stretch Goals",
        "## Resources",
        "## Practitioner Resources",
    ]
    for literal in required_literals:
        if literal not in text:
            fail(f"docs/PROJECT_REQUIREMENTS.md missing required section: {literal}")

    for milestone_number in range(1, 7):
        if f"### Milestone {milestone_number}" not in text:
            fail(f"docs/PROJECT_REQUIREMENTS.md missing Milestone {milestone_number}")

    acceptance_section = text.split("## Acceptance Criteria", 1)[1].split(
        "## Common Pitfalls to Watch For", 1
    )[0]
    checkbox_count = len(re.findall(r"(?m)^- \[[ xX]\] ", acceptance_section))
    if checkbox_count != 8:
        fail(
            "docs/PROJECT_REQUIREMENTS.md must contain eight "
            f"acceptance-criteria checkbox entries, found {checkbox_count}"
        )


def validate_no_empty_files() -> None:
    allowed_empty_files = {
        "data/evaluation/final_v2/grounded_results.jsonl",
        "data/evaluation/final_v2/tone_results.jsonl",
    }

    for path in iter_repository_files():
        if path.stat().st_size == 0 and rel(path) not in allowed_empty_files:
            fail(f"empty file: {rel(path)}")


def validate_references() -> dict[str, Any]:
    parsed = parse_json_files()

    validate_json_references()
    text_counts = validate_text_residue()
    link_counts = validate_markdown_links()
    path_counts = validate_backticked_repository_paths()
    validate_project_requirements_structure()
    validate_no_empty_files()

    return {
        "status": "ok",
        "json_or_jsonl_files": parsed,
        **text_counts,
        **link_counts,
        **path_counts,
    }


def main() -> int:
    result = validate_references()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
