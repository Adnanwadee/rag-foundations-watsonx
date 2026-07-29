"""Section-aware token chunking for the synthetic Markdown corpus."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from rag_foundations.document_loader import LoadedDocument
from rag_foundations.schemas import DocumentChunk


MINILM_TOKENIZER_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE_TOKENS = 220
DEFAULT_CHUNK_OVERLAP_TOKENS = 40
TOKEN_COUNTING_METHOD = f"{MINILM_TOKENIZER_MODEL_ID}:tokenizer"


class Tokenizer(Protocol):
    """Minimal tokenizer behavior needed by the chunker."""

    def encode(self, text: str) -> list[int]:
        """Encode text into token IDs."""

    def decode(self, token_ids: list[int]) -> str:
        """Decode token IDs back into text."""


class MiniLMTokenizer:
    """Lazy no-Torch tokenizer for the MiniLM tokenization baseline."""

    def __init__(
        self,
        model_id: str = MINILM_TOKENIZER_MODEL_ID,
    ) -> None:
        self.model_id = model_id
        self._tokenizer: object | None = None

    def _load(self) -> object:
        if self._tokenizer is None:
            try:
                from huggingface_hub import hf_hub_download
                from tokenizers import Tokenizer as HuggingFaceTokenizer

                tokenizer_path = hf_hub_download(repo_id=self.model_id, filename="tokenizer.json")
                self._tokenizer = HuggingFaceTokenizer.from_file(tokenizer_path)
                self._tokenizer.no_truncation()
                self._tokenizer.no_padding()
                return self._tokenizer
            except Exception as exc:
                self._tokenizer = None
                raise RuntimeError(
                    "The no-Torch tokenizer path could not load tokenizer.json for MiniLM."
                ) from exc
        return self._tokenizer

    def encode(self, text: str) -> list[int]:
        tokenizer = self._load()
        if hasattr(tokenizer, "encode") and tokenizer.__class__.__module__.startswith("tokenizers"):
            return list(tokenizer.encode(text).ids)  # type: ignore[attr-defined]
        return list(tokenizer.encode(text, add_special_tokens=False))  # type: ignore[attr-defined]

    def decode(self, token_ids: list[int]) -> str:
        tokenizer = self._load()
        if hasattr(tokenizer, "decode") and tokenizer.__class__.__module__.startswith("tokenizers"):
            return str(tokenizer.decode(token_ids))  # type: ignore[attr-defined]
        return str(tokenizer.decode(token_ids, skip_special_tokens=True))  # type: ignore[attr-defined]


class SimpleWhitespaceTokenizer:
    """Deterministic tokenizer for fast unit tests without network or model downloads."""

    _pattern = re.compile(r"\S+")

    def __init__(self) -> None:
        self._tokens: list[str] = []

    def encode(self, text: str) -> list[int]:
        self._tokens = self._pattern.findall(text)
        return list(range(len(self._tokens)))

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(self._tokens[token_id] for token_id in token_ids)


@dataclass(frozen=True)
class ChunkingConfig:
    """Token chunking settings for one index build."""

    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS
    token_counting_method: str = TOKEN_COUNTING_METHOD

    @property
    def chunker_config_id(self) -> str:
        return (
            "section-token-v1-"
            f"size-{self.chunk_size_tokens}-overlap-{self.chunk_overlap_tokens}-minilm"
        )

    def validate(self) -> None:
        if self.chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be greater than zero")
        if self.chunk_overlap_tokens < 0:
            raise ValueError("chunk_overlap_tokens must be zero or greater")
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be less than chunk_size_tokens")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _chunk_id(
    *,
    corpus_version: str,
    document_id: str,
    source_path: str,
    section_heading: str,
    chunk_index: int,
    text_checksum: str,
    config: ChunkingConfig,
) -> str:
    payload = "|".join(
        [
            corpus_version,
            document_id,
            source_path,
            section_heading,
            config.chunker_config_id,
            str(config.chunk_size_tokens),
            str(config.chunk_overlap_tokens),
            str(chunk_index),
            text_checksum,
        ]
    )
    return f"chunk-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def create_chunks(
    documents: list[LoadedDocument],
    *,
    tokenizer: Tokenizer | None = None,
    config: ChunkingConfig | None = None,
) -> list[DocumentChunk]:
    """Create deterministic `DocumentChunk` records from loaded documents."""

    active_config = config or ChunkingConfig()
    active_config.validate()
    active_tokenizer = tokenizer or MiniLMTokenizer()
    chunks: list[DocumentChunk] = []

    for document in documents:
        chunk_index = 0
        for section in document.sections:
            section_source = f"## {section.heading}\n\n{section.text.strip()}"
            token_ids = active_tokenizer.encode(section_source)
            if not token_ids:
                continue

            start = 0
            while start < len(token_ids):
                end = min(start + active_config.chunk_size_tokens, len(token_ids))
                chunk_token_ids = token_ids[start:end]
                chunk_text = active_tokenizer.decode(chunk_token_ids).strip()
                if chunk_text:
                    token_count = len(chunk_token_ids)
                    checksum = _sha256(chunk_text)
                    chunk_id = _chunk_id(
                        corpus_version=document.metadata.corpus_version,
                        document_id=document.metadata.document_id,
                        source_path=document.metadata.source_path,
                        section_heading=section.heading,
                        chunk_index=chunk_index,
                        text_checksum=checksum,
                        config=active_config,
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=document.metadata.document_id,
                            corpus_version=document.metadata.corpus_version,
                            chunker_config_id=active_config.chunker_config_id,
                            chunk_size_tokens=active_config.chunk_size_tokens,
                            chunk_overlap_tokens=active_config.chunk_overlap_tokens,
                            token_counting_method=active_config.token_counting_method,
                            chunk_index=chunk_index,
                            text=chunk_text,
                            title=document.metadata.title,
                            section_heading=section.heading,
                            source_path=document.metadata.source_path,
                            token_count=token_count,
                            checksum=checksum,
                            section_number=section.section_number,
                        )
                    )
                    chunk_index += 1

                if end == len(token_ids):
                    break
                start = end - active_config.chunk_overlap_tokens

    return chunks


def summarize_chunks(documents: list[LoadedDocument], chunks: list[DocumentChunk]) -> dict[str, float | int]:
    """Return compact ingestion statistics."""

    token_counts = [chunk.token_count for chunk in chunks]
    return {
        "documents_loaded": len(documents),
        "sections_loaded": sum(len(document.sections) for document in documents),
        "chunks_created": len(chunks),
        "minimum_chunk_tokens": min(token_counts) if token_counts else 0,
        "maximum_chunk_tokens": max(token_counts) if token_counts else 0,
        "average_chunk_tokens": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0,
    }
