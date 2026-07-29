from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rag_foundations import final_v2
from rag_foundations.prompt_assets import grounded_messages


EVIDENCE_PATHS = [
    final_v2.RETRIEVAL_RESULTS_PATH,
    final_v2.GROUNDED_RESULTS_PATH,
    final_v2.TONE_RESULTS_PATH,
    final_v2.RENDERED_REQUESTS_PATH,
    final_v2.EXECUTION_MANIFEST_PATH,
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): final_v2.sha256_file(path) for path in paths if path.exists()}


def final2_g_021_request() -> dict:
    question = next(
        item
        for item in load_json(final_v2.QUESTIONS_PATH)["questions"]
        if item["question_id"] == "final2-g-021"
    )
    retrieval = load_json(final_v2.RETRIEVAL_RESULTS_PATH)
    record = next(item for item in retrieval["records"] if item["question_id"] == "final2-g-021")
    run = {
        "run_id": "final2-grounded::mistralai/mistral-small-3-1-24b-instruct-2503::final2-g-021",
        "model_id": "mistralai/mistral-small-3-1-24b-instruct-2503",
    }
    messages = grounded_messages(
        "a",
        question=question["question"],
        retrieved_context=final_v2.context_string(record["retrieved_chunks"]),
    )
    return final_v2.grounded_request_entry(
        run,
        question_id=question["question_id"],
        question=question["question"],
        chunks=record["retrieved_chunks"],
        messages=messages,
    )


class FakeModel:
    def __init__(self, model_id: str, api_client: object, project_id: str, calls: list[str]) -> None:
        self.model_id = model_id
        self.api_client = api_client
        self.project_id = project_id
        self.calls = calls

    def chat(self, messages: list[dict[str, str]], params: dict[str, object]) -> dict:
        self.calls.append(self.model_id)
        return {"choices": [{"message": {"content": "{\"ok\": true}"}}]}


class FakeFinalV2ChatClient:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[dict[str, object]] = []

    def chat(self, messages: list[dict[str, str]], *, model: str, max_tokens: int) -> str:
        self.calls.append({"messages": messages, "model": model, "max_tokens": max_tokens})
        if not self.outputs:
            raise AssertionError("unexpected chat call")
        return self.outputs.pop(0)


def patch_final_v2_paths(monkeypatch, base: Path) -> None:
    monkeypatch.setattr(final_v2, "FINAL_V2", base)
    monkeypatch.setattr(final_v2, "SCORING", base / "scoring")
    monkeypatch.setattr(final_v2, "HUMAN_REVIEW", base / "human_review")
    monkeypatch.setattr(final_v2, "MANIFESTS", base / "manifests")
    monkeypatch.setattr(final_v2, "QUESTIONS_PATH", base / "final_questions_v2.json")
    monkeypatch.setattr(final_v2, "TONE_INPUTS_PATH", base / "final_tone_inputs_v2.json")
    monkeypatch.setattr(final_v2, "RUN_PLAN_PATH", base / "run_plan.json")
    monkeypatch.setattr(final_v2, "RETRIEVAL_RESULTS_PATH", base / "retrieval_results.json")
    monkeypatch.setattr(final_v2, "GROUNDED_RESULTS_PATH", base / "grounded_results.jsonl")
    monkeypatch.setattr(final_v2, "TONE_RESULTS_PATH", base / "tone_results.jsonl")
    monkeypatch.setattr(final_v2, "DETERMINISTIC_SCORES_PATH", base / "scoring" / "deterministic_scores.json")
    monkeypatch.setattr(final_v2, "FINAL_METRICS_PATH", base / "scoring" / "final_metrics.json")
    monkeypatch.setattr(final_v2, "MODEL_COMPARISON_PATH", base / "scoring" / "model_comparison.json")
    monkeypatch.setattr(final_v2, "FAILURE_ANALYSIS_PATH", base / "scoring" / "failure_analysis.md")
    monkeypatch.setattr(final_v2, "EXECUTION_MANIFEST_PATH", base / "manifests" / "execution_manifest.json")
    monkeypatch.setattr(final_v2, "ARTIFACT_MANIFEST_PATH", base / "manifests" / "artifact_manifest.json")
    monkeypatch.setattr(final_v2, "RENDERED_REQUESTS_PATH", base / "manifests" / "rendered_requests.json")


def test_final_v2_dry_run_counts() -> None:
    summary = final_v2.dry_run()

    assert summary["final_v2_questions"] == 24
    assert summary["final_v2_tone_inputs"] == 20
    assert summary["query_vectors_planned"] == 24
    assert summary["grounded_initial_generation_calls"] == 48
    assert summary["tone_initial_generation_calls"] == 120
    assert summary["total_initial_chat_calls"] == 168
    assert summary["semantic_judge_calls"] == 0
    assert summary["final_v1_cases"] == 0


def test_artifact_manifest_rejects_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "final_v2"
    patch_final_v2_paths(monkeypatch, base)
    final_v2.ensure_dirs()
    artifact = base / "example.json"
    artifact.write_text("{\"ok\": true}\n", encoding="utf-8")
    final_v2.write_json(
        final_v2.ARTIFACT_MANIFEST_PATH,
        {
            "artifact_count": 1,
            "artifacts": {final_v2.rel(artifact): "0" * 64},
        },
    )

    with pytest.raises(ValueError, match="artifact manifest hash mismatch"):
        final_v2.validate_artifact_manifest()


def test_rendered_requests_cover_final_v2_run_plan() -> None:
    requests = final_v2.read_json(final_v2.RENDERED_REQUESTS_PATH)["requests"]

    assert len(requests) == 168
    final_v2.validate_rendered_requests(requests)


def test_frozen_prompt_manifest_hashes_match_selected_files() -> None:
    assert final_v2.validate_frozen_prompt_manifest() == {
        "grounded_candidate": "A",
        "selected_tone_count": 3,
    }


def test_final_v2_dataset_shape_and_ids() -> None:
    questions = load_json(final_v2.QUESTIONS_PATH)["questions"]
    tones = load_json(final_v2.TONE_INPUTS_PATH)["inputs"]

    assert [item["question_id"] for item in questions] == [f"final2-g-{i:03d}" for i in range(1, 25)]
    assert [item["tone_input_id"] for item in tones] == [f"final2-t-{i:03d}" for i in range(1, 21)]
    assert sum(item["expected_answerable"] for item in questions) == 20
    assert len([item for item in questions if item["category"] == "unsupported"]) == 4
    assert all(item["expected_sources"] for item in questions if item["expected_answerable"])
    assert all(not item["expected_sources"] for item in questions if not item["expected_answerable"])


def test_saved_tone_uncertainties_produce_tone_review_records() -> None:
    requirements = final_v2.derive_human_review_requirements()

    assert requirements["flagged_tone_run_ids"]
    assert requirements["mandatory_tone_group_ids"]


def test_every_flagged_tone_output_is_covered_exactly_once() -> None:
    requirements = final_v2.derive_human_review_requirements()
    groups = final_v2.tone_review_groups()
    covered = []
    for group in groups.values():
        if group["triggered_outputs"]:
            covered.extend(output["run_id"] for output in group["triggered_outputs"])

    assert sorted(covered) == requirements["flagged_tone_run_ids"]
    assert len(covered) == len(set(covered))


def test_grouped_triplet_records_contain_all_three_outputs() -> None:
    groups = final_v2.tone_review_groups()
    required = final_v2.derive_human_review_requirements()["mandatory_tone_group_ids"]
    by_id = {
        f"final2-tone-triplet::{group['model_id']}::{group['tone_input_id']}": group
        for group in groups.values()
    }

    assert required
    for group_id in required:
        assert set(by_id[group_id]["tones"]) == set(final_v2.TONE_ORDER)


def test_clean_grounded_and_tone_sample_requirements_by_model() -> None:
    requirements = final_v2.derive_human_review_requirements()

    assert {
        model: len(run_ids)
        for model, run_ids in requirements["clean_grounded_sample_run_ids_by_model"].items()
    } == {
        final_v2.PRIMARY_MODEL: 3,
        final_v2.PREFERRED_COMPARISON_MODEL: 3,
    }
    assert {
        model: len(group_ids)
        for model, group_ids in requirements["clean_tone_triplet_group_ids_by_model"].items()
    } == {
        final_v2.PRIMARY_MODEL: 2,
        final_v2.PREFERRED_COMPARISON_MODEL: 2,
    }


def test_final2_g_021_legitimate_request_passes_leakage_validation() -> None:
    request = final2_g_021_request()

    final_v2.validate_no_expected_leakage([request])


def test_legitimate_metadata_text_overlap_with_prompt_is_not_a_leak() -> None:
    question = next(
        item
        for item in load_json(final_v2.QUESTIONS_PATH)["questions"]
        if item["question_id"] == "final2-g-021"
    )
    request = final2_g_021_request()

    assert question["expected_answer"] in request["messages"][0]["content"]
    final_v2.validate_no_expected_leakage([request])


def test_unauthorized_expected_answer_sentinel_path_is_rejected() -> None:
    request = final2_g_021_request()
    request["allowlisted_input"]["expected_answer"] = "UNIQUE_FORBIDDEN_SENTINEL_FROM_METADATA"

    try:
        final_v2.validate_no_expected_leakage([request])
    except ValueError as exc:
        assert "unauthorized fields" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unauthorized metadata path was not rejected")


def test_appended_forbidden_sentinel_in_messages_is_rejected() -> None:
    request = final2_g_021_request()
    request["messages"][1]["content"] += "\nUNIQUE_FORBIDDEN_SENTINEL_FROM_EXPECTED_ANSWER"

    try:
        final_v2.validate_no_expected_leakage([request])
    except ValueError as exc:
        assert "construction mismatch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("appended content was not rejected")


def test_evaluation_construction_fields_are_rejected() -> None:
    for field in ["atomic_claims", "expected_sources", "label", "scoring"]:
        request = final2_g_021_request()
        request["allowlisted_input"][field] = []
        try:
            final_v2.validate_no_expected_leakage([request])
        except ValueError as exc:
            assert "unauthorized fields" in str(exc)
        else:  # pragma: no cover
            raise AssertionError(f"unauthorized field was not rejected: {field}")


def test_changing_content_after_reconstruction_is_rejected() -> None:
    request = final2_g_021_request()
    request["messages"][0]["content"] += "\nExtra instruction."

    try:
        final_v2.validate_no_expected_leakage([request])
    except ValueError as exc:
        assert "construction mismatch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("message mutation was not rejected")


def test_tone_request_message_mutation_is_rejected() -> None:
    request = next(
        item
        for item in final_v2.read_json(final_v2.RENDERED_REQUESTS_PATH)["requests"]
        if item["task_type"] == "tone"
    )
    request = json.loads(json.dumps(request))
    request["messages"][1]["content"] += "\nUnexpected extra text."

    with pytest.raises(ValueError, match="tone request construction mismatch"):
        final_v2.validate_no_expected_leakage([request])


def test_watsonx_runtime_creation_is_not_repeated_per_request() -> None:
    runtime_calls = 0
    chat_calls: list[str] = []

    def runtime_factory() -> SimpleNamespace:
        nonlocal runtime_calls
        runtime_calls += 1
        return SimpleNamespace(client=object(), settings=SimpleNamespace(watsonx_project_id="project"))

    def model_factory(model_id: str, api_client: object, project_id: str) -> FakeModel:
        return FakeModel(model_id, api_client, project_id, chat_calls)

    client = final_v2.WatsonxChatClient(runtime_factory=runtime_factory, model_factory=model_factory)

    final_v2.call_with_retries([{"role": "user", "content": "one"}], model="model-a", max_tokens=5, client=client)
    final_v2.call_with_retries([{"role": "user", "content": "two"}], model="model-a", max_tokens=5, client=client)

    assert runtime_calls == 1
    assert chat_calls == ["model-a", "model-a"]


def test_watsonx_model_clients_are_cached_by_model_id() -> None:
    created_models: list[str] = []
    chat_calls: list[str] = []

    def model_factory(model_id: str, api_client: object, project_id: str) -> FakeModel:
        created_models.append(model_id)
        return FakeModel(model_id, api_client, project_id, chat_calls)

    client = final_v2.WatsonxChatClient(
        runtime_factory=lambda: SimpleNamespace(client=object(), settings=SimpleNamespace(watsonx_project_id="project")),
        model_factory=model_factory,
    )

    final_v2.chat_call([{"role": "user", "content": "one"}], model="model-a", max_tokens=5, client=client)
    final_v2.chat_call([{"role": "user", "content": "two"}], model="model-a", max_tokens=5, client=client)
    final_v2.chat_call([{"role": "user", "content": "three"}], model="model-b", max_tokens=5, client=client)

    assert created_models == ["model-a", "model-b"]
    assert set(client.models) == {"model-a", "model-b"}


def test_injected_final_v2_execution_path_uses_frozen_inputs(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "final_v2"
    patch_final_v2_paths(monkeypatch, base)
    final_v2.ensure_dirs()
    question = final_v2.build_final_questions()["questions"][0]
    tone_input = final_v2.build_tone_inputs({"questions": [question]})["inputs"][0]
    final_v2.write_json(final_v2.QUESTIONS_PATH, {"questions": [question]})
    final_v2.write_json(final_v2.TONE_INPUTS_PATH, {"inputs": [tone_input]})
    final_v2.write_json(
        final_v2.RUN_PLAN_PATH,
        {
            "runs": [
                {
                    "run_id": "g1",
                    "task_type": "grounded",
                    "model_id": final_v2.PRIMARY_MODEL,
                    "question_id": question["question_id"],
                },
                {
                    "run_id": "t1",
                    "task_type": "tone",
                    "model_id": final_v2.PRIMARY_MODEL,
                    "tone_input_id": tone_input["tone_input_id"],
                    "question_id": question["question_id"],
                    "target_tone": "formal_report_summary",
                },
            ]
        },
    )
    final_v2.write_json(final_v2.EXECUTION_MANIFEST_PATH, {"status": "test"})
    final_v2.write_json(
        final_v2.RETRIEVAL_RESULTS_PATH,
        {
            "status": "complete",
            "records": [
                {
                    "question_id": question["question_id"],
                    "retrieved_chunks": [
                        {
                            "chunk_id": "chunk-1",
                            "document_id": question["expected_sources"][0]["document_id"],
                            "title": "Policy",
                            "section_heading": question["expected_sources"][0]["section_title"],
                            "source_path": "data/documents_v2_1/example.md",
                            "text": question["expected_sources"][0]["source_quote"],
                            "rank": 1,
                        }
                    ],
                }
            ],
        },
    )

    client = FakeFinalV2ChatClient(
        [
            json.dumps(
                {
                    "answerable": True,
                    "answer": question["expected_answer"],
                    "citation_chunk_ids": ["chunk-1"],
                }
            ),
            json.dumps({"tone": "formal_report_summary", "output": tone_input["grounded_answer"]}),
        ]
    )
    monkeypatch.setattr(final_v2, "compute_scores", lambda: {"status": "complete"})
    monkeypatch.setattr(final_v2, "validate_owner_adjudication", lambda: {"status": "test"})

    summary = final_v2.run_final_v2_execution(chat_client=client)

    assert summary["status"] == "complete"
    assert len(final_v2.read_jsonl(final_v2.GROUNDED_RESULTS_PATH)) == 1
    assert len(final_v2.read_jsonl(final_v2.TONE_RESULTS_PATH)) == 1
    assert len(client.calls) == 2


def test_resume_skips_completed_checkpoints_without_rewriting(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "final_v2"
    patch_final_v2_paths(monkeypatch, base)
    final_v2.ensure_dirs()
    question = final_v2.build_final_questions()["questions"][0]
    final_v2.write_json(final_v2.QUESTIONS_PATH, {"questions": [question]})
    final_v2.write_json(final_v2.TONE_INPUTS_PATH, {"inputs": []})
    final_v2.write_json(
        final_v2.RUN_PLAN_PATH,
        {
            "runs": [
                {
                    "run_id": "g-complete",
                    "task_type": "grounded",
                    "model_id": final_v2.PRIMARY_MODEL,
                    "question_id": question["question_id"],
                },
                {
                    "run_id": "g-new",
                    "task_type": "grounded",
                    "model_id": final_v2.PRIMARY_MODEL,
                    "question_id": question["question_id"],
                },
            ]
        },
    )
    chunk = {
        "chunk_id": "chunk-1",
        "document_id": question["expected_sources"][0]["document_id"],
        "title": "Policy",
        "section_heading": question["expected_sources"][0]["section_title"],
        "source_path": "data/documents_v2_1/example.md",
        "text": question["expected_sources"][0]["source_quote"],
        "rank": 1,
    }
    final_v2.write_json(final_v2.RETRIEVAL_RESULTS_PATH, {"status": "complete", "records": [{"question_id": question["question_id"], "retrieved_chunks": [chunk]}]})
    final_v2.write_json(final_v2.EXECUTION_MANIFEST_PATH, {"status": "test"})
    completed = {
        "run_id": "g-complete",
        "task_type": "grounded",
        "model_id": final_v2.PRIMARY_MODEL,
        "question_id": question["question_id"],
        "raw_initial_output": json.dumps(
            {
                "answerable": True,
                "answer": question["expected_answer"],
                "citation_chunk_ids": ["chunk-1"],
            }
        ),
        "final_application_output": {
            "answerable": True,
            "answer": question["expected_answer"],
            "citation_chunk_ids": ["chunk-1"],
        },
        "resolved_citations": [{"chunk_id": "chunk-1"}],
        "retrieved_chunk_ids": ["chunk-1"],
        "repair_retry_count": 0,
        "normalization_status": None,
    }
    final_v2.TONE_RESULTS_PATH.write_text("", encoding="utf-8")

    rendered_complete = final_v2.grounded_request_entry(
        {
            "run_id": "g-complete",
            "task_type": "grounded",
            "model_id": final_v2.PRIMARY_MODEL,
            "question_id": question["question_id"],
        },
        question_id=question["question_id"],
        question=question["question"],
        chunks=[chunk],
        messages=grounded_messages(
            "a",
            question=question["question"],
            retrieved_context=final_v2.context_string([chunk]),
        ),
    )
    completed["request_prompt_hashes"] = [final_v2.sha256_text(message["content"]) for message in rendered_complete["messages"]]
    original_line = json.dumps(completed, sort_keys=True, ensure_ascii=False)
    final_v2.GROUNDED_RESULTS_PATH.write_text(original_line + "\n", encoding="utf-8")
    final_v2.write_json(
        final_v2.RENDERED_REQUESTS_PATH,
        {"created_at_utc": "2026-01-01T00:00:00+00:00", "requests": [rendered_complete]},
    )
    client = FakeFinalV2ChatClient(
        [
            json.dumps(
                {
                    "answerable": True,
                    "answer": question["expected_answer"],
                    "citation_chunk_ids": ["chunk-1"],
                }
            )
        ]
    )
    monkeypatch.setattr(final_v2, "compute_scores", lambda: {"status": "complete"})
    monkeypatch.setattr(final_v2, "validate_owner_adjudication", lambda: {"status": "test"})

    final_v2.run_final_v2_execution(resume=True, chat_client=client)

    lines = final_v2.GROUNDED_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines]
    assert lines[0] == original_line
    assert [row["run_id"] for row in rows] == ["g-complete", "g-new"]
    assert len(final_v2.read_json(final_v2.RENDERED_REQUESTS_PATH)["requests"]) == 2
    assert len(client.calls) == 1


def test_owner_adjudication_validates_against_saved_outputs() -> None:
    summary = final_v2.validate_owner_adjudication()

    assert summary["adjudicator"]
    assert len(summary["grounded_decisions"]) == 24
    assert len(summary["tone_triplet_decisions"]) == 40
    assert summary["owner_adjudication_sha256"] == final_v2.sha256_canonical_file(
        final_v2.OWNER_ADJUDICATION_PATH
    )


def test_public_final_v2_parser_rejects_fake_mode() -> None:
    with pytest.raises(SystemExit):
        final_v2.main(["--execute", "--fake"])


def test_owner_adjudication_rejects_duplicate_grounded_ids(tmp_path: Path, monkeypatch) -> None:
    review_dir = tmp_path / "human_review"
    review_dir.mkdir()
    path = review_dir / "owner_adjudication.json"
    path.write_text(final_v2.OWNER_ADJUDICATION_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["grounded_decisions"][1]["run_id"] = data["grounded_decisions"][0]["run_id"]
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(final_v2, "HUMAN_REVIEW", review_dir)
    monkeypatch.setattr(final_v2, "OWNER_ADJUDICATION_PATH", path)

    with pytest.raises(ValueError, match="duplicate owner adjudication"):
        final_v2.validate_owner_adjudication()


def test_final_metrics_preserve_deterministic_and_human_layers() -> None:
    metrics = final_v2.read_json(final_v2.FINAL_METRICS_PATH)

    assert metrics["scoring_layer"] == "owner_verified_hybrid_final"
    assert metrics["adjudication"]["semantic_review_method"] == "manual owner verification"
    assert metrics["adjudication"]["independent_owner_signoff"] is True
    assert metrics["layers_preserved"]["deterministic_layer_preserved"] is True
    assert metrics["layers_preserved"]["human_layer_preserved"] is True
    assert metrics["record_details"]["grounded"]
    assert {
        detail["label_source"]
        for detail in metrics["record_details"]["grounded"].values()
    } == {"human", "deterministic_clean"}
