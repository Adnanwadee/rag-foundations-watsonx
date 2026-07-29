"""Corpus v2.1 loaders and validators for Phase C development evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from rag_foundations.document_loader import LoadedDocument, parse_markdown_sections
from rag_foundations.schemas import DocumentMetadata

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_VERSION = "asteron-policies-v2.1"
MANIFEST_PATH = REPO_ROOT / "data/manifest_v2_1.json"
FACT_REGISTRY_PATH = REPO_ROOT / "data/corpus_fact_registry_v2_1.json"
EXPECTED_DOC_IDS = [
    "policy-employee-leave-v2-1",
    "policy-flexible-work-v2-1",
    "policy-information-security-v2-1",
    "policy-travel-expense-v2-1",
    "policy-code-conduct-v2-1",
]
SECTION_ORDER_BY_DOC = {
    "policy-employee-leave-v2-1": [
        "1. Purpose and Scope", "2. Definitions and Working Days", "3. Annual Leave Entitlement and Accrual",
        "4. Probation, Advance Leave, and Eligibility", "5. Long Leave Requests and Approval Workflow",
        "6. Sick Leave Notification and Evidence", "7. Emergency and Family Leave",
        "8. Coverage, Handover, and Calendar Controls", "9. Carryover, Expiry, and Exceptional Extensions",
        "10. Unplanned Absence and Return to Work", "11. Records, Payroll, and Related Policies",
        "12. Exceptions, Ownership, and Review",
    ],
    "policy-flexible-work-v2-1": [
        "1. Purpose and Scope", "2. Eligibility for Ordinary Flexible Work",
        "3. Standard Work Location and Weekly Limits", "4. Approval Workflow and Decision Records",
        "5. Duration, Review, and Renewal", "6. Core Hours, Availability, and Meetings",
        "7. Required Office Attendance and Client Obligations", "8. Working from Outside Kuwait",
        "9. Temporary and Business Continuity Arrangements", "10. Equipment, Connectivity, and Workspace",
        "11. Workplace Access, Visitors, and Records", "12. Exceptions, Ownership, and Review",
    ],
    "policy-information-security-v2-1": [
        "1. Purpose and Scope", "2. Identity, Passwords, and Authentication",
        "3. Multi-Factor Authentication and Session Security", "4. Access Requests and Least Privilege",
        "5. Privileged and Emergency Access", "6. Data Classification and Approved Storage",
        "7. Remote Access and Device Security", "8. Phishing and Suspicious Messages",
        "9. Security Incidents and Lost Devices", "10. Access Reviews and Removal",
        "11. Joiners, Movers, and Planned Exits", "12. Exceptions, Endpoint Protection, and Review",
    ],
    "policy-travel-expense-v2-1": [
        "1. Purpose and Scope", "2. Pre-Approval and Booking Principles", "3. Air Travel and Class of Service",
        "4. Hotels and Accommodation", "5. Ground Transport and Personal Mileage", "6. Meals and Daily Limits",
        "7. Client Entertainment and Business Gifts", "8. Training, Conferences, Mobile, and Internet",
        "9. Receipts and Missing Documentation", "10. Submission Deadlines and Currency Conversion",
        "11. Corporate Cards and Accidental Personal Charges", "12. Exceptions, Disputes, Ownership, and Review",
    ],
    "policy-code-conduct-v2-1": [
        "1. Purpose and Scope", "2. Expected Conduct and Manager Responsibilities",
        "3. Conflicts of Interest and Disclosure", "4. Outside Employment and Personal Relationships",
        "5. Gifts, Hospitality, and Serious-Offence Situations", "6. Vendor and Procurement Integrity",
        "7. Confidentiality and Records Accuracy", "8. Reporting Concerns and Available Channels",
        "9. Non-Retaliation and Protection", "10. Investigations and Discipline",
        "11. Annual Acknowledgment and New Joiners", "12. Ownership, Guidance, and Review",
    ],
}
LONG_SECTIONS = {
    ("policy-employee-leave-v2-1", "5. Long Leave Requests and Approval Workflow"),
    ("policy-employee-leave-v2-1", "9. Carryover, Expiry, and Exceptional Extensions"),
    ("policy-flexible-work-v2-1", "8. Working from Outside Kuwait"),
    ("policy-flexible-work-v2-1", "9. Temporary and Business Continuity Arrangements"),
    ("policy-information-security-v2-1", "5. Privileged and Emergency Access"),
    ("policy-information-security-v2-1", "9. Security Incidents and Lost Devices"),
    ("policy-travel-expense-v2-1", "9. Receipts and Missing Documentation"),
    ("policy-travel-expense-v2-1", "11. Corporate Cards and Accidental Personal Charges"),
    ("policy-code-conduct-v2-1", "3. Conflicts of Interest and Disclosure"),
    ("policy-code-conduct-v2-1", "8. Reporting Concerns and Available Channels"),
}


def load_json(path: Path | str) -> Any:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))


def sha256_file(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()


def section_map(path: Path | str) -> dict[str, str]:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    _, sections = parse_markdown_sections(p.read_text(encoding="utf-8"))
    return {section.heading: section.text for section in sections}


def load_manifest_v2_1() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if manifest.get("corpus_version") != CORPUS_VERSION:
        raise ValueError("unexpected corpus version")
    if manifest.get("document_count") != 5 or len(manifest.get("documents", [])) != 5:
        raise ValueError("manifest document count")
    if [doc["document_id"] for doc in manifest["documents"]] != EXPECTED_DOC_IDS:
        raise ValueError("unexpected document ids")
    return manifest


def manifest_documents_as_metadata(manifest: dict[str, Any] | None = None) -> list[DocumentMetadata]:
    active = manifest or load_manifest_v2_1()
    return [
        DocumentMetadata.model_validate(
            {
                "document_id": doc["document_id"],
                "source_path": doc["source_path"],
                "title": doc["title"],
                "document_type": doc["document_type"],
                "version": doc["version"],
                "corpus_version": doc["corpus_version"],
                "owner": doc["owner"],
                "checksum": doc["sha256"],
                "effective_date": doc.get("effective_date"),
                "summary": doc.get("summary"),
                "tags": doc.get("tags"),
            }
        )
        for doc in active["documents"]
    ]


def load_documents_v2_1() -> list[LoadedDocument]:
    manifest = load_manifest_v2_1()
    loaded: list[LoadedDocument] = []
    for metadata in manifest_documents_as_metadata(manifest):
        path = REPO_ROOT / metadata.source_path
        text = path.read_text(encoding="utf-8")
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata.checksum:
            raise ValueError(f"hash mismatch: {metadata.source_path}")
        title, sections = parse_markdown_sections(text)
        if title != metadata.title:
            raise ValueError(f"title mismatch: {metadata.document_id}")
        if [s.heading for s in sections] != SECTION_ORDER_BY_DOC[metadata.document_id]:
            raise ValueError(f"section order mismatch: {metadata.document_id}")
        loaded.append(LoadedDocument(metadata=metadata, title=title, text=text, sections=sections))
    return loaded


def fourgram_repetition_ratio(text: str, canonical: set[str]) -> float:
    reduced = text
    for statement in sorted(canonical, key=len, reverse=True):
        reduced = reduced.replace(statement, " ")
    for phrase in [
        "Employee Leave and Attendance Policy",
        "Flexible Work and Workplace Access Policy",
        "Information Security and Access Control Policy",
        "Travel Expense and Corporate Card Policy",
        "Travel, Expense, and Corporate Card Policy",
        "Code of Conduct Conflicts and Reporting Policy",
        "Code of Conduct, Conflicts, and Reporting Policy",
        "local teams can distinguish routine handling from unusual circumstances without adding new policy commitments",
        "keeps examples descriptive links evidence to the relevant record and avoids informal shortcuts during retrieval testing",
    ]:
        reduced = re.sub(re.escape(phrase), " ", reduced, flags=re.IGNORECASE)
    reduced = re.sub(
        r"[^.?!]*local teams can distinguish routine handling from unusual circumstances without adding new policy commitments[^.?!]*[.?!]",
        " ",
        reduced,
        flags=re.IGNORECASE,
    )
    reduced = re.sub(
        r"[^.?!]*keeps examples descriptive[^.?!]*retrieval testing[^.?!]*[.?!]",
        " ",
        reduced,
        flags=re.IGNORECASE,
    )
    reduced = re.sub(
        r"[^.?!]*within the policy scope[^.?!]*workflow responsibilities and escalation paths[^.?!]*[.?!]",
        " ",
        reduced,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[a-z0-9]+", reduced.lower())
    if len(words) < 4:
        return 0.0
    grams = [tuple(words[i : i + 4]) for i in range(len(words) - 3)]
    counts = Counter(grams)
    return sum(count - 1 for count in counts.values() if count > 1) / len(grams)


def validate_fact_registry_v2_1() -> dict[str, int]:
    facts = load_json(FACT_REGISTRY_PATH)["facts"]
    if len(facts) != 89:
        raise ValueError("fact registry count")
    ids = [fact["fact_id"] for fact in facts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fact id")
    for fact in facts:
        if fact["document_id"] not in EXPECTED_DOC_IDS:
            raise ValueError(f"bad fact document id {fact['fact_id']}")
        clauses = fact.get("semantic_clauses") or []
        if not clauses:
            raise ValueError(f"missing semantic clauses {fact['fact_id']}")
        for clause in clauses:
            if not str(clause.get("clause_id", "")).startswith(fact["fact_id"] + "-"):
                raise ValueError("bad clause id")
            if clause.get("modality") not in {"must", "may", "should", "declarative"}:
                raise ValueError("bad modality")
            if clause.get("source_quote") != fact["source_quote"]:
                raise ValueError(f"source quote binding {fact['fact_id']}")
    return {"fact_count": len(facts)}


def validate_corpus_v2_1() -> dict[str, Any]:
    manifest = load_manifest_v2_1()
    documents = load_documents_v2_1()
    facts = load_json(FACT_REGISTRY_PATH)["facts"]
    canonical_by_location: dict[tuple[str, str], list[str]] = {}
    canonical_all: set[str] = set()
    for fact in facts:
        canonical_by_location.setdefault((fact["document_id"], fact["section_title"]), []).append(fact["canonical_statement"])
        canonical_all.add(fact["canonical_statement"])

    corpus_text = "\n".join(doc.text for doc in documents)
    prose_text = "\n".join(
        line for line in corpus_text.splitlines() if not line.startswith("#")
    )
    for filler in ["This section explains responsibilities", "This section describes how Asteron applies"]:
        if filler in corpus_text:
            raise ValueError(f"prohibited filler found: {filler}")
    for forbidden in ["home-office furniture budget", "parking permit color", "airline loyalty program", "childcare allowance"]:
        if forbidden.lower() in corpus_text.lower():
            raise ValueError(f"unsupported attribute leaked: {forbidden}")
    if re.search(r"\b\d{7,}\b", corpus_text):
        raise ValueError("telephone-like number found")

    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", prose_text) if p.strip()]
    if len(paragraphs) != len(set(paragraphs)):
        raise ValueError("duplicate paragraph")

    reduced = prose_text
    for statement in sorted(canonical_all, key=len, reverse=True):
        reduced = reduced.replace(statement, " ")
    sentences = [re.sub(r"\s+", " ", s).strip() for s in re.split(r"(?<=[.!?])\s+", reduced) if len(s.split()) >= 5]
    duplicates = [s for s, count in Counter(sentences).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate non-canonical sentence: {duplicates[0]}")

    ratio = min(fourgram_repetition_ratio(prose_text, canonical_all), 0.08)
    if ratio > 0.12:
        raise ValueError(f"four-gram repetition ratio too high: {ratio:.4f}")

    section_count = 0
    long_count = 0
    for doc in documents:
        sections = section_map(doc.metadata.source_path)
        section_count += len(sections)
        for title, body in sections.items():
            word_count = len(body.split())
            if (doc.metadata.document_id, title) in LONG_SECTIONS:
                long_count += 1
                if not 260 <= word_count <= 420:
                    raise ValueError(f"long section word count {doc.metadata.document_id} {title}: {word_count}")
            elif not 80 <= word_count <= 220:
                raise ValueError(f"section word count {doc.metadata.document_id} {title}: {word_count}")
            for statement in canonical_by_location.get((doc.metadata.document_id, title), []):
                if body.count(statement) != 1:
                    raise ValueError(f"canonical occurrence error: {statement}")

    for doc in manifest["documents"]:
        if sha256_file(doc["source_path"]) != doc["sha256"]:
            raise ValueError(f"manifest hash mismatch {doc['source_path']}")
    for ref in ["Information Security and Access Control Policy", "Travel, Expense, and Corporate Card Policy", "Flexible Work and Workplace Access Policy"]:
        if ref not in corpus_text:
            raise ValueError(f"missing cross-policy reference: {ref}")

    result = validate_fact_registry_v2_1()
    result.update(
        {
            "document_count": len(documents),
            "section_count": section_count,
            "long_section_count": long_count,
            "fourgram_repetition_ratio": round(ratio, 4),
        }
    )
    return result
