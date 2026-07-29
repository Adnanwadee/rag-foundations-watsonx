"""Build the persistent FAISS index with verified watsonx.ai embeddings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rag_foundations.chunking import (
    ChunkingConfig,
    MiniLMTokenizer,
    create_chunks,
    summarize_chunks,
)
from rag_foundations.document_loader import load_documents
from rag_foundations.faiss_store import (
    SIMILARITY_METRIC,
    WATSONX_EMBEDDING_DIMENSION,
    WATSONX_EMBEDDING_MODEL_ID,
    WATSONX_FAISS_DIR,
    build_faiss_index,
    index_config_for_chunks,
    load_faiss_store,
    metadata_records_for_chunks,
    save_faiss_store,
    validate_index_configuration,
)
from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider
from rag_foundations.watsonx_models import (
    create_runtime,
    get_embedding_model_specs,
    model_id,
    select_embedding_model,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTED_INDEX_DIR = REPO_ROOT / "data/indexes/selected"
MANIFEST_PATH = REPO_ROOT / "data/manifest_v2_1.json"


def assert_no_torch_path_imported() -> None:
    forbidden = ["torch"]
    imported = [name for name in forbidden if name in sys.modules]
    if imported:
        raise RuntimeError(f"Forbidden Torch/local embedding imports detected: {imported}")


def repository_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def validate_preflight_counts(summary: dict[str, int], chunk_count: int) -> None:
    if summary["documents_loaded"] != 5:
        raise RuntimeError(f"Expected 5 documents, got {summary['documents_loaded']}.")
    if summary["sections_loaded"] != 60:
        raise RuntimeError(f"Expected 60 sections, got {summary['sections_loaded']}.")
    if chunk_count != 70:
        raise RuntimeError(
            "Expected 70 deterministic chunks; got "
            f"{chunk_count} from {summary['sections_loaded']} represented sections."
        )


def validate_output_directory(output_dir: Path, *, overwrite: bool) -> Path:
    resolved = output_dir if output_dir.is_absolute() else REPO_ROOT / output_dir
    resolved = resolved.resolve()
    if resolved == SELECTED_INDEX_DIR.resolve() and not overwrite:
        raise FileExistsError(
            "data/indexes/selected is frozen evidence; pass --overwrite to replace it explicitly"
        )
    return resolved


def run_preflight(output_dir: Path) -> None:
    documents = load_documents(
        MANIFEST_PATH,
        repository_root=REPO_ROOT,
        minimum_sections=8,
    )
    document_count = len(documents)
    section_count = sum(len(document.sections) for document in documents)
    store = load_faiss_store(SELECTED_INDEX_DIR)
    validate_index_configuration(
        index=store.index,
        metadata=store.metadata,
        config=store.config,
        expected_embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
    )

    chunk_config = store.config.get("chunker_configuration", {})
    vector_count = int(store.config.get("vector_count", -1))
    metadata_count = len(store.metadata)
    embedding_dimension = int(store.config.get("embedding_dimension", -1))
    validate_preflight_counts(
        {"documents_loaded": document_count, "sections_loaded": section_count},
        metadata_count,
    )
    if vector_count != 70:
        raise RuntimeError(f"Expected selected vector_count 70, got {vector_count}.")
    if int(store.index.ntotal) != 70:
        raise RuntimeError(f"Expected selected FAISS vectors 70, got {store.index.ntotal}.")
    if embedding_dimension != WATSONX_EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected embedding dimension {WATSONX_EMBEDDING_DIMENSION}, "
            f"got {embedding_dimension}."
        )
    if int(chunk_config.get("chunk_size_tokens", -1)) != 220:
        raise RuntimeError("Expected selected chunk_size_tokens 220.")
    if int(chunk_config.get("chunk_overlap_tokens", -1)) != 40:
        raise RuntimeError("Expected selected chunk_overlap_tokens 40.")
    if any(record.get("embedding_model_id") != WATSONX_EMBEDDING_MODEL_ID for record in store.metadata):
        raise RuntimeError("Selected metadata embedding model does not match expected model.")
    if any(int(record.get("embedding_dimension", -1)) != WATSONX_EMBEDDING_DIMENSION for record in store.metadata):
        raise RuntimeError("Selected metadata embedding dimension does not match expected dimension.")

    print("Preflight status: ok")
    print(f"Manifest path: {repository_relative(MANIFEST_PATH)}")
    print(f"Documents loaded: {document_count}")
    print(f"Sections loaded: {section_count}")
    print(f"Selected index directory: {repository_relative(SELECTED_INDEX_DIR)}")
    print(f"Selected vectors: {int(store.index.ntotal)}")
    print(f"Selected metadata records: {metadata_count}")
    print(f"Selected chunk size tokens: {int(chunk_config['chunk_size_tokens'])}")
    print(f"Selected chunk overlap tokens: {int(chunk_config['chunk_overlap_tokens'])}")
    print(f"Selected vector count: {vector_count}")
    print(f"Embedding model: {store.config['embedding_model_id']}")
    print(f"Embedding dimension: {embedding_dimension}")
    print("External calls: 0")
    print("Files written: 0")
    print(f"Output directory: {repository_relative(output_dir)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the watsonx.ai FAISS index.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=WATSONX_FAISS_DIR,
        help="Directory for rebuilt index artifacts; defaults to ignored artifacts/rebuilt-index/.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files.")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate local corpus/chunk counts without watsonx.ai calls or index writes.",
    )
    args = parser.parse_args()
    output_dir = validate_output_directory(args.output_dir, overwrite=args.overwrite)

    assert_no_torch_path_imported()
    if args.preflight_only:
        run_preflight(output_dir)
        assert_no_torch_path_imported()
        return

    runtime = create_runtime()
    embedding_spec = select_embedding_model(get_embedding_model_specs(runtime.client))
    discovered_embedding_model_id = model_id(embedding_spec)
    if discovered_embedding_model_id != WATSONX_EMBEDDING_MODEL_ID:
        raise RuntimeError(
            "Discovered embedding model does not match the verified project embedding model: "
            f"{discovered_embedding_model_id}"
        )
    assert_no_torch_path_imported()

    documents = load_documents(MANIFEST_PATH, repository_root=REPO_ROOT, minimum_sections=8)
    tokenizer = MiniLMTokenizer()
    chunks = create_chunks(documents, tokenizer=tokenizer, config=ChunkingConfig())
    summary = summarize_chunks(documents, chunks)
    assert_no_torch_path_imported()

    validate_preflight_counts(summary, len(chunks))
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
    if any(len(vector) != WATSONX_EMBEDDING_DIMENSION for vector in embeddings):
        raise RuntimeError("Every embedding vector must have 768 dimensions.")
    assert_no_torch_path_imported()

    metadata = metadata_records_for_chunks(
        chunks,
        embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
        embedding_dimension=WATSONX_EMBEDDING_DIMENSION,
    )
    for record in metadata:
        record["source_path"] = Path(record["source_path"]).as_posix()
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
        directory=output_dir,
        overwrite=args.overwrite,
    )

    reloaded = load_faiss_store(output_dir)
    if reloaded.index.ntotal != 70:
        raise RuntimeError(f"Expected reloaded index.ntotal 70, got {reloaded.index.ntotal}.")
    if len(reloaded.metadata) != 70:
        raise RuntimeError(f"Expected reloaded metadata count 70, got {len(reloaded.metadata)}.")

    print("Documents indexed: 5")
    print("Sections loaded: 60")
    print("Chunks indexed: 70")
    print(f"Embedding model: {WATSONX_EMBEDDING_MODEL_ID}")
    print(f"Embedding dimension: {WATSONX_EMBEDDING_DIMENSION}")
    print("FAISS index type: IndexFlatIP")
    print(f"Similarity: {SIMILARITY_METRIC.replace('_', ' ')}")
    print(f"Output directory: {repository_relative(output_dir)}")
    print(f"Index path: {repository_relative(output_dir / 'asteron_policies_watsonx.index')}")
    print(f"Metadata path: {repository_relative(output_dir / 'metadata.json')}")
    assert_no_torch_path_imported()


if __name__ == "__main__":
    main()
