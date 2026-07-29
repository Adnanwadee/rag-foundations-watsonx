"""Grounded generation and local citation resolution."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import ValidationError

from rag_foundations.config import AppSettings
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import CitationValidationError, ModelOutputError, RAGFoundationsError
from rag_foundations.faiss_store import (
    WATSONX_EMBEDDING_MODEL_ID,
    WATSONX_FAISS_DIR,
    load_faiss_store,
    search_faiss_store,
    validate_index_configuration,
    validate_query_text,
)
from rag_foundations.schemas import Citation, GroundedAnswerResult, GroundedModelOutput, RetrievedChunk
from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider
from rag_foundations.watsonx_models import create_runtime


GENERATION_MODEL_ID = "ibm/granite-4-h-small"
GROUNDING_PROMPT_VERSION = "grounded-generation-v1.1"
DEFAULT_TOP_K = 5
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 1.0
DEFAULT_MAX_OUTPUT_TOKENS = 500
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
DEFAULT_REPAIR_RETRY_COUNT = 1


class ChatClient(Protocol):
    """Minimal Chat API behavior used by the grounded generator."""

    def chat(self, messages: list[dict[str, str]], params: dict[str, Any]) -> str:
        """Return the assistant response text."""


class EmbeddingProvider(Protocol):
    """Minimal query embedding behavior used by the grounded generator."""

    def embed_query(self, query: str) -> list[float]:
        """Return one query embedding vector."""


@dataclass(frozen=True)
class GenerationConfig:
    """Low-variance grounded-generation settings."""

    generation_model_id: str = GENERATION_MODEL_ID
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    repair_retry_count: int = DEFAULT_REPAIR_RETRY_COUNT
    prompt_version: str = GROUNDING_PROMPT_VERSION

    @classmethod
    def from_settings(cls, settings: AppSettings | None = None) -> GenerationConfig:
        active = settings or AppSettings()
        return cls(
            generation_model_id=active.watsonx_generation_model_id or GENERATION_MODEL_ID,
            temperature=(
                active.generation_temperature
                if active.generation_temperature is not None
                else DEFAULT_TEMPERATURE
            ),
            top_p=active.generation_top_p if active.generation_top_p is not None else DEFAULT_TOP_P,
            max_output_tokens=(
                active.generation_max_output_tokens
                if active.generation_max_output_tokens is not None
                else DEFAULT_MAX_OUTPUT_TOKENS
            ),
            request_timeout_seconds=(
                active.request_timeout_seconds
                if active.request_timeout_seconds is not None
                else DEFAULT_REQUEST_TIMEOUT_SECONDS
            ),
            repair_retry_count=active.max_repair_retries,
        )

    def chat_params(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_output_tokens,
        }

    def as_artifact_dict(self, *, sdk_version: str) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "maximum_output_tokens": self.max_output_tokens,
            "request_timeout_seconds": self.request_timeout_seconds,
            "repair_retry_count": self.repair_retry_count,
            "prompt_version": self.prompt_version,
            "generation_model_id": self.generation_model_id,
            "sdk_version": sdk_version,
        }


@dataclass(frozen=True)
class GroundedGenerationResult:
    """Validated grounded answer plus the retrieved chunks used to produce it."""

    question: str
    retrieved_chunks: list[RetrievedChunk]
    model_output: GroundedModelOutput
    answer_result: GroundedAnswerResult
    repair_retry_used: bool
    latency_seconds: float


class WatsonxChatClient:
    """Small wrapper around the verified watsonx.ai Chat API."""

    def __init__(self, *, api_client: Any, project_id: str, model_id: str = GENERATION_MODEL_ID) -> None:
        from ibm_watsonx_ai.foundation_models import ModelInference

        self._model = ModelInference(model_id=model_id, api_client=api_client, project_id=project_id)

    def chat(self, messages: list[dict[str, str]], params: dict[str, Any]) -> str:
        response = self._model.chat(messages=messages, params=params)
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelOutputError(
                reason="Chat response did not contain choices[0].message.content",
                repair_retry_used=False,
            ) from exc
        return str(content).strip()


def build_grounded_messages(question: str, retrieved_chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    """Build the strict grounding prompt for the Chat API."""

    validate_query_text(question)
    if not retrieved_chunks:
        raise ValueError("retrieved_chunks must not be empty")

    context_parts: list[str] = []
    for chunk in retrieved_chunks:
        context_parts.append(
            "\n".join(
                [
                    f"chunk_id: {chunk.chunk_id}",
                    f"document_id: {chunk.document_id}",
                    f"document_name: {chunk.title}",
                    f"section_title: {chunk.section_heading}",
                    "chunk_text:",
                    chunk.text,
                ]
            )
        )

    system_prompt = (
        "You are a grounded policy question-answering assistant. Use only the supplied "
        "retrieved context. Do not use external or pretrained factual knowledge. Do not infer "
        "facts that are absent from the context. Preserve exact numbers, dates, conditions, "
        "exceptions, limits, required actions, and prohibited actions. A question is answerable "
        "when the retrieved context explicitly states the answer together with any required "
        "conditions, thresholds, approvals, limits, or exceptions; in that case, set answerable "
        "to true and include those conditions or exceptions in the answer. If the context does not "
        "contain enough evidence, set answerable to false and use exactly: "
        f"{UNSUPPORTED_ANSWER} Cite only chunk IDs included in the supplied context. Return one "
        "JSON object only, with no markdown fences and no text outside JSON. Do not expose "
        "chain-of-thought or internal reasoning."
    )
    user_prompt = (
        "Required JSON schema:\n"
        "{\n"
        '  "answerable": true,\n'
        '  "answer": "answer text",\n'
        '  "citation_chunk_ids": ["valid-retrieved-chunk-id"]\n'
        "}\n\n"
        "For unsupported questions, return:\n"
        "{\n"
        '  "answerable": false,\n'
        f'  "answer": "{UNSUPPORTED_ANSWER}",\n'
        '  "citation_chunk_ids": []\n'
        "}\n\n"
        f"Question:\n{question}\n\n"
        "Retrieved context:\n\n"
        + "\n\n---\n\n".join(context_parts)
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _normalize_model_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("model output must be a JSON object")
    normalized = dict(payload)
    if "answerable" in normalized:
        if "is_answerable" in normalized:
            raise ValueError("model output must not include both answerable and is_answerable")
        normalized["is_answerable"] = normalized.pop("answerable")
    return normalized


def parse_grounded_model_output(raw_output: str) -> GroundedModelOutput:
    """Parse strict JSON model output and validate it against the existing contract."""

    try:
        parsed = json.loads(raw_output.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg}") from exc
    return GroundedModelOutput.model_validate(_normalize_model_payload(parsed))


def validate_citation_chunk_ids(
    model_output: GroundedModelOutput,
    retrieved_chunks: list[RetrievedChunk],
) -> None:
    """Ensure all model-provided citation IDs refer to retrieved chunks only."""

    retrieved_ids = {chunk.chunk_id for chunk in retrieved_chunks}
    unknown_ids = [chunk_id for chunk_id in model_output.citation_chunk_ids if chunk_id not in retrieved_ids]
    if unknown_ids:
        raise CitationValidationError(
            "Model cited chunk IDs that were not retrieved.",
            unknown_chunk_ids=unknown_ids,
            retrieved_chunk_ids=sorted(retrieved_ids),
        )


def resolve_citations_locally(
    model_output: GroundedModelOutput,
    retrieved_chunks: list[RetrievedChunk],
) -> list[Citation]:
    """Construct full Citation objects from retrieved metadata, not model metadata."""

    validate_citation_chunk_ids(model_output, retrieved_chunks)
    retrieved_by_id = {chunk.chunk_id: chunk for chunk in retrieved_chunks}
    citations: list[Citation] = []
    for index, chunk_id in enumerate(model_output.citation_chunk_ids, start=1):
        chunk = retrieved_by_id[chunk_id]
        citations.append(
            Citation(
                citation_id=f"citation-{index}-{chunk.chunk_id}",
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                section_heading=chunk.section_heading,
                source_path=chunk.source_path,
                supporting_quote=chunk.text,
                corpus_version=chunk.corpus_version,
                page_number=chunk.page_number,
                index_id=chunk.index_id,
                experiment_id=chunk.experiment_id,
            )
        )
    return citations


def build_grounded_answer_result(
    model_output: GroundedModelOutput,
    retrieved_chunks: list[RetrievedChunk],
) -> GroundedAnswerResult:
    """Validate model citations and return the application-owned grounded result."""

    citations = resolve_citations_locally(model_output, retrieved_chunks)
    return GroundedAnswerResult(
        answer=model_output.answer,
        is_answerable=model_output.is_answerable,
        citations=citations,
    )


def _validation_reason(raw_output: str, exc: Exception) -> str:
    return f"Unable to validate grounded model JSON: {exc}; raw_output={raw_output}"


def call_and_validate_grounded_model(
    *,
    chat_client: ChatClient,
    messages: list[dict[str, str]],
    retrieved_chunks: list[RetrievedChunk],
    generation_config: GenerationConfig,
) -> tuple[GroundedModelOutput, bool]:
    """Call the model and apply the one-retry malformed-output policy."""

    attempts = 1 + min(generation_config.repair_retry_count, 1)
    last_reason = "unknown validation failure"
    for attempt in range(attempts):
        raw_output = chat_client.chat(messages, generation_config.chat_params())
        try:
            model_output = parse_grounded_model_output(raw_output)
            validate_citation_chunk_ids(model_output, retrieved_chunks)
            return model_output, attempt > 0
        except (ValueError, ValidationError, CitationValidationError) as exc:
            last_reason = _validation_reason(raw_output, exc)
            if attempt + 1 >= attempts:
                break
            messages = messages + [
                {
                    "role": "assistant",
                    "content": raw_output,
                },
                {
                    "role": "user",
                    "content": (
                        "Your previous response failed validation. Return only one JSON object "
                        "matching this schema exactly: "
                        '{"answerable": boolean, "answer": string, '
                        '"citation_chunk_ids": [string]}. '
                        f"Validation error: {exc}"
                    ),
                },
            ]

    raise ModelOutputError(reason=last_reason, repair_retry_used=attempts > 1)


def generate_grounded_answer(
    question: str,
    *,
    retrieved_chunks: list[RetrievedChunk],
    chat_client: ChatClient,
    generation_config: GenerationConfig | None = None,
) -> GroundedGenerationResult:
    """Generate and validate one grounded answer from already-retrieved chunks."""

    active_config = generation_config or GenerationConfig()
    messages = build_grounded_messages(question, retrieved_chunks)
    started = time.perf_counter()
    model_output, repair_retry_used = call_and_validate_grounded_model(
        chat_client=chat_client,
        messages=messages,
        retrieved_chunks=retrieved_chunks,
        generation_config=active_config,
    )
    answer_result = build_grounded_answer_result(model_output, retrieved_chunks)
    return GroundedGenerationResult(
        question=question,
        retrieved_chunks=retrieved_chunks,
        model_output=model_output,
        answer_result=answer_result,
        repair_retry_used=repair_retry_used,
        latency_seconds=round(time.perf_counter() - started, 4),
    )


def retrieve_top_k_chunks(
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    embedding_provider: EmbeddingProvider,
    index_directory: str = str(WATSONX_FAISS_DIR),
) -> list[RetrievedChunk]:
    """Retrieve Top-K chunks from the persisted watsonx FAISS index."""

    validated_question = validate_query_text(question)
    store = load_faiss_store(index_directory)
    validate_index_configuration(
        index=store.index,
        metadata=store.metadata,
        config=store.config,
        expected_embedding_model_id=WATSONX_EMBEDDING_MODEL_ID,
    )
    query_vector = embedding_provider.embed_query(validated_question)
    return search_faiss_store(store, query_vector, top_k=top_k)


def create_live_grounded_components(
    *,
    settings: AppSettings | None = None,
    generation_config: GenerationConfig | None = None,
) -> tuple[EmbeddingProvider, ChatClient, GenerationConfig]:
    """Create live watsonx embedding and Chat clients for smoke scripts."""

    active_settings = settings or AppSettings()
    active_config = generation_config or GenerationConfig.from_settings(active_settings)
    if active_config.generation_model_id != GENERATION_MODEL_ID:
        raise RAGFoundationsError(
            "Configured generation model does not match the verified grounded-generation model.",
            configured_generation_model_id=active_config.generation_model_id,
            expected_generation_model_id=GENERATION_MODEL_ID,
        )
    runtime = create_runtime(active_settings)
    embedding_provider = WatsonxEmbeddingProvider(
        model_id=WATSONX_EMBEDDING_MODEL_ID,
        api_client=runtime.client,
    )
    chat_client = WatsonxChatClient(
        api_client=runtime.client,
        project_id=runtime.settings.watsonx_project_id or "",
        model_id=active_config.generation_model_id,
    )
    return embedding_provider, chat_client, active_config
