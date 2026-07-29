"""Application orchestration for CLI RAG requests."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import Field

from rag_foundations.config import AppSettings
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.faiss_store import validate_query_text
from rag_foundations.grounded_generation import (
    DEFAULT_TOP_K,
    ChatClient,
    EmbeddingProvider,
    GenerationConfig,
    GroundedGenerationResult,
    generate_grounded_answer,
    retrieve_top_k_chunks,
)
from rag_foundations.schemas import (
    AllToneResult,
    GroundedAnswerResult,
    RetrievedChunk,
    StrictModel,
    ToneName,
    ToneResult,
)
from rag_foundations.tone_transformation import (
    AllToneTransformationResult,
    TONE_ORDER,
    ToneTransformationResult,
    transform_all_tones,
    transform_tone,
)


RetrieveFn = Callable[..., list[RetrievedChunk]]
GenerateFn = Callable[..., GroundedGenerationResult]
TransformToneFn = Callable[..., ToneTransformationResult]
TransformAllTonesFn = Callable[..., AllToneTransformationResult]


class PipelineResult(StrictModel):
    """Small application-level result for CLI serialization."""

    question: str
    grounded_result: GroundedAnswerResult
    tone_result: ToneResult | None = None
    all_tone_result: AllToneResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class PipelineComponents:
    """Injectable retrieval, generation, and tone-transformation components."""

    embedding_provider: EmbeddingProvider
    chat_client: ChatClient
    generation_config: GenerationConfig
    tone_generation_configs: dict[ToneName, GenerationConfig] = field(default_factory=dict)
    retrieve_fn: RetrieveFn = retrieve_top_k_chunks
    generate_fn: GenerateFn = generate_grounded_answer
    transform_tone_fn: TransformToneFn = transform_tone
    transform_all_tones_fn: TransformAllTonesFn = transform_all_tones


def create_live_pipeline_components(settings: AppSettings | None = None) -> PipelineComponents:
    """Create frozen Final v2 watsonx components for the end-to-end CLI."""

    from rag_foundations.frozen_v2_runtime import create_frozen_v2_pipeline_components

    return create_frozen_v2_pipeline_components(settings=settings)


def _coerce_tone(tone: ToneName | str | None) -> ToneName | None:
    if tone is None:
        return None
    return ToneName(tone)


def _unsupported_tone_result(grounded_result: GroundedAnswerResult, tone: ToneName) -> ToneResult:
    return ToneResult(tone=tone, output=UNSUPPORTED_ANSWER, citations=list(grounded_result.citations))


def _unsupported_all_tones_result(grounded_result: GroundedAnswerResult) -> AllToneResult:
    return AllToneResult(
        original_answer=grounded_result.answer,
        variations=[_unsupported_tone_result(grounded_result, tone) for tone in TONE_ORDER],
    )


def _metadata(
    *,
    mode: str,
    top_k: int,
    grounded_generation: GroundedGenerationResult,
    generation_config: GenerationConfig,
    tone_generation_configs: dict[ToneName, GenerationConfig],
    tone_generation: ToneTransformationResult | None,
    all_tone_generation: AllToneTransformationResult | None,
    elapsed_seconds: float,
) -> dict[str, Any]:
    retrieved_chunks = grounded_generation.retrieved_chunks
    first_chunk = retrieved_chunks[0] if retrieved_chunks else None
    data: dict[str, Any] = {
        "mode": mode,
        "top_k": top_k,
        "retrieved_chunk_count": len(retrieved_chunks),
        "grounded_generation_latency_seconds": grounded_generation.latency_seconds,
        "grounded_repair_retry_used": grounded_generation.repair_retry_used,
        "request_latency_seconds": round(elapsed_seconds, 4),
        "grounded_prompt_version": generation_config.prompt_version,
        "generation_model_id": generation_config.generation_model_id,
        "temperature": generation_config.temperature,
        "top_p": generation_config.top_p,
        "maximum_output_tokens": generation_config.max_output_tokens,
        "request_timeout_seconds": generation_config.request_timeout_seconds,
        "repair_retry_count": generation_config.repair_retry_count,
    }
    if first_chunk is not None:
        data.update(
            {
                "embedding_model_id": first_chunk.embedding_model_id,
                "embedding_dimension": first_chunk.embedding_dimension,
                "index_id": first_chunk.index_id,
            }
        )
    if tone_generation is not None:
        data.update(
            {
                "tone_prompt_version": tone_generation_configs.get(
                    tone_generation.tone_result.tone,
                    GenerationConfig(),
                ).prompt_version,
                "tone_repair_retry_used": tone_generation.repair_retry_used,
                "tone_latency_seconds": tone_generation.latency_seconds,
            }
        )
    if all_tone_generation is not None:
        data["tone_prompt_versions"] = {
            tone.value: tone_generation_configs.get(tone, GenerationConfig()).prompt_version
            for tone in TONE_ORDER
        }
        data["tone_repair_retry_used_by_tone"] = {
            tone.value: result.repair_retry_used
            for tone, result in all_tone_generation.tone_results.items()
        }
        data["tone_latency_seconds_by_tone"] = {
            tone.value: result.latency_seconds for tone, result in all_tone_generation.tone_results.items()
        }
    return data


def run_question(
    question: str,
    *,
    tone: ToneName | str | None = None,
    all_tones: bool = False,
    top_k: int = DEFAULT_TOP_K,
    components: PipelineComponents | None = None,
) -> PipelineResult:
    """Run retrieval, grounded generation, and optional tone transformation."""

    validated_question = validate_query_text(question)
    selected_tone = _coerce_tone(tone)
    if selected_tone is not None and all_tones:
        raise ValueError("--tone and --all-tones are mutually exclusive")

    started = time.perf_counter()
    active_components = components or create_live_pipeline_components()
    retrieved_chunks = active_components.retrieve_fn(
        validated_question,
        top_k=top_k,
        embedding_provider=active_components.embedding_provider,
    )
    grounded_generation = active_components.generate_fn(
        validated_question,
        retrieved_chunks=retrieved_chunks,
        chat_client=active_components.chat_client,
        generation_config=active_components.generation_config,
    )
    grounded_result = grounded_generation.answer_result

    mode = "grounded_only"
    tone_generation: ToneTransformationResult | None = None
    all_tone_generation: AllToneTransformationResult | None = None
    tone_result: ToneResult | None = None
    all_tone_result: AllToneResult | None = None

    if selected_tone is not None:
        mode = f"tone:{selected_tone.value}"
        if grounded_result.is_answerable:
            tone_generation = active_components.transform_tone_fn(
                grounded_result,
                selected_tone,
                chat_client=active_components.chat_client,
                generation_config=active_components.tone_generation_configs.get(selected_tone),
            )
            tone_result = tone_generation.tone_result
        else:
            tone_result = _unsupported_tone_result(grounded_result, selected_tone)

    if all_tones:
        mode = "all_tones"
        if grounded_result.is_answerable:
            all_tone_generation = active_components.transform_all_tones_fn(
                grounded_result,
                chat_client=active_components.chat_client,
                generation_configs=active_components.tone_generation_configs,
            )
            all_tone_result = all_tone_generation.all_tone_result
        else:
            all_tone_result = _unsupported_all_tones_result(grounded_result)

    return PipelineResult(
        question=validated_question,
        grounded_result=grounded_result,
        tone_result=tone_result,
        all_tone_result=all_tone_result,
        metadata=_metadata(
            mode=mode,
            top_k=top_k,
            grounded_generation=grounded_generation,
            generation_config=active_components.generation_config,
            tone_generation_configs=active_components.tone_generation_configs,
            tone_generation=tone_generation,
            all_tone_generation=all_tone_generation,
            elapsed_seconds=time.perf_counter() - started,
        ),
    )
