import pytest
from pydantic import ValidationError

from rag_foundations.config import AppSettings
from rag_foundations.errors import MissingConfigurationError


ENV_NAMES = [
    "WATSONX_URL",
    "WATSONX_PROJECT_ID",
    "WATSONX_API_KEY",
    "WATSONX_GENERATION_MODEL_ID",
    "WATSONX_COMPARISON_MODEL_ID",
    "WATSONX_EMBEDDING_MODEL_ID",
    "CHUNK_SIZE_TOKENS",
    "CHUNK_OVERLAP_TOKENS",
    "TOP_K",
    "REQUEST_TIMEOUT_SECONDS",
    "MAX_REPAIR_RETRIES",
    "GENERATION_TEMPERATURE",
    "GENERATION_TOP_P",
    "GENERATION_MAX_OUTPUT_TOKENS",
    "GENERATION_RANDOM_SEED",
]


@pytest.fixture(autouse=True)
def clear_phase1_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_settings_load_without_real_secrets() -> None:
    settings = AppSettings(_env_file=None)

    assert settings.watsonx_api_key is None
    assert settings.watsonx_generation_model_id is None
    assert settings.watsonx_embedding_model_id is None
    assert settings.max_repair_retries == 1


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_REPAIR_RETRIES", "0")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("GENERATION_TEMPERATURE", "0.2")
    monkeypatch.setenv("GENERATION_TOP_P", "0.9")

    settings = AppSettings(_env_file=None)

    assert settings.max_repair_retries == 0
    assert settings.request_timeout_seconds == 12.5
    assert settings.generation_temperature == 0.2
    assert settings.generation_top_p == 0.9


def test_python_field_name_population_works() -> None:
    settings = AppSettings(watsonx_url="https://example.com", _env_file=None)

    assert settings.watsonx_url == "https://example.com"


def test_uppercase_alias_constructor_population_works() -> None:
    settings = AppSettings(WATSONX_URL="https://example.com", _env_file=None)

    assert settings.watsonx_url == "https://example.com"


def test_unknown_constructor_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AppSettings(watsonx_urll="https://example.com", _env_file=None)


def test_malformed_api_key_input_is_hidden_in_validation_error() -> None:
    secret_value = "raw-secret-value"

    with pytest.raises(ValidationError) as exc_info:
        AppSettings(WATSONX_API_KEY={"api_key": secret_value}, _env_file=None)

    error_text = str(exc_info.value)
    assert secret_value not in error_text
    assert "WATSONX_API_KEY" in error_text or "watsonx_api_key" in error_text


def test_unknown_api_key_like_field_hides_supplied_secret_value() -> None:
    secret_value = "misspelled-secret-value"

    with pytest.raises(ValidationError) as exc_info:
        AppSettings(WATSONX_API_KYE=secret_value, _env_file=None)

    error_text = str(exc_info.value)
    assert secret_value not in error_text
    assert "WATSONX_API_KYE" in error_text


def test_api_key_repr_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATSONX_API_KEY", "super-secret-key")

    settings = AppSettings(_env_file=None)

    assert settings.watsonx_api_key is not None
    assert settings.watsonx_api_key.get_secret_value() == "super-secret-key"
    assert "super-secret-key" not in repr(settings)
    assert "super-secret-key" not in str(settings)


def test_missing_watsonx_credentials_raise_safe_error() -> None:
    settings = AppSettings(_env_file=None)

    with pytest.raises(MissingConfigurationError) as exc_info:
        settings.require_watsonx_credentials()

    error = exc_info.value
    assert error.missing_fields == ["WATSONX_URL", "WATSONX_PROJECT_ID", "WATSONX_API_KEY"]
    assert "secret" not in str(error).lower()


def test_watsonx_credentials_check_passes_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATSONX_URL", "https://example.invalid")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "project-id")
    monkeypatch.setenv("WATSONX_API_KEY", "secret-value")

    settings = AppSettings(_env_file=None)

    settings.require_watsonx_credentials()


@pytest.mark.parametrize("value", ["-1", "2"])
def test_validation_rejects_invalid_retry_count(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("MAX_REPAIR_RETRIES", value)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_validation_rejects_invalid_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "0")

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_validation_rejects_nonfinite_timeout(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", value)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("GENERATION_TEMPERATURE", "-0.1"),
        ("GENERATION_TEMPERATURE", "2.1"),
        ("GENERATION_TEMPERATURE", "nan"),
        ("GENERATION_TEMPERATURE", "inf"),
        ("GENERATION_TOP_P", "0"),
        ("GENERATION_TOP_P", "1.1"),
        ("GENERATION_TOP_P", "nan"),
        ("GENERATION_TOP_P", "-inf"),
    ],
)
def test_validation_rejects_invalid_generation_ranges(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


@pytest.mark.parametrize(
    ("size", "overlap"),
    [
        ("100", "100"),
        ("100", "101"),
    ],
)
def test_chunk_overlap_must_be_less_than_chunk_size(
    monkeypatch: pytest.MonkeyPatch,
    size: str,
    overlap: str,
) -> None:
    monkeypatch.setenv("CHUNK_SIZE_TOKENS", size)
    monkeypatch.setenv("CHUNK_OVERLAP_TOKENS", overlap)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_no_guessed_model_id_defaults() -> None:
    settings = AppSettings(_env_file=None)

    assert settings.watsonx_generation_model_id is None
    assert settings.watsonx_comparison_model_id is None
    assert settings.watsonx_embedding_model_id is None
