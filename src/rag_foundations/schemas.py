"""Pydantic contracts for Project 1."""

from __future__ import annotations

import math
import re
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from rag_foundations.constants import UNSUPPORTED_ANSWER

WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


class ToneName(StrEnum):
    FORMAL_REPORT_SUMMARY = "formal_report_summary"
    CASUAL_MESSAGE = "casual_message"
    CONCISE_EXECUTIVE_BRIEFING = "concise_executive_briefing"


class ScoreType(StrEnum):
    COSINE_DISTANCE = "cosine_distance"
    COSINE_SIMILARITY = "cosine_similarity"
    L2_DISTANCE = "l2_distance"
    OTHER = "other"


def _require_nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_clean_nonblank(value: str) -> str:
    _require_nonblank(value)
    if value != value.strip():
        raise ValueError("must not contain leading or trailing whitespace")
    return value


def _validate_source_path(value: str) -> str:
    _require_clean_nonblank(value)
    if ":" in value:
        raise ValueError("must not contain colon characters")
    if "\\" in value:
        raise ValueError("must use forward slashes")
    if WINDOWS_ABSOLUTE_PATH.match(value):
        raise ValueError("must be repository-relative")
    if "://" in value:
        raise ValueError("must not be a URI")
    if value == ".":
        raise ValueError("must refer to a file path")
    if value.startswith("./"):
        raise ValueError("must not start with ./")
    if value.endswith("/"):
        raise ValueError("must not be a directory path")
    if "//" in value:
        raise ValueError("must not contain empty path segments")
    if "." in value.split("/"):
        raise ValueError("must not contain current-directory path segments")

    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError("must be repository-relative")
    if ".." in path.parts:
        raise ValueError("must not contain path traversal")
    return value


def _require_finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("must be finite")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentMetadata(StrictModel):
    document_id: str
    source_path: str
    title: str
    document_type: str
    version: str
    corpus_version: str
    owner: str
    checksum: str
    effective_date: str | None = None
    created_at: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    supersedes: str | None = None

    @field_validator(
        "document_id",
        "title",
        "document_type",
        "version",
        "corpus_version",
        "owner",
        "checksum",
    )
    @classmethod
    def required_strings_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)

    @field_validator("source_path")
    @classmethod
    def source_path_is_repository_relative(cls, value: str) -> str:
        return _validate_source_path(value)


class DocumentChunk(StrictModel):
    chunk_id: str
    document_id: str
    corpus_version: str
    chunker_config_id: str
    chunk_size_tokens: int
    chunk_overlap_tokens: int
    token_counting_method: str
    chunk_index: int
    text: str
    title: str
    section_heading: str
    source_path: str
    token_count: int
    checksum: str
    start_char: int | None = None
    end_char: int | None = None
    page_number: int | None = None
    section_number: str | None = None
    paragraph_index: int | None = None

    @field_validator(
        "chunk_id",
        "document_id",
        "corpus_version",
        "chunker_config_id",
        "token_counting_method",
        "text",
        "title",
        "section_heading",
        "checksum",
    )
    @classmethod
    def required_strings_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)

    @field_validator("source_path")
    @classmethod
    def source_path_is_repository_relative(cls, value: str) -> str:
        return _validate_source_path(value)

    @field_validator("chunk_size_tokens", "token_count")
    @classmethod
    def positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("chunk_overlap_tokens", "chunk_index")
    @classmethod
    def nonnegative_ints(cls, value: int) -> int:
        if value < 0:
            raise ValueError("must be zero or greater")
        return value

    @field_validator("start_char")
    @classmethod
    def start_char_nonnegative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("must be zero or greater")
        return value

    @field_validator("end_char", "page_number", "paragraph_index")
    @classmethod
    def optional_nonnegative_ints(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("must be zero or greater")
        return value

    @model_validator(mode="after")
    def validate_chunk_bounds(self) -> DocumentChunk:
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be less than chunk_size_tokens")
        if self.start_char is not None and self.end_char is not None:
            if self.end_char <= self.start_char:
                raise ValueError("end_char must be greater than start_char")
        return self


class RetrievedChunk(StrictModel):
    chunk_id: str
    document_id: str
    corpus_version: str
    chunker_config_id: str
    embedding_model_id: str
    embedding_dimension: int
    index_id: str
    rank: int
    raw_score: float
    score_type: ScoreType
    text: str
    title: str
    section_heading: str
    source_path: str
    retriever_name: str
    retriever_config: dict[str, Any]
    page_number: int | None = None
    normalized_relevance: float | None = None
    experiment_id: str | None = None

    @field_validator(
        "chunk_id",
        "document_id",
        "corpus_version",
        "chunker_config_id",
        "embedding_model_id",
        "index_id",
        "text",
        "title",
        "section_heading",
        "retriever_name",
    )
    @classmethod
    def required_strings_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)

    @field_validator("source_path")
    @classmethod
    def source_path_is_repository_relative(cls, value: str) -> str:
        return _validate_source_path(value)

    @field_validator("rank", "embedding_dimension")
    @classmethod
    def positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("normalized_relevance")
    @classmethod
    def normalized_relevance_range(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError("must be between 0 and 1")
        return value

    @field_validator("raw_score")
    @classmethod
    def raw_score_is_finite(cls, value: float) -> float:
        return _require_finite(value)

    @field_validator("page_number")
    @classmethod
    def page_number_nonnegative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("must be zero or greater")
        return value


class Citation(StrictModel):
    citation_id: str
    chunk_id: str
    document_id: str
    title: str
    section_heading: str
    source_path: str
    supporting_quote: str | None = None
    corpus_version: str | None = None
    page_number: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    index_id: str | None = None
    experiment_id: str | None = None

    @field_validator("citation_id", "chunk_id", "document_id", "title", "section_heading")
    @classmethod
    def required_strings_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)

    @field_validator("source_path")
    @classmethod
    def source_path_is_repository_relative(cls, value: str) -> str:
        return _validate_source_path(value)

    @field_validator("supporting_quote")
    @classmethod
    def optional_supporting_quote_not_blank(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_nonblank(value)
        return value

    @field_validator("page_number", "start_char", "end_char")
    @classmethod
    def optional_nonnegative_ints(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("must be zero or greater")
        return value

    @model_validator(mode="after")
    def validate_offsets(self) -> Citation:
        if self.start_char is not None and self.end_char is not None:
            if self.end_char <= self.start_char:
                raise ValueError("end_char must be greater than start_char")
        return self


class GroundedModelOutput(StrictModel):
    answer: str
    is_answerable: bool
    citation_chunk_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_grounded_model_output(self) -> GroundedModelOutput:
        self.answer = _require_nonblank(self.answer)
        normalized_ids = [_require_clean_nonblank(chunk_id) for chunk_id in self.citation_chunk_ids]
        if len(normalized_ids) != len(set(normalized_ids)):
            raise ValueError("citation_chunk_ids must be unique")

        if self.is_answerable:
            if self.answer.strip() == UNSUPPORTED_ANSWER:
                raise ValueError("answerable output must not use the unsupported answer")
            if not normalized_ids:
                raise ValueError("answerable output requires at least one citation chunk ID")
        else:
            if self.answer != UNSUPPORTED_ANSWER:
                raise ValueError("unanswerable output must use the canonical unsupported answer")
            if normalized_ids:
                raise ValueError("unanswerable output must not include citation chunk IDs")
        return self


class GroundedAnswerResult(StrictModel):
    answer: str
    is_answerable: bool
    citations: list[Citation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_grounded_answer_result(self) -> GroundedAnswerResult:
        self.answer = _require_nonblank(self.answer)
        if self.is_answerable:
            if self.answer.strip() == UNSUPPORTED_ANSWER:
                raise ValueError("answerable result must not use the unsupported answer")
            if not self.citations:
                raise ValueError("answerable result requires at least one citation")
        else:
            if self.answer != UNSUPPORTED_ANSWER:
                raise ValueError("unanswerable result must use the canonical unsupported answer")
            if self.citations:
                raise ValueError("unanswerable result must not include citations")
        return self


class ToneModelOutput(StrictModel):
    tone: ToneName
    output: str

    @field_validator("output")
    @classmethod
    def output_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)


class ToneResult(StrictModel):
    tone: ToneName
    output: str
    citations: list[Citation] = Field(default_factory=list)

    @field_validator("output")
    @classmethod
    def output_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)


class AllToneResult(StrictModel):
    original_answer: str
    variations: list[ToneResult]

    @field_validator("original_answer")
    @classmethod
    def original_answer_not_blank(cls, value: str) -> str:
        return _require_nonblank(value)

    @model_validator(mode="after")
    def validate_variations(self) -> AllToneResult:
        expected = [
            ToneName.FORMAL_REPORT_SUMMARY,
            ToneName.CASUAL_MESSAGE,
            ToneName.CONCISE_EXECUTIVE_BRIEFING,
        ]
        tones = [variation.tone for variation in self.variations]
        if len(self.variations) != 3:
            raise ValueError("exactly three tone variations are required")
        if tones != expected:
            raise ValueError("tone variations must appear exactly once in deterministic order")

        first_citations = self.variations[0].citations
        for variation in self.variations[1:]:
            if variation.citations != first_citations:
                raise ValueError("all tone variations must contain identical citation lists")
        return self
