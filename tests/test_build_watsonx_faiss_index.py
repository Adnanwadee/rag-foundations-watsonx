from __future__ import annotations

import os
import subprocess
import sys
import hashlib
from pathlib import Path

import pytest

from scripts import build_watsonx_faiss_index as builder

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/build_watsonx_faiss_index.py"
SELECTED_FILES = [
    REPO_ROOT / "data/indexes/selected/asteron_policies_watsonx.index",
    REPO_ROOT / "data/indexes/selected/metadata.json",
    REPO_ROOT / "data/indexes/selected/index_config.json",
]


def file_hashes(paths: list[Path]) -> dict[Path, str]:
    return {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def test_index_builder_preflight_requires_five_sixty_seventy() -> None:
    builder.validate_preflight_counts({"documents_loaded": 5, "sections_loaded": 60}, 70)

    with pytest.raises(RuntimeError, match="Expected 60 sections"):
        builder.validate_preflight_counts({"documents_loaded": 5, "sections_loaded": 70}, 70)

    with pytest.raises(RuntimeError, match="Expected 70 deterministic chunks"):
        builder.validate_preflight_counts({"documents_loaded": 5, "sections_loaded": 60}, 69)


def test_index_builder_rejects_selected_output_without_overwrite() -> None:
    with pytest.raises(FileExistsError, match="frozen evidence"):
        builder.validate_output_directory(Path("data/indexes/selected"), overwrite=False)


def test_index_builder_allows_selected_output_with_explicit_overwrite() -> None:
    assert builder.validate_output_directory(
        Path("data/indexes/selected"),
        overwrite=True,
    ).is_absolute()


def test_index_builder_default_output_is_not_selected_index() -> None:
    assert builder.WATSONX_FAISS_DIR.as_posix() == "artifacts/rebuilt-index"
    assert builder.WATSONX_FAISS_DIR != Path("data/indexes/selected")


def test_index_builder_entrypoint_constants_are_initialized() -> None:
    assert builder.REPO_ROOT.is_dir()
    assert builder.SELECTED_INDEX_DIR == builder.REPO_ROOT / "data/indexes/selected"


def test_index_builder_direct_preflight_entrypoint_is_offline(tmp_path: Path) -> None:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = (
        src_path if not env.get("PYTHONPATH") else os.pathsep.join([src_path, env["PYTHONPATH"]])
    )
    for name in ("WATSONX_URL", "WATSONX_PROJECT_ID", "WATSONX_API_KEY"):
        env.pop(name, None)
    env["HF_HUB_OFFLINE"] = "1"
    output_dir = tmp_path / "rebuilt-index"
    before = file_hashes(SELECTED_FILES)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--preflight-only",
            "--output-dir",
            str(output_dir),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Preflight status: ok" in result.stdout
    assert "Documents loaded: 5" in result.stdout
    assert "Sections loaded: 60" in result.stdout
    assert "Selected vectors: 70" in result.stdout
    assert "Selected metadata records: 70" in result.stdout
    assert "Selected chunk size tokens: 220" in result.stdout
    assert "Selected chunk overlap tokens: 40" in result.stdout
    assert "Selected vector count: 70" in result.stdout
    assert "Embedding dimension: 768" in result.stdout
    assert "External calls: 0" in result.stdout
    assert "Files written: 0" in result.stdout
    assert not output_dir.exists()
    assert file_hashes(SELECTED_FILES) == before
