from pathlib import Path

import pytest

from rag_foundations.faiss_store import (
    WATSONX_EMBEDDING_DIMENSION,
    WATSONX_EMBEDDING_MODEL_ID,
    WATSONX_FAISS_DIR,
    build_faiss_index,
    index_config_for_chunks,
    load_faiss_store,
    metadata_records_for_chunks,
    save_faiss_store,
    search_faiss_store,
    validate_query_text,
)
from rag_foundations.schemas import DocumentChunk, RetrievedChunk


def _vector(active_index: int) -> list[float]:
    vector = [0.0] * WATSONX_EMBEDDING_DIMENSION
    vector[active_index] = 1.0
    return vector


def _chunk(chunk_index: int, *, chunk_id: str | None = None) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id or f"chunk-{chunk_index}",
        document_id="policy-remote-work",
        corpus_version="asteron-policies-v1",
        chunker_config_id="section-token-v1-size-220-overlap-40-minilm",
        chunk_size_tokens=220,
        chunk_overlap_tokens=40,
        token_counting_method="test-tokenizer",
        chunk_index=chunk_index,
        text=f"Chunk text {chunk_index}",
        title="Remote Work Policy",
        section_heading="Maximum Remote Days and Office Attendance",
        source_path="data/documents_v2_1/flexible_work_workplace_access_policy.md",
        token_count=3,
        checksum=f"checksum-{chunk_index}",
    )


def _store(tmp_path: Path, vectors: list[list[float]] | None = None):
    chunks = [_chunk(0), _chunk(1)]
    metadata = metadata_records_for_chunks(
        chunks,
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
    )
    index = build_faiss_index(vectors or [_vector(0), _vector(1)], metadata)
    config = index_config_for_chunks(
        chunks,
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
        vector_count=len(chunks),
    )
    save_faiss_store(
        index=index,
        metadata=metadata,
        config=config,
        directory=tmp_path / "faiss",
        overwrite=True,
    )
    return load_faiss_store(tmp_path / "faiss")


def test_build_save_and_reload_small_temporary_faiss_index(tmp_path: Path) -> None:
    store = _store(tmp_path)

    assert store.index.ntotal == 2
    assert len(store.metadata) == 2


def test_reload_preserves_metadata_order(tmp_path: Path) -> None:
    store = _store(tmp_path)

    assert [record["chunk_id"] for record in store.metadata] == ["chunk-0", "chunk-1"]
    assert [record["faiss_position"] for record in store.metadata] == [0, 1]


def test_cosine_search_ranks_expected_vector_first(tmp_path: Path) -> None:
    store = _store(tmp_path)

    results = search_faiss_store(store, _vector(1), top_k=2)

    assert results[0].chunk_id == "chunk-1"
    assert results[0].raw_score == pytest.approx(1.0)


def test_top_k_is_respected(tmp_path: Path) -> None:
    store = _store(tmp_path)

    results = search_faiss_store(store, _vector(0), top_k=1)

    assert len(results) == 1


def test_dimension_mismatch_fails() -> None:
    chunks = [_chunk(0)]
    metadata = metadata_records_for_chunks(
        chunks,
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
    )

    with pytest.raises(ValueError, match="expected embedding dimension"):
        build_faiss_index([[1.0, 0.0]], metadata)


def test_vector_metadata_count_mismatch_fails() -> None:
    metadata = metadata_records_for_chunks(
        [_chunk(0), _chunk(1)],
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
    )

    with pytest.raises(ValueError, match="counts must match"):
        build_faiss_index([_vector(0)], metadata)


def test_blank_query_fails() -> None:
    with pytest.raises(ValueError, match="question must not be blank"):
        validate_query_text(" ")


def test_returned_results_validate_as_retrieved_chunks(tmp_path: Path) -> None:
    store = _store(tmp_path)

    results = search_faiss_store(store, _vector(0), top_k=1)

    assert isinstance(results[0], RetrievedChunk)
    assert results[0].score_type == "cosine_similarity"


def test_save_uses_temporary_directory_not_real_data_faiss(tmp_path: Path) -> None:
    store = _store(tmp_path)

    assert store.index_path.is_relative_to(tmp_path)
    assert not store.index_path.is_relative_to(Path.cwd() / WATSONX_FAISS_DIR)
