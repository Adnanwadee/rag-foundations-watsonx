"""Offline tests for selected file-based prompt assets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_foundations.prompt_assets import (
    asset_hash_manifest,
    grounded_messages,
    load_few_shot,
    load_text_asset,
    render_template,
    tone_messages,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


EXPECTED_PROMPT_FILES = {
    "prompts/v2/grounded/candidate_a.system.txt",
    "prompts/v2/grounded/candidate_a.user.txt",
    "prompts/v2/tones/formal.system.txt",
    "prompts/v2/tones/formal.user.txt",
    "prompts/v2/tones/casual.system.txt",
    "prompts/v2/tones/casual.user.txt",
    "prompts/v2/tones/executive.system.txt",
    "prompts/v2/tones/executive.user.txt",
    "prompts/v2/few_shot/formal.json",
    "prompts/v2/few_shot/casual.json",
    "prompts/v2/few_shot/executive.json",
    "prompts/v2/schemas/grounded_output.schema.json",
    "prompts/v2/schemas/tone_output.schema.json",
}


def test_expected_prompt_files_and_hashes_exist() -> None:
    hashes = asset_hash_manifest()
    assert EXPECTED_PROMPT_FILES <= set(hashes)
    assert all(len(value) == 64 for value in hashes.values())


def test_prompt_template_rendering_is_strict() -> None:
    template = "Question: {{ question }}\nContext: {{ retrieved_context }}"
    assert render_template(template, {"question": "Q", "retrieved_context": "C"}) == "Question: Q\nContext: C"
    with pytest.raises(ValueError, match="missing"):
        render_template(template, {"question": "Q"})
    with pytest.raises(ValueError, match="unknown"):
        render_template(template, {"question": "Q", "retrieved_context": "C", "extra": "x"})


def test_grounded_prompts_have_expected_variables_and_anti_copy_rule() -> None:
    user = load_text_asset("prompts/v2/grounded/candidate_a.user.txt")
    system = load_text_asset("prompts/v2/grounded/candidate_a.system.txt")
    assert set(user.variables) == {"question", "retrieved_context"}
    assert "Do not copy irrelevant chunk text" in system.text
    messages = grounded_messages("a", question="What is the rule?", retrieved_context="[chunk_id: c1]")
    assert "{{" not in messages[1]["content"]


def test_tone_prompts_have_three_few_shots_and_do_not_generate_citations() -> None:
    for tone in ("formal_report_summary", "casual_message", "concise_executive_briefing"):
        examples = load_few_shot(tone)
        assert len(examples) == 3
        messages = tone_messages(tone, original_question="Q", grounded_answer="A")
        assert "Do not create, alter, or remove citations" in messages[0]["content"]
        assert "{{" not in messages[1]["content"]


def test_output_schemas_are_strict_json_objects() -> None:
    for path in (
        "prompts/v2/schemas/grounded_output.schema.json",
        "prompts/v2/schemas/tone_output.schema.json",
    ):
        schema = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
