import pytest
from pydantic import ValidationError

from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.schemas import (
    AllToneResult,
    Citation,
    DocumentChunk,
    DocumentMetadata,
    GroundedAnswerResult,
    GroundedModelOutput,
    RetrievedChunk,
    ScoreType,
    ToneModelOutput,
    ToneName,
    ToneResult,
)


def valid_citation(**overrides: object) -> Citation:
    data = {
        "citation_id": "citation-1",
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "title": "Policy",
        "section_heading": "Eligibility",
        "source_path": "docs/policies/policy.md",
    }
    data.update(overrides)
    return Citation(**data)


def valid_chunk(**overrides: object) -> DocumentChunk:
    data = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "corpus_version": "corpus-v1",
        "chunker_config_id": "chunker-v1",
        "chunk_size_tokens": 200,
        "chunk_overlap_tokens": 20,
        "token_counting_method": "verified-tokenizer",
        "chunk_index": 0,
        "text": "Employees receive ten days of paid leave.",
        "title": "Employee Leave Policy",
        "section_heading": "Paid Leave",
        "source_path": "docs/policies/employee-leave.md",
        "token_count": 9,
        "checksum": "abc123",
    }
    data.update(overrides)
    return DocumentChunk(**data)


def test_document_metadata_accepts_valid_repository_relative_path() -> None:
    metadata = DocumentMetadata(
        document_id="doc-1",
        source_path="docs/policies/policy.md",
        title="Policy",
        document_type="policy",
        version="1.0",
        corpus_version="corpus-v1",
        owner="HR",
        checksum="abc123",
    )

    assert metadata.source_path == "docs/policies/policy.md"


def test_document_metadata_accepts_required_example_path() -> None:
    metadata = DocumentMetadata(
        document_id="doc-1",
        source_path="data/policies/employee_leave_policy.md",
        title="Policy",
        document_type="policy",
        version="1.0",
        corpus_version="corpus-v1",
        owner="HR",
        checksum="abc123",
    )

    assert metadata.source_path == "data/policies/employee_leave_policy.md"


@pytest.mark.parametrize(
    "source_path",
    [
        "C:/absolute/path/policy.md",
        "C:\\Users\\HP\\policy.md",
        "/docs/policies/policy.md",
        "../policy.md",
        "docs\\policies\\policy.md",
        "./data/file.md",
        "data//file.md",
        ".",
        "data/policies/",
        "https://example.com/file.md",
        " data/policies/file.md",
        "data/policies/file.md ",
        "data/./file.md",
        "C:file.md",
        "file:/tmp/file.md",
        "folder:name/file.md",
    ],
)
def test_document_metadata_rejects_invalid_paths(source_path: str) -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(
            document_id="doc-1",
            source_path=source_path,
            title="Policy",
            document_type="policy",
            version="1.0",
            corpus_version="corpus-v1",
            owner="HR",
            checksum="abc123",
        )


@pytest.mark.parametrize(
    "schema_factory",
    [
        lambda path: valid_chunk(source_path=path),
        lambda path: RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            corpus_version="corpus-v1",
            chunker_config_id="chunker-v1",
            embedding_model_id="verified-embedding-model",
            embedding_dimension=768,
            index_id="index-v1",
            rank=1,
            raw_score=0.42,
            score_type=ScoreType.COSINE_SIMILARITY,
            text="Chunk text",
            title="Policy",
            section_heading="Section",
            source_path=path,
            retriever_name="retriever",
            retriever_config={"top_k": 3},
        ),
        lambda path: valid_citation(source_path=path),
    ],
)
@pytest.mark.parametrize(
    "source_path",
    [
        "C:/absolute/path/policy.md",
        "C:\\Users\\HP\\policy.md",
        "/docs/policies/policy.md",
        "../policy.md",
        "docs\\policies\\policy.md",
        "./data/file.md",
        "data//file.md",
        ".",
        "data/policies/",
        "https://example.com/file.md",
        " data/policies/file.md",
        "data/policies/file.md ",
        "data/./file.md",
        "C:file.md",
        "file:/tmp/file.md",
        "folder:name/file.md",
    ],
)
def test_source_path_rules_apply_to_all_path_contracts(
    schema_factory: object,
    source_path: str,
) -> None:
    with pytest.raises(ValidationError):
        schema_factory(source_path)  # type: ignore[operator]


def test_valid_document_chunk_succeeds() -> None:
    chunk = valid_chunk()

    assert chunk.chunk_id == "chunk-1"


@pytest.mark.parametrize(
    "overrides",
    [
        {"text": " "},
        {"token_count": 0},
        {"chunk_index": -1},
        {"chunk_overlap_tokens": 200},
        {"chunk_overlap_tokens": 201},
        {"start_char": -1},
        {"page_number": -1},
        {"paragraph_index": -1},
        {"start_char": 10, "end_char": 10},
        {"start_char": 10, "end_char": 9},
        {"end_char": -1},
    ],
)
def test_document_chunk_negative_cases_fail(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        valid_chunk(**overrides)


def test_retrieved_chunk_allows_raw_score_outside_zero_to_one() -> None:
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        corpus_version="corpus-v1",
        chunker_config_id="chunker-v1",
        embedding_model_id="verified-embedding-model",
        embedding_dimension=768,
        index_id="index-v1",
        rank=1,
        raw_score=-3.5,
        score_type=ScoreType.COSINE_DISTANCE,
        text="Chunk text",
        title="Policy",
        section_heading="Section",
        source_path="docs/policies/policy.md",
        retriever_name="retriever",
        retriever_config={"top_k": 3},
    )

    assert chunk.raw_score == -3.5


@pytest.mark.parametrize("raw_score", [float("nan"), float("inf"), float("-inf")])
def test_retrieved_chunk_rejects_nonfinite_raw_score(raw_score: float) -> None:
    with pytest.raises(ValidationError):
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            corpus_version="corpus-v1",
            chunker_config_id="chunker-v1",
            embedding_model_id="verified-embedding-model",
            embedding_dimension=768,
            index_id="index-v1",
            rank=1,
            raw_score=raw_score,
            score_type=ScoreType.COSINE_DISTANCE,
            text="Chunk text",
            title="Policy",
            section_heading="Section",
            source_path="docs/policies/policy.md",
            retriever_name="retriever",
            retriever_config={"top_k": 3},
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"rank": 0},
        {"embedding_dimension": 0},
        {"normalized_relevance": -0.1},
        {"normalized_relevance": 1.1},
        {"normalized_relevance": float("nan")},
        {"normalized_relevance": float("inf")},
        {"source_path": "/absolute.md"},
        {"text": ""},
        {"page_number": -1},
    ],
)
def test_retrieved_chunk_negative_cases_fail(overrides: dict[str, object]) -> None:
    data = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "corpus_version": "corpus-v1",
        "chunker_config_id": "chunker-v1",
        "embedding_model_id": "verified-embedding-model",
        "embedding_dimension": 768,
        "index_id": "index-v1",
        "rank": 1,
        "raw_score": 0.42,
        "score_type": ScoreType.COSINE_SIMILARITY,
        "text": "Chunk text",
        "title": "Policy",
        "section_heading": "Section",
        "source_path": "docs/policies/policy.md",
        "retriever_name": "retriever",
        "retriever_config": {"top_k": 3},
    }
    data.update(overrides)
    with pytest.raises(ValidationError):
        RetrievedChunk(**data)


def test_citation_supporting_quote_optional_but_not_blank_when_present() -> None:
    assert valid_citation(supporting_quote=None).supporting_quote is None

    with pytest.raises(ValidationError):
        valid_citation(supporting_quote=" ")


@pytest.mark.parametrize(
    "overrides",
    [
        {"page_number": -1},
        {"start_char": -1},
        {"end_char": -1},
        {"start_char": 5, "end_char": 5},
        {"start_char": 6, "end_char": 5},
    ],
)
def test_citation_numeric_negative_cases_fail(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        valid_citation(**overrides)


def test_valid_answerable_model_output_succeeds() -> None:
    output = GroundedModelOutput(
        answer="Employees receive ten days of paid leave.",
        is_answerable=True,
        citation_chunk_ids=["chunk-1"],
    )

    assert output.citation_chunk_ids == ["chunk-1"]


def test_answerable_model_output_without_citations_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(answer="Answer", is_answerable=True, citation_chunk_ids=[])


def test_duplicate_citation_ids_fail() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(
            answer="Answer",
            is_answerable=True,
            citation_chunk_ids=["chunk-1", "chunk-1"],
        )


@pytest.mark.parametrize(
    "answer",
    [
        f"{UNSUPPORTED_ANSWER} ",
        f" {UNSUPPORTED_ANSWER}",
    ],
)
def test_answerable_model_output_rejects_canonical_answer_with_whitespace(answer: str) -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(answer=answer, is_answerable=True, citation_chunk_ids=["chunk-1"])


@pytest.mark.parametrize(
    "answer",
    [
        f"{UNSUPPORTED_ANSWER} ",
        f" {UNSUPPORTED_ANSWER}",
    ],
)
def test_unanswerable_model_output_requires_exact_canonical_answer(answer: str) -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(answer=answer, is_answerable=False, citation_chunk_ids=[])


def test_citation_id_surrounding_whitespace_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(answer="Answer", is_answerable=True, citation_chunk_ids=[" chunk-1 "])


def test_duplicate_citation_ids_cannot_bypass_with_whitespace() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(
            answer="Answer",
            is_answerable=True,
            citation_chunk_ids=["chunk-1", " chunk-1 "],
        )


def test_unanswerable_model_output_with_exact_canonical_response_succeeds() -> None:
    output = GroundedModelOutput(
        answer=UNSUPPORTED_ANSWER,
        is_answerable=False,
        citation_chunk_ids=[],
    )

    assert output.answer == UNSUPPORTED_ANSWER


def test_unanswerable_model_output_with_citations_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(
            answer=UNSUPPORTED_ANSWER,
            is_answerable=False,
            citation_chunk_ids=["chunk-1"],
        )


def test_unanswerable_model_output_with_noncanonical_answer_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedModelOutput(answer="I do not know.", is_answerable=False, citation_chunk_ids=[])


@pytest.mark.parametrize(
    "answer",
    [
        f"{UNSUPPORTED_ANSWER} ",
        f" {UNSUPPORTED_ANSWER}",
    ],
)
def test_answerable_application_result_rejects_canonical_answer_with_whitespace(
    answer: str,
) -> None:
    with pytest.raises(ValidationError):
        GroundedAnswerResult(answer=answer, is_answerable=True, citations=[valid_citation()])


@pytest.mark.parametrize(
    "answer",
    [
        f"{UNSUPPORTED_ANSWER} ",
        f" {UNSUPPORTED_ANSWER}",
    ],
)
def test_unanswerable_application_result_requires_exact_canonical_answer(answer: str) -> None:
    with pytest.raises(ValidationError):
        GroundedAnswerResult(answer=answer, is_answerable=False, citations=[])


def test_answerable_application_result_without_citations_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswerResult(answer="Answer", is_answerable=True, citations=[])


def test_unanswerable_application_result_with_citations_fails() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswerResult(
            answer=UNSUPPORTED_ANSWER,
            is_answerable=False,
            citations=[valid_citation()],
        )


@pytest.mark.parametrize("tone", list(ToneName))
def test_every_valid_tone_name_succeeds(tone: ToneName) -> None:
    output = ToneModelOutput(tone=tone, output="Tone text")

    assert output.tone == tone


def test_unknown_tone_fails() -> None:
    with pytest.raises(ValidationError):
        ToneModelOutput(tone="unknown", output="Tone text")


def test_blank_tone_output_fails() -> None:
    with pytest.raises(ValidationError):
        ToneModelOutput(tone=ToneName.FORMAL_REPORT_SUMMARY, output=" ")


def test_all_tone_result_with_exactly_three_unique_tones_succeeds() -> None:
    citation = valid_citation()
    result = AllToneResult(
        original_answer="Answer",
        variations=[
            ToneResult(tone=ToneName.FORMAL_REPORT_SUMMARY, output="Formal", citations=[citation]),
            ToneResult(tone=ToneName.CASUAL_MESSAGE, output="Casual", citations=[citation]),
            ToneResult(
                tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
                output="Brief",
                citations=[citation],
            ),
        ],
    )

    assert [variation.tone for variation in result.variations] == list(ToneName)


def test_all_tone_result_missing_tone_fails() -> None:
    citation = valid_citation()
    with pytest.raises(ValidationError):
        AllToneResult(
            original_answer="Answer",
            variations=[
                ToneResult(tone=ToneName.FORMAL_REPORT_SUMMARY, output="Formal", citations=[citation]),
                ToneResult(tone=ToneName.CASUAL_MESSAGE, output="Casual", citations=[citation]),
            ],
        )


def test_all_tone_result_duplicate_tone_fails() -> None:
    citation = valid_citation()
    with pytest.raises(ValidationError):
        AllToneResult(
            original_answer="Answer",
            variations=[
                ToneResult(tone=ToneName.FORMAL_REPORT_SUMMARY, output="Formal", citations=[citation]),
                ToneResult(tone=ToneName.CASUAL_MESSAGE, output="Casual", citations=[citation]),
                ToneResult(tone=ToneName.CASUAL_MESSAGE, output="Duplicate", citations=[citation]),
            ],
        )


def test_all_tone_result_different_citation_lists_fail() -> None:
    citation = valid_citation()
    other_citation = valid_citation(citation_id="citation-2", chunk_id="chunk-2")
    with pytest.raises(ValidationError):
        AllToneResult(
            original_answer="Answer",
            variations=[
                ToneResult(tone=ToneName.FORMAL_REPORT_SUMMARY, output="Formal", citations=[citation]),
                ToneResult(tone=ToneName.CASUAL_MESSAGE, output="Casual", citations=[other_citation]),
                ToneResult(
                    tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
                    output="Brief",
                    citations=[citation],
                ),
            ],
        )
