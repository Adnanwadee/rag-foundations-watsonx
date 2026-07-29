"""Small watsonx.ai SDK helpers for access checks and model discovery."""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from rag_foundations.config import AppSettings


@dataclass(frozen=True)
class WatsonxRuntime:
    settings: AppSettings
    credentials: Any
    client: Any


def sdk_version() -> str:
    return importlib.metadata.version("ibm-watsonx-ai")


def region_from_url(url: str) -> str:
    host = urlparse(url).netloc or urlparse(url).path
    parts = host.split(".")
    return parts[0] if len(parts) > 1 and parts[0] in {"us-south", "eu-de", "eu-gb"} else host


def create_runtime(settings: AppSettings | None = None) -> WatsonxRuntime:
    active_settings = settings or AppSettings()
    active_settings.require_watsonx_credentials()

    from ibm_watsonx_ai import APIClient, Credentials

    credentials = Credentials(
        url=active_settings.watsonx_url,
        api_key=active_settings.watsonx_api_key.get_secret_value(),  # type: ignore[union-attr]
    )
    client = APIClient(credentials=credentials, project_id=active_settings.watsonx_project_id)
    return WatsonxRuntime(settings=active_settings, credentials=credentials, client=client)


def get_chat_model_specs(client: Any) -> list[dict[str, Any]]:
    response = client.foundation_models.get_chat_model_specs(get_all=True)
    return list(response.get("resources", []))


def get_embedding_model_specs(client: Any) -> list[dict[str, Any]]:
    response = client.foundation_models.get_embeddings_model_specs(get_all=True)
    return list(response.get("resources", []))


def model_id(spec: dict[str, Any]) -> str:
    return str(spec.get("model_id") or spec.get("id") or "")


def lifecycle_ids(spec: dict[str, Any]) -> list[str]:
    return [str(item.get("id")) for item in spec.get("lifecycle", []) if isinstance(item, dict)]


def is_available(spec: dict[str, Any]) -> bool:
    ids = lifecycle_ids(spec)
    return "available" in ids and "withdrawn" not in ids


def is_deprecated(spec: dict[str, Any]) -> bool:
    return "deprecated" in lifecycle_ids(spec)


def function_ids(spec: dict[str, Any]) -> set[str]:
    functions = spec.get("functions", [])
    return {str(item.get("id")) for item in functions if isinstance(item, dict)}


def task_ids(spec: dict[str, Any]) -> set[str]:
    raw_tasks = spec.get("task_ids") or spec.get("tasks") or []
    if isinstance(raw_tasks, list):
        return {str(task) for task in raw_tasks}
    return set()


def select_primary_chat_model(specs: list[dict[str, Any]]) -> dict[str, Any]:
    preferred_ids = ["ibm/granite-4-h-small"]
    eligible = [
        spec
        for spec in specs
        if is_available(spec)
        and not is_deprecated(spec)
        and "text_chat" in function_ids(spec)
        and "question_answering" in task_ids(spec)
        and "retrieval_augmented_generation" in task_ids(spec)
    ]
    for preferred_id in preferred_ids:
        for spec in eligible:
            if model_id(spec) == preferred_id:
                return spec
    if eligible:
        return eligible[0]
    raise RuntimeError("No eligible chat model was discovered.")


def select_comparison_chat_model(
    specs: list[dict[str, Any]],
    *,
    primary_model_id: str,
) -> dict[str, Any] | None:
    eligible = [
        spec
        for spec in specs
        if model_id(spec) != primary_model_id
        and is_available(spec)
        and not is_deprecated(spec)
        and "text_chat" in function_ids(spec)
    ]
    for spec in eligible:
        label = str(spec.get("label", "")).lower()
        if "small" in label or "mini" in label:
            return spec
    return eligible[0] if eligible else None


def select_embedding_model(specs: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        spec
        for spec in specs
        if is_available(spec) and not is_deprecated(spec) and "embedding" in function_ids(spec)
    ]
    for spec in eligible:
        if model_id(spec) == "ibm/granite-embedding-278m-multilingual":
            return spec
    if eligible:
        return eligible[0]
    raise RuntimeError("No eligible embedding model was discovered.")


def verify_project_access(client: Any, project_id: str) -> bool:
    details = client.projects.get_details(project_id=project_id)
    return bool(details)


def run_chat_smoke_test(client: Any, *, project_id: str, model_id_value: str) -> str:
    from ibm_watsonx_ai.foundation_models import ModelInference

    model = ModelInference(model_id=model_id_value, api_client=client, project_id=project_id)
    response = model.chat(
        messages=[
            {
                "role": "system",
                "content": "You are testing IBM watsonx.ai connectivity. Answer briefly.",
            },
            {"role": "user", "content": "Reply with: watsonx access confirmed"},
        ]
    )
    content = response["choices"][0]["message"]["content"]
    if not str(content).strip():
        raise RuntimeError("Chat smoke test returned an empty assistant response.")
    return str(content).strip()
