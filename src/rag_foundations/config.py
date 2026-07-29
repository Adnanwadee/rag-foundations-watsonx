"""Environment-backed settings for the RAG CLI and evaluation tooling."""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from rag_foundations.errors import MissingConfigurationError


class AppSettings(BaseSettings):
    """Environment-backed settings.

    Ordinary offline loading succeeds without a local `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
        populate_by_name=True,
        hide_input_in_errors=True,
    )

    watsonx_url: str | None = Field(default=None, alias="WATSONX_URL")
    watsonx_project_id: str | None = Field(default=None, alias="WATSONX_PROJECT_ID")
    watsonx_api_key: SecretStr | None = Field(default=None, alias="WATSONX_API_KEY")
    watsonx_generation_model_id: str | None = Field(
        default=None,
        alias="WATSONX_GENERATION_MODEL_ID",
    )
    watsonx_comparison_model_id: str | None = Field(
        default=None,
        alias="WATSONX_COMPARISON_MODEL_ID",
    )
    watsonx_embedding_model_id: str | None = Field(
        default=None,
        alias="WATSONX_EMBEDDING_MODEL_ID",
    )

    chunk_size_tokens: int | None = Field(default=None, alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int | None = Field(default=None, alias="CHUNK_OVERLAP_TOKENS")
    top_k: int | None = Field(default=None, alias="TOP_K")

    request_timeout_seconds: float | None = Field(
        default=None,
        alias="REQUEST_TIMEOUT_SECONDS",
    )
    max_repair_retries: int = Field(default=1, alias="MAX_REPAIR_RETRIES")
    generation_temperature: float | None = Field(
        default=None,
        alias="GENERATION_TEMPERATURE",
    )
    generation_top_p: float | None = Field(default=None, alias="GENERATION_TOP_P")
    generation_max_output_tokens: int | None = Field(
        default=None,
        alias="GENERATION_MAX_OUTPUT_TOKENS",
    )
    generation_random_seed: int | None = Field(
        default=None,
        alias="GENERATION_RANDOM_SEED",
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator(
        "watsonx_url",
        "watsonx_project_id",
        "watsonx_generation_model_id",
        "watsonx_comparison_model_id",
        "watsonx_embedding_model_id",
        mode="before",
    )
    @classmethod
    def blank_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("chunk_size_tokens", "top_k", "generation_max_output_tokens")
    @classmethod
    def optional_positive_int(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("chunk_overlap_tokens")
    @classmethod
    def optional_nonnegative_int(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("must be zero or greater")
        return value

    @field_validator("request_timeout_seconds")
    @classmethod
    def optional_positive_float(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or value <= 0):
            raise ValueError("must be greater than zero")
        return value

    @field_validator("max_repair_retries")
    @classmethod
    def repair_retries_must_be_zero_or_one(cls, value: int) -> int:
        if value not in (0, 1):
            raise ValueError("must be 0 or 1")
        return value

    @field_validator("generation_temperature")
    @classmethod
    def optional_temperature_range(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or not 0 <= value <= 2):
            raise ValueError("must be between 0 and 2")
        return value

    @field_validator("generation_top_p")
    @classmethod
    def optional_top_p_range(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or not 0 < value <= 1):
            raise ValueError("must be greater than 0 and no greater than 1")
        return value

    @model_validator(mode="after")
    def validate_chunk_config_consistency(self) -> AppSettings:
        if self.chunk_size_tokens is not None and self.chunk_overlap_tokens is not None:
            if self.chunk_overlap_tokens >= self.chunk_size_tokens:
                raise ValueError("CHUNK_OVERLAP_TOKENS must be less than CHUNK_SIZE_TOKENS")
        return self

    def require_watsonx_credentials(self) -> None:
        """Raise when watsonx.ai credentials required for live calls are absent."""

        missing: list[str] = []
        if not self.watsonx_url:
            missing.append("WATSONX_URL")
        if not self.watsonx_project_id:
            missing.append("WATSONX_PROJECT_ID")
        if self.watsonx_api_key is None or not self.watsonx_api_key.get_secret_value().strip():
            missing.append("WATSONX_API_KEY")

        if missing:
            raise MissingConfigurationError(missing)
