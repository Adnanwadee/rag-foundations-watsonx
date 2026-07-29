"""watsonx.ai embedding provider for FAISS-backed retrieval."""

from __future__ import annotations

from typing import Any

from rag_foundations.config import AppSettings
from rag_foundations.errors import RAGFoundationsError


class WatsonxEmbeddingProvider:
    """Direct wrapper around `ibm_watsonx_ai.foundation_models.Embeddings`."""

    def __init__(
        self,
        *,
        model_id: str,
        api_client: Any | None = None,
        settings: AppSettings | None = None,
        embeddings_cls: Any | None = None,
    ) -> None:
        self.model_id = model_id
        self._api_client = api_client
        self._settings = settings
        self._embeddings_cls = embeddings_cls
        self._embeddings: Any | None = None
        self._embedding_dimension: int | None = None

    @property
    def embedding_dimension(self) -> int | None:
        return self._embedding_dimension

    @staticmethod
    def _validate_text(text: str) -> None:
        if not text.strip():
            raise ValueError("text must not be blank")

    def _load_embeddings(self) -> Any:
        if self._embeddings is not None:
            return self._embeddings

        embeddings_cls = self._embeddings_cls
        if embeddings_cls is None:
            from ibm_watsonx_ai.foundation_models import Embeddings

            embeddings_cls = Embeddings

        if self._api_client is not None:
            self._embeddings = embeddings_cls(model_id=self.model_id, api_client=self._api_client)
            return self._embeddings

        settings = self._settings or AppSettings()
        settings.require_watsonx_credentials()
        from ibm_watsonx_ai import APIClient, Credentials

        credentials = Credentials(
            url=settings.watsonx_url,
            api_key=settings.watsonx_api_key.get_secret_value(),  # type: ignore[union-attr]
        )
        client = APIClient(credentials=credentials, project_id=settings.watsonx_project_id)
        self._embeddings = embeddings_cls(
            model_id=self.model_id,
            api_client=client,
            project_id=settings.watsonx_project_id,
        )
        return self._embeddings

    @staticmethod
    def _to_vector(value: Any) -> list[float]:
        if hasattr(value, "tolist"):
            value = value.tolist()
        return [float(item) for item in value]

    def _validate_vectors(self, vectors: list[list[float]], expected_count: int) -> list[list[float]]:
        if len(vectors) != expected_count:
            raise RAGFoundationsError(
                "Embedding output count mismatch.",
                expected_count=expected_count,
                actual_count=len(vectors),
            )
        if not vectors or any(not vector for vector in vectors):
            raise RAGFoundationsError("Embedding output must contain non-empty vectors.")

        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1:
            raise RAGFoundationsError(
                "Embedding vectors have inconsistent dimensions.",
                dimensions=sorted(dimensions),
            )
        self._embedding_dimension = dimensions.pop()
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            raise ValueError("texts must not be empty")
        for text in texts:
            self._validate_text(text)

        try:
            result = self._load_embeddings().embed_documents(texts)
            vectors = [self._to_vector(vector) for vector in result]
        except Exception as exc:
            raise RAGFoundationsError("watsonx embedding request failed.", reason=str(exc)) from exc
        return self._validate_vectors(vectors, len(texts))

    def embed_query(self, query: str) -> list[float]:
        self._validate_text(query)
        try:
            result = self._load_embeddings().embed_query(query)
            vector = self._to_vector(result)
        except Exception as exc:
            raise RAGFoundationsError("watsonx query embedding request failed.", reason=str(exc)) from exc
        return self._validate_vectors([vector], 1)[0]
