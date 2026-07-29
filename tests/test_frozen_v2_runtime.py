from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from rag_foundations import frozen_v2_runtime
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.pipeline import run_question
from rag_foundations.schemas import RetrievedChunk, ScoreType, ToneName


class FakeEmbeddings:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def embed_query(self, query: str) -> list[float]:
        return [1.0] * 768


class FakeModel:
    responses: list[str] = []
    prompts: list[list[dict[str, str]]] = []

    def __init__(self, model_id: str, api_client: object, project_id: str) -> None:
        self.model_id = model_id
        self.api_client = api_client
        self.project_id = project_id

    def chat(self, messages: list[dict[str, str]], params: dict[str, object]) -> dict:
        self.prompts.append(messages)
        if self.responses:
            content = self.responses.pop(0)
        else:
            user = messages[-1]["content"]
            chunk_id = re.search(r"\[(chunk-[a-f0-9]+)\]", user)
            if chunk_id:
                content = json.dumps(
                    {
                        "answerable": True,
                        "answer": "The policy answer is supported by the retrieved context.",
                        "citation_chunk_ids": [chunk_id.group(1)],
                    }
                )
            else:
                tone = "formal_report_summary"
                for candidate in [item.value for item in ToneName]:
                    if candidate in user or candidate in messages[0]["content"]:
                        tone = candidate
                        break
                content = json.dumps({"tone": tone, "output": f"{tone}: rewritten answer"})
        return {"choices": [{"message": {"content": content}}]}


def fake_runtime_factory(settings: object | None = None) -> SimpleNamespace:
    return SimpleNamespace(client=object(), settings=SimpleNamespace(watsonx_project_id="project"))


@pytest.fixture(autouse=True)
def reset_fake_model() -> None:
    FakeModel.responses = []
    FakeModel.prompts = []


def fixed_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-ce42d98784e641b9b33898d3",
        document_id="employee_leave_attendance_policy",
        corpus_version="asteron-policies-v2.1",
        chunker_config_id="section-token-v1-size-220-overlap-40-minilm",
        embedding_model_id=frozen_v2_runtime.EMBEDDING_MODEL,
        embedding_dimension=768,
        index_id="chunk-220-overlap-40",
        rank=1,
        raw_score=0.99,
        score_type=ScoreType.COSINE_SIMILARITY,
        text="Part-time employees receive pro-rated annual leave based on contracted weekly hours.",
        title="Employee Leave and Attendance Policy",
        section_heading="3. Annual Leave Entitlement",
        source_path="data/documents_v2_1/employee_leave_attendance_policy.md",
        retriever_name="faiss-watsonx-flat-ip-retriever",
        retriever_config={"top_k": 5},
    )


def fake_components(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        frozen_v2_runtime,
        "load_faiss_store",
        lambda path: SimpleNamespace(index=SimpleNamespace(ntotal=1, d=768), metadata=[], config={}),
    )
    monkeypatch.setattr(frozen_v2_runtime, "validate_index_configuration", lambda **kwargs: None)
    monkeypatch.setattr(
        frozen_v2_runtime,
        "search_faiss_store",
        lambda store, query_vector, *, top_k: [fixed_chunk()],
    )
    return frozen_v2_runtime.create_frozen_v2_pipeline_components(
        runtime_factory=fake_runtime_factory,
        model_factory=FakeModel,
        embeddings_cls=FakeEmbeddings,
    )


def test_frozen_runtime_verifies_protected_hashes() -> None:
    summary = frozen_v2_runtime.verify_frozen_v2_artifacts()

    assert summary["configuration"]["selected_grounded_candidate"] == "A"
    assert summary["index_manifest"]["selected_retrieval_configuration"] == "chunk-220-overlap-40"


def test_frozen_runtime_rejects_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    protected = frozen_v2_runtime.read_json(frozen_v2_runtime.PROTECTED_HASHES_PATH)
    protected["protected_files"]["prompts/v2/grounded/candidate_a.user.txt"] = "0" * 64
    path = tmp_path / "protected_hashes.json"
    path.write_text(json.dumps(protected), encoding="utf-8")
    monkeypatch.setattr(frozen_v2_runtime, "PROTECTED_HASHES_PATH", path)

    with pytest.raises(ValueError, match="frozen artifact hash mismatch"):
        frozen_v2_runtime.verify_frozen_v2_artifacts()


def test_frozen_cli_runtime_uses_candidate_a_top5_and_local_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_question("What receipt threshold applies to expense documentation?", components=fake_components(monkeypatch))

    assert result.metadata["top_k"] == 5
    assert result.metadata["generation_model_id"] == frozen_v2_runtime.PRIMARY_MODEL
    assert result.grounded_result.citations
    assert result.grounded_result.citations[0].title
    assert "prompts/v2/grounded/candidate_a" not in result.grounded_result.answer


def test_frozen_cli_runtime_supports_all_baseline_v2_tones(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_question("What standard applies to business records and corrections?", all_tones=True, components=fake_components(monkeypatch))

    assert result.all_tone_result is not None
    assert [item.tone for item in result.all_tone_result.variations] == [
        ToneName.FORMAL_REPORT_SUMMARY,
        ToneName.CASUAL_MESSAGE,
        ToneName.CONCISE_EXECUTIVE_BRIEFING,
    ]
    assert set(result.metadata["tone_prompt_versions"].values()) == {
        "baseline_v2::formal_report_summary",
        "baseline_v2::casual_message",
        "baseline_v2::concise_executive_briefing",
    }


def test_frozen_runtime_normalizes_unsupported_refusal_and_skips_tone_call(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeModel.responses = [
        json.dumps({"answerable": False, "answer": "No answer is present.", "citation_chunk_ids": []})
    ]

    result = run_question("Which office dress-code color is mandatory?", tone=ToneName.CASUAL_MESSAGE, components=fake_components(monkeypatch))

    assert result.grounded_result.answer == UNSUPPORTED_ANSWER
    assert result.grounded_result.is_answerable is False
    assert result.tone_result is not None
    assert result.tone_result.output == UNSUPPORTED_ANSWER
    assert len(FakeModel.prompts) == 1


def test_frozen_runtime_repairs_malformed_grounded_json(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeModel.responses = [
        "not json",
        json.dumps(
            {
                "answerable": True,
                "answer": "The answer is repaired.",
                "citation_chunk_ids": ["chunk-ce42d98784e641b9b33898d3"],
            }
        ),
    ]

    result = run_question("How is annual leave calculated for a part-time employee?", components=fake_components(monkeypatch))

    assert result.grounded_result.answer == "The answer is repaired."
    assert result.metadata["grounded_repair_retry_used"] is True


def test_frozen_runtime_repairs_malformed_tone_json(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeModel.responses = [
        json.dumps(
            {
                "answerable": True,
                "answer": "The policy answer is supported.",
                "citation_chunk_ids": ["chunk-ce42d98784e641b9b33898d3"],
            }
        ),
        "not json",
        json.dumps({"tone": "casual_message", "output": "casual_message: repaired"}),
    ]

    result = run_question("How is annual leave calculated for a part-time employee?", tone=ToneName.CASUAL_MESSAGE, components=fake_components(monkeypatch))

    assert result.tone_result is not None
    assert result.tone_result.output == "casual_message: repaired"
    assert result.metadata["tone_repair_retry_used"] is True
