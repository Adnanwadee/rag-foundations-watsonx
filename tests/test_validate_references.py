from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import validate_references

SECRET_ASSIGNMENT = "WATSONX_" + "API_KEY=" + '"{value}"\n'


def test_reference_validator_skips_only_repository_root_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(validate_references, "REPO_ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        SECRET_ASSIGNMENT.format(value="root-secret-value"),
        encoding="utf-8",
    )

    validate_references.validate_text_residue()


def test_reference_validator_scans_nested_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(validate_references, "REPO_ROOT", tmp_path)
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".env").write_text(
        SECRET_ASSIGNMENT.format(value="nested-secret-value"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="possible credential in nested/.env"):
        validate_references.validate_text_residue()


def test_reference_validator_scans_env_example(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(validate_references, "REPO_ROOT", tmp_path)
    (tmp_path / ".env.example").write_text(
        SECRET_ASSIGNMENT.format(value="example-secret-value"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="possible credential in .env.example"):
        validate_references.validate_text_residue()


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
