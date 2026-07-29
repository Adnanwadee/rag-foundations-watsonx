"""Minimal persistent FAISS store for watsonx.ai embeddings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from rag_foundations.schemas import DocumentChunk, RetrievedChunk, ScoreType


WATSONX_FAISS_DIR = Path("artifacts/rebuilt-index")
SELECTED_FAISS_DIR = Path("data/indexes/selected")
WATSONX_FAISS_INDEX_PATH = WATSONX_FAISS_DIR / "asteron_policies_watsonx.index"
WATSONX_FAISS_METADATA_PATH = WATSONX_FAISS_DIR / "metadata.json"
WATSONX_FAISS_CONFIG_PATH = WATSONX_FAISS_DIR / "index_config.json"
WATSONX_FAISS_INDEX_ID = "asteron_policies_watsonx_faiss_v1"
WATSONX_EMBEDDING_MODEL_ID = "ibm/granite-embedding-278m-multilingual"
WATSONX_EMBEDDING_DIMENSION = 768
SIMILARITY_METRIC = "cosine_similarity"
FAISS_INDEX_VERSION = "faiss-flat-ip-v1"
FAISS_RETRIEVER_NAME = "faiss-watsonx-flat-ip-retriever"


@dataclass(frozen=True)
class LoadedFaissStore:
    """Loaded FAISS index plus persisted metadata and config."""

    index: Any
    metadata: list[dict[str, Any]]
    config: dict[str, Any]
    index_path: Path
    metadata_path: Path
    config_path: Path


def _require_faiss() -> Any:
    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError("faiss-cpu is required for the FAISS retrieval baseline.") from exc
    return faiss


def validate_query_text(question: str) -> str:
    """Validate query text before embedding."""

    if not question.strip():
        raise ValueError("question must not be blank")
    return question


def vectors_to_float32_matrix(
    vectors: list[list[float]],
    *,
    expected_dimension: int = WATSONX_EMBEDDING_DIMENSION,
) -> np.ndarray:
    """Validate vectors and return a contiguous float32 matrix."""

    if not vectors:
        raise ValueError("vectors must not be empty")
    first_dimension = len(vectors[0])
    if first_dimension <= 0:
        raise ValueError("vectors must not contain zero-length vectors")
    if first_dimension != expected_dimension:
        raise ValueError(
            f"expected embedding dimension {expected_dimension}, got {first_dimension}"
        )
    for vector in vectors:
        if len(vector) == 0:
            raise ValueError("vectors must not contain zero-length vectors")
        if len(vector) != first_dimension:
            raise ValueError("vectors must have consistent embedding dimensions")

    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError("vectors must form a 2D matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("vectors must contain only finite values")
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms == 0):
        raise ValueError("vectors must not contain zero-norm vectors")
    return np.ascontiguousarray(matrix, dtype=np.float32)


def l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """Return a contiguous L2-normalized float32 matrix."""

    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("matrix must be non-empty and two-dimensional")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("vectors must not contain zero-norm vectors")
    normalized = matrix / norms
    return np.ascontiguousarray(normalized, dtype=np.float32)


def metadata_records_for_chunks(
    chunks: list[DocumentChunk],
    *,
    embedding_model_id: str,
    embedding_dimension: int,
    index_id: str = WATSONX_FAISS_INDEX_ID,
) -> list[dict[str, Any]]:
    """Build deterministic FAISS metadata records from chunks."""

    if not chunks:
        raise ValueError("chunks must not be empty")

    records: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    for position, chunk in enumerate(chunks):
        if chunk.chunk_id in seen_chunk_ids:
            raise ValueError(f"duplicate chunk_id: {chunk.chunk_id}")
        seen_chunk_ids.add(chunk.chunk_id)
        records.append(
            {
                "faiss_position": position,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_title": chunk.title,
                "section_heading": chunk.section_heading,
                "source_path": chunk.source_path,
                "corpus_version": chunk.corpus_version,
                "chunker_config_id": chunk.chunker_config_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "text": chunk.text,
                "checksum": chunk.checksum,
                "embedding_model_id": embedding_model_id,
                "embedding_dimension": embedding_dimension,
                "index_id": index_id,
            }
        )
    return records


def validate_metadata_records(metadata: list[dict[str, Any]]) -> None:
    """Validate metadata order and uniqueness."""

    if not metadata:
        raise ValueError("metadata must not be empty")
    seen_chunk_ids: set[str] = set()
    for position, record in enumerate(metadata):
        if int(record.get("faiss_position", -1)) != position:
            raise ValueError("metadata faiss_position values must be sequential")
        chunk_id = str(record.get("chunk_id", ""))
        if not chunk_id:
            raise ValueError("metadata records require chunk_id")
        if chunk_id in seen_chunk_ids:
            raise ValueError(f"duplicate chunk_id: {chunk_id}")
        seen_chunk_ids.add(chunk_id)
        if not str(record.get("text", "")).strip():
            raise ValueError("metadata records require chunk text")


def build_faiss_index(
    vectors: list[list[float]],
    metadata: list[dict[str, Any]],
    *,
    expected_dimension: int = WATSONX_EMBEDDING_DIMENSION,
) -> Any:
    """Build an exact IndexFlatIP index with L2-normalized vectors."""

    if len(vectors) != len(metadata):
        raise ValueError("vector and metadata counts must match")
    validate_metadata_records(metadata)
    matrix = vectors_to_float32_matrix(vectors, expected_dimension=expected_dimension)
    normalized = l2_normalize(matrix)
    faiss = _require_faiss()
    index = faiss.IndexFlatIP(expected_dimension)
    index.add(normalized)
    if index.ntotal != len(metadata):
        raise RuntimeError(f"expected index.ntotal {len(metadata)}, got {index.ntotal}")
    return index


def index_config_for_chunks(
    chunks: list[DocumentChunk],
    *,
    embedding_model_id: str,
    embedding_dimension: int,
    vector_count: int,
    index_id: str = WATSONX_FAISS_INDEX_ID,
) -> dict[str, Any]:
    """Create persisted FAISS index configuration."""

    if not chunks:
        raise ValueError("chunks must not be empty")
    first = chunks[0]
    return {
        "index_id": index_id,
        "index_version": FAISS_INDEX_VERSION,
        "corpus_version": first.corpus_version,
        "embedding_model_id": embedding_model_id,
        "embedding_dimension": embedding_dimension,
        "similarity_metric": SIMILARITY_METRIC,
        "vector_count": vector_count,
        "creation_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chunker_configuration": {
            "chunker_config_id": first.chunker_config_id,
            "chunk_size_tokens": first.chunk_size_tokens,
            "chunk_overlap_tokens": first.chunk_overlap_tokens,
            "token_counting_method": first.token_counting_method,
        },
    }


def validate_index_configuration(
    *,
    index: Any,
    metadata: list[dict[str, Any]],
    config: dict[str, Any],
    expected_embedding_model_id: str | None = None,
) -> None:
    """Validate loaded index, metadata, and config agree."""

    validate_metadata_records(metadata)
    vector_count = int(config.get("vector_count", -1))
    embedding_dimension = int(config.get("embedding_dimension", -1))
    if vector_count != len(metadata):
        raise ValueError("config vector_count must match metadata count")
    if int(index.ntotal) != vector_count:
        raise ValueError("FAISS index vector count must match config vector_count")
    if int(index.d) != embedding_dimension:
        raise ValueError("FAISS index dimension must match config embedding_dimension")
    if embedding_dimension != WATSONX_EMBEDDING_DIMENSION:
        raise ValueError(
            f"expected embedding dimension {WATSONX_EMBEDDING_DIMENSION}, got {embedding_dimension}"
        )
    if config.get("similarity_metric") != SIMILARITY_METRIC:
        raise ValueError("FAISS index must use cosine similarity")
    if expected_embedding_model_id and config.get("embedding_model_id") != expected_embedding_model_id:
        raise ValueError("configured embedding model does not match expected embedding model")


def save_faiss_store(
    *,
    index: Any,
    metadata: list[dict[str, Any]],
    config: dict[str, Any],
    directory: Path | str = WATSONX_FAISS_DIR,
    overwrite: bool = False,
) -> None:
    """Persist the FAISS index, metadata, and config."""

    directory_path = Path(directory)
    if directory_path.as_posix().rstrip("/") == SELECTED_FAISS_DIR.as_posix() and not overwrite:
        raise FileExistsError("selected frozen FAISS index is protected; pass overwrite=True explicitly")
    index_path = directory_path / WATSONX_FAISS_INDEX_PATH.name
    metadata_path = directory_path / WATSONX_FAISS_METADATA_PATH.name
    config_path = directory_path / WATSONX_FAISS_CONFIG_PATH.name

    existing = [path for path in (index_path, metadata_path, config_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("FAISS index files already exist; use rebuild to overwrite")
    directory_path.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for path in existing:
            path.unlink()

    validate_index_configuration(index=index, metadata=metadata, config=config)
    faiss = _require_faiss()
    faiss.write_index(index, str(index_path))
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_faiss_store(directory: Path | str = WATSONX_FAISS_DIR) -> LoadedFaissStore:
    """Load a persisted FAISS store and validate internal consistency."""

    directory_path = Path(directory)
    index_path = directory_path / WATSONX_FAISS_INDEX_PATH.name
    metadata_path = directory_path / WATSONX_FAISS_METADATA_PATH.name
    config_path = directory_path / WATSONX_FAISS_CONFIG_PATH.name
    faiss = _require_faiss()
    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, list):
        raise ValueError("metadata.json must contain a list")
    if not isinstance(config, dict):
        raise ValueError("index_config.json must contain an object")
    validate_index_configuration(index=index, metadata=metadata, config=config)
    return LoadedFaissStore(
        index=index,
        metadata=metadata,
        config=config,
        index_path=index_path,
        metadata_path=metadata_path,
        config_path=config_path,
    )


def search_faiss_store(
    store: LoadedFaissStore,
    query_vector: list[float],
    *,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Search FAISS and map positions to RetrievedChunk contracts."""

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    matrix = vectors_to_float32_matrix(
        [query_vector],
        expected_dimension=int(store.config["embedding_dimension"]),
    )
    normalized = l2_normalize(matrix)
    limit = min(top_k, int(store.index.ntotal))
    scores, positions = store.index.search(normalized, limit)

    results: list[RetrievedChunk] = []
    for rank, (score, position) in enumerate(zip(scores[0], positions[0]), start=1):
        if int(position) < 0:
            continue
        record = store.metadata[int(position)]
        results.append(
            RetrievedChunk(
                chunk_id=str(record["chunk_id"]),
                document_id=str(record["document_id"]),
                corpus_version=str(record["corpus_version"]),
                chunker_config_id=str(record["chunker_config_id"]),
                embedding_model_id=str(store.config["embedding_model_id"]),
                embedding_dimension=int(store.config["embedding_dimension"]),
                index_id=str(store.config["index_id"]),
                rank=rank,
                raw_score=float(score),
                score_type=ScoreType.COSINE_SIMILARITY,
                text=str(record["text"]),
                title=str(record["document_title"]),
                section_heading=str(record["section_heading"]),
                source_path=str(record["source_path"]),
                retriever_name=FAISS_RETRIEVER_NAME,
                retriever_config={
                    "top_k": top_k,
                    "index_path": store.index_path.as_posix(),
                    "similarity_metric": SIMILARITY_METRIC,
                },
            )
        )
    return results
