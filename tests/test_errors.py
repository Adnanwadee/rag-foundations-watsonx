from rag_foundations.errors import (
    ChunkTokenLimitError,
    CitationValidationError,
    ConfigurationError,
    MissingConfigurationError,
    ModelOutputError,
    RAGFoundationsError,
)


def test_error_hierarchy() -> None:
    assert issubclass(ConfigurationError, RAGFoundationsError)
    assert issubclass(MissingConfigurationError, ConfigurationError)
    assert issubclass(ModelOutputError, RAGFoundationsError)
    assert issubclass(ChunkTokenLimitError, RAGFoundationsError)
    assert issubclass(CitationValidationError, RAGFoundationsError)


def test_chunk_token_limit_error_retains_safe_fields() -> None:
    error = ChunkTokenLimitError(
        chunk_id="chunk-1",
        token_count=1200,
        embedding_input_limit=1000,
        chunker_config_id="chunker-a",
    )

    assert error.chunk_id == "chunk-1"
    assert error.token_count == 1200
    assert error.embedding_input_limit == 1000
    assert error.chunker_config_id == "chunker-a"
    error_text = str(error)
    assert "chunk-1" in error_text
    assert "token_count" in error_text
    assert "1200" in error_text
    assert "embedding_input_limit" in error_text
    assert "1000" in error_text


def test_model_output_error_retains_safe_reason() -> None:
    error = ModelOutputError(reason="invalid json", repair_retry_used=True)

    assert error.reason == "invalid json"
    assert error.repair_retry_used is True
    assert "invalid json" in str(error)


def test_error_strings_redact_sensitive_detail_values() -> None:
    error = RAGFoundationsError("safe message", api_key="secret-value")

    assert "secret-value" not in str(error)
    assert "<redacted>" in str(error)


def test_error_strings_do_not_redact_token_count_or_max_tokens() -> None:
    error = RAGFoundationsError("safe message", token_count=100, max_tokens=200)

    error_text = str(error)
    assert "token_count" in error_text
    assert "100" in error_text
    assert "max_tokens" in error_text
    assert "200" in error_text


def test_error_strings_redact_sensitive_assignment_patterns() -> None:
    error = ModelOutputError(
        reason="invalid json password: hunter2 access_token=abc123 api_key=key123",
        repair_retry_used=False,
    )

    error_text = str(error)
    assert "hunter2" not in error_text
    assert "abc123" not in error_text
    assert "key123" not in error_text
    assert "password: <redacted>" in error_text
    assert "access_token= <redacted>" in error_text
    assert "api_key= <redacted>" in error_text


def test_safe_reason_text_remains_readable() -> None:
    error = ModelOutputError(reason="invalid json missing required answer field", repair_retry_used=True)

    assert "invalid json missing required answer field" in str(error)


def test_model_output_error_reason_attribute_is_sanitized() -> None:
    error = ModelOutputError(reason="bad output api_key=abc123", repair_retry_used=False)

    assert "abc123" not in error.reason
    assert "api_key= <redacted>" in error.reason
    assert "abc123" not in str(error)


def test_base_error_message_attribute_is_sanitized() -> None:
    error = RAGFoundationsError("failed password: hunter2")

    assert "hunter2" not in error.message
    assert "password: <redacted>" in error.message
    assert "hunter2" not in str(error)


def test_nested_diagnostic_secret_keys_are_redacted() -> None:
    error = RAGFoundationsError(
        "safe message",
        context={
            "api_key": "secret-key",
            "nested": [{"password": "secret-password"}, ("access_token=abc123",)],
        },
    )

    error_text = str(error)
    assert "secret-key" not in error_text
    assert "secret-password" not in error_text
    assert "abc123" not in error_text
    assert "<redacted>" in error_text


def test_safe_nested_diagnostics_remain_readable() -> None:
    error = RAGFoundationsError(
        "safe message",
        context={
            "token_count": 100,
            "max_tokens": 200,
            "chunks": ["chunk-1", {"embedding_input_limit": 1000}],
        },
    )

    error_text = str(error)
    assert "token_count" in error_text
    assert "100" in error_text
    assert "max_tokens" in error_text
    assert "200" in error_text
    assert "chunk-1" in error_text
    assert "embedding_input_limit" in error_text
