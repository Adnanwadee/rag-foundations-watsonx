"""Typed project errors with safe diagnostics."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_DETAIL_KEYS = (
    "api_key",
    "password",
    "secret",
    "access_token",
    "auth_token",
    "credential",
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([a-z0-9_]*(?:api_key|password|access_token|auth_token|secret|credential))\s*([=:])\s*"
    r"([^,\s;]+)"
)


def _redact_text(value: str) -> str:
    return SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)} <redacted>", value)


def _safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, dict):
        safe_dict: dict[Any, Any] = {}
        for nested_key, nested_value in value.items():
            if isinstance(nested_key, str) and any(
                marker in nested_key.lower() for marker in SENSITIVE_DETAIL_KEYS
            ):
                safe_dict[nested_key] = "<redacted>"
            else:
                safe_dict[nested_key] = _safe_value(nested_value)
        return safe_dict
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_safe_value(item) for item in value)
    return value


def _safe_details(details: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in details.items():
        if any(marker in key.lower() for marker in SENSITIVE_DETAIL_KEYS):
            safe[key] = "<redacted>"
        else:
            safe[key] = _safe_value(value)
    return safe


class RAGFoundationsError(Exception):
    """Base class for project errors."""

    def __init__(self, message: str, **details: Any) -> None:
        self.message = _redact_text(message)
        self.details = _safe_details(details)
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if not self.details:
            return self.message
        return f"{self.message} | details={self.details}"


class ConfigurationError(RAGFoundationsError):
    """Raised when application configuration is invalid."""


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is absent."""

    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = missing_fields
        super().__init__(
            "Missing required configuration.",
            missing_fields=missing_fields,
        )


class ModelOutputError(RAGFoundationsError):
    """Raised when model output cannot be validated."""

    def __init__(self, reason: str, repair_retry_used: bool) -> None:
        self.reason = _redact_text(reason)
        self.repair_retry_used = repair_retry_used
        super().__init__(
            "Model output validation failed.",
            reason=self.reason,
            repair_retry_used=repair_retry_used,
        )


class ChunkTokenLimitError(RAGFoundationsError):
    """Raised when a chunk exceeds the verified embedding input limit."""

    def __init__(
        self,
        *,
        chunk_id: str,
        token_count: int,
        embedding_input_limit: int,
        chunker_config_id: str,
    ) -> None:
        self.chunk_id = chunk_id
        self.token_count = token_count
        self.embedding_input_limit = embedding_input_limit
        self.chunker_config_id = chunker_config_id
        super().__init__(
            "Chunk exceeds verified embedding input limit.",
            chunk_id=chunk_id,
            token_count=token_count,
            embedding_input_limit=embedding_input_limit,
            chunker_config_id=chunker_config_id,
        )


class CitationValidationError(RAGFoundationsError):
    """Raised when citation data is invalid."""
