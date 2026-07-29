import json
import re
from pathlib import Path

from rag_foundations.document_loader import normalize_manifest_record, sha256_file
from rag_foundations.schemas import DocumentMetadata


DOCUMENT_DIR = Path("data/documents_v2_1")
MANIFEST_PATH = Path("data/manifest_v2_1.json")
EXPECTED_FILES = {
    "employee_leave_attendance_policy.md": "Employee Leave and Attendance Policy",
    "flexible_work_workplace_access_policy.md": "Flexible Work and Workplace Access Policy",
    "information_security_access_control_policy.md": "Information Security and Access Control Policy",
    "travel_expense_corporate_card_policy.md": "Travel, Expense, and Corporate Card Policy",
    "code_conduct_conflicts_reporting_policy.md": "Code of Conduct, Conflicts, and Reporting Policy",
}


def _manifest_records() -> list[DocumentMetadata]:
    records = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["documents"]
    return [DocumentMetadata.model_validate(normalize_manifest_record(record)) for record in records]


def test_exactly_five_policy_files_exist() -> None:
    files = {path.name for path in DOCUMENT_DIR.glob("*.md")}

    assert files == set(EXPECTED_FILES)


def test_manifest_contains_exactly_five_valid_records_with_unique_ids() -> None:
    records = _manifest_records()

    assert len(records) == 5
    assert len({record.document_id for record in records}) == 5


def test_manifest_paths_exist_and_checksums_match() -> None:
    for metadata in _manifest_records():
        source_path = Path(metadata.source_path)

        assert source_path.exists()
        assert sha256_file(source_path) == metadata.checksum


def test_each_document_has_required_title_sections_and_length() -> None:
    for file_name, title in EXPECTED_FILES.items():
        text = (DOCUMENT_DIR / file_name).read_text(encoding="utf-8")
        word_count = len(re.findall(r"\b\S+\b", text))
        section_count = len(re.findall(r"(?m)^##\s+", text))

        assert f"# {title}" in text
        assert section_count >= 8
        assert word_count >= 1400
