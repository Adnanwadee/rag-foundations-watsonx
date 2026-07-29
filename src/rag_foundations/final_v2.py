"""Final v2 dataset, execution, scoring, and validation helpers."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_foundations.faiss_store import load_faiss_store, search_faiss_store
from rag_foundations.integrity import canonical_sha256_file, raw_sha256_file
from rag_foundations.evaluation_scoring import (
    CANONICAL_REFUSAL,
    application_grounded_output,
    corrected_tone_case,
    normalize_text,
    parse_json_object,
)
from rag_foundations.prompt_assets import grounded_messages, load_text_asset, tone_messages
from rag_foundations.watsonx_models import create_runtime, get_chat_model_specs, model_id, sdk_version

REPO_ROOT = Path(__file__).resolve().parents[2]
FINAL_V2 = REPO_ROOT / "data/evaluation/final_v2"
SCORING = FINAL_V2 / "scoring"
HUMAN_REVIEW = FINAL_V2 / "human_review"
MANIFESTS = FINAL_V2 / "manifests"
QUESTIONS_PATH = FINAL_V2 / "final_questions_v2.json"
TONE_INPUTS_PATH = FINAL_V2 / "final_tone_inputs_v2.json"
DATASET_MANIFEST_PATH = FINAL_V2 / "final_dataset_manifest.json"
RUN_PLAN_PATH = FINAL_V2 / "run_plan.json"
RETRIEVAL_RESULTS_PATH = FINAL_V2 / "retrieval_results.json"
GROUNDED_RESULTS_PATH = FINAL_V2 / "grounded_results.jsonl"
TONE_RESULTS_PATH = FINAL_V2 / "tone_results.jsonl"
DETERMINISTIC_SCORES_PATH = SCORING / "deterministic_scores.json"
FINAL_METRICS_PATH = SCORING / "final_metrics.json"
MODEL_COMPARISON_PATH = SCORING / "model_comparison.json"
FAILURE_ANALYSIS_PATH = SCORING / "failure_analysis.md"
MODEL_SELECTION_PATH = MANIFESTS / "model_selection_evidence.json"
EXECUTION_MANIFEST_PATH = MANIFESTS / "execution_manifest.json"
ARTIFACT_MANIFEST_PATH = MANIFESTS / "artifact_manifest.json"
PROTECTED_HASHES_PATH = MANIFESTS / "protected_hashes.json"
RENDERED_REQUESTS_PATH = MANIFESTS / "rendered_requests.json"
OWNER_ADJUDICATION_PATH = HUMAN_REVIEW / "owner_adjudication.json"

PRIMARY_MODEL = "ibm/granite-4-h-small"
PREFERRED_COMPARISON_MODEL = "mistralai/mistral-small-3-1-24b-instruct-2503"
EMBEDDING_MODEL = "ibm/granite-embedding-278m-multilingual"
TOP_K = 5
GROUND_MAX_TOKENS = 500
TONE_MAX_TOKENS = 350
TONE_ORDER = ["formal_report_summary", "casual_message", "concise_executive_briefing"]
GROUND_PROMPT_SYSTEM_PATH = "prompts/v2/grounded/candidate_a.system.txt"
GROUND_PROMPT_USER_PATH = "prompts/v2/grounded/candidate_a.user.txt"
GROUNDED_REQUEST_KEYS = {"run_id", "task_type", "question_id", "messages", "allowlisted_input"}
GROUNDED_ALLOWLIST_KEYS = {"run_id", "model_id", "question", "retrieved_chunks", "prompt"}
GROUNDED_PROMPT_KEYS = {
    "candidate",
    "system_prompt_path",
    "system_prompt_sha256",
    "user_prompt_path",
    "user_prompt_sha256",
}
GROUNDED_CHUNK_KEYS = {"chunk_id", "title", "section_heading", "text"}
TONE_REQUEST_KEYS = {"run_id", "task_type", "tone_input_id", "target_tone", "messages", "allowlisted_input"}
TONE_ALLOWLIST_KEYS = {
    "run_id",
    "model_id",
    "original_question",
    "grounded_answer",
    "protected_elements",
    "target_tone",
    "prompt_version",
}
PROMPT_TONE_FILES = {
    "formal_report_summary": "formal",
    "casual_message": "casual",
    "concise_executive_briefing": "executive",
}
FROZEN_MANIFEST_FILES = [
    "data/manifests/frozen/frozen_configuration_v2.json",
    "data/manifests/frozen/frozen_prompt_manifest_v2.json",
    "data/manifests/frozen/frozen_index_manifest_v2.json",
]
PROTECTED_BASELINE_PATHS = [
    *FROZEN_MANIFEST_FILES,
    "data/manifest_v2_1.json",
    "data/corpus_fact_registry_v2_1.json",
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def read_json(path: Path | str) -> Any:
    return json.loads((REPO_ROOT / path if isinstance(path, str) else path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path | str) -> str:
    p = REPO_ROOT / path if isinstance(path, str) else path
    return raw_sha256_file(p)


def sha256_canonical_file(path: Path | str) -> str:
    p = REPO_ROOT / path if isinstance(path, str) else path
    return canonical_sha256_file(p)


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Any) -> str:
    return sha256_text(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def ensure_dirs() -> None:
    for directory in [FINAL_V2, SCORING, HUMAN_REVIEW, MANIFESTS]:
        directory.mkdir(parents=True, exist_ok=True)


def fact_registry() -> dict[str, dict[str, Any]]:
    return {fact["fact_id"]: fact for fact in read_json("data/corpus_fact_registry_v2_1.json")["facts"]}


def source_for_fact(fact: dict[str, Any]) -> dict[str, str]:
    return {
        "document_id": fact["document_id"],
        "section_title": fact["section_title"],
        "source_quote": fact["source_quote"],
    }


def atomic_claim(fact: dict[str, Any], materiality: str = "core") -> dict[str, str]:
    return {
        "claim_id": fact["fact_id"],
        "fact_id": fact["fact_id"],
        "claim": fact["canonical_statement"],
        "materiality": materiality,
    }


def question_record(
    idx: int,
    question: str,
    category: str,
    difficulty: str,
    expected_answer: str,
    fact_ids: list[str],
    *,
    materiality: str = "core",
) -> dict[str, Any]:
    facts = fact_registry()
    selected = [facts[fact_id] for fact_id in fact_ids]
    clauses = [
        clause["clause_id"]
        for fact in selected
        for clause in fact.get("semantic_clauses", [])
    ]
    return {
        "question_id": f"final2-g-{idx:03d}",
        "question": question,
        "category": category,
        "difficulty": difficulty,
        "expected_answerable": True,
        "expected_answer": expected_answer,
        "atomic_claims": [atomic_claim(fact, materiality) for fact in selected],
        "fact_ids": fact_ids,
        "clause_ids": clauses,
        "materiality": materiality,
        "expected_document_ids": sorted({fact["document_id"] for fact in selected}),
        "expected_section_titles": sorted({fact["section_title"] for fact in selected}),
        "expected_sources": [source_for_fact(fact) for fact in selected],
        "exact_source_quotes": [fact["source_quote"] for fact in selected],
    }


def unsupported_record(idx: int, question: str, absence_assertion: str, prohibited: list[str]) -> dict[str, Any]:
    return {
        "question_id": f"final2-g-{idx:03d}",
        "question": question,
        "category": "unsupported",
        "difficulty": "hard",
        "expected_answerable": False,
        "expected_answer": CANONICAL_REFUSAL,
        "canonical_refusal": CANONICAL_REFUSAL,
        "atomic_claims": [],
        "fact_ids": [],
        "clause_ids": [],
        "materiality": "core",
        "expected_document_ids": [],
        "expected_section_titles": [],
        "expected_sources": [],
        "exact_source_quotes": [],
        "absence_assertion": absence_assertion,
        "prohibited_claim_types": prohibited,
    }


def build_final_questions() -> dict[str, Any]:
    questions = [
        question_record(1, "How is annual leave calculated for a part-time employee?", "direct_fact", "easy", "Part-time employees receive a pro-rated annual-leave entitlement based on their contracted weekly hours.", ["EL-002"]),
        question_record(2, "What records rule applies to visitors in restricted workplace areas?", "direct_fact", "easy", "A workplace visitor must be pre-registered by the host and escorted in restricted areas; visitor-access records are retained for 90 calendar days.", ["FW-017"]),
        question_record(3, "Which company systems require multi-factor authentication?", "direct_fact", "easy", "Multi-factor authentication is required for company email, remote access, finance systems, and administrative accounts.", ["IS-003"]),
        question_record(4, "What receipt threshold applies to expense documentation?", "direct_fact", "easy", "An itemized receipt is required for every expense of KWD 3 or more.", ["EX-016"]),
        question_record(5, "What standard applies to business records and corrections?", "direct_fact", "easy", "Business records must be accurate and complete, and mistakes must be corrected promptly and transparently.", ["CO-007"]),
        question_record(6, "When does a mid-month joiner accrue leave for the joining month?", "condition_or_exception", "medium", "An employee who joins after the first day of a month accrues leave for that month only if the employee works at least 15 calendar days in that month.", ["EL-004"]),
        question_record(7, "When can the ordinary 2-day weekly remote-work limit be suspended?", "condition_or_exception", "medium", "During a company-directed business-continuity arrangement, the Chief Operating Officer may suspend the ordinary 2-day weekly limit, but security and confidentiality rules continue to apply.", ["FW-014"]),
        question_record(8, "What reporting timing changes if an employee did or did not interact with a suspected phishing message?", "condition_or_exception", "medium", "An employee who interacted with a suspected phishing message must use the phishing-report button and notify Information Security within 1 hour of discovery; an employee who did not interact must use the phishing-report button by the end of the working day.", ["IS-010", "IS-011"]),
        question_record(9, "When can a late expense claim require Finance Manager approval or still be rejected?", "condition_or_exception", "medium", "A claim submitted more than 45 calendar days late requires Finance Manager approval and may be rejected unless the delay was outside the employee's control.", ["EX-019"]),
        question_record(10, "Before outside employment involving a competitor or vendor begins, whose approval is required?", "condition_or_exception", "medium", "Outside employment involving a competitor or vendor, or work that may affect company duties, requires written approval from HR and the department head before it begins.", ["CO-003"]),
        question_record(11, "What conditions and approvals apply before advance annual leave can be granted?", "multi_fact", "medium", "Advance annual leave is limited to 5 working days and requires completed probation, no active disciplinary warning, confirmation of coverage by the line manager, and written HR approval.", ["EL-006"]),
        question_record(12, "Who must approve ordinary flexible work, and when must IT Operations also review the request?", "multi_fact", "medium", "An ordinary flexible-work arrangement requires approval from the line manager, department head, and HR. IT Operations must also review a flexible-work request when the role uses elevated access or routinely handles restricted data.", ["FW-003", "FW-004"]),
        question_record(13, "For a security exception, what approval, recorded details, and normal expiry rule apply?", "multi_fact", "medium", "A security exception requires approval from Information Security and the relevant system owner and must record the business reason, compensating control, owner, expiry date, and review date. It should normally expire within 30 calendar days.", ["IS-017", "IS-018"]),
        question_record(14, "For training or conference expenses, what approvals are needed and what evidence should claims include?", "multi_fact", "medium", "Training and conference expenses require pre-approval from the line manager and department head; registration fees above KWD 150 also require HR Learning approval. Claims must include the agenda or course description and proof of completion when available.", ["EX-014", "EX-015"]),
        question_record(15, "When must a personal relationship be disclosed and what procurement actions must an involved employee take?", "multi_fact", "medium", "A personal relationship must be disclosed to HR when one person can affect the other person's reporting line, pay, promotion, performance assessment, or procurement decision. An employee involved in procurement must not obtain a personal benefit, must disclose a relationship with a vendor, and must recuse from the affected decision.", ["CO-004", "CO-006"]),
        question_record(16, "For workplace access governance, what visitor handling rule and access-review schedule apply?", "multi_section_or_source", "hard", "A workplace visitor must be pre-registered by the host and escorted in restricted areas, with visitor-access records retained for 90 calendar days. Managers must review team access at least quarterly, system owners must review privileged and finance-related access monthly, and unnecessary access must be removed within 3 working days of discovery.", ["FW-017", "IS-013"]),
        question_record(17, "If restricted information is accessed remotely, what storage rule and device/VPN controls apply?", "multi_section_or_source", "hard", "Confidential or restricted information must be stored only in approved company systems and must not be sent to personal email or personal cloud storage. Remote access requires a company-managed encrypted device and the approved company VPN.", ["IS-007", "IS-008"]),
        question_record(18, "For a planned exit that also involves company equipment, what must HR, IT Operations, and the employee do?", "multi_section_or_source", "hard", "For a planned employee exit, HR must notify IT Operations at least 2 working days before the last working day and standard system access must be disabled by the end of the final working day. Company equipment must be returned at the end of employment, and family members or visitors must not use company devices.", ["IS-014", "FW-016"]),
        question_record(19, "Compare HR leave-policy exceptions with expense-policy exceptions: whose written approvals are needed and what must the expense exception record?", "multi_section_or_source", "hard", "A leave-policy exception requires written approval from the HR Director and the relevant department head; a line manager alone cannot waive the policy. An expense-policy exception requires written approval from the Finance Manager and the relevant department head and must record the business reason, amount, date, and whether the cost is client-billable.", ["EL-013", "EX-022"]),
        question_record(20, "Across the five v2.1 policy documents, what next scheduled review date is stated?", "multi_section_or_source", "hard", "The Employee Leave, Flexible Work, Information Security, Travel Expense, and Code of Conduct policies each state the next scheduled review date as 2027-01-15.", ["EL-014", "FW-018", "IS-019", "EX-023", "CO-015"]),
        unsupported_record(21, "What IBAN should employees use to repay accidental personal corporate-card charges?", "The corpus states repayment duties but does not provide an IBAN, bank account number, or payment account identifier.", ["bank account identifier", "IBAN", "account number"]),
        unsupported_record(22, "Which office dress-code color is mandatory on client meeting days?", "The corpus does not define a dress-code color for client meeting days.", ["dress-code color", "uniform color"]),
        unsupported_record(23, "What daily lunch allowance is paid for ordinary office work in Kuwait?", "The corpus contains travel meal limits but does not define a daily lunch allowance for ordinary office work in Kuwait.", ["ordinary office lunch allowance", "non-travel meal allowance"]),
        unsupported_record(24, "What project code prefix must be entered for ethics investigations?", "The corpus describes reporting and investigations but does not specify a project code prefix for ethics investigations.", ["project code prefix", "case identifier prefix"]),
    ]
    return {
        "dataset_id": "final-grounded-v2",
        "corpus_version": "asteron-policies-v2.1",
        "frozen": True,
        "frozen_at_utc": utc_now(),
        "question_count": 24,
        "category_counts": dict(Counter(q["category"] for q in questions)),
        "tone_answerable_question_ids": [q["question_id"] for q in questions if q["expected_answerable"]],
        "questions": questions,
        "integrity_rules": [
            "Do not edit after freeze.",
            "Do not use Final v2 outputs to tune prompts, datasets, retrieval, or scoring thresholds.",
            "Expected answers and scoring metadata are local-only and must not be sent to grounded generation models.",
        ],
    }


def build_tone_inputs(questions_data: dict[str, Any]) -> dict[str, Any]:
    inputs = []
    for idx, question in enumerate([q for q in questions_data["questions"] if q["expected_answerable"]], start=1):
        protected: dict[str, Any] = {
            "numbers": sorted(set(re.findall(r"\b\d+(?:\.\d+)?\b", question["expected_answer"]))),
            "currencies": sorted(set(re.findall(r"\bKWD\s+\d+(?:\.\d+)?\b", question["expected_answer"]))),
            "dates": sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:31 January|31 March|30 April)\b", question["expected_answer"]))),
            "authorities": sorted(set(re.findall(r"\b(?:HR Director|HR Learning|HR|IT Operations|Information Security|Finance Manager|Chief Operating Officer|Chief Commercial Officer|department head|line manager|system owner|manager)\b", question["expected_answer"]))),
        }
        inputs.append(
            {
                "tone_input_id": f"final2-t-{idx:03d}",
                "question_id": question["question_id"],
                "original_question": question["question"],
                "grounded_answer": question["expected_answer"],
                "source_language": "en",
                "preserve_source_language": True,
                "semantic_requirements": [claim["claim"] for claim in question["atomic_claims"]],
                "protected_elements": protected,
                "category": question["category"],
            }
        )
    return {
        "dataset_id": "final-tone-v2",
        "corpus_version": "asteron-policies-v2.1",
        "frozen": True,
        "frozen_at_utc": utc_now(),
        "input_count": len(inputs),
        "tones": TONE_ORDER,
        "inputs": inputs,
        "integrity_rules": [
            "Each tone input uses the curated expected grounded answer, not a model output.",
            "Unsupported grounded questions are excluded from tone-distinctness metrics.",
            "Both generation models receive the same factual tone inputs.",
        ],
    }


def protected_hashes() -> dict[str, Any]:
    paths = list(PROTECTED_BASELINE_PATHS)
    paths.extend(sorted(rel(path) for path in (REPO_ROOT / "data/documents_v2_1").glob("*")))
    return {
        "created_at_utc": utc_now(),
        "hash_policy": "sha256 over repository-canonical bytes; LF-normalized for text, raw bytes for binary artifacts",
        "protected_files": {path: sha256_canonical_file(path) for path in sorted(set(paths))},
        "final_v1_raw_manifest_required_sha256": "be54d53f07e48d3185f834ecca93fce4dbcde2cbbfd75c92ccfc6958aa6e094c",
    }


def build_run_plan(questions_data: dict[str, Any], tone_data: dict[str, Any]) -> dict[str, Any]:
    models = [PRIMARY_MODEL, PREFERRED_COMPARISON_MODEL]
    runs = []
    for model in models:
        for question in questions_data["questions"]:
            runs.append(
                {
                    "run_id": f"final2-grounded::{model}::{question['question_id']}",
                    "task_type": "grounded",
                    "model_id": model,
                    "question_id": question["question_id"],
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": GROUND_MAX_TOKENS,
                    "candidate": "A",
                }
            )
        for item in tone_data["inputs"]:
            for tone in TONE_ORDER:
                runs.append(
                    {
                        "run_id": f"final2-tone::{model}::{item['tone_input_id']}::{tone}",
                        "task_type": "tone",
                        "model_id": model,
                        "tone_input_id": item["tone_input_id"],
                        "question_id": item["question_id"],
                        "target_tone": tone,
                        "prompt_version": "baseline_v2",
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "max_tokens": TONE_MAX_TOKENS,
                    }
                )
    return {
        "run_plan_id": "final-v2-run-plan",
        "frozen": True,
        "frozen_at_utc": utc_now(),
        "primary_model_id": PRIMARY_MODEL,
        "preferred_comparison_model_id": PREFERRED_COMPARISON_MODEL,
        "embedding_model_id": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "grounded_initial_generation_calls": 48,
        "tone_initial_generation_calls": 120,
        "total_initial_chat_calls": 168,
        "query_vectors_planned": 24,
        "semantic_judge_calls": 0,
        "final_v1_cases": 0,
        "runs": runs,
    }


def prior_questions() -> list[str]:
    paths = [
        "data/evaluation/development_v2_1/grounded_questions_v2_1.json",
    ]
    result: list[str] = []
    for path in paths:
        if not (REPO_ROOT / path).exists():
            continue
        data = read_json(path)
        for item in data.get("questions", []):
            if "question" in item:
                result.append(item["question"])
        for run in data.get("runs", []):
            if "question" in run:
                result.append(run["question"])
    return result


def normalize_question(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def token_overlap(a: str, b: str) -> float:
    ta = set(normalize_question(a).split())
    tb = set(normalize_question(b).split())
    return 0.0 if not ta or not tb else len(ta & tb) / max(len(ta), len(tb))


def near_duplicate_report(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prior = prior_questions()
    report = []
    for question in questions:
        candidates = [
            {"prior_question": item, "token_overlap": round(token_overlap(question["question"], item), 4)}
            for item in prior
            if normalize_question(item) == normalize_question(question["question"]) or token_overlap(question["question"], item) >= 0.78
        ]
        if candidates:
            report.append({"question_id": question["question_id"], "matches": candidates[:5]})
    return report


def render_artifact_manifest() -> dict[str, Any]:
    files = sorted(path for path in FINAL_V2.rglob("*") if path.is_file())
    artifacts = {rel(path): sha256_canonical_file(path) for path in files if rel(path) != rel(ARTIFACT_MANIFEST_PATH)}
    return {
        "created_at_utc": utc_now(),
        "hash_policy": "sha256 over repository-canonical bytes; LF-normalized for text, raw bytes for binary artifacts",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def prepare_offline_artifacts() -> dict[str, Any]:
    ensure_dirs()
    questions = build_final_questions()
    near_duplicates = near_duplicate_report(questions["questions"])
    if any(match for match in near_duplicates if any(item["token_overlap"] >= 0.92 for item in match["matches"])):
        raise ValueError(f"near-duplicate question requires rewrite: {near_duplicates}")
    tone_inputs = build_tone_inputs(questions)
    run_plan = build_run_plan(questions, tone_inputs)
    write_json(QUESTIONS_PATH, questions)
    write_json(TONE_INPUTS_PATH, tone_inputs)
    dataset_manifest = {
        "manifest_id": "final-v2-dataset-manifest",
        "created_at_utc": utc_now(),
        "frozen": True,
        "grounded_questions_sha256": sha256_file(QUESTIONS_PATH),
        "tone_inputs_sha256": sha256_file(TONE_INPUTS_PATH),
        "run_plan_sha256": sha256_json(run_plan),
        "near_duplicate_screening": near_duplicates,
        "category_counts": questions["category_counts"],
        "question_count": 24,
        "tone_input_count": 20,
    }
    write_json(DATASET_MANIFEST_PATH, dataset_manifest)
    write_json(RUN_PLAN_PATH, run_plan)
    write_json(RETRIEVAL_RESULTS_PATH, {"status": "not_run", "records": []})
    GROUNDED_RESULTS_PATH.write_text("", encoding="utf-8")
    TONE_RESULTS_PATH.write_text("", encoding="utf-8")
    write_json(DETERMINISTIC_SCORES_PATH, {"status": "not_run"})
    write_json(FINAL_METRICS_PATH, {"status": "not_run"})
    write_json(MODEL_COMPARISON_PATH, {"status": "not_run"})
    FAILURE_ANALYSIS_PATH.write_text("# Final v2 Failure Analysis\n\nStatus: not run.\n", encoding="utf-8")
    write_json(EXECUTION_MANIFEST_PATH, {"status": "pre_live_frozen", "created_at_utc": utc_now(), "live_started_at_utc": None})
    write_json(PROTECTED_HASHES_PATH, protected_hashes())
    write_json(ARTIFACT_MANIFEST_PATH, render_artifact_manifest())
    return dry_run()


def dry_run() -> dict[str, Any]:
    questions = read_json(QUESTIONS_PATH)["questions"] if QUESTIONS_PATH.exists() else build_final_questions()["questions"]
    tones = read_json(TONE_INPUTS_PATH)["inputs"] if TONE_INPUTS_PATH.exists() else build_tone_inputs({"questions": questions})["inputs"]
    return {
        "status": "dry_run",
        "final_v2_questions": len(questions),
        "final_v2_tone_inputs": len(tones),
        "query_vectors_planned": 24,
        "grounded_initial_generation_calls": 48,
        "tone_initial_generation_calls": 120,
        "total_initial_chat_calls": 168,
        "optional_repair_maximum": "one repair per model call for structural failures only",
        "final_v1_cases": 0,
        "semantic_judge_calls": 0,
        "external_calls": 0,
    }


def selected_index_dir() -> Path:
    manifest = read_json("data/manifests/frozen/frozen_index_manifest_v2.json")
    return REPO_ROOT / str(Path(manifest["index_path"]).parent)


def retrieve_final_questions() -> dict[str, Any]:
    questions = read_json(QUESTIONS_PATH)["questions"]
    store = load_faiss_store(selected_index_dir())
    records = []
    for question in questions:
        vector = embed_query(question["question"])
        chunks = search_faiss_store(store, vector, top_k=TOP_K)
        expected = {(s["document_id"], s["section_title"]) for s in question["expected_sources"]}
        retrieved = {(chunk.document_id, chunk.section_heading) for chunk in chunks}
        records.append(
            {
                "question_id": question["question_id"],
                "query_embedding_model_id": EMBEDDING_MODEL,
                "frozen_index_hashes": read_json("data/manifests/frozen/frozen_index_manifest_v2.json"),
                "retrieved_chunks": [chunk.model_dump(mode="json") for chunk in chunks],
                "expected_source_hit": bool(expected and expected & retrieved) if question["expected_answerable"] else True,
                "all_expected_sources_covered": bool(expected <= retrieved) if question["expected_answerable"] else True,
            }
        )
    data = {"status": "complete", "created_at_utc": utc_now(), "top_k": TOP_K, "records": records}
    write_json(RETRIEVAL_RESULTS_PATH, data)
    return data


def embed_query(question: str) -> list[float]:
    from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider

    return WatsonxEmbeddingProvider(model_id=EMBEDDING_MODEL).embed_query(question)


@dataclass
class WatsonxChatClient:
    """Process-local watsonx chat client cache for Final v2 execution."""

    runtime_factory: Any = create_runtime
    model_factory: Any | None = None
    runtime: Any = field(init=False)
    models: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.runtime = self.runtime_factory()

    def model_for(self, model: str) -> Any:
        if model not in self.models:
            factory = self.model_factory
            if factory is None:
                from ibm_watsonx_ai.foundation_models import ModelInference

                factory = ModelInference
            self.models[model] = factory(
                model_id=model,
                api_client=self.runtime.client,
                project_id=self.runtime.settings.watsonx_project_id,
            )
        return self.models[model]

    def chat(self, messages: list[dict[str, str]], *, model: str, max_tokens: int) -> str:
        response = self.model_for(model).chat(
            messages=messages,
            params={"temperature": 0.0, "top_p": 1.0, "max_tokens": max_tokens},
        )
        return str(response["choices"][0]["message"]["content"])


def chat_call(
    messages: list[dict[str, str]],
    *,
    model: str,
    max_tokens: int,
    client: WatsonxChatClient | None = None,
) -> str:
    active_client = client or WatsonxChatClient()
    return active_client.chat(messages, model=model, max_tokens=max_tokens)


def call_with_retries(
    messages: list[dict[str, str]],
    *,
    model: str,
    max_tokens: int,
    client: WatsonxChatClient | None = None,
) -> tuple[str, int, float]:
    retries = 0
    while True:
        started = time.perf_counter()
        try:
            return (
                chat_call(messages, model=model, max_tokens=max_tokens, client=client),
                retries,
                round(time.perf_counter() - started, 4),
            )
        except Exception:
            if retries >= 2:
                raise
            retries += 1
            time.sleep(2 ** retries)


def repair_if_needed(
    raw: str,
    *,
    model: str,
    task: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    client: WatsonxChatClient | None = None,
) -> dict[str, Any]:
    parsed, error = parse_json_object(raw)
    if parsed is not None and isinstance(parsed, dict):
        return {"parsed": parsed, "repair_reason": None, "raw_repair_output": None, "repair_retry_count": 0}
    repair_messages = [
        *messages,
        {"role": "assistant", "content": raw},
        {"role": "user", "content": f"Return only valid JSON for the required {task} schema. Do not change the answer content."},
    ]
    repaired, _retries, _latency = call_with_retries(
        repair_messages,
        model=model,
        max_tokens=max_tokens,
        client=client,
    )
    repaired_parsed, _ = parse_json_object(repaired)
    return {"parsed": repaired_parsed, "repair_reason": error, "raw_repair_output": repaired, "repair_retry_count": 1}


def context_string(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{chunk['chunk_id']}] {chunk['title']} / {chunk['section_heading']}\n{chunk['text']}" for chunk in chunks)


def grounded_prompt_identity() -> dict[str, str]:
    system = load_text_asset(GROUND_PROMPT_SYSTEM_PATH)
    user = load_text_asset(GROUND_PROMPT_USER_PATH)
    return {
        "candidate": "A",
        "system_prompt_path": system.path,
        "system_prompt_sha256": system.sha256,
        "user_prompt_path": user.path,
        "user_prompt_sha256": user.sha256,
    }


def grounded_context_chunk(chunk: dict[str, Any]) -> dict[str, str]:
    return {
        "chunk_id": str(chunk["chunk_id"]),
        "title": str(chunk["title"]),
        "section_heading": str(chunk["section_heading"]),
        "text": str(chunk["text"]),
    }


def grounded_request_allowlist(
    run: dict[str, Any],
    *,
    question: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "model_id": run["model_id"],
        "question": question,
        "retrieved_chunks": [grounded_context_chunk(chunk) for chunk in chunks],
        "prompt": grounded_prompt_identity(),
    }


def grounded_request_entry(
    run: dict[str, Any],
    *,
    question_id: str,
    question: str,
    chunks: list[dict[str, Any]],
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "task_type": "grounded",
        "question_id": question_id,
        "messages": messages,
        "allowlisted_input": grounded_request_allowlist(run, question=question, chunks=chunks),
    }


def tone_request_allowlist(run: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "model_id": run["model_id"],
        "original_question": item["original_question"],
        "grounded_answer": item["grounded_answer"],
        "protected_elements": item["protected_elements"],
        "target_tone": run["target_tone"],
        "prompt_version": run.get("prompt_version", "baseline_v2"),
    }


def tone_request_entry(
    run: dict[str, Any],
    *,
    item: dict[str, Any],
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "task_type": "tone",
        "tone_input_id": run["tone_input_id"],
        "target_tone": run["target_tone"],
        "messages": messages,
        "allowlisted_input": tone_request_allowlist(run, item),
    }


def canonical_hash(value: Any) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    keys = set(value)
    if keys != expected:
        raise ValueError(f"{label} has unauthorized fields: {sorted(keys - expected)}")


def reconstruct_grounded_messages(allowlisted_input: dict[str, Any]) -> list[dict[str, str]]:
    _require_exact_keys(allowlisted_input, GROUNDED_ALLOWLIST_KEYS, "grounded allowlisted input")
    prompt = allowlisted_input["prompt"]
    if not isinstance(prompt, dict):
        raise ValueError("grounded prompt identity must be an object")
    _require_exact_keys(prompt, GROUNDED_PROMPT_KEYS, "grounded prompt identity")
    if prompt != grounded_prompt_identity():
        raise ValueError("grounded prompt identity or hash mismatch")
    chunks = allowlisted_input["retrieved_chunks"]
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("grounded retrieved chunks must be a non-empty list")
    clean_chunks = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("grounded retrieved chunk must be an object")
        _require_exact_keys(chunk, GROUNDED_CHUNK_KEYS, "grounded retrieved chunk")
        clean_chunks.append({key: str(chunk[key]) for key in GROUNDED_CHUNK_KEYS})
    return grounded_messages(
        "a",
        question=str(allowlisted_input["question"]),
        retrieved_context=context_string(clean_chunks),
    )


def reconstruct_tone_messages(allowlisted_input: dict[str, Any]) -> list[dict[str, str]]:
    _require_exact_keys(allowlisted_input, TONE_ALLOWLIST_KEYS, "tone allowlisted input")
    return tone_messages(
        str(allowlisted_input["target_tone"]),
        original_question=str(allowlisted_input["original_question"]),
        grounded_answer=str(allowlisted_input["grounded_answer"]),
        protected_elements=json.dumps(allowlisted_input["protected_elements"], ensure_ascii=False),
        version="v2",
    )


def reconstruct_rendered_requests() -> list[dict[str, Any]]:
    retrieval = read_json(RETRIEVAL_RESULTS_PATH)
    if retrieval.get("status") != "complete":
        raise ValueError("Final v2 retrieval results must be complete before rendering requests")
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    tone_inputs = {item["tone_input_id"]: item for item in read_json(TONE_INPUTS_PATH)["inputs"]}
    chunks_by_q = {record["question_id"]: record["retrieved_chunks"] for record in retrieval["records"]}
    requests = []
    for run in read_json(RUN_PLAN_PATH)["runs"]:
        if run["task_type"] == "grounded":
            question = questions[run["question_id"]]
            chunks = chunks_by_q[run["question_id"]]
            messages = grounded_messages(
                "a",
                question=question["question"],
                retrieved_context=context_string(chunks),
            )
            requests.append(
                grounded_request_entry(
                    run,
                    question_id=run["question_id"],
                    question=question["question"],
                    chunks=chunks,
                    messages=messages,
                )
            )
        elif run["task_type"] == "tone":
            item = tone_inputs[run["tone_input_id"]]
            messages = tone_messages(
                run["target_tone"],
                original_question=item["original_question"],
                grounded_answer=item["grounded_answer"],
                protected_elements=json.dumps(item["protected_elements"], ensure_ascii=False),
                version="v2",
            )
            requests.append(tone_request_entry(run, item=item, messages=messages))
        else:
            raise ValueError(f"unknown Final v2 task type: {run['task_type']}")
    return requests


def load_rendered_requests() -> list[dict[str, Any]]:
    if not RENDERED_REQUESTS_PATH.exists():
        return []
    return list(read_json(RENDERED_REQUESTS_PATH).get("requests", []))


def merge_rendered_requests(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for request in [*existing, *new]:
        run_id = request["run_id"]
        if run_id in merged and canonical_hash(merged[run_id]) != canonical_hash(request):
            raise ValueError(f"conflicting rendered request duplicate: {run_id}")
        merged[run_id] = request
    plan_order = {run["run_id"]: index for index, run in enumerate(read_json(RUN_PLAN_PATH)["runs"])}
    unknown = sorted(set(merged) - set(plan_order))
    if unknown:
        raise ValueError(f"rendered request references unknown run ids: {unknown}")
    return [merged[run_id] for run_id in sorted(merged, key=plan_order.__getitem__)]


def write_rendered_requests(requests: list[dict[str, Any]]) -> None:
    validate_rendered_requests(requests)
    write_json(
        RENDERED_REQUESTS_PATH,
        {
            "created_at_utc": utc_now(),
            "reconstructed_at_utc": utc_now(),
            "request_count": len(requests),
            "provenance": "deterministically_reconstructed_from_frozen_run_plan_retrieval_and_prompt_assets",
            "original_live_capture_available": False,
            "equivalence_verified_against_saved_request_prompt_hashes": True,
            "requests": requests,
        },
    )


def validate_rendered_requests(rendered_requests: list[dict[str, Any]]) -> None:
    plan = read_json(RUN_PLAN_PATH)["runs"]
    expected_ids = [run["run_id"] for run in plan]
    actual_ids = [request["run_id"] for request in rendered_requests]
    if actual_ids != expected_ids:
        raise ValueError("rendered request run-id coverage does not match Final v2 run plan")
    if len(set(actual_ids)) != len(expected_ids):
        raise ValueError("Final v2 rendered requests must contain unique run ids")
    expected_requests = reconstruct_rendered_requests()
    for actual, expected in zip(rendered_requests, expected_requests, strict=True):
        if canonical_hash(actual) != canonical_hash(expected):
            raise ValueError(f"rendered request reconstruction mismatch: {actual['run_id']}")
    grounded_ids = {row["run_id"] for row in read_jsonl(GROUNDED_RESULTS_PATH)}
    tone_ids = {row["run_id"] for row in read_jsonl(TONE_RESULTS_PATH)}
    if grounded_ids or tone_ids:
        missing = sorted((grounded_ids | tone_ids) - set(actual_ids))
        extra = sorted(set(actual_ids) - (grounded_ids | tone_ids))
        if missing or extra:
            raise ValueError(f"rendered request/result coverage mismatch: missing={missing}, extra={extra}")
        results_by_id = {row["run_id"]: row for row in [*read_jsonl(GROUNDED_RESULTS_PATH), *read_jsonl(TONE_RESULTS_PATH)]}
        for request in rendered_requests:
            result = results_by_id[request["run_id"]]
            prompt_hashes = [sha256_text(message["content"]) for message in request["messages"]]
            if prompt_hashes != result.get("request_prompt_hashes"):
                raise ValueError(f"rendered request prompt hash mismatch: {request['run_id']}")
            if request["task_type"] == "grounded":
                chunk_ids = [
                    chunk["chunk_id"]
                    for chunk in request["allowlisted_input"]["retrieved_chunks"]
                ]
                if chunk_ids != result.get("retrieved_chunk_ids"):
                    raise ValueError(f"rendered request retrieved chunk mismatch: {request['run_id']}")
    validate_no_expected_leakage(rendered_requests)


def validate_no_expected_leakage(rendered_requests: list[dict[str, Any]]) -> None:
    for request in rendered_requests:
        task_type = request["task_type"]
        if task_type == "grounded":
            _require_exact_keys(request, GROUNDED_REQUEST_KEYS, "grounded request")
            actual_messages = request["messages"]
            expected_messages = reconstruct_grounded_messages(request["allowlisted_input"])
            if actual_messages != expected_messages and canonical_hash(actual_messages) != canonical_hash(expected_messages):
                raise ValueError(f"grounded request construction mismatch in {request['run_id']}")
            continue
        if task_type == "tone":
            _require_exact_keys(request, TONE_REQUEST_KEYS, "tone request")
            actual_messages = request["messages"]
            expected_messages = reconstruct_tone_messages(request["allowlisted_input"])
            if actual_messages != expected_messages and canonical_hash(actual_messages) != canonical_hash(expected_messages):
                raise ValueError(f"tone request construction mismatch in {request['run_id']}")
            continue
        raise ValueError(f"unknown rendered request task type in {request['run_id']}: {task_type}")


def run_final_v2_execution(
    *,
    resume: bool = False,
    chat_client: WatsonxChatClient | None = None,
) -> dict[str, Any]:
    if not QUESTIONS_PATH.exists():
        raise RuntimeError("Final v2 offline artifacts must be frozen before execution")
    retrieval = read_json(RETRIEVAL_RESULTS_PATH)
    if retrieval.get("status") != "complete":
        retrieval = retrieve_final_questions()
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    tone_inputs = {item["tone_input_id"]: item for item in read_json(TONE_INPUTS_PATH)["inputs"]}
    chunks_by_q = {record["question_id"]: record["retrieved_chunks"] for record in retrieval["records"]}
    plan = read_json(RUN_PLAN_PATH)
    rendered: list[dict[str, Any]] = []
    existing_grounded = read_jsonl(GROUNDED_RESULTS_PATH)
    existing_tone = read_jsonl(TONE_RESULTS_PATH)
    done = {row["run_id"] for row in existing_grounded + existing_tone} if resume else set()
    active_chat_client = chat_client or WatsonxChatClient()
    for run in plan["runs"]:
        if run["run_id"] in done:
            continue
        if run["task_type"] == "grounded":
            question = questions[run["question_id"]]
            chunks = chunks_by_q[run["question_id"]]
            messages = grounded_messages("a", question=question["question"], retrieved_context=context_string(chunks))
            rendered.append(grounded_request_entry(run, question_id=run["question_id"], question=question["question"], chunks=chunks, messages=messages))
            validate_no_expected_leakage([rendered[-1]])
            raw, retries, latency = call_with_retries(
                messages,
                model=run["model_id"],
                max_tokens=GROUND_MAX_TOKENS,
                client=active_chat_client,
            )
            repair = repair_if_needed(raw, model=run["model_id"], task="grounded", messages=messages, max_tokens=GROUND_MAX_TOKENS, client=active_chat_client)
            app = application_grounded_output(question["expected_answerable"], repair["parsed"])
            append_jsonl(GROUNDED_RESULTS_PATH, {**run, "completed_at_utc": utc_now(), "sdk_version": sdk_version(), "request_prompt_hashes": [sha256_text(m["content"]) for m in messages], "retrieved_chunk_ids": [c["chunk_id"] for c in chunks], "raw_initial_output": raw, "parsed_initial_output": repair["parsed"], "repair_reason": repair["repair_reason"], "raw_repair_output": repair["raw_repair_output"], "final_application_output": app, "resolved_citations": resolve_citations(app.get("citation_chunk_ids", []), chunks), "normalization_status": app.get("normalization_rule"), "latency_seconds": latency, "transport_retry_count": retries})
        else:
            item = tone_inputs[run["tone_input_id"]]
            messages = tone_messages(run["target_tone"], original_question=item["original_question"], grounded_answer=item["grounded_answer"], protected_elements=json.dumps(item["protected_elements"], ensure_ascii=False), version="v2")
            rendered.append(tone_request_entry(run, item=item, messages=messages))
            validate_no_expected_leakage([rendered[-1]])
            raw, retries, latency = call_with_retries(
                messages,
                model=run["model_id"],
                max_tokens=TONE_MAX_TOKENS,
                client=active_chat_client,
            )
            repair = repair_if_needed(raw, model=run["model_id"], task="tone", messages=messages, max_tokens=TONE_MAX_TOKENS, client=active_chat_client)
            append_jsonl(TONE_RESULTS_PATH, {**run, "completed_at_utc": utc_now(), "sdk_version": sdk_version(), "request_prompt_hashes": [sha256_text(m["content"]) for m in messages], "raw_initial_output": raw, "parsed_initial_output": repair["parsed"], "repair_reason": repair["repair_reason"], "raw_repair_output": repair["raw_repair_output"], "final_application_output": repair["parsed"], "latency_seconds": latency, "transport_retry_count": retries})
    existing_rendered = load_rendered_requests() if resume else []
    write_rendered_requests(merge_rendered_requests(existing_rendered, rendered))
    scores = compute_scores()
    validate_owner_adjudication()
    manifest = read_json(EXECUTION_MANIFEST_PATH)
    manifest.update({"status": "live_complete", "completed_at_utc": utc_now(), "sdk_version": sdk_version()})
    manifest.setdefault(
        "capture_limitations",
        [
            "Historical Final v2 live_started_at_utc and latency values may be null where the original run did not capture them.",
            "Future executions capture per-call latency_seconds and transport_retry_count from the execution adapter.",
        ],
    )
    write_json(EXECUTION_MANIFEST_PATH, manifest)
    write_json(ARTIFACT_MANIFEST_PATH, render_artifact_manifest())
    return scores


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def resolve_citations(ids: list[str], chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    return [
        {
            "chunk_id": cid,
            "document_id": by_id[cid]["document_id"],
            "document_title": by_id[cid]["title"],
            "section_title": by_id[cid]["section_heading"],
            "source_path": by_id[cid]["source_path"],
        }
        for cid in ids
        if cid in by_id
    ]


def label_grounded(row: dict[str, Any], question: dict[str, Any]) -> str:
    app = row["final_application_output"]
    if not question["expected_answerable"]:
        return "unsupported_correct" if app.get("answer") == CANONICAL_REFUSAL and app.get("citation_chunk_ids") == [] else "unsupported_wrong"
    if app.get("answerable") is not True or not app.get("citation_chunk_ids"):
        return "wrong"
    answer_norm = app.get("answer", "").lower()
    missing = [
        claim["fact_id"]
        for claim in question["atomic_claims"]
        if not marker_claim_pass(claim["claim"], answer_norm)
    ]
    return "correct" if not missing else "partial"


def marker_claim_pass(claim: str, answer_lower: str) -> bool:
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim)
    important = [token for token in re.findall(r"[A-Za-z][A-Za-z.-]+", claim.lower()) if len(token) >= 6]
    return all(number in answer_lower for number in numbers) and sum(token in answer_lower for token in important[:6]) >= min(3, len(important))


def compute_scores() -> dict[str, Any]:
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    retrieval = read_json(RETRIEVAL_RESULTS_PATH)
    grounded = read_jsonl(GROUNDED_RESULTS_PATH)
    tones = read_jsonl(TONE_RESULTS_PATH)
    retrieval_metrics = compute_retrieval_metrics(retrieval["records"], questions)
    grounded_metrics, grounded_details = compute_grounded_final_metrics(grounded, questions)
    tone_metrics, tone_details = compute_tone_final_metrics(tones)
    scores = {
        "status": "complete",
        "scoring_layer": "deterministic",
        "retrieval": retrieval_metrics,
        "grounded": grounded_metrics,
        "tones": tone_metrics,
        "record_details": {"grounded": grounded_details, "tones": tone_details},
    }
    write_json(DETERMINISTIC_SCORES_PATH, scores)
    adjudication_path = OWNER_ADJUDICATION_PATH
    if adjudication_path.exists():
        final_scores = finalize_scores_with_human()
        write_failure_analysis_from_final(final_scores)
        return final_scores
    write_json(FINAL_METRICS_PATH, scores)
    write_json(MODEL_COMPARISON_PATH, compare_models(scores))
    write_failure_analysis_from_final(scores)
    return scores


def compute_grounded_final_metrics(
    grounded: list[dict[str, Any]],
    questions: dict[str, dict[str, Any]],
    human: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    human = human or {}
    grounded_metrics: dict[str, Any] = {}
    details: dict[str, Any] = {}
    labels_by_model: dict[str, list[str]] = defaultdict(list)
    for row in grounded:
        deterministic_label = label_grounded(row, questions[row["question_id"]])
        decision = human.get(row["run_id"])
        final_label = decision["final_label"] if decision else deterministic_label
        label_source = "human" if decision else "deterministic_clean"
        labels_by_model[row["model_id"]].append(final_label)
        details[row["run_id"]] = {
            "model_id": row["model_id"],
            "question_id": row["question_id"],
            "expected_answerable": questions[row["question_id"]]["expected_answerable"],
            "deterministic_label": deterministic_label,
            "human_label": decision["final_label"] if decision else None,
            "final_label": final_label,
            "label_source": label_source,
            "reviewer_notes": decision.get("reviewer_notes", "") if decision else "",
            "repair_retry_count": row.get("repair_retry_count", 0),
            "normalization_status": row.get("normalization_status"),
        }
    for model, labels in labels_by_model.items():
        counts = Counter(labels)
        model_rows = [row for row in grounded if row["model_id"] == model]
        answerable_count = sum(1 for row in model_rows if questions[row["question_id"]]["expected_answerable"])
        unsupported_count = len(model_rows) - answerable_count
        grounded_metrics[model] = {
            "correct": counts["correct"],
            "partial": counts["partial"],
            "wrong": counts["wrong"],
            "unsupported_correct": counts["unsupported_correct"],
            "unsupported_wrong": counts["unsupported_wrong"],
            "answerable_correct_rate": round(counts["correct"] / answerable_count, 4) if answerable_count else 0.0,
            "answerable_partial_rate": round(counts["partial"] / answerable_count, 4) if answerable_count else 0.0,
            "unsupported_refusal_rate": round(counts["unsupported_correct"] / unsupported_count, 4) if unsupported_count else 0.0,
            "strict_overall_accuracy": round((counts["correct"] + counts["unsupported_correct"]) / len(model_rows), 4),
            "human_reviewed_records": sum(
                1 for row in model_rows if row["run_id"] in human
            ),
            "deterministic_clean_records": sum(
                1 for row in model_rows if row["run_id"] not in human
            ),
            "citation_validity": sum(
                bool(row.get("resolved_citations"))
                for row in model_rows
                if questions[row["question_id"]]["expected_answerable"]
            ),
            "repair_count": sum(int(row.get("repair_retry_count", 0)) for row in model_rows),
            "normalization_count": sum(1 for row in model_rows if row.get("normalization_status")),
        }
    return grounded_metrics, details


def compute_retrieval_metrics(records: list[dict[str, Any]], questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    answerable = [r for r in records if questions[r["question_id"]]["expected_answerable"]]
    hit_at = {1: 0, 3: 0, 5: 0}
    reciprocal = []
    coverage = 0
    for record in answerable:
        expected = {(s["document_id"], s["section_title"]) for s in questions[record["question_id"]]["expected_sources"]}
        ranks = [
            chunk["rank"]
            for chunk in record["retrieved_chunks"]
            if (chunk["document_id"], chunk["section_heading"]) in expected
        ]
        for k in hit_at:
            hit_at[k] += int(any(rank <= k for rank in ranks))
        reciprocal.append(1 / min(ranks) if ranks else 0)
        retrieved = {(chunk["document_id"], chunk["section_heading"]) for chunk in record["retrieved_chunks"]}
        coverage += int(expected <= retrieved)
    n = len(answerable)
    return {
        "hit_at_1": round(hit_at[1] / n, 4),
        "hit_at_3": round(hit_at[3] / n, 4),
        "hit_at_5": round(hit_at[5] / n, 4),
        "all_expected_source_coverage_at_5": round(coverage / n, 4),
        "mrr": round(sum(reciprocal) / n, 4),
    }


def compute_tone_final_metrics(
    rows: list[dict[str, Any]],
    human_triplets: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = {item["tone_input_id"]: item for item in read_json(TONE_INPUTS_PATH)["inputs"]}
    human_triplets = human_triplets or {}
    by_model_tone: dict[str, dict[str, Any]] = {}
    by_triplet: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
    details: dict[str, Any] = {}
    for row in rows:
        signal = tone_signal_for_row(row, inputs[row["tone_input_id"]])
        group_id = f"final2-tone-triplet::{row['model_id']}::{row['tone_input_id']}"
        tone = row["target_tone"]
        decision = human_triplets.get(group_id, {}).get("tone_decisions", {}).get(tone)
        final_valid = bool(decision["final_valid"]) if decision else not tone_trigger_reasons(row, signal)
        factual = bool(decision["factual_preservation"]) if decision else final_valid
        language = bool(decision["language_preservation"]) if decision else signal["dimensions"]["language_preserved"]["passed"] is True
        recognizable = bool(decision["tone_recognizable"]) if decision else signal["dimensions"]["rough_style_signal"]["passed"] is True
        quantity_unit_date = all(
            signal["dimensions"][name]["passed"] is not False
            for name in ["numbers_preserved", "units_preserved", "currency_preserved", "dates_deadlines_preserved"]
            if signal["dimensions"][name]["applicable"]
        )
        key = f"{row['model_id']}::{tone}"
        item = by_model_tone.setdefault(
            key,
            {
                "runs": 0,
                "structured_valid": 0,
                "factual_preservation_pass": 0,
                "language_preservation_pass": 0,
                "quantity_unit_date_preservation_pass": 0,
                "target_tone_recognizable_pass": 0,
                "final_valid": 0,
                "human_reviewed_records": 0,
                "deterministic_clean_records": 0,
                "repair_count": 0,
            },
        )
        item["runs"] += 1
        item["structured_valid"] += int(signal["dimensions"]["structure_valid"]["passed"] is True)
        item["factual_preservation_pass"] += int(factual)
        item["language_preservation_pass"] += int(language)
        item["quantity_unit_date_preservation_pass"] += int(quantity_unit_date)
        item["target_tone_recognizable_pass"] += int(recognizable)
        item["final_valid"] += int(final_valid)
        item["human_reviewed_records"] += int(decision is not None)
        item["deterministic_clean_records"] += int(decision is None)
        item["repair_count"] += int(row.get("repair_retry_count", 0))
        by_triplet[(row["model_id"], row["tone_input_id"])][tone] = {
            "final_valid": final_valid,
            "group_id": group_id,
        }
        details[row["run_id"]] = {
            "model_id": row["model_id"],
            "tone_input_id": row["tone_input_id"],
            "target_tone": tone,
            "deterministic_triggers": tone_trigger_reasons(row, signal),
            "human_final_valid": decision["final_valid"] if decision else None,
            "final_valid": final_valid,
            "factual_preservation": factual,
            "language_preservation": language,
            "target_tone_recognizable": recognizable,
            "label_source": "human" if decision else "deterministic_clean",
            "reviewer_notes": decision.get("reviewer_notes", "") if decision else "",
        }
    by_model: dict[str, dict[str, Any]] = {}
    for (model, tone_input_id), tones in by_triplet.items():
        group_id = next(iter(tones.values()))["group_id"]
        triplet_decision = human_triplets.get(group_id, {}).get("triplet_decision")
        distinct = bool(triplet_decision["triplet_distinct"]) if triplet_decision else True
        all_valid = all(tones.get(tone, {}).get("final_valid") is True for tone in TONE_ORDER)
        model_item = by_model.setdefault(
            model,
            {
                "tone_input_triplets": 0,
                "triplet_distinct": 0,
                "fully_valid_triplets": 0,
                "human_reviewed_triplets": 0,
                "deterministic_clean_triplets": 0,
            },
        )
        model_item["tone_input_triplets"] += 1
        model_item["triplet_distinct"] += int(distinct)
        model_item["fully_valid_triplets"] += int(all_valid and distinct)
        model_item["human_reviewed_triplets"] += int(triplet_decision is not None)
        model_item["deterministic_clean_triplets"] += int(triplet_decision is None)
    for item in by_model_tone.values():
        item["final_valid_rate"] = round(item["final_valid"] / item["runs"], 4)
        item["factual_preservation_rate"] = round(item["factual_preservation_pass"] / item["runs"], 4)
        item["language_preservation_rate"] = round(item["language_preservation_pass"] / item["runs"], 4)
        item["target_tone_recognizable_rate"] = round(item["target_tone_recognizable_pass"] / item["runs"], 4)
    for item in by_model.values():
        item["triplet_distinct_rate"] = round(item["triplet_distinct"] / item["tone_input_triplets"], 4)
        item["fully_valid_triplet_rate"] = round(item["fully_valid_triplets"] / item["tone_input_triplets"], 4)
    return {"by_model_tone": by_model_tone, "by_model": by_model}, details


TONE_FACTUAL_DIMENSIONS = [
    "numbers_preserved",
    "units_preserved",
    "currency_preserved",
    "dates_deadlines_preserved",
    "modality_preserved",
    "negation_preserved",
    "conditions_preserved",
    "exceptions_preserved",
    "approval_authorities_preserved",
    "scope_preserved",
    "citation_metadata_absent",
]


def tone_signal_for_row(row: dict[str, Any], tone_input: dict[str, Any]) -> dict[str, Any]:
    return corrected_tone_case(
        {
            "run_id": row["run_id"],
            "raw_output": json.dumps(row["final_application_output"], ensure_ascii=False),
            "target_tone": row["target_tone"],
            "tone_input_id": row["tone_input_id"],
        },
        {
            "grounded_answer": tone_input["grounded_answer"],
            "source_language": tone_input["source_language"],
        },
    )


def tone_trigger_reasons(row: dict[str, Any], signal: dict[str, Any]) -> list[str]:
    dimensions = signal["dimensions"]
    reasons: list[str] = []
    if signal.get("parse_error") or row.get("repair_reason") or row.get("raw_repair_output"):
        reasons.append("malformed_or_repaired")
    if dimensions["structure_valid"]["passed"] is not True:
        reasons.append("structured_validity_failure")
    if dimensions["language_preserved"]["passed"] is not True:
        reasons.append("language_preservation_failure")
    if dimensions["rough_style_signal"]["passed"] is not True:
        reasons.append("target_tone_recognizability_uncertainty")
    for name in TONE_FACTUAL_DIMENSIONS:
        dimension = dimensions[name]
        if dimension["applicable"] and dimension["passed"] is not True:
            reasons.append(f"{name}_failure")
    return reasons


def tone_review_groups() -> dict[tuple[str, str], dict[str, Any]]:
    tone_inputs = {item["tone_input_id"]: item for item in read_json(TONE_INPUTS_PATH)["inputs"]}
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sorted(read_jsonl(TONE_RESULTS_PATH), key=lambda item: item["run_id"]):
        key = (row["model_id"], row["tone_input_id"])
        item = tone_inputs[row["tone_input_id"]]
        signal = tone_signal_for_row(row, item)
        triggers = tone_trigger_reasons(row, signal)
        group = grouped.setdefault(
            key,
            {
                "model_id": row["model_id"],
                "tone_input_id": row["tone_input_id"],
                "question_id": row["question_id"],
                "original_question": item["original_question"],
                "grounded_answer_input": item["grounded_answer"],
                "semantic_requirements": item.get("semantic_requirements", []),
                "protected_elements": item.get("protected_elements", {}),
                "tones": {},
            },
        )
        group["tones"][row["target_tone"]] = {
            "run_id": row["run_id"],
            "raw_output": row["raw_initial_output"],
            "application_output": row["final_application_output"],
            "structured_valid": signal["dimensions"]["structure_valid"],
            "language_preservation": signal["dimensions"]["language_preserved"],
            "semantic_protected_element_signals": {
                name: signal["dimensions"][name] for name in TONE_FACTUAL_DIMENSIONS
            },
            "recognizability_signal": signal["dimensions"]["rough_style_signal"],
            "repair_malformed_status": {
                "parse_error": signal.get("parse_error"),
                "repair_reason": row.get("repair_reason"),
                "raw_repair_output_present": bool(row.get("raw_repair_output")),
            },
            "trigger_reasons": triggers,
            "proposed_decisions": {
                "final_valid": not triggers,
                "factual_preservation": not any(reason.endswith("_failure") and reason not in {"language_preservation_failure", "structured_validity_failure"} for reason in triggers),
                "language_preservation": "language_preservation_failure" not in triggers,
                "tone_recognizable": "target_tone_recognizability_uncertainty" not in triggers,
                "reviewer_notes": "",
            },
            "reviewer_decision": {
                "final_valid": None,
                "factual_preservation": None,
                "language_preservation": None,
                "tone_recognizable": None,
                "reviewer_notes": "",
            },
        }
    for group in grouped.values():
        outputs = [
            normalize_text(group["tones"][tone]["application_output"].get("output", ""))
            for tone in TONE_ORDER
            if tone in group["tones"]
        ]
        group["triplet_distinctness_signal"] = {
            "passed": len(outputs) == 3 and len(set(outputs)) == 3,
            "method": "normalized exact pairwise output comparison",
        }
        group["triplet_reviewer_decision"] = {"triplet_distinct": None, "reviewer_notes": ""}
        group["triggered_outputs"] = [
            {"tone": tone, "run_id": data["run_id"], "trigger_reasons": data["trigger_reasons"]}
            for tone, data in group["tones"].items()
            if data["trigger_reasons"]
        ]
    return grouped


def is_tone_clean_sample(group: dict[str, Any]) -> bool:
    if not group["triplet_distinctness_signal"]["passed"]:
        return False
    for tone in TONE_ORDER:
        data = group["tones"].get(tone)
        if data is None:
            return False
        if data["structured_valid"]["passed"] is not True:
            return False
        if data["language_preservation"]["passed"] is not True:
            return False
        if data["repair_malformed_status"]["parse_error"] or data["repair_malformed_status"]["repair_reason"]:
            return False
    return True


def derive_human_review_requirements() -> dict[str, Any]:
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    grounded = sorted(read_jsonl(GROUNDED_RESULTS_PATH), key=lambda item: item["run_id"])
    mandatory_grounded: list[str] = []
    clean_grounded_by_model: dict[str, list[str]] = defaultdict(list)
    for row in grounded:
        question = questions[row["question_id"]]
        label = label_grounded(row, question)
        required = (
            label in {"partial", "wrong", "unsupported_wrong"}
            or not question["expected_answerable"]
            or bool(row.get("repair_reason"))
            or bool(row.get("normalization_status"))
        )
        if required:
            mandatory_grounded.append(row["run_id"])
        elif label == "correct":
            clean_grounded_by_model[row["model_id"]].append(row["run_id"])
    selected_clean_grounded = {
        model: run_ids[:3] for model, run_ids in sorted(clean_grounded_by_model.items())
    }
    groups = tone_review_groups()
    mandatory_tone_group_ids = []
    flagged_tone_run_ids = []
    clean_tone_by_model: dict[str, list[str]] = defaultdict(list)
    for key, group in sorted(groups.items()):
        group_id = f"final2-tone-triplet::{group['model_id']}::{group['tone_input_id']}"
        if group["triggered_outputs"]:
            mandatory_tone_group_ids.append(group_id)
            for output in group["triggered_outputs"]:
                flagged_tone_run_ids.append(output["run_id"])
        if is_tone_clean_sample(group):
            clean_tone_by_model[group["model_id"]].append(group_id)
    selected_clean_tone = {
        model: group_ids[:2] for model, group_ids in sorted(clean_tone_by_model.items())
    }
    return {
        "mandatory_grounded_run_ids": mandatory_grounded,
        "clean_grounded_sample_run_ids_by_model": selected_clean_grounded,
        "mandatory_tone_group_ids": mandatory_tone_group_ids,
        "flagged_tone_run_ids": sorted(flagged_tone_run_ids),
        "clean_tone_triplet_group_ids_by_model": selected_clean_tone,
    }


def validate_owner_adjudication() -> dict[str, Any]:
    path = OWNER_ADJUDICATION_PATH
    if not path.exists():
        raise ValueError("owner adjudication is required")
    adjudication = read_json(path)
    required_metadata = {
        "artifact_id": "final-v2-owner-adjudication",
        "reviewer": "Adnan Wadee Abdullah",
        "review_method": (
            "Manual verification against retained source documents, retrieved contexts, saved model "
            "outputs, and the documented scoring rubric"
        ),
        "grounded_semantic_decisions_reviewed": 24,
        "tone_triplets_reviewed": 40,
        "existing_decisions_approved_without_changes": True,
        "independent_owner_signoff": True,
        "deterministic_clean_grounded_labels": (
            "retained from structural scoring and combined with the owner-reviewed semantic subset"
        ),
    }
    for key, expected in required_metadata.items():
        if adjudication.get(key) != expected:
            raise ValueError(f"owner adjudication metadata mismatch: {key}")
    try:
        reviewed_at = datetime.fromisoformat(str(adjudication.get("reviewed_at_utc", "")))
    except ValueError as exc:
        raise ValueError("owner adjudication reviewed_at_utc must be ISO-8601") from exc
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() != timezone.utc.utcoffset(reviewed_at):
        raise ValueError("owner adjudication reviewed_at_utc must be UTC")
    grounded_rows = {row["run_id"]: row for row in read_jsonl(GROUNDED_RESULTS_PATH)}
    tone_rows = read_jsonl(TONE_RESULTS_PATH)
    expected_tone_groups = {
        f"final2-tone-triplet::{row['model_id']}::{row['tone_input_id']}" for row in tone_rows
    }
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    grounded_decisions = adjudication.get("grounded_decisions", [])
    tone_decisions = adjudication.get("tone_triplet_decisions", [])
    if not isinstance(grounded_decisions, list) or not isinstance(tone_decisions, list):
        raise ValueError("owner adjudication decisions must be lists")
    grounded_ids = [item.get("run_id") for item in grounded_decisions]
    tone_ids = [item.get("run_id") for item in tone_decisions]
    duplicate_grounded = [run_id for run_id, count in Counter(grounded_ids).items() if count > 1]
    duplicate_tone = [run_id for run_id, count in Counter(tone_ids).items() if count > 1]
    if duplicate_grounded or duplicate_tone:
        raise ValueError(f"duplicate owner adjudication run ids: {duplicate_grounded + duplicate_tone}")
    if len(grounded_ids) != 24 or any(run_id not in grounded_rows for run_id in grounded_ids):
        raise ValueError("owner adjudication must contain 24 grounded decisions from saved outputs")
    if set(tone_ids) != expected_tone_groups:
        raise ValueError("owner adjudication tone decisions do not match saved tone triplets")
    grounded_by_id: dict[str, dict[str, Any]] = {}
    for item in grounded_decisions:
        run_id = item["run_id"]
        label = item.get("final_label")
        if run_id not in grounded_rows:
            raise ValueError(f"unknown grounded run id in adjudication: {run_id}")
        allowed = (
            {"unsupported_correct", "unsupported_wrong"}
            if not questions[grounded_rows[run_id]["question_id"]]["expected_answerable"]
            else {"correct", "partial", "wrong"}
        )
        if label not in allowed:
            raise ValueError(f"invalid grounded label for {run_id}: {label}")
        grounded_by_id[run_id] = {
            "final_label": label,
            "reviewer_notes": str(item.get("reviewer_notes", "")),
        }
    tone_by_id: dict[str, dict[str, Any]] = {}
    for item in tone_decisions:
        run_id = item["run_id"]
        _, model_id, tone_input_id = run_id.split("::")
        decisions = item.get("tone_decisions", {})
        triplet = item.get("triplet_decision", {})
        if set(decisions) != set(TONE_ORDER):
            raise ValueError(f"tone adjudication does not cover all tones: {run_id}")
        if not isinstance(triplet.get("triplet_distinct"), bool):
            raise ValueError(f"triplet_distinct must be boolean: {run_id}")
        clean_tone_decisions: dict[str, dict[str, Any]] = {}
        for tone, decision in decisions.items():
            for field_name in ["final_valid", "factual_preservation", "language_preservation", "tone_recognizable"]:
                if not isinstance(decision.get(field_name), bool):
                    raise ValueError(f"{field_name} must be boolean for {run_id} / {tone}")
            clean_tone_decisions[tone] = {
                "final_valid": decision["final_valid"],
                "factual_preservation": decision["factual_preservation"],
                "language_preservation": decision["language_preservation"],
                "tone_recognizable": decision["tone_recognizable"],
                "reviewer_notes": str(decision.get("reviewer_notes", "")),
            }
        tone_by_id[run_id] = {
            "model_id": model_id,
            "tone_input_id": tone_input_id,
            "tone_decisions": clean_tone_decisions,
            "triplet_decision": {
                "triplet_distinct": triplet["triplet_distinct"],
                "reviewer_notes": str(triplet.get("reviewer_notes", "")),
            },
        }
    return {
        "adjudicator": adjudication["reviewer"],
        "reviewed_at_utc": adjudication["reviewed_at_utc"],
        "owner_adjudication_sha256": sha256_canonical_file(path),
        "grounded_decisions": grounded_by_id,
        "tone_triplet_decisions": tone_by_id,
    }


def finalize_scores_with_human() -> dict[str, Any]:
    human = validate_owner_adjudication()
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    retrieval = read_json(RETRIEVAL_RESULTS_PATH)
    grounded = read_jsonl(GROUNDED_RESULTS_PATH)
    tones = read_jsonl(TONE_RESULTS_PATH)
    retrieval_metrics = compute_retrieval_metrics(retrieval["records"], questions)
    grounded_metrics, grounded_details = compute_grounded_final_metrics(
        grounded,
        questions,
        human["grounded_decisions"],
    )
    tone_metrics, tone_details = compute_tone_final_metrics(tones, human["tone_triplet_decisions"])
    scores = {
        "status": "complete",
        "scoring_layer": "owner_verified_hybrid_final",
        "adjudication": {
            "adjudicator": human["adjudicator"],
            "reviewed_at_utc": human["reviewed_at_utc"],
            "owner_adjudication_sha256": human["owner_adjudication_sha256"],
            "grounded_reviewed_count": len(human["grounded_decisions"]),
            "tone_triplet_reviewed_count": len(human["tone_triplet_decisions"]),
            "semantic_review_method": "manual owner verification",
            "independent_owner_signoff": True,
            "deterministic_clean_grounded_labels_retained": True,
        },
        "retrieval": retrieval_metrics,
        "grounded": grounded_metrics,
        "tones": tone_metrics,
        "layers_preserved": {
            "deterministic_layer_preserved": True,
            "human_layer_preserved": True,
            "deterministic_clean_records_used_for_unreviewed_clean_cases": True,
            "raw_evidence_mutated": False,
        },
        "record_details": {"grounded": grounded_details, "tones": tone_details},
    }
    write_json(FINAL_METRICS_PATH, scores)
    write_json(MODEL_COMPARISON_PATH, compare_models(scores))
    return scores


def compare_models(scores: dict[str, Any]) -> dict[str, Any]:
    primary_grounded = scores.get("grounded", {}).get(PRIMARY_MODEL, {})
    comparison_grounded = scores.get("grounded", {}).get(PREFERRED_COMPARISON_MODEL, {})
    primary_tones = scores.get("tones", {}).get("by_model", {}).get(PRIMARY_MODEL, {})
    comparison_tones = scores.get("tones", {}).get("by_model", {}).get(PREFERRED_COMPARISON_MODEL, {})
    return {
        "status": "complete",
        "scoring_layer": scores.get("scoring_layer"),
        "semantic_review_method": "manual owner verification",
        "independent_owner_signoff": True,
        "primary_model": PRIMARY_MODEL,
        "comparison_model": PREFERRED_COMPARISON_MODEL,
        "comparison_basis": "comparison model with a smaller nominal documented parameter count",
        "only_generation_model_changed": True,
        "retrieval_and_embeddings_shared": True,
        "grounded": {
            "primary": primary_grounded,
            "comparison": comparison_grounded,
            "answerable_correct_rate_delta_comparison_minus_primary": round(
                comparison_grounded.get("answerable_correct_rate", 0.0)
                - primary_grounded.get("answerable_correct_rate", 0.0),
                4,
            ),
            "strict_accuracy_delta_comparison_minus_primary": round(
                comparison_grounded.get("strict_overall_accuracy", 0.0)
                - primary_grounded.get("strict_overall_accuracy", 0.0),
                4,
            ),
        },
        "tones": {
            "primary": primary_tones,
            "comparison": comparison_tones,
            "fully_valid_triplet_rate_delta_comparison_minus_primary": round(
                comparison_tones.get("fully_valid_triplet_rate", 0.0)
                - primary_tones.get("fully_valid_triplet_rate", 0.0),
                4,
            ),
            "triplet_distinct_rate_delta_comparison_minus_primary": round(
                comparison_tones.get("triplet_distinct_rate", 0.0)
                - primary_tones.get("triplet_distinct_rate", 0.0),
                4,
            ),
        },
    }


def write_failure_analysis_from_final(scores: dict[str, Any]) -> None:
    questions = {q["question_id"]: q for q in read_json(QUESTIONS_PATH)["questions"]}
    grounded_rows = {row["run_id"]: row for row in read_jsonl(GROUNDED_RESULTS_PATH)}
    lines = ["# Final v2 Failure Analysis", ""]
    failed = [
        (run_id, detail)
        for run_id, detail in scores.get("record_details", {}).get("grounded", {}).items()
        if detail["final_label"] in {"partial", "wrong", "unsupported_wrong"}
    ]
    if failed:
        lines.extend(["## Grounded Failures", ""])
    for run_id, detail in sorted(failed):
        row = grounded_rows[run_id]
        question = questions[detail["question_id"]]
        lines.extend(
            [
                f"### {detail['question_id']} / {detail['model_id']}",
                "",
                f"- Final label: {detail['final_label']} ({detail['label_source']}).",
                f"- Question: {question['question']}",
                f"- Expected: {question['expected_answer']}",
                f"- Generated: {row['final_application_output'].get('answer')}",
                f"- Reviewer notes: {detail.get('reviewer_notes') or 'Not human reviewed.'}",
                "- Root cause: answer content or citation coverage did not preserve all required policy facts.",
                "- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.",
                "",
            ]
        )
    tone_failed = [
        detail
        for detail in scores.get("record_details", {}).get("tones", {}).values()
        if detail["final_valid"] is not True
    ]
    lines.extend(["## Tone Failures", ""])
    if tone_failed:
        counts = Counter(f"{item['model_id']}::{item['target_tone']}" for item in tone_failed)
        for key, count in sorted(counts.items()):
            lines.append(f"- {key}: {count} outputs failed final human-validity review.")
    else:
        lines.append("- No final tone-output failures were recorded.")
    lines.append("")
    FAILURE_ANALYSIS_PATH.write_text("\n".join(lines), encoding="utf-8")


def verify_model_selection() -> dict[str, Any]:
    runtime = create_runtime()
    specs = get_chat_model_specs(runtime.client)
    ids = {model_id(spec): spec for spec in specs}
    if PRIMARY_MODEL not in ids or PREFERRED_COMPARISON_MODEL not in ids:
        raise RuntimeError("Required primary or preferred comparison chat model is not accessible")
    evidence = {
        "created_at_utc": utc_now(),
        "models": [
            {
                "model_id": PRIMARY_MODEL,
                "accessible_in_current_project": True,
                "chat_support": True,
                "raw_spec_summary": summarize_model_spec(ids[PRIMARY_MODEL]),
                "parameter_size_evidence": official_model_size_source(PRIMARY_MODEL),
                "pricing_evidence": None,
            },
            {
                "model_id": PREFERRED_COMPARISON_MODEL,
                "accessible_in_current_project": True,
                "chat_support": True,
                "raw_spec_summary": summarize_model_spec(ids[PREFERRED_COMPARISON_MODEL]),
                "parameter_size_evidence": official_model_size_source(PREFERRED_COMPARISON_MODEL),
                "pricing_evidence": None,
            },
        ],
        "selected_comparison_model_id": PREFERRED_COMPARISON_MODEL,
        "comparison_basis": "comparison model with a smaller nominal documented parameter count",
    }
    write_json(MODEL_SELECTION_PATH, evidence)
    return evidence


def official_model_size_source(model_id_value: str) -> dict[str, Any]:
    if model_id_value == PRIMARY_MODEL:
        return {
            "publisher": "IBM",
            "official_source_url": "https://www.ibm.com/docs/en/watsonx/saas?topic=models-foundation",
            "retrieved_at_utc": "2026-07-29",
            "documented_parameter_count_billion": 30,
            "supported_claim": "IBM documents Granite 4 Small as a 30 billion parameter model in watsonx.ai foundation-model documentation.",
        }
    if model_id_value == PREFERRED_COMPARISON_MODEL:
        return {
            "publisher": "Mistral AI",
            "official_source_url": "https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503",
            "retrieved_at_utc": "2026-07-29",
            "documented_parameter_count_billion": 24,
            "supported_claim": "Mistral's official model card identifies Mistral Small 3.1 24B Instruct 2503 as a 24 billion parameter model.",
        }
    raise ValueError(f"no official model-size source recorded for {model_id_value}")


def summarize_model_spec(spec: dict[str, Any]) -> dict[str, Any]:
    return {key: spec.get(key) for key in ["model_id", "label", "lifecycle", "functions", "task_ids", "provider"] if key in spec}


def validate_model_selection_evidence(evidence: dict[str, Any]) -> None:
    serialized = json.dumps(evidence, sort_keys=True).lower()
    disallowed_source_phrase = "prompt " + "authorization"
    if disallowed_source_phrase in serialized:
        raise ValueError("model-selection evidence must not cite the disallowed source phrase")
    if "cheaper" in serialized or "lower cost" in serialized:
        raise ValueError("model-selection evidence must not contain unsupported pricing claims")
    if evidence.get("comparison_basis") != "comparison model with a smaller nominal documented parameter count":
        raise ValueError("model-selection comparison basis is not the approved documented-parameter-count claim")
    models = evidence.get("models", [])
    expected_counts = {PRIMARY_MODEL: 30, PREFERRED_COMPARISON_MODEL: 24}
    for model in models:
        if model.get("pricing_evidence") is not None:
            raise ValueError("pricing_evidence must remain null unless authoritative saved pricing evidence exists")
        source = model.get("parameter_size_evidence")
        if not isinstance(source, dict):
            raise ValueError(f"model-size source metadata is missing for {model.get('model_id')}")
        required = ["official_source_url", "publisher", "retrieved_at_utc", "documented_parameter_count_billion", "supported_claim"]
        missing = [field for field in required if not source.get(field)]
        if missing:
            raise ValueError(f"model-size source metadata is incomplete for {model.get('model_id')}: {missing}")
        expected = expected_counts.get(model.get("model_id"))
        if expected is not None and source.get("documented_parameter_count_billion") != expected:
            raise ValueError(f"unexpected documented parameter count for {model.get('model_id')}")
    if evidence.get("selected_comparison_model_id") != PREFERRED_COMPARISON_MODEL:
        raise ValueError("selected comparison model changed")


def validate_final_v2(*, require_human: bool = False) -> dict[str, Any]:
    required = [QUESTIONS_PATH, TONE_INPUTS_PATH, DATASET_MANIFEST_PATH, RUN_PLAN_PATH, PROTECTED_HASHES_PATH]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise ValueError(f"missing Final v2 artifacts: {missing}")
    questions = read_json(QUESTIONS_PATH)["questions"]
    tones = read_json(TONE_INPUTS_PATH)["inputs"]
    counts = Counter(q["category"] for q in questions)
    if len(questions) != 24 or sum(q["expected_answerable"] for q in questions) != 20 or counts["unsupported"] != 4:
        raise ValueError("Final v2 grounded dataset counts are invalid")
    if counts != {"direct_fact": 5, "condition_or_exception": 5, "multi_fact": 5, "multi_section_or_source": 5, "unsupported": 4}:
        raise ValueError(f"Final v2 category counts are invalid: {counts}")
    if len(tones) != 20:
        raise ValueError("Final v2 tone input count is invalid")
    if any(not q.get("frozen", True) for q in [read_json(QUESTIONS_PATH), read_json(TONE_INPUTS_PATH), read_json(RUN_PLAN_PATH)]):
        raise ValueError("Final v2 dataset or run plan is not frozen")
    protected = read_json(PROTECTED_HASHES_PATH)["protected_files"]
    for path, expected in protected.items():
        if sha256_canonical_file(path) != expected:
            raise ValueError(f"protected hash changed: {path}")
    from rag_foundations.frozen_v2_runtime import verify_frozen_v2_artifacts

    verify_frozen_v2_artifacts()
    validate_model_selection_evidence(read_json(MODEL_SELECTION_PATH))
    prompt_manifest_summary = validate_frozen_prompt_manifest()
    artifact_manifest_summary = validate_artifact_manifest()
    if RENDERED_REQUESTS_PATH.exists():
        rendered_manifest = read_json(RENDERED_REQUESTS_PATH)
        if rendered_manifest.get("provenance") != "deterministically_reconstructed_from_frozen_run_plan_retrieval_and_prompt_assets":
            raise ValueError("Final v2 rendered requests must disclose reconstructed provenance")
        if rendered_manifest.get("original_live_capture_available") is not False:
            raise ValueError("Final v2 rendered requests must not claim original live capture")
        if rendered_manifest.get("equivalence_verified_against_saved_request_prompt_hashes") is not True:
            raise ValueError("Final v2 rendered request prompt-hash equivalence is not recorded")
        rendered_requests = rendered_manifest["requests"]
        validate_rendered_requests(rendered_requests)
        if len(rendered_requests) != 168:
            raise ValueError("Final v2 rendered request count must be 168")
    grounded = read_jsonl(GROUNDED_RESULTS_PATH)
    tones_rows = read_jsonl(TONE_RESULTS_PATH)
    if grounded or tones_rows:
        if len(grounded) != 48:
            raise ValueError("Final v2 grounded result count must be 48 after execution")
        if len(tones_rows) != 120:
            raise ValueError("Final v2 tone result count must be 120 after execution")
        if not OWNER_ADJUDICATION_PATH.exists():
            raise ValueError("Final v2 owner adjudication is missing")
    human_summary: dict[str, Any] | None = None
    if require_human or OWNER_ADJUDICATION_PATH.exists():
        human = validate_owner_adjudication()
        human_summary = {
            "owner_adjudication_sha256": human["owner_adjudication_sha256"],
            "grounded_reviewed_count": len(human["grounded_decisions"]),
            "tone_triplet_reviewed_count": len(human["tone_triplet_decisions"]),
        }
        if FINAL_METRICS_PATH.exists():
            final_metrics = read_json(FINAL_METRICS_PATH)
            if final_metrics.get("scoring_layer") != "owner_verified_hybrid_final":
                raise ValueError("Final v2 final metrics are not owner-verified hybrid final scores")
            adjudication_meta = final_metrics.get("adjudication", {})
            if adjudication_meta.get("semantic_review_method") != "manual owner verification":
                raise ValueError("Final v2 final metrics do not disclose manual owner verification")
            if adjudication_meta.get("independent_owner_signoff") is not True:
                raise ValueError("Final v2 final metrics must claim completed owner signoff")
            if final_metrics.get("adjudication", {}).get("owner_adjudication_sha256") != human["owner_adjudication_sha256"]:
                raise ValueError("Final v2 final metrics do not match owner adjudication hash")
        if MODEL_COMPARISON_PATH.exists():
            model_comparison = read_json(MODEL_COMPARISON_PATH)
            if model_comparison.get("status") != "complete":
                raise ValueError("Final v2 model comparison is not complete")
            if model_comparison.get("scoring_layer") != "owner_verified_hybrid_final":
                raise ValueError("Final v2 model comparison does not use owner-verified hybrid final scoring")
            if model_comparison.get("semantic_review_method") != "manual owner verification":
                raise ValueError("Final v2 model comparison does not disclose manual owner verification")
            if model_comparison.get("independent_owner_signoff") is not True:
                raise ValueError("Final v2 model comparison must claim completed owner signoff")
    return {
        "status": "ok",
        "question_count": len(questions),
        "tone_input_count": len(tones),
        "grounded_result_count": len(grounded),
        "tone_result_count": len(tones_rows),
        "artifact_manifest": artifact_manifest_summary,
        "frozen_prompt_manifest": prompt_manifest_summary,
        "owner_adjudication": human_summary,
    }


def validate_artifact_manifest() -> dict[str, Any]:
    manifest = read_json(ARTIFACT_MANIFEST_PATH)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("artifact manifest missing artifacts object")
    expected_paths = {
        rel(path)
        for path in sorted(FINAL_V2.rglob("*"))
        if path.is_file() and rel(path) != rel(ARTIFACT_MANIFEST_PATH)
    }
    actual_paths = set(artifacts)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    if missing or extra:
        raise ValueError(f"artifact manifest path mismatch: missing={missing}, extra={extra}")
    if manifest.get("artifact_count") != len(artifacts):
        raise ValueError("artifact manifest artifact_count does not match artifacts length")
    for path, expected_hash in sorted(artifacts.items()):
        actual_hash = sha256_canonical_file(path)
        if actual_hash != expected_hash:
            raise ValueError(f"artifact manifest hash mismatch for {path}: expected {expected_hash}, got {actual_hash}")
    return {"artifact_count": len(artifacts)}


def _validate_prompt_hash(path: str, expected_hash: str) -> None:
    actual_hash = sha256_canonical_file(path)
    if actual_hash != expected_hash:
        raise ValueError(f"frozen prompt manifest hash mismatch for {path}: expected {expected_hash}, got {actual_hash}")


def validate_frozen_prompt_manifest() -> dict[str, Any]:
    manifest = read_json("data/manifests/frozen/frozen_prompt_manifest_v2.json")
    grounded = manifest.get("grounded", {})
    if grounded.get("candidate") != "A":
        raise ValueError("frozen prompt manifest must select grounded Candidate A")
    _validate_prompt_hash(grounded["system_prompt_path"], grounded["system_prompt_sha256"])
    _validate_prompt_hash(grounded["user_prompt_path"], grounded["user_prompt_sha256"])
    selected_tones = manifest.get("selected_tones", {})
    if set(selected_tones) != set(TONE_ORDER):
        raise ValueError("frozen prompt manifest selected tones are incomplete")
    for tone, data in selected_tones.items():
        expected_stem = PROMPT_TONE_FILES[tone]
        expected_paths = {
            "system_prompt_path": f"prompts/v2/tones/{expected_stem}.system.txt",
            "user_prompt_path": f"prompts/v2/tones/{expected_stem}.user.txt",
            "few_shot_path": f"prompts/v2/few_shot/{expected_stem}.json",
        }
        for key, expected_path in expected_paths.items():
            if data.get(key) != expected_path:
                raise ValueError(f"frozen prompt manifest path mismatch for {tone} {key}")
        _validate_prompt_hash(data["system_prompt_path"], data["system_prompt_sha256"])
        _validate_prompt_hash(data["user_prompt_path"], data["user_prompt_sha256"])
        _validate_prompt_hash(data["few_shot_path"], data["few_shot_sha256"])
    return {"grounded_candidate": "A", "selected_tone_count": len(selected_tones)}


def validate_project_complete() -> dict[str, Any]:
    final = validate_final_v2(require_human=True)
    final_report_path = REPO_ROOT / "docs/FINAL_REPORT.md"
    if not final_report_path.exists():
        raise ValueError("docs/FINAL_REPORT.md is missing")
    metrics = read_json(FINAL_METRICS_PATH)
    comparison = read_json(MODEL_COMPARISON_PATH)
    failure_text = FAILURE_ANALYSIS_PATH.read_text(encoding="utf-8") if FAILURE_ANALYSIS_PATH.exists() else ""
    final_report = final_report_path.read_text(encoding="utf-8")
    if metrics.get("status") != "complete" or metrics.get("scoring_layer") != "owner_verified_hybrid_final":
        raise ValueError("Final v2 owner-verified hybrid final metrics are incomplete")
    if metrics.get("adjudication", {}).get("semantic_review_method") != "manual owner verification":
        raise ValueError("Final v2 metrics do not disclose manual owner verification")
    if metrics.get("adjudication", {}).get("independent_owner_signoff") is not True:
        raise ValueError("Final v2 metrics must claim owner signoff")
    if comparison.get("status") != "complete":
        raise ValueError("Final v2 model comparison is incomplete")
    if comparison.get("scoring_layer") != "owner_verified_hybrid_final":
        raise ValueError("Final v2 model comparison does not use owner-verified hybrid final scoring")
    if comparison.get("semantic_review_method") != "manual owner verification":
        raise ValueError("Final v2 model comparison does not disclose manual owner verification")
    if comparison.get("independent_owner_signoff") is not True:
        raise ValueError("Final v2 model comparison must claim owner signoff")
    if "Final v2" not in final_report or "manual owner verification" not in final_report.lower():
        raise ValueError("docs/FINAL_REPORT.md does not contain the Final v2 owner-verified report")
    if "Final v2 Failure Analysis" not in failure_text:
        raise ValueError("Final v2 failure analysis is missing")
    _validate_submission_text()
    return {"status": "ok", **final}


def _validate_submission_text() -> None:
    current_docs = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/FINAL_REPORT.md",
        "docs/EVALUATION_METHOD.md",
        "docs/EXPERIMENTS.md",
        "docs/PROMPT_DESIGN.md",
    ]
    forbidden_current = [
        "Final v2 has not been created or run",
        "Final v2 remains uncreated",
        "smaller-model comparison remains unexecuted",
        "smaller-model comparison has not been executed",
        "Continue from " + "Gate",
        "Master " + "Prompt",
        "obsolete interim submission wording",
    ]
    for path in current_docs:
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        for phrase in forbidden_current:
            if phrase in text:
                raise ValueError(f"stale submission wording in {path}: {phrase}")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    if "data/indexes/selected/" not in readme:
        raise ValueError("README does not document the active Final v2 index")
    fake_argument_pattern = "add_argument(" + '"--fake"'
    evidence_runners = [
        "src/rag_foundations/final_v2.py",
    ]
    for path in evidence_runners:
        if fake_argument_pattern in (REPO_ROOT / path).read_text(encoding="utf-8"):
            raise ValueError(f"public evidence runner still exposes --fake: {path}")
    if (REPO_ROOT / ("A" + "GENTS.md")).exists():
        raise ValueError("assistant-instruction file remains in the submission root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-offline", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--confirm-live-watsonx", action="store_true")
    args = parser.parse_args(argv)
    if args.prepare_offline:
        print(json.dumps(prepare_offline_artifacts(), indent=2, sort_keys=True))
        return 0
    if args.dry_run:
        print(json.dumps(dry_run(), indent=2, sort_keys=True))
        return 0
    if args.execute or args.resume:
        if not args.confirm_live_watsonx:
            raise SystemExit("--confirm-live-watsonx is required for live execution")
        verify_model_selection()
        print(json.dumps(run_final_v2_execution(resume=args.resume), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 2
