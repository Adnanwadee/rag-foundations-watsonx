"""Build the persistent FAISS index with verified watsonx.ai embeddings."""

from __future__ import annotations

import argparse
import sys

from rag_foundations.chunking import ChunkingConfig, MiniLMTokenizer, create_chunks, summarize_chunks
from rag_foundations.document_loader import load_documents
from rag_foundations.faiss_store import (
    SIMILARITY_METRIC,
    WATSONX_EMBEDDING_DIMENSION,
    WATSONX_EMBEDDING_MODEL_ID,
    WATSONX_FAISS_DIR,
    WATSONX_FAISS_INDEX_PATH,
    WATSONX_FAISS_METADATA_PATH,
    build_faiss_index,
    index_config_for_chunks,
    load_faiss_store,
    metadata_records_for_chunks,
    save_faiss_store,
)
from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider
from rag_foundations.watsonx_models import (
    create_runtime,
    get_embedding_model_specs,
    model_id,
    select_embedding_model,
)


def assert_no_torch_path_imported() -> None:
    forbidden = ["torch"]
    imported = [name for name in forbidden if name in sys.modules]
    if imported:
        raise RuntimeError(f"Forbidden Torch/local embedding imports detected: {imported}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the watsonx.ai FAISS index.")
    parser.add_argument("--rebuild", action="store_true", help="Replace existing FAISS index files.")
    args = parser.parse_args()

    assert_no_torch_path_imported()
    runtime = create_runtime()
    embedding_spec = select_embedding_model(get_embedding_model_specs(runtime.client))
    discovered_embedding_model_id = model_id(embedding_spec)
    if discovered_embedding_model_id != WATSONX_EMBEDDING_MODEL_ID:
        raise RuntimeError(
            "Discovered embedding model does not match the verified project embedding model: "
            f"{discovered_embedding_model_id}"
        )
    assert_no_torch_path_imported()

    documents = load_documents(minimum_sections=8)
    tokenizer = MiniLMTokenizer()
    chunks = create_chunks(documents, tokenizer=tokenizer, config=ChunkingConfig())
    summary = summarize_chunks(documents, chunks)
    assert_no_torch_path_imported()

    if summary["documents_loaded"] != 5:
        raise RuntimeError(f"Expected 5 documents, got {summary['documents_loaded']}.")
    if summary["sections_loaded"] != 70:
        raise RuntimeError(f"Expected 70 sections, got {summary['sections_loaded']}.")
    if len(chunks) != 70:
        raise RuntimeError(
            "Expected 70 deterministic chunks; got "
            f"{len(chunks)} from {summary['sections_loaded']} represented sections."
        )
    if any(not chunk.text.strip() for chunk in chunks):
        raise RuntimeError("All chunk texts must be non-empty.")
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise RuntimeError("Chunk IDs must be unique.")

    provider = WatsonxEmbeddingProvider(
        model_id=WATSONX_EMBEDDING_MODEL_ID,
        api_client=runtime.client,
    )
    embeddings = provider.embed_documents([chunk.text for chunk in chunks])
    if len(embeddings) != len(chunks):
        raise RuntimeError(f"Expected {len(chunks)} embedding vectors, got {len(embeddings)}.")
    if provider.embedding_dimension != WATSONX_EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected embedding dimension {WATSONX_EMBEDDING_DIMENSION}, "
            f"got {provider.embedding_dimension}."
        )
    assert_no_torch_path_imported()

    metadata = metadata_records_for_chunks(
        chunks,
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
    )
    index = build_faiss_index(
        embeddings,
        metadata,
        expected_dimension=WATSONX_EMBEDDING_DIMENSION,
    )
    if index.ntotal != 70:
        raise RuntimeError(f"Expected index.ntotal 70, got {index.ntotal}.")
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
        directory=WATSONX_FAISS_DIR,
        overwrite=args.rebuild,
    )

    reloaded = load_faiss_store(WATSONX_FAISS_DIR)
    if reloaded.index.ntotal != 70:
        raise RuntimeError(f"Expected reloaded index.ntotal 70, got {reloaded.index.ntotal}.")
    if len(reloaded.metadata) != 70:
        raise RuntimeError(f"Expected reloaded metadata count 70, got {len(reloaded.metadata)}.")

    print("Documents indexed: 5")
    print("Sections represented: 70")
    print("Chunks indexed: 70")
    print(f"Embedding model: {WATSONX_EMBEDDING_MODEL_ID}")
    print(f"Embedding dimension: {WATSONX_EMBEDDING_DIMENSION}")
    print("FAISS index type: IndexFlatIP")
    print(f"Similarity: {SIMILARITY_METRIC.replace('_', ' ')}")
    print(f"Index path: {WATSONX_FAISS_INDEX_PATH.as_posix()}")
    print(f"Metadata path: {WATSONX_FAISS_METADATA_PATH.as_posix()}")
    assert_no_torch_path_imported()


if __name__ == "__main__":
    main()
