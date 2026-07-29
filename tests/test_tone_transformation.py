import pytest

from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import ModelOutputError
from rag_foundations.grounded_generation import GenerationConfig
from rag_foundations.schemas import Citation, GroundedAnswerResult, ToneName, ToneResult
from rag_foundations.tone_transformation import (
    CASUAL_MESSAGE_FEW_SHOT_MARKER,
    CASUAL_MESSAGE_PROMPT_VERSION,
    CONCISE_EXECUTIVE_BRIEFING_FEW_SHOT_MARKER,
    CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
    FORMAL_REPORT_SUMMARY_FEW_SHOT_MARKER,
    FORMAL_REPORT_SUMMARY_PROMPT_VERSION,
    build_all_tone_result,
    build_casual_message_messages,
    build_concise_executive_briefing_messages,
    build_formal_report_summary_messages,
    call_and_validate_formal_tone_model,
    call_and_validate_tone_model,
    transform_all_tones,
    transform_casual_message,
    transform_concise_executive_briefing,
    transform_formal_report_summary,
)


class FakeChatClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[list[dict[str, str]]] = []
        self.params: list[dict[str, object]] = []

    def chat(self, messages: list[dict[str, str]], params: dict[str, object]) -> str:
        self.calls.append(messages)
        self.params.append(params)
        if not self.responses:
            raise AssertionError("unexpected chat call")
        return self.responses.pop(0)


def citation(**overrides: object) -> Citation:
    data = {
        "citation_id": "citation-1-chunk-1",
        "chunk_id": "chunk-1",
        "document_id": "policy-remote-work",
        "title": "Remote Work Policy",
        "section_heading": "5. Maximum Remote Days and Office Attendance",
        "source_path": "data/documents_v2_1/flexible_work_workplace_access_policy.md",
        "supporting_quote": "Eligible employees may work remotely up to 2 working days per week.",
        "corpus_version": "asteron-policies-v1",
        "index_id": "asteron_policies_watsonx_faiss_v1",
    }
    data.update(overrides)
    return Citation(**data)


def grounded_answer(answer: str | None = None) -> GroundedAnswerResult:
    return GroundedAnswerResult(
        answer=answer or "Eligible employees may work remotely up to 2 working days per week.",
        is_answerable=True,
        citations=[citation()],
    )


def config(retries: int = 1) -> GenerationConfig:
    return GenerationConfig(
        repair_retry_count=retries,
        prompt_version=FORMAL_REPORT_SUMMARY_PROMPT_VERSION,
    )


def test_valid_formal_tone_model_output_builds_tone_result() -> None:
    chat = FakeChatClient(
        [
            (
                '{"tone": "formal_report_summary", "output": '
                '"Eligible employees may work remotely up to 2 working days per week."}'
            )
        ]
    )

    result = transform_formal_report_summary(
        grounded_answer(),
        chat_client=chat,
        generation_config=config(),
    )

    assert result.model_output.tone == ToneName.FORMAL_REPORT_SUMMARY
    assert result.tone_result.tone == ToneName.FORMAL_REPORT_SUMMARY
    assert result.tone_result.output == (
        "Eligible employees may work remotely up to 2 working days per week."
    )
    assert result.repair_retry_used is False


def test_grounded_citations_are_copied_unchanged() -> None:
    source = grounded_answer()
    chat = FakeChatClient(
        [
            (
                '{"tone": "formal_report_summary", "output": '
                '"Remote work may be used for up to 2 working days per week."}'
            )
        ]
    )

    result = transform_formal_report_summary(
        source,
        chat_client=chat,
        generation_config=config(),
    )

    assert result.tone_result.citations == source.citations
    assert result.tone_result.citations is not source.citations


def test_answerable_status_is_preserved_on_application_result() -> None:
    source = grounded_answer()
    chat = FakeChatClient(
        [
            (
                '{"tone": "formal_report_summary", "output": '
                '"Remote work may be used for up to 2 working days per week."}'
            )
        ]
    )

    result = transform_formal_report_summary(
        source,
        chat_client=chat,
        generation_config=config(),
    )

    assert result.source_answer.is_answerable is True


def test_prompt_does_not_ask_tone_model_to_create_citation_metadata() -> None:
    messages = build_formal_report_summary_messages(grounded_answer())
    combined = "\n".join(message["content"] for message in messages)

    assert "Do not generate citation metadata" in combined
    assert "source paths" in combined
    assert "document names" in combined
    assert "chunk IDs" in combined


def test_malformed_json_followed_by_one_successful_repair() -> None:
    chat = FakeChatClient(
        [
            "not json",
            (
                '{"tone": "formal_report_summary", "output": '
                '"Remote work may be used for up to 2 working days per week."}'
            ),
        ]
    )

    output, repaired = call_and_validate_formal_tone_model(
        chat_client=chat,
        messages=[{"role": "user", "content": "Answer"}],
        grounded_result=grounded_answer(),
        generation_config=config(retries=1),
    )

    assert output.tone == ToneName.FORMAL_REPORT_SUMMARY
    assert repaired is True
    assert len(chat.calls) == 2


def test_invalid_output_on_both_attempts_raises_safe_typed_error() -> None:
    chat = FakeChatClient(["api_key=super-secret", "password: hunter2"])

    with pytest.raises(ModelOutputError) as exc_info:
        call_and_validate_formal_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=grounded_answer(),
            generation_config=config(retries=1),
        )

    assert "super-secret" not in str(exc_info.value)
    assert "hunter2" not in str(exc_info.value)
    assert exc_info.value.repair_retry_used is True


def test_unanswerable_grounded_result_preserves_canonical_refusal_without_model_call() -> None:
    source = GroundedAnswerResult(
        answer=UNSUPPORTED_ANSWER,
        is_answerable=False,
        citations=[],
    )
    chat = FakeChatClient([])

    result = transform_formal_report_summary(
        source,
        chat_client=chat,
        generation_config=config(),
    )

    assert result.tone_result.output == UNSUPPORTED_ANSWER
    assert result.source_answer.is_answerable is False
    assert result.tone_result.citations == []
    assert chat.calls == []


def test_prompt_includes_the_few_shot_example() -> None:
    messages = build_formal_report_summary_messages(grounded_answer())
    user_prompt = messages[1]["content"]

    assert FORMAL_REPORT_SUMMARY_FEW_SHOT_MARKER in user_prompt
    assert '"tone": "formal_report_summary"' in user_prompt


def test_prompt_includes_full_grounded_answer_without_silent_truncation() -> None:
    full_answer = (
        "Employees should use the phishing report button or send the message to "
        "security@asteron.example. Suspicious emails must be reported within 1 hour "
        "of discovery if the employee clicked a link, opened an attachment, entered "
        "credentials, approved a payment change, or replied with confidential "
        "information. If the employee only received the message and did not interact "
        "with it, reporting by the end of the working day is acceptable."
    )

    messages = build_formal_report_summary_messages(grounded_answer(full_answer))

    assert full_answer in messages[1]["content"]


def test_tone_model_output_with_citation_metadata_is_rejected() -> None:
    chat = FakeChatClient(
        [
            (
                '{"tone": "formal_report_summary", "output": '
                '"Remote Work Policy allows up to 2 working days per week."}'
            )
        ]
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_formal_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=grounded_answer(),
            generation_config=config(retries=0),
        )


def test_valid_casual_output_builds_tone_result() -> None:
    chat = FakeChatClient(
        [
            (
                '{"tone": "casual_message", "output": '
                '"You can work remotely up to 2 working days per week."}'
            )
        ]
    )

    result = transform_casual_message(
        grounded_answer(),
        chat_client=chat,
        generation_config=GenerationConfig(prompt_version=CASUAL_MESSAGE_PROMPT_VERSION),
    )

    assert result.model_output.tone == ToneName.CASUAL_MESSAGE
    assert result.tone_result.tone == ToneName.CASUAL_MESSAGE
    assert result.tone_result.citations == grounded_answer().citations
    assert result.source_answer.is_answerable is True


def test_casual_prompt_includes_few_shot_and_full_answer() -> None:
    answer = (
        "Submit the claim within 15 calendar days after the expense date, unless the "
        "delay was outside the employee's control."
    )

    messages = build_casual_message_messages(grounded_answer(answer))
    combined = "\n".join(message["content"] for message in messages)

    assert CASUAL_MESSAGE_FEW_SHOT_MARKER in combined
    assert '"tone": "casual_message"' in combined
    assert answer in combined
    assert "Do not generate citation metadata" in combined
    assert "15 calendar days" in combined
    assert "unless" in combined


def test_casual_malformed_json_followed_by_one_successful_repair() -> None:
    chat = FakeChatClient(
        [
            "not json",
            (
                '{"tone": "casual_message", "output": '
                '"You can work remotely up to 2 working days per week."}'
            ),
        ]
    )

    output, repaired = call_and_validate_tone_model(
        chat_client=chat,
        messages=[{"role": "user", "content": "Answer"}],
        grounded_result=grounded_answer(),
        generation_config=GenerationConfig(
            repair_retry_count=1,
            prompt_version=CASUAL_MESSAGE_PROMPT_VERSION,
        ),
        expected_tone=ToneName.CASUAL_MESSAGE,
    )

    assert output.tone == ToneName.CASUAL_MESSAGE
    assert repaired is True
    assert len(chat.calls) == 2


def test_casual_two_invalid_responses_raise_safe_typed_error() -> None:
    chat = FakeChatClient(["api_key=super-secret", "password: hunter2"])

    with pytest.raises(ModelOutputError) as exc_info:
        call_and_validate_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=grounded_answer(),
            generation_config=GenerationConfig(
                repair_retry_count=1,
                prompt_version=CASUAL_MESSAGE_PROMPT_VERSION,
            ),
            expected_tone=ToneName.CASUAL_MESSAGE,
        )

    assert "super-secret" not in str(exc_info.value)
    assert "hunter2" not in str(exc_info.value)


def test_valid_executive_output_builds_tone_result() -> None:
    chat = FakeChatClient(
        [
            (
                '{"tone": "concise_executive_briefing", "output": '
                '"Key rule: remote work is limited to 2 working days per week."}'
            )
        ]
    )

    result = transform_concise_executive_briefing(
        grounded_answer(),
        chat_client=chat,
        generation_config=GenerationConfig(
            prompt_version=CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
        ),
    )

    assert result.model_output.tone == ToneName.CONCISE_EXECUTIVE_BRIEFING
    assert result.tone_result.tone == ToneName.CONCISE_EXECUTIVE_BRIEFING
    assert result.tone_result.citations == grounded_answer().citations
    assert result.source_answer.is_answerable is True


def test_executive_prompt_includes_few_shot_and_full_answer() -> None:
    answer = (
        "Suspicious emails must be reported within 1 hour if the employee clicked a link; "
        "if there was no interaction, reporting by the end of the working day is acceptable."
    )

    messages = build_concise_executive_briefing_messages(grounded_answer(answer))
    combined = "\n".join(message["content"] for message in messages)

    assert CONCISE_EXECUTIVE_BRIEFING_FEW_SHOT_MARKER in combined
    assert '"tone": "concise_executive_briefing"' in combined
    assert answer in combined
    assert "Do not generate citation metadata" in combined
    assert "1 hour" in combined
    assert "if there was no interaction" in combined


def test_executive_malformed_json_followed_by_one_successful_repair() -> None:
    chat = FakeChatClient(
        [
            "not json",
            (
                '{"tone": "concise_executive_briefing", "output": '
                '"Key rule: remote work is limited to 2 working days per week."}'
            ),
        ]
    )

    output, repaired = call_and_validate_tone_model(
        chat_client=chat,
        messages=[{"role": "user", "content": "Answer"}],
        grounded_result=grounded_answer(),
        generation_config=GenerationConfig(
            repair_retry_count=1,
            prompt_version=CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
        ),
        expected_tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
    )

    assert output.tone == ToneName.CONCISE_EXECUTIVE_BRIEFING
    assert repaired is True
    assert len(chat.calls) == 2


def test_executive_two_invalid_responses_raise_safe_typed_error() -> None:
    chat = FakeChatClient(["api_key=super-secret", "password: hunter2"])

    with pytest.raises(ModelOutputError) as exc_info:
        call_and_validate_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=grounded_answer(),
            generation_config=GenerationConfig(
                repair_retry_count=1,
                prompt_version=CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
            ),
            expected_tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
        )

    assert "super-secret" not in str(exc_info.value)
    assert "hunter2" not in str(exc_info.value)


def test_unanswerable_input_bypasses_all_tone_model_calls() -> None:
    source = GroundedAnswerResult(answer=UNSUPPORTED_ANSWER, is_answerable=False, citations=[])
    chat = FakeChatClient([])

    result = transform_all_tones(source, chat_client=chat)

    assert chat.calls == []
    assert result.source_answer.is_answerable is False
    assert [variation.tone for variation in result.all_tone_result.variations] == [
        ToneName.FORMAL_REPORT_SUMMARY,
        ToneName.CASUAL_MESSAGE,
        ToneName.CONCISE_EXECUTIVE_BRIEFING,
    ]
    for variation in result.all_tone_result.variations:
        assert variation.output == UNSUPPORTED_ANSWER
        assert variation.citations == []


def test_all_tone_result_contains_three_required_tones_with_identical_citations() -> None:
    chat = FakeChatClient(
        [
            '{"tone": "formal_report_summary", "output": "Remote work is permitted up to 2 working days per week."}',
            '{"tone": "casual_message", "output": "You can work remotely up to 2 working days per week."}',
            '{"tone": "concise_executive_briefing", "output": "Key rule: remote work is capped at 2 working days per week."}',
        ]
    )
    source = grounded_answer()

    result = transform_all_tones(source, chat_client=chat)

    assert result.all_tone_result.original_answer == source.answer
    assert [variation.tone for variation in result.all_tone_result.variations] == [
        ToneName.FORMAL_REPORT_SUMMARY,
        ToneName.CASUAL_MESSAGE,
        ToneName.CONCISE_EXECUTIVE_BRIEFING,
    ]
    assert all(variation.citations == source.citations for variation in result.all_tone_result.variations)
    assert result.source_answer.is_answerable is True


def test_duplicate_tone_identifiers_are_not_accepted() -> None:
    source = grounded_answer()
    duplicate_results = [
        ToneResult(
            tone=ToneName.FORMAL_REPORT_SUMMARY,
            output="Formal output with 2 working days per week.",
            citations=source.citations,
        ),
        ToneResult(
            tone=ToneName.FORMAL_REPORT_SUMMARY,
            output="Duplicate output with 2 working days per week.",
            citations=source.citations,
        ),
        ToneResult(
            tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
            output="Executive output with 2 working days per week.",
            citations=source.citations,
        ),
    ]

    with pytest.raises((KeyError, ValueError)):
        build_all_tone_result(source, duplicate_results)


def test_tone_output_missing_required_surface_marker_is_rejected() -> None:
    source = grounded_answer("Employees may work remotely up to 2 working days per week.")
    chat = FakeChatClient(
        ['{"tone": "casual_message", "output": "You can work remotely up to 2 days per week."}']
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=source,
            generation_config=GenerationConfig(
                repair_retry_count=0,
                prompt_version=CASUAL_MESSAGE_PROMPT_VERSION,
            ),
            expected_tone=ToneName.CASUAL_MESSAGE,
        )


def test_tone_output_unsupported_no_exceptions_statement_is_rejected() -> None:
    source = grounded_answer("Employees may work remotely up to 2 working days per week.")
    chat = FakeChatClient(
        [
            (
                '{"tone": "concise_executive_briefing", "output": '
                '"Key rule: up to 2 working days per week. No exceptions mentioned."}'
            )
        ]
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=source,
            generation_config=GenerationConfig(
                repair_retry_count=0,
                prompt_version=CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
            ),
            expected_tone=ToneName.CONCISE_EXECUTIVE_BRIEFING,
        )


def test_tone_output_unsupported_time_off_wording_is_rejected() -> None:
    source = grounded_answer("Employees may work remotely up to 2 working days per week.")
    chat = FakeChatClient(
        [
            (
                '{"tone": "casual_message", "output": '
                '"You can take up to 2 working days off per week."}'
            )
        ]
    )

    with pytest.raises(ModelOutputError):
        call_and_validate_tone_model(
            chat_client=chat,
            messages=[{"role": "user", "content": "Answer"}],
            grounded_result=source,
            generation_config=GenerationConfig(
                repair_retry_count=0,
                prompt_version=CASUAL_MESSAGE_PROMPT_VERSION,
            ),
            expected_tone=ToneName.CASUAL_MESSAGE,
        )
