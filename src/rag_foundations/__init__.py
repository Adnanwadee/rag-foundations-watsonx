"""RAG Foundations package."""

from rag_foundations.config import AppSettings
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import (
    ChunkTokenLimitError,
    CitationValidationError,
    ConfigurationError,
    MissingConfigurationError,
    ModelOutputError,
    RAGFoundationsError,
)
from rag_foundations.schemas import (
    AllToneResult,
    Citation,
    DocumentChunk,
    DocumentMetadata,
    GroundedAnswerResult,
    GroundedModelOutput,
    RetrievedChunk,
    ScoreType,
    ToneModelOutput,
    ToneName,
    ToneResult,
)

__all__ = [
    "AllToneResult",
    "AppSettings",
    "ChunkTokenLimitError",
    "Citation",
    "CitationValidationError",
    "ConfigurationError",
    "DocumentChunk",
    "DocumentMetadata",
    "GroundedAnswerResult",
    "GroundedModelOutput",
    "MissingConfigurationError",
    "ModelOutputError",
    "RAGFoundationsError",
    "RetrievedChunk",
    "ScoreType",
    "ToneModelOutput",
    "ToneName",
    "ToneResult",
    "UNSUPPORTED_ANSWER",
]
