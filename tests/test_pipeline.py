from __future__ import annotations

import pytest

from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import RAGFoundationsError
from rag_foundations.grounded_generation import GenerationConfig, GroundedGenerationResult
from rag_foundations.pipeline import PipelineComponents, run_question
from rag_foundations.schemas import (
    AllToneResult,
    Citation,
    GroundedAnswerResult,
    GroundedModelOutput,
    RetrievedChunk,
    ScoreType,
    ToneModelOutput,
    ToneName,
    ToneResult,
)
from rag_foundations.tone_transformation import (
    AllToneTransformationResult,
    ToneTransformationResult,
)


class FakeEmbeddingProvider:
    def embed_query(self, query: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeChatClient:
    def chat(self, messages: list[dict[str, str]], params: dict[str, object]) -> str:
        raise AssertionError("pipeline tests must not call a real chat client")


def citation() -> Citation:
    return Citation(
        citation_id="citation-1-chunk-1",
        chunk_id="chunk-1",
        document_id="policy-remote-work",
        title="Remote Work Policy",
        section_heading="5. Maximum Remote Days and Office Attendance",
        source_path="data/documents_v2_1/flexible_work_workplace_access_policy.md",
        supporting_quote="Eligible employees may work remotely up to 2 working days per week.",
        corpus_version="asteron-policies-v1",
        index_id="asteron_policies_watsonx_faiss_v1",
    )


def retrieved_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="policy-remote-work",
        corpus_version="asteron-policies-v1",
        chunker_config_id="section-token-v1-size-220-overlap-40-minilm",
        embedding_model_id="ibm/granite-embedding-278m-multilingual",
        embedding_dimension=768,
        index_id="asteron_policies_watsonx_faiss_v1",
        rank=1,
        raw_score=0.91,
        score_type=ScoreType.COSINE_SIMILARITY,
        text="Eligible employees may work remotely up to 2 working days per week.",
        title="Remote Work Policy",
        section_heading="5. Maximum Remote Days and Office Attendance",
        source_path="data/documents_v2_1/flexible_work_workplace_access_policy.md",
        retriever_name="faiss-watsonx-flat-ip-retriever",
        retriever_config={"top_k": 5},
    )


def grounded_answer(answerable: bool = True) -> GroundedAnswerResult:
    if not answerable:
        return GroundedAnswerResult(answer=UNSUPPORTED_ANSWER, is_answerable=False, citations=[])
    return GroundedAnswerResult(
        answer="Eligible employees may work remotely up to 2 working days per week.",
        is_answerable=True,
        citations=[citation()],
    )


class FakeComponents:
    def __init__(self, *, answerable: bool = True) -> None:
        self.answerable = answerable
        self.retrieve_calls: list[dict[str, object]] = []
        self.generate_calls = 0
        self.tone_calls: list[ToneName] = []
        self.all_tone_calls = 0
        self.embedding_provider = FakeEmbeddingProvider()
        self.chat_client = FakeChatClient()
        self.generation_config = GenerationConfig()
        self.tone_generation_configs = {
            tone: GenerationConfig(prompt_version=f"{tone.value}-prompt")
            for tone in ToneName
        }

    def retrieve(self, question: str, *, top_k: int, embedding_provider: object) -> list[RetrievedChunk]:
        self.retrieve_calls.append(
            {"question": question, "top_k": top_k, "embedding_provider": embedding_provider}
        )
        return [retrieved_chunk()]

    def generate(
        self,
        question: str,
        *,
        retrieved_chunks: list[RetrievedChunk],
        chat_client: object,
        generation_config: GenerationConfig,
    ) -> GroundedGenerationResult:
        self.generate_calls += 1
        result = grounded_answer(self.answerable)
        return GroundedGenerationResult(
            question=question,
            retrieved_chunks=retrieved_chunks,
            model_output=GroundedModelOutput(
                answer=result.answer,
                is_answerable=result.is_answerable,
                citation_chunk_ids=[item.chunk_id for item in result.citations],
            ),
            answer_result=result,
            repair_retry_used=False,
            latency_seconds=0.01,
        )

    def transform_tone(
        self,
        grounded_result: GroundedAnswerResult,
        tone: ToneName,
        *,
        chat_client: object,
        generation_config: GenerationConfig | None,
    ) -> ToneTransformationResult:
        self.tone_calls.append(tone)
        tone_result = ToneResult(
            tone=tone,
            output=f"{tone.value}: {grounded_result.answer}",
            citations=list(grounded_result.citations),
        )
        model_output = ToneModelOutput(tone=tone, output=tone_result.output)
        return ToneTransformationResult(
            source_answer=grounded_result,
            model_output=model_output,
            tone_result=tone_result,
            repair_retry_used=False,
            latency_seconds=0.02,
        )

    def transform_all_tones(
        self,
        grounded_result: GroundedAnswerResult,
        *,
        chat_client: object,
        generation_configs: dict[ToneName, GenerationConfig],
    ) -> AllToneTransformationResult:
        self.all_tone_calls += 1
        tone_results = {
            tone: self.transform_tone(
                grounded_result,
                tone,
                chat_client=chat_client,
                generation_config=generation_configs[tone],
            )
            for tone in ToneName
        }
        all_result = AllToneResult(
            original_answer=grounded_result.answer,
            variations=[tone_results[tone].tone_result for tone in ToneName],
        )
        return AllToneTransformationResult(
            source_answer=grounded_result,
            all_tone_result=all_result,
            tone_results=tone_results,
        )

    def components(self) -> PipelineComponents:
        return PipelineComponents(
            embedding_provider=self.embedding_provider,
            chat_client=self.chat_client,
            generation_config=self.generation_config,
            tone_generation_configs=self.tone_generation_configs,
            retrieve_fn=self.retrieve,
            generate_fn=self.generate,
            transform_tone_fn=self.transform_tone,
            transform_all_tones_fn=self.transform_all_tones,
        )


def test_grounded_only_answerable_request() -> None:
    fake = FakeComponents()

    result = run_question("How many remote days?", components=fake.components())

    assert result.grounded_result.is_answerable is True
    assert result.grounded_result.citations[0].document_id == "policy-remote-work"
    assert result.tone_result is None
    assert result.all_tone_result is None


def test_grounded_only_unsupported_request() -> None:
    fake = FakeComponents(answerable=False)

    result = run_question("Does Asteron provide gym memberships?", components=fake.components())

    assert result.grounded_result.answer == UNSUPPORTED_ANSWER
    assert result.grounded_result.citations == []
    assert fake.tone_calls == []
    assert fake.all_tone_calls == 0


def test_one_tone_request() -> None:
    fake = FakeComponents()

    result = run_question(
        "How many remote days?",
        tone=ToneName.CASUAL_MESSAGE,
        components=fake.components(),
    )

    assert result.tone_result is not None
    assert result.tone_result.tone == ToneName.CASUAL_MESSAGE
    assert fake.tone_calls == [ToneName.CASUAL_MESSAGE]


def test_all_tone_request() -> None:
    fake = FakeComponents()

    result = run_question("How many remote days?", all_tones=True, components=fake.components())

    assert result.all_tone_result is not None
    assert [variation.tone for variation in result.all_tone_result.variations] == list(ToneName)
    assert fake.all_tone_calls == 1


def test_unsupported_request_bypasses_all_tone_calls() -> None:
    fake = FakeComponents(answerable=False)

    result = run_question("Does Asteron provide gym memberships?", all_tones=True, components=fake.components())

    assert result.all_tone_result is not None
    assert [variation.output for variation in result.all_tone_result.variations] == [
        UNSUPPORTED_ANSWER,
        UNSUPPORTED_ANSWER,
        UNSUPPORTED_ANSWER,
    ]
    assert fake.tone_calls == []
    assert fake.all_tone_calls == 0


def test_citations_preserved_across_outputs() -> None:
    fake = FakeComponents()

    result = run_question("How many remote days?", all_tones=True, components=fake.components())

    assert result.all_tone_result is not None
    expected = result.grounded_result.citations
    assert all(variation.citations == expected for variation in result.all_tone_result.variations)


def test_top_5_retrieval_is_requested() -> None:
    fake = FakeComponents()

    run_question("How many remote days?", components=fake.components())

    assert fake.retrieve_calls[0]["top_k"] == 5


def test_pipeline_loads_index_through_existing_retrieval_without_rebuild() -> None:
    fake = FakeComponents()

    run_question("How many remote days?", components=fake.components())

    assert len(fake.retrieve_calls) == 1
    assert fake.generate_calls == 1


def test_blank_question_rejected_safely() -> None:
    fake = FakeComponents()

    with pytest.raises(ValueError, match="question must not be blank"):
        run_question("   ", components=fake.components())

    assert fake.retrieve_calls == []


def test_component_errors_remain_sanitized() -> None:
    def broken_retrieve(question: str, *, top_k: int, embedding_provider: object) -> list[RetrievedChunk]:
        raise RAGFoundationsError("retrieval failed api_key=secret-value")

    fake = FakeComponents()
    components = fake.components()
    components.retrieve_fn = broken_retrieve

    with pytest.raises(RAGFoundationsError) as exc_info:
        run_question("How many remote days?", components=components)

    assert "secret-value" not in str(exc_info.value)
    assert "api_key= <redacted>" in str(exc_info.value)


def test_tone_and_all_tones_are_mutually_exclusive() -> None:
    fake = FakeComponents()

    with pytest.raises(ValueError, match="mutually exclusive"):
        run_question(
            "How many remote days?",
            tone=ToneName.FORMAL_REPORT_SUMMARY,
            all_tones=True,
            components=fake.components(),
        )
