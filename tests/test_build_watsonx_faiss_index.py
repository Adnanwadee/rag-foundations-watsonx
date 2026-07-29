from __future__ import annotations

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
