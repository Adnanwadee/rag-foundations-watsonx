"""Frozen Final v2 runtime used by the public CLI."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag_foundations.config import AppSettings
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import CitationValidationError, ModelOutputError
from rag_foundations.faiss_store import (
    load_faiss_store,
    search_faiss_store,
    validate_index_configuration,
    validate_query_text,
)
from rag_foundations.integrity import canonical_sha256_file, raw_sha256_file
from rag_foundations.grounded_generation import (
    GenerationConfig,
    GroundedGenerationResult,
    build_grounded_answer_result,
    parse_grounded_model_output,
    validate_citation_chunk_ids,
)
from rag_foundations.prompt_assets import grounded_messages, tone_messages
from rag_foundations.schemas import (
    AllToneResult,
    GroundedAnswerResult,
    GroundedModelOutput,
    RetrievedChunk,
    ToneModelOutput,
    ToneName,
    ToneResult,
)
from rag_foundations.tone_transformation import AllToneTransformationResult, ToneTransformationResult
from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider
from rag_foundations.watsonx_models import create_runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_MODEL = "ibm/granite-4-h-small"
EMBEDDING_MODEL = "ibm/granite-embedding-278m-multilingual"
TOP_K = 5
PROTECTED_HASHES_PATH = REPO_ROOT / "data/evaluation/final_v2/manifests/protected_hashes.json"
FROZEN_CONFIGURATION_PATH = REPO_ROOT / "data/manifests/frozen/frozen_configuration_v2.json"
FROZEN_INDEX_MANIFEST_PATH = REPO_ROOT / "data/manifests/frozen/frozen_index_manifest_v2.json"
FROZEN_PROMPT_MANIFEST_PATH = REPO_ROOT / "data/manifests/frozen/frozen_prompt_manifest_v2.json"
TONE_ORDER = [
    ToneName.FORMAL_REPORT_SUMMARY,
    ToneName.CASUAL_MESSAGE,
    ToneName.CONCISE_EXECUTIVE_BRIEFING,
]
PROMPT_TONE_FILES = {
    "formal_report_summary": "formal",
    "casual_message": "casual",
    "concise_executive_briefing": "executive",
}


class FrozenWatsonxChatClient:
    """Chat client that reuses one watsonx runtime and one model instance."""

    def __init__(
        self,
        *,
        runtime: Any,
        model_id: str = PRIMARY_MODEL,
        model_factory: Any | None = None,
    ) -> None:
        self.runtime = runtime
        self.model_id = model_id
        self.model_factory = model_factory
        self.models: dict[str, Any] = {}

    def model_for(self, model_id: str) -> Any:
        if model_id not in self.models:
            factory = self.model_factory
            if factory is None:
                from ibm_watsonx_ai.foundation_models import ModelInference

                factory = ModelInference
            self.models[model_id] = factory(
                model_id=model_id,
                api_client=self.runtime.client,
                project_id=self.runtime.settings.watsonx_project_id,
            )
        return self.models[model_id]

    def chat(self, messages: list[dict[str, str]], params: dict[str, Any]) -> str:
        response = self.model_for(self.model_id).chat(messages=messages, params=params)
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelOutputError(
                reason="Chat response did not contain choices[0].message.content",
                repair_retry_used=False,
            ) from exc
        return str(content).strip()


def sha256_file(path: Path | str) -> str:
    p = REPO_ROOT / path if isinstance(path, str) else path
    return canonical_sha256_file(p)


def read_json(path: Path | str) -> Any:
    p = REPO_ROOT / path if isinstance(path, str) else path
    return json.loads(p.read_text(encoding="utf-8"))


def _protected_hash(path: str, protected: dict[str, str]) -> None:
    if path not in protected:
        raise ValueError(f"missing protected hash for frozen artifact: {path}")
    if sha256_file(path) != protected[path]:
        raise ValueError(f"frozen artifact hash mismatch: {path}")


def verify_frozen_v2_artifacts() -> dict[str, Any]:
    protected = read_json(PROTECTED_HASHES_PATH)["protected_files"]
    config = read_json(FROZEN_CONFIGURATION_PATH)
    index_manifest = read_json(FROZEN_INDEX_MANIFEST_PATH)
    prompt_manifest = read_json(FROZEN_PROMPT_MANIFEST_PATH)
    required_paths = [
        "data/manifests/frozen/frozen_configuration_v2.json",
        "data/manifests/frozen/frozen_prompt_manifest_v2.json",
        "data/manifests/frozen/frozen_index_manifest_v2.json",
        "data/indexes/selected/asteron_policies_watsonx.index",
        "data/indexes/selected/metadata.json",
        "data/indexes/selected/index_config.json",
        "prompts/v2/grounded/candidate_a.system.txt",
        "prompts/v2/grounded/candidate_a.user.txt",
        "prompts/v2/tones/formal.system.txt",
        "prompts/v2/tones/formal.user.txt",
        "prompts/v2/tones/casual.system.txt",
        "prompts/v2/tones/casual.user.txt",
        "prompts/v2/tones/executive.system.txt",
        "prompts/v2/tones/executive.user.txt",
        "prompts/v2/few_shot/formal.json",
        "prompts/v2/few_shot/casual.json",
        "prompts/v2/few_shot/executive.json",
    ]
    for path in required_paths:
        _protected_hash(path, protected)
    if config.get("selected_grounded_candidate") != "A":
        raise ValueError("frozen runtime requires grounded Candidate A")
    if config.get("generation_model_id") != PRIMARY_MODEL:
        raise ValueError("frozen runtime requires the primary Final v2 model")
    if config.get("embedding_configuration", {}).get("top_k") != TOP_K:
        raise ValueError("frozen runtime requires Top-5 retrieval")
    if index_manifest.get("selected_retrieval_configuration") != "chunk-220-overlap-40":
        raise ValueError("frozen runtime requires chunk-220-overlap-40")
    validate_frozen_index_manifest(index_manifest)
    validate_frozen_configuration(config, index_manifest)
    if prompt_manifest.get("grounded", {}).get("candidate") != "A":
        raise ValueError("frozen runtime prompt manifest requires Candidate A")
    grounded = prompt_manifest["grounded"]
    _protected_hash(grounded["system_prompt_path"], protected)
    if sha256_file(grounded["system_prompt_path"]) != grounded["system_prompt_sha256"]:
        raise ValueError("frozen runtime prompt manifest system hash mismatch")
    _protected_hash(grounded["user_prompt_path"], protected)
    if sha256_file(grounded["user_prompt_path"]) != grounded["user_prompt_sha256"]:
        raise ValueError("frozen runtime prompt manifest user hash mismatch")
    selected_tones = prompt_manifest.get("selected_tones", {})
    if set(selected_tones) != {tone.value for tone in TONE_ORDER}:
        raise ValueError("frozen runtime prompt manifest selected tone set is incomplete")
    for tone_name, tone_manifest in selected_tones.items():
        stem = PROMPT_TONE_FILES[tone_name]
        expected_paths = {
            "system_prompt_path": f"prompts/v2/tones/{stem}.system.txt",
            "user_prompt_path": f"prompts/v2/tones/{stem}.user.txt",
            "few_shot_path": f"prompts/v2/few_shot/{stem}.json",
        }
        for key, expected_path in expected_paths.items():
            if tone_manifest.get(key) != expected_path:
                raise ValueError(f"frozen runtime prompt manifest path mismatch: {tone_name} {key}")
        for path_key, hash_key in [
            ("system_prompt_path", "system_prompt_sha256"),
            ("user_prompt_path", "user_prompt_sha256"),
            ("few_shot_path", "few_shot_sha256"),
        ]:
            _protected_hash(tone_manifest[path_key], protected)
            if sha256_file(tone_manifest[path_key]) != tone_manifest[hash_key]:
                raise ValueError(f"frozen runtime prompt manifest hash mismatch: {tone_name} {path_key}")
    return {"configuration": config, "index_manifest": index_manifest, "prompt_manifest": prompt_manifest}


def _manifest_hash(path: str, expected: str) -> None:
    if raw_sha256_file(REPO_ROOT / path) != expected:
        raise ValueError(f"frozen manifest internal hash mismatch: {path}")


def validate_frozen_index_manifest(index_manifest: dict[str, Any]) -> None:
    if index_manifest.get("index_path") != "data/indexes/selected/asteron_policies_watsonx.index":
        raise ValueError("frozen index manifest selected index path mismatch")
    _manifest_hash(index_manifest["index_path"], index_manifest["index_sha256"])
    _manifest_hash(index_manifest["metadata_path"], index_manifest["metadata_sha256"])
    _manifest_hash(index_manifest["index_config_path"], index_manifest["index_config_sha256"])
    index_config = read_json(index_manifest["index_config_path"])
    expected = {
        "embedding_model_id": EMBEDDING_MODEL,
        "embedding_dimension": 768,
        "faiss_type": "IndexFlatIP",
        "top_k": TOP_K,
        "chunk_size_tokens": 220,
        "chunk_overlap_tokens": 40,
    }
    for key, value in expected.items():
        source = index_manifest
        if key in {"chunk_size_tokens", "chunk_overlap_tokens"}:
            source = index_config["chunker_configuration"]
        if source.get(key) != value:
            raise ValueError(f"frozen index manifest {key} mismatch")
    if index_config.get("index_version") != "faiss-flat-ip-v1":
        raise ValueError("frozen index manifest FAISS index type mismatch")


def validate_frozen_configuration(config: dict[str, Any], index_manifest: dict[str, Any]) -> None:
    _manifest_hash("data/manifest_v2_1.json", config["document_manifest_sha256"])
    _manifest_hash("data/corpus_fact_registry_v2_1.json", config["fact_registry_sha256"])
    dataset_paths = {
        "diagnostic_regressions_v2_1": "data/evaluation/development_v2_1/diagnostic_regressions_v2_1.json",
        "grounded_questions_v2_1": "data/evaluation/development_v2_1/grounded_questions_v2_1.json",
        "tone_inputs_v2_1": "data/evaluation/development_v2_1/tone_inputs_v2_1.json",
        "validation_summary_v2_1": "data/evaluation/development_v2_1/validation_summary_v2_1.json",
    }
    for key, path in dataset_paths.items():
        _manifest_hash(path, config["development_dataset_hashes"][key])
    if config["prompt_manifest_path"] != "data/manifests/frozen/frozen_prompt_manifest_v2.json":
        raise ValueError("frozen configuration prompt manifest path mismatch")
    if config["embedding_configuration"]["index_manifest_path"] != "data/manifests/frozen/frozen_index_manifest_v2.json":
        raise ValueError("frozen configuration index manifest path mismatch")
    if index_manifest["selected_retrieval_configuration"] != config["selected_retrieval_configuration"]:
        raise ValueError("frozen configuration/index selection mismatch")


def selected_index_dir() -> Path:
    manifest = read_json(FROZEN_INDEX_MANIFEST_PATH)
    return REPO_ROOT / str(Path(manifest["index_path"]).parent)


def _context_string(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{chunk.chunk_id}] {chunk.title} / {chunk.section_heading}\n{chunk.text}"
        for chunk in chunks
    )


def _canonicalized_grounded_output(raw_output: str) -> str:
    parsed = json.loads(raw_output.strip())
    if parsed.get("answerable") is False and parsed.get("citation_chunk_ids") == []:
        parsed["answer"] = UNSUPPORTED_ANSWER
    if parsed.get("is_answerable") is False and parsed.get("citation_chunk_ids") == []:
        parsed["answer"] = UNSUPPORTED_ANSWER
    return json.dumps(parsed, ensure_ascii=False)


def _call_and_validate_grounded_v2(
    *,
    chat_client: Any,
    messages: list[dict[str, str]],
    retrieved_chunks: list[RetrievedChunk],
    generation_config: GenerationConfig,
) -> tuple[GroundedModelOutput, bool]:
    attempts = 1 + min(generation_config.repair_retry_count, 1)
    last_reason = "unknown validation failure"
    active_messages = messages
    for attempt in range(attempts):
        raw_output = chat_client.chat(active_messages, generation_config.chat_params())
        try:
            model_output = parse_grounded_model_output(_canonicalized_grounded_output(raw_output))
            validate_citation_chunk_ids(model_output, retrieved_chunks)
            return model_output, attempt > 0
        except (ValueError, ValidationError, CitationValidationError) as exc:
            last_reason = f"Unable to validate Final v2 grounded JSON: {exc}"
            if attempt + 1 >= attempts:
                break
            active_messages = active_messages + [
                {"role": "assistant", "content": raw_output},
                {"role": "user", "content": "Return only valid JSON matching the required schema."},
            ]
    raise ModelOutputError(reason=last_reason, repair_retry_used=attempts > 1)


def generate_grounded_answer_v2(
    question: str,
    *,
    retrieved_chunks: list[RetrievedChunk],
    chat_client: Any,
    generation_config: GenerationConfig | None = None,
) -> GroundedGenerationResult:
    active_config = generation_config or frozen_grounded_generation_config()
    messages = grounded_messages(
        "a",
        question=question,
        retrieved_context=_context_string(retrieved_chunks),
    )
    started = time.perf_counter()
    model_output, repair_retry_used = _call_and_validate_grounded_v2(
        chat_client=chat_client,
        messages=messages,
        retrieved_chunks=retrieved_chunks,
        generation_config=active_config,
    )
    return GroundedGenerationResult(
        question=question,
        retrieved_chunks=retrieved_chunks,
        model_output=model_output,
        answer_result=build_grounded_answer_result(model_output, retrieved_chunks),
        repair_retry_used=repair_retry_used,
        latency_seconds=round(time.perf_counter() - started, 4),
    )


def _call_and_validate_tone_v2(
    *,
    chat_client: Any,
    messages: list[dict[str, str]],
    expected_tone: ToneName,
    generation_config: GenerationConfig,
) -> tuple[ToneModelOutput, bool]:
    attempts = 1 + min(generation_config.repair_retry_count, 1)
    last_reason = "unknown validation failure"
    active_messages = messages
    for attempt in range(attempts):
        raw_output = chat_client.chat(active_messages, generation_config.chat_params())
        try:
            parsed = ToneModelOutput.model_validate(json.loads(raw_output.strip()))
            if parsed.tone != expected_tone:
                raise ValueError(f"tone output must use {expected_tone.value}")
            return parsed, attempt > 0
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            last_reason = f"Unable to validate Final v2 tone JSON: {exc}"
            if attempt + 1 >= attempts:
                break
            active_messages = active_messages + [
                {"role": "assistant", "content": raw_output},
                {"role": "user", "content": f'Return only valid JSON: {{"tone":"{expected_tone.value}","output":"text"}}.'},
            ]
    raise ModelOutputError(reason=last_reason, repair_retry_used=attempts > 1)


def frozen_grounded_generation_config() -> GenerationConfig:
    return GenerationConfig(
        generation_model_id=PRIMARY_MODEL,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=500,
        request_timeout_seconds=60.0,
        repair_retry_count=1,
        prompt_version="final-v2-grounded-candidate-a",
    )


def frozen_tone_generation_config(tone: ToneName) -> GenerationConfig:
    return replace(
        frozen_grounded_generation_config(),
        max_output_tokens=350,
        prompt_version=f"baseline_v2::{tone.value}",
    )


def create_frozen_v2_pipeline_components(
    settings: AppSettings | None = None,
    *,
    runtime_factory: Any = create_runtime,
    model_factory: Any | None = None,
    embeddings_cls: Any | None = None,
) -> Any:
    from rag_foundations.pipeline import PipelineComponents

    verify_frozen_v2_artifacts()
    active_settings = settings or AppSettings()
    runtime = runtime_factory(active_settings)
    store = load_faiss_store(selected_index_dir())
    validate_index_configuration(
        index=store.index,
        metadata=store.metadata,
        config=store.config,
        expected_embedding_model_id=EMBEDDING_MODEL,
    )
    embedding_provider = WatsonxEmbeddingProvider(
        model_id=EMBEDDING_MODEL,
        api_client=runtime.client,
        settings=active_settings,
        embeddings_cls=embeddings_cls,
    )
    chat_client = FrozenWatsonxChatClient(runtime=runtime, model_factory=model_factory)
    last_question = {"value": ""}

    def retrieve_frozen(
        question: str,
        *,
        top_k: int,
        embedding_provider: Any,
    ) -> list[RetrievedChunk]:
        if top_k != TOP_K:
            raise ValueError("Final v2 frozen runtime requires Top-5 retrieval")
        vector = embedding_provider.embed_query(validate_query_text(question))
        return search_faiss_store(store, vector, top_k=TOP_K)

    def generate_frozen(
        question: str,
        *,
        retrieved_chunks: list[RetrievedChunk],
        chat_client: Any,
        generation_config: GenerationConfig,
    ) -> GroundedGenerationResult:
        last_question["value"] = question
        return generate_grounded_answer_v2(
            question,
            retrieved_chunks=retrieved_chunks,
            chat_client=chat_client,
            generation_config=generation_config,
        )

    def transform_tone_frozen(
        grounded_result: GroundedAnswerResult,
        tone: ToneName,
        *,
        chat_client: Any,
        generation_config: GenerationConfig | None,
    ) -> ToneTransformationResult:
        active_config = generation_config or frozen_tone_generation_config(tone)
        messages = tone_messages(
            tone.value,
            original_question=last_question["value"],
            grounded_answer=grounded_result.answer,
            protected_elements="{}",
            version="v2",
        )
        started = time.perf_counter()
        model_output, repair_retry_used = _call_and_validate_tone_v2(
            chat_client=chat_client,
            messages=messages,
            expected_tone=tone,
            generation_config=active_config,
        )
        tone_result = ToneResult(tone=tone, output=model_output.output, citations=list(grounded_result.citations))
        return ToneTransformationResult(
            source_answer=grounded_result,
            model_output=model_output,
            tone_result=tone_result,
            repair_retry_used=repair_retry_used,
            latency_seconds=round(time.perf_counter() - started, 4),
        )

    def transform_all_tones_frozen(
        grounded_result: GroundedAnswerResult,
        *,
        chat_client: Any,
        generation_configs: dict[ToneName, GenerationConfig],
    ) -> AllToneTransformationResult:
        tone_results = {
            tone: transform_tone_frozen(
                grounded_result,
                tone,
                chat_client=chat_client,
                generation_config=generation_configs[tone],
            )
            for tone in TONE_ORDER
        }
        all_result = AllToneResult(
            original_answer=grounded_result.answer,
            variations=[tone_results[tone].tone_result for tone in TONE_ORDER],
        )
        return AllToneTransformationResult(
            source_answer=grounded_result,
            all_tone_result=all_result,
            tone_results=tone_results,
        )

    return PipelineComponents(
        embedding_provider=embedding_provider,
        chat_client=chat_client,
        generation_config=frozen_grounded_generation_config(),
        tone_generation_configs={tone: frozen_tone_generation_config(tone) for tone in TONE_ORDER},
        retrieve_fn=retrieve_frozen,
        generate_fn=generate_frozen,
        transform_tone_fn=transform_tone_frozen,
        transform_all_tones_fn=transform_all_tones_frozen,
    )
