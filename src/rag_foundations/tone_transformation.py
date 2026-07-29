"""Tone transformation for grounded RAG answers."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, replace

from pydantic import ValidationError

from rag_foundations.config import AppSettings
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import ModelOutputError, RAGFoundationsError
from rag_foundations.grounded_generation import (
    GENERATION_MODEL_ID,
    ChatClient,
    GenerationConfig,
    WatsonxChatClient,
)
from rag_foundations.schemas import (
    AllToneResult,
    GroundedAnswerResult,
    ToneModelOutput,
    ToneName,
    ToneResult,
)
from rag_foundations.watsonx_models import create_runtime


FORMAL_REPORT_SUMMARY_PROMPT_VERSION = "formal-report-summary-v1"
CASUAL_MESSAGE_PROMPT_VERSION = "casual-message-v1.5"
CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION = "concise-executive-briefing-v1.2"
FORMAL_REPORT_SUMMARY_FEW_SHOT_MARKER = "Few-shot example - formal_report_summary"
CASUAL_MESSAGE_FEW_SHOT_MARKER = "Few-shot example - casual_message"
CONCISE_EXECUTIVE_BRIEFING_FEW_SHOT_MARKER = (
    "Few-shot example - concise_executive_briefing"
)
PROMPT_VERSIONS = {
    ToneName.FORMAL_REPORT_SUMMARY: FORMAL_REPORT_SUMMARY_PROMPT_VERSION,
    ToneName.CASUAL_MESSAGE: CASUAL_MESSAGE_PROMPT_VERSION,
    ToneName.CONCISE_EXECUTIVE_BRIEFING: CONCISE_EXECUTIVE_BRIEFING_PROMPT_VERSION,
}
TONE_ORDER = [
    ToneName.FORMAL_REPORT_SUMMARY,
    ToneName.CASUAL_MESSAGE,
    ToneName.CONCISE_EXECUTIVE_BRIEFING,
]


@dataclass(frozen=True)
class ToneTransformationResult:
    """Validated tone model output plus application-owned tone result."""

    source_answer: GroundedAnswerResult
    model_output: ToneModelOutput
    tone_result: ToneResult
    repair_retry_used: bool
    latency_seconds: float


@dataclass(frozen=True)
class AllToneTransformationResult:
    """Sequential all-tone result plus per-tone execution metadata."""

    source_answer: GroundedAnswerResult
    all_tone_result: AllToneResult
    tone_results: dict[ToneName, ToneTransformationResult]


def formal_tone_generation_config(settings: AppSettings | None = None) -> GenerationConfig:
    """Use verified generation settings with the formal-tone prompt version."""

    return replace(
        GenerationConfig.from_settings(settings),
        prompt_version=FORMAL_REPORT_SUMMARY_PROMPT_VERSION,
    )


def tone_generation_config(tone: ToneName, settings: AppSettings | None = None) -> GenerationConfig:
    """Use verified generation settings with the selected tone prompt version."""

    return replace(
        GenerationConfig.from_settings(settings),
        prompt_version=PROMPT_VERSIONS[tone],
    )


def build_formal_report_summary_messages(
    grounded_result: GroundedAnswerResult,
) -> list[dict[str, str]]:
    """Build the strict formal-report tone prompt for the Chat API."""

    if not grounded_result.is_answerable:
        raise ValueError("unanswerable grounded results must not be sent to the tone model")

    system_prompt = (
        "You transform a validated grounded policy answer into the formal_report_summary tone. "
        "The output must be professional, objective, concise, neutral, and suitable for a formal "
        "report summary. Use only the grounded answer supplied by the user. Preserve all factual "
        "claims, answerable status, exact numbers, dates, thresholds, time limits, conditions, "
        "approvals, and exceptions. Do not add new factual claims. Do not remove material "
        "qualifications. Do not use external knowledge. Return JSON only, with no markdown fence "
        "and no explanation outside JSON. Do not generate citation metadata, source paths, "
        "document names, section titles, scores, supporting quotes, or chunk IDs. Do not expose "
        "chain-of-thought. The JSON schema is exactly: "
        '{"tone": "formal_report_summary", "output": "transformed text"}.'
    )
    user_prompt = (
        f"{FORMAL_REPORT_SUMMARY_FEW_SHOT_MARKER}:\n"
        "Input grounded answer:\n"
        "Team members must submit the request within 5 working days, unless HR grants a "
        "documented exception.\n"
        "Expected JSON output:\n"
        "{\n"
        '  "tone": "formal_report_summary",\n'
        '  "output": "The request must be submitted within 5 working days, unless HR grants '
        'a documented exception."\n'
        "}\n\n"
        "Transform this grounded answer into formal_report_summary. Preserve the full answer "
        "without silent truncation and do not output citation metadata.\n\n"
        "Answerable status: true\n"
        "Grounded answer:\n"
        f"{grounded_result.answer}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_casual_message_messages(grounded_result: GroundedAnswerResult) -> list[dict[str, str]]:
    """Build the strict casual-message tone prompt for the Chat API."""

    if not grounded_result.is_answerable:
        raise ValueError("unanswerable grounded results must not be sent to the tone model")

    system_prompt = (
        "You transform a validated grounded policy answer into the casual_message tone. "
        "The output must be natural, conversational, easy to read, friendly without being "
        "unprofessional, concise, and recognizably different from a formal report. Use only "
        "the grounded answer supplied by the user. Preserve all factual claims, answerable "
        "status, exact numbers, dates, deadlines, limits, conditions, approvals, and exceptions. "
        "Do not add facts, remove material qualifications, soften mandatory policy language, "
        "change precise terms such as working days into different terms, omit contact methods "
        "such as buttons or email addresses, alter location phrases, use external knowledge, use "
        "slang that reduces clarity, or add emojis. Copy exact phrases such as working days, "
        "returning to Kuwait, email addresses, and KWD amounts when they appear in the grounded "
        "answer. Do not say leave, time off, or days off unless the grounded answer uses that "
        "meaning. Return JSON only, with no markdown fence and no explanation outside "
        "JSON. Do not generate citation metadata, source paths, document names, section titles, "
        "scores, supporting quotes, or chunk IDs. Do not expose chain-of-thought. The JSON "
        "schema is exactly: "
        '{"tone": "casual_message", "output": "transformed text"}.'
    )
    user_prompt = (
        f"{CASUAL_MESSAGE_FEW_SHOT_MARKER}:\n"
        "Input grounded answer:\n"
        "Team members must submit the request within 5 working days, unless HR grants a "
        "documented exception.\n"
        "Expected JSON output:\n"
        "{\n"
        '  "tone": "casual_message",\n'
        '  "output": "Please submit the request within 5 working days. If HR grants a '
        'documented exception, that exception still applies."\n'
        "}\n\n"
        "Transform this grounded answer into casual_message. Preserve the full answer without "
        "silent truncation and do not output citation metadata. If the grounded answer is a "
        "short fragment, turn it into a simple conversational sentence only when doing so does "
        "not add new facts.\n\n"
        "Answerable status: true\n"
        "Grounded answer:\n"
        f"{grounded_result.answer}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_concise_executive_briefing_messages(
    grounded_result: GroundedAnswerResult,
) -> list[dict[str, str]]:
    """Build the strict executive-briefing tone prompt for the Chat API."""

    if not grounded_result.is_answerable:
        raise ValueError("unanswerable grounded results must not be sent to the tone model")

    system_prompt = (
        "You transform a validated grounded policy answer into the "
        "concise_executive_briefing tone. The output must be decision-oriented, direct, "
        "concise, scannable, suitable for an executive reader, and focused on the main policy "
        "rule, action, threshold, or implication. It must be recognizably different from both "
        "formal_report_summary and casual_message. Use only the grounded answer supplied by "
        "the user. Preserve all factual claims, answerable status, exact numbers, dates, "
        "deadlines, limits, conditions, approvals, and exceptions. Do not add unsupported "
        "recommendations, invent business impact, invent risk assessments, remove material "
        "conditions, omit required procedures or contact methods, change precise terms such as "
        "working days into different terms, alter location phrases, state that no exceptions are "
        "mentioned unless the grounded answer explicitly says that, or use external knowledge. "
        "Copy exact phrases such as working days, returning to Kuwait, email addresses, and KWD "
        "amounts when they appear in the grounded answer. Return JSON only, with no markdown "
        "fence and no explanation outside JSON. Do not generate citation metadata, source paths, "
        "document names, section titles, scores, supporting quotes, or chunk IDs. Do not expose "
        "chain-of-thought. The JSON schema is exactly: "
        '{"tone": "concise_executive_briefing", "output": "transformed text"}.'
    )
    user_prompt = (
        f"{CONCISE_EXECUTIVE_BRIEFING_FEW_SHOT_MARKER}:\n"
        "Input grounded answer:\n"
        "Team members must submit the request within 5 working days, unless HR grants a "
        "documented exception.\n"
        "Expected JSON output:\n"
        "{\n"
        '  "tone": "concise_executive_briefing",\n'
        '  "output": "Key rule: submit the request within 5 working days. Exception: '
        'a documented HR exception may apply."\n'
        "}\n\n"
        "Transform this grounded answer into concise_executive_briefing. Preserve the full "
        "answer without silent truncation and do not output citation metadata.\n\n"
        "Answerable status: true\n"
        "Grounded answer:\n"
        f"{grounded_result.answer}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_tone_messages(
    grounded_result: GroundedAnswerResult,
    tone: ToneName,
) -> list[dict[str, str]]:
    """Build tone-specific prompt messages."""

    builders = {
        ToneName.FORMAL_REPORT_SUMMARY: build_formal_report_summary_messages,
        ToneName.CASUAL_MESSAGE: build_casual_message_messages,
        ToneName.CONCISE_EXECUTIVE_BRIEFING: build_concise_executive_briefing_messages,
    }
    return builders[tone](grounded_result)


def parse_tone_model_output(
    raw_output: str,
    *,
    expected_tone: ToneName = ToneName.FORMAL_REPORT_SUMMARY,
) -> ToneModelOutput:
    """Parse strict JSON tone output and validate it against the existing contract."""

    try:
        parsed = json.loads(raw_output.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg}") from exc
    output = ToneModelOutput.model_validate(parsed)
    if output.tone != expected_tone:
        raise ValueError(f"tone output must use {expected_tone}")
    return output


def _citation_metadata_values(grounded_result: GroundedAnswerResult) -> list[str]:
    values: list[str] = []
    for citation in grounded_result.citations:
        values.extend(
            [
                citation.citation_id,
                citation.chunk_id,
                citation.document_id,
                citation.title,
                citation.section_heading,
                citation.source_path,
            ]
        )
    return [value for value in values if value]


def validate_no_tone_citation_metadata(
    model_output: ToneModelOutput,
    grounded_result: GroundedAnswerResult,
) -> None:
    """Reject model output that includes locally owned citation metadata."""

    output_text = model_output.output
    leaked_values = [value for value in _citation_metadata_values(grounded_result) if value in output_text]
    if leaked_values:
        raise ValueError("tone output must not include citation metadata")


def _required_surface_markers(grounded_answer: str) -> list[str]:
    markers: list[str] = []
    lower_answer = grounded_answer.lower()
    for phrase in [
        "working days",
        "returning to Kuwait",
        "phishing report button",
    ]:
        if phrase.lower() in lower_answer:
            markers.append(phrase)
    markers.extend(re.findall(r"[\w.\-+]+@[\w.\-]+\.\w+", grounded_answer))
    markers.extend(re.findall(r"\bKWD\s+\d+\b", grounded_answer))
    return markers


def validate_tone_surface_preservation(
    model_output: ToneModelOutput,
    grounded_result: GroundedAnswerResult,
) -> None:
    """Apply deterministic checks for exact surface facts that must not drift."""

    output = model_output.output
    missing = [marker for marker in _required_surface_markers(grounded_result.answer) if marker not in output]
    if missing:
        raise ValueError(f"tone output did not preserve required surface markers: {missing}")
    if "no exceptions mentioned" in output.lower() and "no exceptions mentioned" not in grounded_result.answer.lower():
        raise ValueError("tone output added an unsupported no-exceptions statement")
    if not re.search(r"\b(leave|off)\b", grounded_result.answer, flags=re.IGNORECASE):
        if re.search(r"\b(days?\s+off|time\s+off)\b", output, flags=re.IGNORECASE):
            raise ValueError("tone output added unsupported leave or time-off wording")


def _validation_reason(raw_output: str, exc: Exception) -> str:
    return f"Unable to validate tone model JSON: {exc}; raw_output={raw_output}"


def call_and_validate_formal_tone_model(
    *,
    chat_client: ChatClient,
    messages: list[dict[str, str]],
    grounded_result: GroundedAnswerResult,
    generation_config: GenerationConfig,
) -> tuple[ToneModelOutput, bool]:
    """Call the formal model and apply the one-retry malformed-output policy."""

    return call_and_validate_tone_model(
        chat_client=chat_client,
        messages=messages,
        grounded_result=grounded_result,
        generation_config=generation_config,
        expected_tone=ToneName.FORMAL_REPORT_SUMMARY,
    )


def call_and_validate_tone_model(
    *,
    chat_client: ChatClient,
    messages: list[dict[str, str]],
    grounded_result: GroundedAnswerResult,
    generation_config: GenerationConfig,
    expected_tone: ToneName,
) -> tuple[ToneModelOutput, bool]:
    """Call the model and apply the one-retry malformed-output policy."""

    attempts = 1 + min(generation_config.repair_retry_count, 1)
    last_reason = "unknown validation failure"
    for attempt in range(attempts):
        raw_output = chat_client.chat(messages, generation_config.chat_params())
        try:
            model_output = parse_tone_model_output(raw_output, expected_tone=expected_tone)
            validate_no_tone_citation_metadata(model_output, grounded_result)
            validate_tone_surface_preservation(model_output, grounded_result)
            return model_output, attempt > 0
        except (ValueError, ValidationError) as exc:
            last_reason = _validation_reason(raw_output, exc)
            if attempt + 1 >= attempts:
                break
            messages = messages + [
                {"role": "assistant", "content": raw_output},
                {
                    "role": "user",
                    "content": (
                        "Your previous response failed validation. Return only one JSON object "
                        "matching this schema exactly: "
                        f'{{"tone": "{expected_tone}", "output": string}}. '
                        "Do not include citation metadata. "
                        f"Validation error: {exc}"
                    ),
                },
            ]

    raise ModelOutputError(reason=last_reason, repair_retry_used=attempts > 1)


def build_tone_result(
    model_output: ToneModelOutput,
    grounded_result: GroundedAnswerResult,
) -> ToneResult:
    """Construct the application-owned tone result with copied citations."""

    return ToneResult(
        tone=model_output.tone,
        output=model_output.output,
        citations=list(grounded_result.citations),
    )


def transform_formal_report_summary(
    grounded_result: GroundedAnswerResult,
    *,
    chat_client: ChatClient,
    generation_config: GenerationConfig | None = None,
) -> ToneTransformationResult:
    """Transform one validated grounded answer into formal_report_summary."""

    active_config = generation_config or GenerationConfig(
        prompt_version=FORMAL_REPORT_SUMMARY_PROMPT_VERSION
    )
    started = time.perf_counter()
    if not grounded_result.is_answerable:
        model_output = ToneModelOutput(
            tone=ToneName.FORMAL_REPORT_SUMMARY,
            output=UNSUPPORTED_ANSWER,
        )
        tone_result = build_tone_result(model_output, grounded_result)
        return ToneTransformationResult(
            source_answer=grounded_result,
            model_output=model_output,
            tone_result=tone_result,
            repair_retry_used=False,
            latency_seconds=round(time.perf_counter() - started, 4),
        )

    messages = build_formal_report_summary_messages(grounded_result)
    model_output, repair_retry_used = call_and_validate_formal_tone_model(
        chat_client=chat_client,
        messages=messages,
        grounded_result=grounded_result,
        generation_config=active_config,
    )
    tone_result = build_tone_result(model_output, grounded_result)
    return ToneTransformationResult(
        source_answer=grounded_result,
        model_output=model_output,
        tone_result=tone_result,
        repair_retry_used=repair_retry_used,
        latency_seconds=round(time.perf_counter() - started, 4),
    )


def transform_tone(
    grounded_result: GroundedAnswerResult,
    tone: ToneName,
    *,
    chat_client: ChatClient,
    generation_config: GenerationConfig | None = None,
) -> ToneTransformationResult:
    """Transform one validated grounded answer into one selected tone."""

    if tone == ToneName.FORMAL_REPORT_SUMMARY:
        return transform_formal_report_summary(
            grounded_result,
            chat_client=chat_client,
            generation_config=generation_config,
        )

    active_config = generation_config or GenerationConfig(prompt_version=PROMPT_VERSIONS[tone])
    started = time.perf_counter()
    if not grounded_result.is_answerable:
        model_output = ToneModelOutput(tone=tone, output=UNSUPPORTED_ANSWER)
        tone_result = build_tone_result(model_output, grounded_result)
        return ToneTransformationResult(
            source_answer=grounded_result,
            model_output=model_output,
            tone_result=tone_result,
            repair_retry_used=False,
            latency_seconds=round(time.perf_counter() - started, 4),
        )

    messages = build_tone_messages(grounded_result, tone)
    model_output, repair_retry_used = call_and_validate_tone_model(
        chat_client=chat_client,
        messages=messages,
        grounded_result=grounded_result,
        generation_config=active_config,
        expected_tone=tone,
    )
    tone_result = build_tone_result(model_output, grounded_result)
    return ToneTransformationResult(
        source_answer=grounded_result,
        model_output=model_output,
        tone_result=tone_result,
        repair_retry_used=repair_retry_used,
        latency_seconds=round(time.perf_counter() - started, 4),
    )


def transform_casual_message(
    grounded_result: GroundedAnswerResult,
    *,
    chat_client: ChatClient,
    generation_config: GenerationConfig | None = None,
) -> ToneTransformationResult:
    """Transform one validated grounded answer into casual_message."""

    return transform_tone(
        grounded_result,
        ToneName.CASUAL_MESSAGE,
        chat_client=chat_client,
        generation_config=generation_config,
    )


def transform_concise_executive_briefing(
    grounded_result: GroundedAnswerResult,
    *,
    chat_client: ChatClient,
    generation_config: GenerationConfig | None = None,
) -> ToneTransformationResult:
    """Transform one validated grounded answer into concise_executive_briefing."""

    return transform_tone(
        grounded_result,
        ToneName.CONCISE_EXECUTIVE_BRIEFING,
        chat_client=chat_client,
        generation_config=generation_config,
    )


def build_all_tone_result(
    grounded_result: GroundedAnswerResult,
    tone_results: list[ToneResult],
) -> AllToneResult:
    """Build the application-owned all-tone result in stable order."""

    by_tone = {result.tone: result for result in tone_results}
    ordered = [by_tone[tone] for tone in TONE_ORDER]
    return AllToneResult(original_answer=grounded_result.answer, variations=ordered)


def transform_all_tones(
    grounded_result: GroundedAnswerResult,
    *,
    chat_client: ChatClient,
    generation_configs: dict[ToneName, GenerationConfig] | None = None,
) -> AllToneTransformationResult:
    """Sequentially transform one grounded answer into all three required tones."""

    configs = generation_configs or {}
    results: dict[ToneName, ToneTransformationResult] = {}
    for tone in TONE_ORDER:
        results[tone] = transform_tone(
            grounded_result,
            tone,
            chat_client=chat_client,
            generation_config=configs.get(tone),
        )
    all_tone_result = build_all_tone_result(
        grounded_result,
        [results[tone].tone_result for tone in TONE_ORDER],
    )
    return AllToneTransformationResult(
        source_answer=grounded_result,
        all_tone_result=all_tone_result,
        tone_results=results,
    )


def create_live_formal_tone_components(
    *,
    settings: AppSettings | None = None,
    generation_config: GenerationConfig | None = None,
) -> tuple[ChatClient, GenerationConfig]:
    """Create a live watsonx Chat client for tone-transformation calls."""

    active_settings = settings or AppSettings()
    active_config = generation_config or formal_tone_generation_config(active_settings)
    if active_config.generation_model_id != GENERATION_MODEL_ID:
        raise RAGFoundationsError(
            "Configured generation model does not match the verified tone-transformation model.",
            configured_generation_model_id=active_config.generation_model_id,
            expected_generation_model_id=GENERATION_MODEL_ID,
        )
    runtime = create_runtime(active_settings)
    chat_client = WatsonxChatClient(
        api_client=runtime.client,
        project_id=runtime.settings.watsonx_project_id or "",
        model_id=active_config.generation_model_id,
    )
    return chat_client, active_config


def create_live_tone_components(
    *,
    settings: AppSettings | None = None,
) -> tuple[ChatClient, dict[ToneName, GenerationConfig]]:
    """Create a live watsonx Chat client and per-tone configs for smoke scripts."""

    active_settings = settings or AppSettings()
    configs = {tone: tone_generation_config(tone, active_settings) for tone in TONE_ORDER}
    for tone, config in configs.items():
        if config.generation_model_id != GENERATION_MODEL_ID:
            raise RAGFoundationsError(
                "Configured generation model does not match the verified tone-transformation model.",
                tone=tone,
                configured_generation_model_id=config.generation_model_id,
                expected_generation_model_id=GENERATION_MODEL_ID,
            )
    runtime = create_runtime(active_settings)
    chat_client = WatsonxChatClient(
        api_client=runtime.client,
        project_id=runtime.settings.watsonx_project_id or "",
        model_id=configs[ToneName.FORMAL_REPORT_SUMMARY].generation_model_id,
    )
    return chat_client, configs
