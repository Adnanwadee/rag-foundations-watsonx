from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import validate_references

SECRET_ASSIGNMENT = "WATSONX_" + "API_KEY=" + '"{value}"\n'


def set_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_references, "REPO_ROOT", tmp_path)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def complete_assignment_brief() -> str:
    checkboxes = "\n".join(f"- [ ] Criterion {number}" for number in range(1, 9))
    milestones = "\n".join(f"### Milestone {number}\n- Work" for number in range(1, 7))
    return f"""This file preserves the original assignment brief.

# Project 1: Prompting & RAG Foundations

**Stack:** watsonx.ai
**Duration:** 6 days
**Difficulty:** Tier 1 - Foundation

## Overview
Text.

## What to Build
Text.

## Milestones
{milestones}

## Key Concepts to Understand
Text.

## Acceptance Criteria
### The system must:
{checkboxes}

## Common Pitfalls to Watch For
Text.

## Stretch Goals
Text.

## Resources
Text.

## Practitioner Resources
Text.
"""


def test_reference_validator_skips_only_repository_root_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(
        tmp_path / ".env",
        SECRET_ASSIGNMENT.format(value="root-secret-value"),
    )

    validate_references.validate_text_residue()


def test_reference_validator_scans_nested_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(
        tmp_path / "nested" / ".env",
        SECRET_ASSIGNMENT.format(value="nested-secret-value"),
    )

    with pytest.raises(ValueError, match="possible credential in nested/.env"):
        validate_references.validate_text_residue()


def test_reference_validator_scans_env_example(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(
        tmp_path / ".env.example",
        SECRET_ASSIGNMENT.format(value="example-secret-value"),
    )

    with pytest.raises(ValueError, match="possible credential in .env.example"):
        validate_references.validate_text_residue()


def test_env_example_rejects_real_credential_like_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(
        tmp_path / ".env.example",
        "WATSONX_API_KEY=abcd1234efgh5678ijkl\n",
    )

    with pytest.raises(ValueError, match="possible credential in .env.example"):
        validate_references.validate_text_residue()


def test_safe_angle_bracket_placeholder_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / ".env.example", "WATSONX_API_KEY=<your-ibm-cloud-api-key>\n")

    validate_references.validate_text_residue()


def test_safe_variable_placeholder_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / ".env.example", "WATSONX_API_KEY=${WATSONX_API_KEY}\n")

    validate_references.validate_text_residue()


def test_windows_absolute_path_in_markdown_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    windows_path = "C:" + r"\Users\name\repo"
    write(tmp_path / "README.md", f"Use {windows_path}.")

    with pytest.raises(ValueError, match="absolute/personal path in README.md"):
        validate_references.validate_text_residue()


def test_unix_personal_absolute_path_in_markdown_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "docs" / "EVALUATION_METHOD.md", "Use /home/name/repo.")

    with pytest.raises(
        ValueError,
        match="absolute/personal path in docs/EVALUATION_METHOD.md",
    ):
        validate_references.validate_text_residue()


def test_missing_relative_markdown_link_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "[Missing](docs/MISSING.md)\n")

    with pytest.raises(ValueError, match="missing Markdown link target in README.md"):
        validate_references.validate_markdown_links()


def test_valid_relative_markdown_link_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "[Architecture](docs/ARCHITECTURE.md)\n")
    write(tmp_path / "docs" / "ARCHITECTURE.md", "# Architecture\n")

    validate_references.validate_markdown_links()


def test_pure_markdown_anchor_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "[Section](#section)\n")

    validate_references.validate_markdown_links()


def test_external_https_link_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "[IBM](https://www.ibm.com/docs)\n")

    validate_references.validate_markdown_links()


def test_missing_backticked_src_path_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "`src/rag_foundations/missing.py`\n")

    with pytest.raises(ValueError, match="missing backticked repository path in README.md"):
        validate_references.validate_backticked_repository_paths()


def test_valid_backticked_repository_path_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "`src/rag_foundations/cli.py`\n")
    write(tmp_path / "src" / "rag_foundations" / "cli.py", "")

    validate_references.validate_backticked_repository_paths()


def test_backticked_command_with_spaces_is_not_treated_as_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "`src/rag_foundations/missing.py --help`\n")

    validate_references.validate_backticked_repository_paths()


def test_reference_to_deleted_documentation_validator_script_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    deleted_script = "validate_" + "documentation.py"
    write(tmp_path / "docs" / "LIVE_SMOKE_TEST.md", f"python scripts/{deleted_script}\n")

    with pytest.raises(
        ValueError,
        match="forbidden public reference in docs/LIVE_SMOKE_TEST.md",
    ):
        validate_references.validate_text_residue()


def test_duplicate_project_requirements_h1_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(
        tmp_path / "docs" / "PROJECT_REQUIREMENTS.md",
        complete_assignment_brief() + "\n# Project 1: Prompting & RAG Foundations\n",
    )

    with pytest.raises(ValueError, match="exactly one assignment H1"):
        validate_references.validate_project_requirements_structure()


def test_one_complete_assignment_brief_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "docs" / "PROJECT_REQUIREMENTS.md", complete_assignment_brief())

    validate_references.validate_project_requirements_structure()


def test_allowed_directory_path_ending_in_slash_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "README.md", "`docs/`\n")
    (tmp_path / "docs").mkdir()

    validate_references.validate_backticked_repository_paths()


def test_json_and_jsonl_parsing_behavior_remains_intact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_repo_root(tmp_path, monkeypatch)
    write(tmp_path / "valid.json", '{"status": "ok"}\n')
    write(tmp_path / "valid.jsonl", '{"row": 1}\n\n{"row": 2}\n')

    assert validate_references.parse_json_files() == 2

    write(tmp_path / "invalid.jsonl", '{"row":\n')
    with pytest.raises(ValueError, match="invalid JSONL invalid.jsonl:1"):
        validate_references.parse_json_files()


def test_root_env_is_not_tracked() -> None:
    if not Path(".git").exists():
        assert not Path(".env").exists()
        return

    result = subprocess.run(
        ["git", "ls-files", ".env"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout == ""
