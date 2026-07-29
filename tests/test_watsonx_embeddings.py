import pytest

from rag_foundations.errors import RAGFoundationsError
from rag_foundations.watsonx_embeddings import WatsonxEmbeddingProvider


class FakeEmbeddings:
    def __init__(self, *, model_id: str, api_client: object | None = None, **kwargs: object) -> None:
        self.model_id = model_id
        self.api_client = api_client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 2.0, 3.0] for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return [1.0, 2.0, 3.0]


def provider(embeddings_cls: object = FakeEmbeddings) -> WatsonxEmbeddingProvider:
    return WatsonxEmbeddingProvider(
        model_id="ibm/granite-embedding-278m-multilingual",
        api_client=object(),
        embeddings_cls=embeddings_cls,
    )


def test_blank_query_fails_without_sdk_call() -> None:
    with pytest.raises(ValueError):
        provider().embed_query(" ")


def test_blank_document_input_fails_without_sdk_call() -> None:
    with pytest.raises(ValueError):
        provider().embed_documents(["valid", " "])


def test_empty_document_list_fails_without_sdk_call() -> None:
    with pytest.raises(ValueError):
        provider().embed_documents([])


def test_successful_mocked_document_embeddings_return_vectors() -> None:
    vectors = provider().embed_documents(["alpha", "beta"])

    assert vectors == [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    assert provider().model_id == "ibm/granite-embedding-278m-multilingual"


def test_successful_mocked_query_embedding_returns_one_vector() -> None:
    active_provider = provider()

    vector = active_provider.embed_query("remote work days")

    assert vector == [1.0, 2.0, 3.0]
    assert active_provider.embedding_dimension == 3


def test_inconsistent_dimensions_fail() -> None:
    class InconsistentEmbeddings(FakeEmbeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 2.0], [1.0, 2.0, 3.0]]

    with pytest.raises(RAGFoundationsError):
        provider(InconsistentEmbeddings).embed_documents(["alpha", "beta"])


def test_input_output_count_mismatch_fails() -> None:
    class CountMismatchEmbeddings(FakeEmbeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 2.0, 3.0]]

    with pytest.raises(RAGFoundationsError):
        provider(CountMismatchEmbeddings).embed_documents(["alpha", "beta"])


def test_error_output_does_not_expose_api_key_assignment() -> None:
    class FailingEmbeddings(FakeEmbeddings):
        def embed_query(self, query: str) -> list[float]:
            raise RuntimeError("request failed api_key=secret")

    with pytest.raises(RAGFoundationsError) as exc_info:
        provider(FailingEmbeddings).embed_query("remote work days")

    message = str(exc_info.value)
    assert "super-secret-value" not in message
    assert "api_key= <redacted>" in message
