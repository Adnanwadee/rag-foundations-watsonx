"""Versioned prompt asset loading, validation, and strict rendering."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = REPO_ROOT / "prompts" / "v2"
PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")

@dataclass(frozen=True)
class PromptAsset:
    path: str
    text: str
    sha256: str
    variables: tuple[str, ...]

def repository_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_text_asset(path: str | Path) -> PromptAsset:
    p = (REPO_ROOT / path).resolve()
    if not p.is_file():
        raise FileNotFoundError(path)
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"blank prompt asset: {path}")
    variables = tuple(sorted(set(PLACEHOLDER_RE.findall(text))))
    return PromptAsset(repository_relative(p), text, sha256_text(text), variables)

def render_template(text: str, variables: dict[str, str]) -> str:
    expected = set(PLACEHOLDER_RE.findall(text))
    provided = set(variables)
    if expected - provided:
        raise ValueError(f"missing template variables: {sorted(expected - provided)}")
    if provided - expected:
        raise ValueError(f"unknown template variables: {sorted(provided - expected)}")
    rendered = PLACEHOLDER_RE.sub(lambda m: str(variables[m.group(1)]), text)
    if PLACEHOLDER_RE.search(rendered):
        raise ValueError("unresolved prompt variable remains")
    if not rendered.strip():
        raise ValueError("rendered prompt is blank")
    return rendered

def load_few_shot(tone: str, *, version: str = "v2") -> list[dict[str, Any]]:
    if version != "v2":
        raise ValueError("only selected v2 prompt assets are available")
    mapping = {
        "formal_report_summary": "formal",
        "casual_message": "casual",
        "concise_executive_briefing": "executive",
    }
    if tone not in mapping:
        raise ValueError("unknown tone")
    path = PROMPT_ROOT / "few_shot" / f"{mapping[tone]}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(data) != 3:
        raise ValueError("each tone requires exactly three few-shot examples")
    return data

def render_examples(tone: str, *, version: str = "v2") -> str:
    blocks = []
    for example in load_few_shot(tone, version=version):
        expected = example["expected_output"]
        if not isinstance(expected, str):
            expected = json.dumps(expected, ensure_ascii=False, sort_keys=True)
        blocks.append(
            "\n".join(
                [
                    "Few-shot example:",
                    f"Original question: {example['original_question']}",
                    f"Grounded answer: {example['grounded_answer']}",
                    f"Expected output: {expected}",
                ]
            )
        )
    return "\n\n".join(blocks)

def asset_hash_manifest() -> dict[str, str]:
    files = sorted(path for path in PROMPT_ROOT.rglob("*") if path.is_file())
    return {repository_relative(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

def grounded_messages(candidate: str, *, question: str, retrieved_context: str) -> list[dict[str, str]]:
    if candidate != "a":
        raise ValueError("only selected grounded Candidate A is available")
    system = load_text_asset("prompts/v2/grounded/candidate_a.system.txt")
    user = load_text_asset("prompts/v2/grounded/candidate_a.user.txt")
    return [
        {"role": "system", "content": system.text},
        {
            "role": "user",
            "content": render_template(
                user.text,
                {"question": question, "retrieved_context": retrieved_context},
            ),
        },
    ]

def tone_messages(
    tone: str,
    *,
    original_question: str,
    grounded_answer: str,
    protected_elements: str = "{}",
    version: str = "v2",
) -> list[dict[str, str]]:
    if version != "v2":
        raise ValueError("only selected v2 prompt assets are available")
    mapping = {
        "formal_report_summary": "formal",
        "casual_message": "casual",
        "concise_executive_briefing": "executive",
    }
    if tone not in mapping:
        raise ValueError("unknown tone")
    system = load_text_asset(f"prompts/v2/tones/{mapping[tone]}.system.txt")
    user = load_text_asset(f"prompts/v2/tones/{mapping[tone]}.user.txt")
    content = render_examples(tone, version=version) + "\n\n" + system.text
    variables = {"original_question": original_question, "grounded_answer": grounded_answer}
    if "protected_elements" in user.variables:
        variables["protected_elements"] = protected_elements
    if "tone" in user.variables:
        variables["tone"] = tone
    return [
        {"role": "system", "content": content},
        {
            "role": "user",
            "content": render_template(user.text, variables),
        },
    ]
