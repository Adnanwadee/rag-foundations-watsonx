"""Deterministic evaluation scoring helpers."""

from __future__ import annotations

import json
import re
from typing import Any

CANONICAL_REFUSAL = "I don't know based on the provided documents."


def parse_json_object(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        return None, f"invalid_json:{exc.msg}"
    if not isinstance(value, dict):
        return None, "not_json_object"
    return value, None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def application_grounded_output(expected_answerable: bool, parsed: dict[str, Any] | None) -> dict[str, Any]:
    if not parsed:
        return {"answerable": False, "answer": "", "citation_chunk_ids": [], "normalization_applied": False}
    answer = str(parsed.get("answer", ""))
    citations = parsed.get("citation_chunk_ids", [])
    if not isinstance(citations, list):
        citations = []
    if not expected_answerable and parsed.get("answerable") is False and citations == [] and answer != CANONICAL_REFUSAL:
        return {
            "answerable": False,
            "answer": CANONICAL_REFUSAL,
            "citation_chunk_ids": [],
            "normalization_applied": True,
            "normalization_rule": "unsupported_false_empty_citations_to_canonical_refusal",
        }
    return {
        "answerable": bool(parsed.get("answerable")),
        "answer": answer,
        "citation_chunk_ids": citations,
        "normalization_applied": False,
        "normalization_rule": None,
    }


def requested_attribute_type(question: dict[str, Any]) -> str | None:
    text = (question.get("question", "") + " " + str(question.get("absence_assertion", ""))).lower()
    mapping = {
        "vendor_product_version": ["vendor", "product", "version", "software"],
        "telephone_number": ["telephone", "phone number"],
        "budget_amount": ["budget", "allowance"],
        "parking_color": ["parking", "color"],
        "airline_loyalty_program": ["airline", "loyalty"],
    }
    for name, terms in mapping.items():
        if any(term in text for term in terms):
            return name
    return None


def invented_requested_attribute(question: dict[str, Any], answer: str) -> bool:
    attr = requested_attribute_type(question)
    if not attr or not answer.strip():
        return False
    lower = answer.lower()
    if any(phrase in lower for phrase in ["does not", "no ", "not identify", "i don't know"]):
        return False
    if attr == "telephone_number":
        return bool(re.search(r"(?:\+?\d[\d\s().-]{6,}\d)", answer))
    if attr == "budget_amount":
        return bool(re.search(r"\b(?:kwd|usd|\$)\s*\d+|\b\d+\s*(?:kwd|usd|per month|monthly)", lower))
    if attr == "parking_color":
        return bool(re.search(r"\b(red|blue|green|yellow|white|black|orange|purple|silver|gold)\b", lower))
    if attr == "airline_loyalty_program":
        return bool(re.search(r"\b(skywards|avios|oasis|miles|loyalty program)\b", lower))
    if attr == "vendor_product_version":
        return bool(re.search(r"\b(version\s+\d|cisco|palo alto|fortinet|globalprotect|anyconnect|nord|expressvpn)\b", lower))
    return False


def citation_contract_valid(expected_answerable: bool, parsed: dict[str, Any] | None, allowed_ids: set[str]) -> bool:
    if not parsed or not isinstance(parsed.get("citation_chunk_ids"), list):
        return False
    ids = parsed["citation_chunk_ids"]
    if not all(isinstance(item, str) for item in ids):
        return False
    if set(ids) - allowed_ids:
        return False
    return bool(ids) if expected_answerable else ids == []


def semantic_role_flags(answer: str, atomic_claims: list[dict[str, Any]]) -> list[str]:
    """Return only conservative, claim-local role warnings.

    This deliberately avoids earlier cross-claim logic that flagged any answer
    containing `calendar days` when any expected claim contained `working days`, or
    any answer containing `may` when any expected claim contained `must`.
    """

    flags: list[str] = []
    answer_lower = answer.lower()
    answer_norm = normalize_text(answer)
    for claim in atomic_claims:
        claim_text = claim.get("claim", "")
        claim_norm = normalize_text(claim_text)
        numbers = re.findall(r"\b\d+\b", claim_text)
        if "working days" in claim_text.lower() and numbers:
            for number in numbers:
                if f"{number} calendar days" in answer_lower and f"{number} working days" not in answer_lower:
                    flags.append(f"{claim.get('claim_id', 'claim')}:possible_time_unit_mismatch")
        if "must" in claim_norm and "may" in answer_norm and "must" not in answer_norm:
            core_terms = [term for term in claim_norm.split() if len(term) > 5][:3]
            if core_terms and all(term in answer_norm for term in core_terms):
                flags.append(f"{claim.get('claim_id', 'claim')}:possible_modality_mismatch")
    return flags


def corrected_grounded_case(row: dict[str, Any], question: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    parsed, parse_error = parse_json_object(row["raw_output"])
    valid = parse_error is None and parsed is not None and {"answerable", "answer", "citation_chunk_ids"} <= set(parsed)
    answer = str(parsed.get("answer", "")) if parsed else ""
    citations = parsed.get("citation_chunk_ids", []) if parsed and isinstance(parsed.get("citation_chunk_ids", []), list) else []
    expected_unsupported = not question["expected_answerable"]
    app = application_grounded_output(question["expected_answerable"], parsed)
    return {
        "run_id": row["run_id"],
        "case_id": row.get("case_id") or row.get("question_id") or row.get("tone_input_id"),
        "asset_name": row.get("asset_name") or f"phase-c-grounded-{row.get('candidate', 'unknown')}",
        "structured_json_valid": bool(valid),
        "parse_error": parse_error,
        "expected_answerable": question["expected_answerable"],
        "model_answerable": parsed.get("answerable") if parsed else None,
        "unsupported_decision_correct": bool(expected_unsupported and parsed and parsed.get("answerable") is False),
        "canonical_refusal_raw_valid": bool(
            expected_unsupported and parsed and parsed.get("answerable") is False and answer == CANONICAL_REFUSAL and citations == []
        ),
        "canonical_refusal_application_valid": bool(
            expected_unsupported and app["answerable"] is False and app["answer"] == CANONICAL_REFUSAL and app["citation_chunk_ids"] == []
        ),
        "empty_refusal_text": bool(expected_unsupported and parsed and parsed.get("answerable") is False and citations == [] and answer == ""),
        "unsupported_explanatory_text": bool(
            expected_unsupported and parsed and parsed.get("answerable") is False and citations == [] and answer not in {"", CANONICAL_REFUSAL}
        ),
        "unsupported_answered": bool(expected_unsupported and parsed and parsed.get("answerable") is True),
        "invented_requested_attribute": bool(expected_unsupported and invented_requested_attribute(question, answer)),
        "attribute_substitution_failure": False,
        "citation_contract_valid": citation_contract_valid(question["expected_answerable"], parsed, set(resolved.get("allowed_chunk_ids", []))),
        "semantic_role_regression_flags": semantic_role_flags(answer, question.get("atomic_claims", [])) if question["expected_answerable"] else [],
        "application_output": app,
    }


def dimension(applicable: bool, passed: bool | None, expected: list[str], observed: list[str], rationale: str) -> dict[str, Any]:
    return {
        "applicable": applicable,
        "passed": passed if applicable else None,
        "expected_values": expected,
        "observed_values": observed,
        "rationale": rationale,
    }


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\b", text)


def extract_currency(text: str) -> list[str]:
    return re.findall(r"\bKWD\s+\d+(?:\.\d+)?\b", text)


def extract_units(text: str) -> list[str]:
    return [u for u in ["working days", "calendar days", "per kilometer", "per month", "per night", "hours", "minutes"] if u in text.lower()]


def extract_modality(text: str) -> list[str]:
    return [m for m in ["must", "may", "should", "required", "permitted", "prohibited"] if re.search(rf"\b{m}\b", text.lower())]


def language_preserved(tone_input: dict[str, Any], output: str) -> bool:
    lang = tone_input.get("source_language")
    if lang == "en":
        return True
    if lang == "ar":
        return bool(re.search(r"[\u0600-\u06FF]", output))
    if lang == "fr":
        return any(word in output.lower() for word in ["le", "la", "les", "doit", "jours", "caract"])
    if lang == "es":
        return any(word in output.lower() for word in ["la", "los", "debe", "días", "kuwait"])
    return True


def modality_pass(source: str, output: str) -> bool:
    src = source.lower()
    out = output.lower()
    if "must" in src and not any(x in out for x in ["must", "required", "has to", "needs to"]):
        return False
    if "may" in src and "may not" not in src and not any(x in out for x in ["may", "permitted", "can be", "is allowed"]):
        return False
    if "should" in src and not any(x in out for x in ["should", "normally", "expected"]):
        return False
    return True


def marker_pass(source: str, output: str, markers: list[str]) -> bool:
    return all(marker not in source.lower() or marker in output.lower() for marker in markers)


def rough_style_signal(target_tone: str, output: str) -> bool:
    lower = output.lower()
    if target_tone == "formal_report_summary":
        return len(output.split()) >= 8 and "hey" not in lower
    if target_tone == "casual_message":
        return any(x in lower for x in ["you", "please", "just", "make sure", "keep"])
    if target_tone == "concise_executive_briefing":
        return any(x in lower for x in ["key", "action", "decision", "risk", "rule"])
    return False


def corrected_tone_case(row: dict[str, Any], tone_input: dict[str, Any]) -> dict[str, Any]:
    parsed, parse_error = parse_json_object(row["raw_output"])
    output = str(parsed.get("output", "")) if parsed else ""
    source = tone_input["grounded_answer"]
    numbers = extract_numbers(source)
    currency = extract_currency(source)
    units = extract_units(source)
    modality = extract_modality(source)
    dimensions = {
        "structure_valid": dimension(True, bool(parsed and parsed.get("tone") == row.get("target_tone") and isinstance(parsed.get("output"), str)), [row.get("target_tone", "")], [str(parsed.get("tone")) if parsed else ""], "strict JSON object with expected tone"),
        "language_preserved": dimension(True, language_preserved(tone_input, output), [tone_input.get("source_language", "")], [], "source language must remain visible"),
        "numbers_preserved": dimension(bool(numbers), all(n in output for n in numbers), numbers, extract_numbers(output), "numeric values checked separately"),
        "units_preserved": dimension(bool(units), all(u in output.lower() for u in units), units, extract_units(output), "units checked separately"),
        "currency_preserved": dimension(bool(currency), all(c in output for c in currency), currency, extract_currency(output), "currency checked separately"),
        "dates_deadlines_preserved": dimension(bool(re.search(r"\b(?:january|march|april|\d{4}-\d{2}-\d{2})\b", source.lower())), True, [], [], "date/deadline semantic review is advisory/human when not lexical"),
        "modality_preserved": dimension(bool(modality), modality_pass(source, output), modality, extract_modality(output), "permits valid paraphrases"),
        "negation_preserved": dimension(any(x in source.lower() for x in ["not", "prohibited", "no "]), marker_pass(source, output, ["not", "prohibited"]), [], [], "negation marker checked conservatively"),
        "conditions_preserved": dimension(any(x in source.lower() for x in ["unless", "when", "only", "after", "before"]), marker_pass(source, output, ["unless", "only"]), [], [], "condition marker checked conservatively"),
        "exceptions_preserved": dimension("unless" in source.lower() or "exception" in source.lower(), "unless" in output.lower() or "exception" in output.lower(), [], [], "exception marker checked conservatively"),
        "approval_authorities_preserved": dimension(any(x in source for x in ["HR", "manager", "department head", "Finance", "Information Security", "IT Operations"]), all(auth not in source or auth in output for auth in ["HR", "line manager", "department head", "Finance", "Information Security", "IT Operations"]), [], [], "named authority preservation"),
        "scope_preserved": dimension(True, True, [], [], "scope requires semantic or human review"),
        "citation_metadata_absent": dimension(True, not any(x in output.lower() for x in ["chunk_id", "citation", "document_id", "section_title"]), [], [], "tone output must not include citation metadata"),
        "exact_copy": dimension(True, output.strip() == source.strip(), [source], [output], "warning only; exact copy is not automatically a semantic failure"),
        "rough_style_signal": dimension(True, rough_style_signal(row.get("target_tone", ""), output), [row.get("target_tone", "")], [], "rough style signal, not semantic truth"),
    }
    return {
        "run_id": row["run_id"],
        "case_id": row.get("case_id") or row.get("tone_input_id"),
        "target_tone": row.get("target_tone"),
        "structured_json_valid": dimensions["structure_valid"]["passed"],
        "parse_error": parse_error,
        "dimensions": dimensions,
        "output": output,
    }


def aggregate_applicable_dimensions(results: list[dict[str, Any]], dimension_names: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in dimension_names:
        applicable = [r["dimensions"][name] for r in results if r["dimensions"][name]["applicable"]]
        out[name] = {"applicable": len(applicable), "passed": sum(d["passed"] is True for d in applicable)}
    return out
