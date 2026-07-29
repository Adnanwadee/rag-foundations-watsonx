from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import build_watsonx_faiss_index as builder


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
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = (
        src_path if not env.get("PYTHONPATH") else os.pathsep.join([src_path, env["PYTHONPATH"]])
    )
    output_dir = tmp_path / "rebuilt-index"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_watsonx_faiss_index.py",
            "--preflight-only",
            "--output-dir",
            str(output_dir),
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Preflight status: ok" in result.stdout
    assert "External calls: 0" in result.stdout
    assert not (output_dir / "asteron_policies_watsonx.index").exists()
