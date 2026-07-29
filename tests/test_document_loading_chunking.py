from rag_foundations.chunking import ChunkingConfig, SimpleWhitespaceTokenizer, create_chunks
from rag_foundations.document_loader import load_documents


def test_all_five_documents_load_with_sections() -> None:
    documents = load_documents(minimum_sections=8)

    assert len(documents) == 5
    assert sum(len(document.sections) for document in documents) == 60
    assert all(document.title for document in documents)


def test_chunking_preserves_metadata_and_non_empty_text() -> None:
    documents = load_documents(minimum_sections=8)
    config = ChunkingConfig(chunk_size_tokens=80, chunk_overlap_tokens=20)

    chunks = create_chunks(documents, tokenizer=SimpleWhitespaceTokenizer(), config=config)

    assert chunks
    assert all(chunk.text.strip() for chunk in chunks)
    assert all(chunk.token_count > 0 for chunk in chunks)
    assert all(chunk.chunk_overlap_tokens < chunk.chunk_size_tokens for chunk in chunks)
    assert {chunk.document_id for chunk in chunks} == {
        "policy-employee-leave-v2-1",
        "policy-flexible-work-v2-1",
        "policy-information-security-v2-1",
        "policy-travel-expense-v2-1",
        "policy-code-conduct-v2-1",
    }
    assert all(chunk.source_path.startswith("data/documents_v2_1/") for chunk in chunks)


def test_chunk_ids_are_deterministic_across_runs() -> None:
    documents = load_documents(minimum_sections=8)
    config = ChunkingConfig(chunk_size_tokens=80, chunk_overlap_tokens=20)

    first = create_chunks(documents, tokenizer=SimpleWhitespaceTokenizer(), config=config)
    second = create_chunks(documents, tokenizer=SimpleWhitespaceTokenizer(), config=config)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_long_section_creates_multiple_chunks() -> None:
    documents = load_documents(minimum_sections=8)
    config = ChunkingConfig(chunk_size_tokens=45, chunk_overlap_tokens=10)

    chunks = create_chunks(documents[:1], tokenizer=SimpleWhitespaceTokenizer(), config=config)

    section_counts: dict[str, int] = {}
    for chunk in chunks:
        section_counts[chunk.section_heading] = section_counts.get(chunk.section_heading, 0) + 1

    assert max(section_counts.values()) > 1
