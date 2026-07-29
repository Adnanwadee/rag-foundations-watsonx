"""Load the synthetic Markdown policy corpus and validate its manifest."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag_foundations.errors import RAGFoundationsError
from rag_foundations.schemas import DocumentMetadata


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
MANIFEST_METADATA_FIELDS = {
    "document_id",
    "source_path",
    "title",
    "document_type",
    "version",
    "corpus_version",
    "owner",
    "checksum",
    "effective_date",
    "created_at",
    "summary",
    "tags",
    "supersedes",
}


@dataclass(frozen=True)
class LoadedSection:
    """A Markdown section extracted from a source document."""

    heading: str
    level: int
    text: str
    section_number: str


@dataclass(frozen=True)
class LoadedDocument:
    """A validated source document with parsed Markdown sections."""

    metadata: DocumentMetadata
    title: str
    text: str
    sections: list[LoadedSection]


class DocumentLoadError(RAGFoundationsError):
    """Raised when the local document corpus cannot be loaded."""


def sha256_text(text: str) -> str:
    """Return a SHA-256 checksum for UTF-8 text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path | str) -> str:
    """Return a SHA-256 checksum for exact file bytes."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_manifest_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize supported manifest variants to the public DocumentMetadata shape."""

    normalized = dict(record)
    if "checksum" not in normalized and "sha256" in normalized:
        normalized["checksum"] = normalized["sha256"]
    return {key: value for key, value in normalized.items() if key in MANIFEST_METADATA_FIELDS}


def load_manifest(manifest_path: Path | str = Path("data/manifest_v2_1.json")) -> list[DocumentMetadata]:
    """Read and validate the corpus manifest."""

    path = Path(manifest_path)
    if not path.exists():
        raise DocumentLoadError("Manifest file is missing.", manifest_path=str(path))

    try:
        raw_records: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocumentLoadError("Manifest JSON is invalid.", manifest_path=str(path), reason=str(exc)) from exc

    if isinstance(raw_records, dict) and isinstance(raw_records.get("documents"), list):
        raw_records = raw_records["documents"]
    if not isinstance(raw_records, list):
        raise DocumentLoadError("Manifest must contain a list of records.", manifest_path=str(path))

    metadata_records: list[DocumentMetadata] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(raw_records):
        try:
            metadata = DocumentMetadata.model_validate(normalize_manifest_record(record))
        except ValidationError as exc:
            raise DocumentLoadError("Manifest record is invalid.", record_index=index, reason=str(exc)) from exc

        if metadata.document_id in seen_ids:
            raise DocumentLoadError("Duplicate document_id in manifest.", document_id=metadata.document_id)
        seen_ids.add(metadata.document_id)
        metadata_records.append(metadata)

    return metadata_records


def parse_markdown_sections(text: str) -> tuple[str, list[LoadedSection]]:
    """Extract the document title and level-2 Markdown sections."""

    headings = list(HEADING_PATTERN.finditer(text))
    title = ""
    for heading in headings:
        if len(heading.group(1)) == 1:
            title = heading.group(2).strip()
            break

    sections: list[LoadedSection] = []
    section_index = 0
    for index, heading in enumerate(headings):
        level = len(heading.group(1))
        if level != 2:
            continue

        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section_text = text[start:end].strip()
        heading_text = heading.group(2).strip()
        if section_text:
            section_index += 1
            sections.append(
                LoadedSection(
                    heading=heading_text,
                    level=level,
                    text=section_text,
                    section_number=str(section_index),
                )
            )

    return title, sections


def load_documents(
    manifest_path: Path | str = Path("data/manifest_v2_1.json"),
    *,
    repository_root: Path | str = Path("."),
    minimum_sections: int = 3,
) -> list[LoadedDocument]:
    """Load all manifest documents and validate checksums and section structure."""

    root = Path(repository_root)
    metadata_records = load_manifest(manifest_path)
    loaded: list[LoadedDocument] = []

    for metadata in metadata_records:
        source_file = root / metadata.source_path
        if not source_file.exists():
            raise DocumentLoadError(
                "Manifest source file is missing.",
                document_id=metadata.document_id,
                source_path=metadata.source_path,
            )

        text = source_file.read_text(encoding="utf-8")
        if not text.strip():
            raise DocumentLoadError("Document is empty.", document_id=metadata.document_id)

        checksum = sha256_file(source_file)
        if checksum != metadata.checksum:
            raise DocumentLoadError(
                "Document checksum mismatch.",
                document_id=metadata.document_id,
                source_path=metadata.source_path,
                expected_checksum=metadata.checksum,
                actual_checksum=checksum,
            )

        title, sections = parse_markdown_sections(text)
        if not title:
            raise DocumentLoadError("Document title is missing.", document_id=metadata.document_id)
        if len(sections) < minimum_sections:
            raise DocumentLoadError(
                "Document does not contain enough meaningful sections.",
                document_id=metadata.document_id,
                section_count=len(sections),
                minimum_sections=minimum_sections,
            )

        loaded.append(
            LoadedDocument(
                metadata=metadata,
                title=title,
                text=text,
                sections=sections,
            )
        )

    return loaded
