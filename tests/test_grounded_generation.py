import pytest

from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import CitationValidationError, ModelOutputError
from rag_foundations.grounded_generation import (
    GROUNDING_PROMPT_VERSION,
    GenerationConfig,
    build_grounded_messages,
    build_grounded_answer_result,
    call_and_validate_grounded_model,
    generate_grounded_answer,
    parse_grounded_model_output,
    resolve_citations_locally,
)
from rag_foundations.schemas import RetrievedChunk, ScoreType


class FakeChatClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], params: dict[str, object]) -> str:
        self.calls.append(messages)
        if not self.responses:
            raise AssertionError("unexpected chat call")
        return self.responses.pop(0)


def retrieved_chunk(**overrides: object) -> RetrievedChunk:
    data = {
        "chunk_id": "chunk-1",
        "document_id": "policy-remote-work",
        "corpus_version": "asteron-policies-v1",
        "chunker_config_id": "section-token-v1-size-220-overlap-40-minilm",
        "embedding_model_id": "ibm/granite-embedding-278m-multilingual",
        "embedding_dimension": 768,
        "index_id": "asteron_policies_watsonx_faiss_v1",
        "rank": 1,
        "raw_score": 0.91,
        "score_type": ScoreType.COSINE_SIMILARITY,
        "text": "Eligible employees may work remotely up to 2 working days per week.",
        "title": "Remote Work Policy",
        "section_heading": "5. Maximum Remote Days and Office Attendance",
        "source_path": "data/documents_v2_1/flexible_work_workplace_access_policy.md",
        "retriever_name": "faiss-watsonx-flat-ip-retriever",
        "retriever_config": {"top_k": 5},
    }
    data.update(overrides)
    return RetrievedChunk(**data)


def config(retries: int = 1) -> GenerationConfig:
    return GenerationConfig(repair_retry_count=retries)


def test_answerable_valid_output_with_retrieved_citation_ids() -> None:
    chunk = retrieved_chunk()
    chat = FakeChatClient(
        [
            (
                '{"answerable": true, "answer": "Eligible employees may work remotely '
                'up to 2 working days per week.", "citation_chunk_ids": ["chunk-1"]}'
            )
        ]
    )

    result = generate_grounded_answer(
        "How many days may employees work remotely?",
        retrieved_chunks=[chunk],
        chat_client=chat,
        generation_config=config(),
    )

    assert result.model_output.is_answerable is True
    assert result.model_output.citation_chunk_ids == ["chunk-1"]
    assert result.answer_result.citations[0].chunk_id == "chunk-1"
    assert result.repair_retry_used is False


def test_unanswerable_valid_output_with_zero_citations() -> None:
    model_output = parse_grounded_model_output(
        (
            '{"answerable": false, '
            f'"answer": "{UNSUPPORTED_ANSWER}", '
            '"citation_chunk_ids": []}'
        )
    )

    result = build_grounded_answer_result(model_output, [retrieved_chunk()])

    assert result.is_answerable is False
    assert result.answer == UNSUPPORTED_ANSWER
    assert result.citations == []


def test_model_cites_unknown_chunk_id() -> None:
    model_output = parse_grounded_model_output(
        '{"answerable": true, "answer": "Answer.", "citation_chunk_ids": ["chunk-missing"]}'
    )

    with pytest.raises(CitationValidationError):
        resolve_citations_locally(model_output, [retrieved_chunk()])


def test_answerable_output_has_no_citations() -> None:
    chat = FakeChatClient(
        ['{"answerable": true, "answer": "Answer.", "citation_chunk_ids": []}']
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_grounded_model(
            chat_client=chat,
            messages=[],
            retrieved_chunks=[retrieved_chunk()],
            generation_config=config(retries=0),
        )


def test_unanswerable_output_has_citations() -> None:
    chat = FakeChatClient(
        [
            (
                '{"answerable": false, '
                f'"answer": "{UNSUPPORTED_ANSWER}", '
                '"citation_chunk_ids": ["chunk-1"]}'
            )
        ]
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_grounded_model(
            chat_client=chat,
            messages=[],
            retrieved_chunks=[retrieved_chunk()],
            generation_config=config(retries=0),
        )


def test_malformed_json_followed_by_successful_single_repair() -> None:
    chat = FakeChatClient(
        [
            "not json",
            '{"answerable": true, "answer": "Answer.", "citation_chunk_ids": ["chunk-1"]}',
        ]
    )

    output, repaired = call_and_validate_grounded_model(
        chat_client=chat,
        messages=[{"role": "user", "content": "Question"}],
        retrieved_chunks=[retrieved_chunk()],
        generation_config=config(retries=1),
    )

    assert output.is_answerable is True
    assert repaired is True
    assert len(chat.calls) == 2


def test_malformed_json_on_both_attempts_produces_typed_safe_failure() -> None:
    chat = FakeChatClient(["api_key=secret bad", "password: hunter2 still bad"])

    with pytest.raises(ModelOutputError) as exc_info:
        call_and_validate_grounded_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Question"}],
            retrieved_chunks=[retrieved_chunk()],
            generation_config=config(retries=1),
        )

    message = str(exc_info.value)
    assert "super-secret" not in message
    assert "hunter2" not in message
    assert "password: <redacted>" in message


def test_citation_metadata_is_resolved_locally() -> None:
    chunk = retrieved_chunk(title="Local Title", section_heading="Local Section")
    model_output = parse_grounded_model_output(
        '{"answerable": true, "answer": "Answer.", "citation_chunk_ids": ["chunk-1"]}'
    )

    citations = resolve_citations_locally(model_output, [chunk])

    assert citations[0].title == "Local Title"
    assert citations[0].section_heading == "Local Section"
    assert citations[0].source_path == "data/documents_v2_1/flexible_work_workplace_access_policy.md"


def test_citation_supporting_evidence_exactly_matches_local_chunk_text() -> None:
    chunk = retrieved_chunk(text="Exact local retrieved text.")
    model_output = parse_grounded_model_output(
        '{"answerable": true, "answer": "Answer.", "citation_chunk_ids": ["chunk-1"]}'
    )

    citations = resolve_citations_locally(model_output, [chunk])

    assert citations[0].supporting_quote == "Exact local retrieved text."


def test_secret_values_do_not_appear_in_errors_or_logs() -> None:
    chat = FakeChatClient(["invalid api_key=secret"])

    with pytest.raises(ModelOutputError) as exc_info:
        call_and_validate_grounded_model(
            chat_client=chat,
            messages=[],
            retrieved_chunks=[retrieved_chunk()],
            generation_config=config(retries=0),
        )

    assert "very-secret-value" not in exc_info.value.reason
    assert "very-secret-value" not in str(exc_info.value)
    assert "api_key= <redacted>" in str(exc_info.value)


def test_prompt_includes_all_top5_chunks_and_ids_without_truncation() -> None:
    chunks = [
        retrieved_chunk(
            chunk_id=f"chunk-{index}",
            rank=index,
            document_id=f"doc-{index}",
            title=f"Policy {index}",
            section_heading=f"Section {index}",
            text=f"Full exact chunk text {index}. Threshold KWD {index}.",
        )
        for index in range(1, 6)
    ]

    messages = build_grounded_messages("Question?", chunks)
    user_prompt = messages[1]["content"]

    for chunk in chunks:
        assert f"chunk_id: {chunk.chunk_id}" in user_prompt
        assert f"document_id: {chunk.document_id}" in user_prompt
        assert f"document_name: {chunk.title}" in user_prompt
        assert f"section_title: {chunk.section_heading}" in user_prompt
        assert chunk.text in user_prompt


def test_prompt_keeps_document_and_section_labels_with_correct_chunk_text() -> None:
    gift_text = (
        "A gift or hospitality item with an estimated value of KWD 20 or less may be "
        "accepted if it is appropriate and not cash or a cash equivalent."
    )
    chunk = retrieved_chunk(
        chunk_id="chunk-gifts",
        document_id="policy-code-of-conduct",
        title="Code of Conduct",
        section_heading="6. Gifts and Hospitality",
        text=gift_text,
    )

    user_prompt = build_grounded_messages("What is the gift threshold?", [chunk])[1]["content"]

    assert "chunk_id: chunk-gifts" in user_prompt
    assert "document_id: policy-code-of-conduct" in user_prompt
    assert "document_name: Code of Conduct" in user_prompt
    assert "section_title: 6. Gifts and Hospitality" in user_prompt
    assert gift_text in user_prompt


def test_prompt_clarifies_conditional_supported_policy_facts_are_answerable() -> None:
    system_prompt = build_grounded_messages("Question?", [retrieved_chunk()])[0]["content"]

    assert GROUNDING_PROMPT_VERSION == "grounded-generation-v1.1"
    assert "conditions, thresholds, approvals, limits, or exceptions" in system_prompt
    assert "set answerable to true" in system_prompt
    assert "If the context does not contain enough evidence" in system_prompt


def test_conditional_supported_policy_answer_preserves_conditions_and_exception() -> None:
    chunk = retrieved_chunk(
        chunk_id="chunk-gifts",
        text=(
            "A gift or hospitality item with an estimated value of KWD 20 or less may be "
            "accepted if it is appropriate and not cash or a cash equivalent. Anything above "
            "KWD 20 must be disclosed to the manager and HR before acceptance when practical."
        ),
    )
    chat = FakeChatClient(
        [
            (
                '{"answerable": true, "answer": "The maximum estimated value is KWD 20 '
                'or less, provided the courtesy is appropriate and not cash or a cash '
                'equivalent; anything above KWD 20 must be disclosed to the manager and HR '
                'before acceptance when practical.", "citation_chunk_ids": ["chunk-gifts"]}'
            )
        ]
    )

    result = generate_grounded_answer(
        "What is the maximum estimated value?",
        retrieved_chunks=[chunk],
        chat_client=chat,
        generation_config=config(),
    )

    assert result.model_output.is_answerable is True
    assert "KWD 20 or less" in result.answer_result.answer
    assert "not cash or a cash equivalent" in result.answer_result.answer
    assert "manager and HR" in result.answer_result.answer


def test_unsupported_question_still_returns_canonical_refusal() -> None:
    model_output = parse_grounded_model_output(
        (
            '{"answerable": false, '
            f'"answer": "{UNSUPPORTED_ANSWER}", '
            '"citation_chunk_ids": []}'
        )
    )

    result = build_grounded_answer_result(model_output, [retrieved_chunk()])

    assert result.is_answerable is False
    assert result.answer == UNSUPPORTED_ANSWER
    assert result.citations == []
