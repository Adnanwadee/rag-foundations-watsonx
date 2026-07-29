"""Command-line interface for the frozen Final v2 RAG workflow."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from typing import Sequence

from rag_foundations.errors import RAGFoundationsError
from rag_foundations.pipeline import PipelineResult, run_question
from rag_foundations.schemas import Citation, ToneName, ToneResult


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m rag_foundations.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ask = subparsers.add_parser("ask", help="Ask one grounded policy question.")
    ask.add_argument("question", help="Question to answer from the persisted FAISS corpus.")
    tone_group = ask.add_mutually_exclusive_group()
    tone_group.add_argument("--tone", choices=[tone.value for tone in ToneName])
    tone_group.add_argument("--all-tones", action="store_true")
    ask.add_argument("--json", action="store_true", help="Print valid JSON only.")
    return parser


def _source_label(citation: Citation) -> str:
    title = citation.title or citation.document_id
    return f"{title} | {citation.section_heading} | {citation.source_path}"


def _print_sources(citations: list[Citation]) -> None:
    print("Sources:")
    if not citations:
        print("- None")
        return
    for citation in citations:
        print(f"- {_source_label(citation)}")


def _tone_heading(tone: ToneName) -> str:
    return {
        ToneName.FORMAL_REPORT_SUMMARY: "Formal report summary",
        ToneName.CASUAL_MESSAGE: "Casual message",
        ToneName.CONCISE_EXECUTIVE_BRIEFING: "Concise executive briefing",
    }[tone]


def _print_tone_result(tone_result: ToneResult) -> None:
    print()
    print(f"{_tone_heading(tone_result.tone)} ({tone_result.tone.value}):")
    print(tone_result.output)


def print_human(result: PipelineResult) -> None:
    """Print a concise human-readable CLI response."""

    print("Answer:")
    print(result.grounded_result.answer)
    print()
    print(f"Answerable status: {str(result.grounded_result.is_answerable).lower()}")
    print()
    _print_sources(result.grounded_result.citations)

    if result.tone_result is not None:
        _print_tone_result(result.tone_result)

    if result.all_tone_result is not None:
        for tone_result in result.all_tone_result.variations:
            _print_tone_result(tone_result)


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, RAGFoundationsError):
        return str(exc)
    safe = RAGFoundationsError("CLI request failed.", error_type=type(exc).__name__, reason=str(exc))
    return str(safe)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "ask":
            sdk_stderr = io.StringIO()
            with contextlib.redirect_stderr(sdk_stderr):
                result = run_question(
                    args.question,
                    tone=args.tone,
                    all_tones=args.all_tones,
                )
            if args.json:
                print(json.dumps(result.model_dump(mode="json", exclude_none=True), indent=2))
            else:
                print_human(result)
            return 0
    except SystemExit as exc:
        return int(exc.code)
    except (RAGFoundationsError, ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {_safe_error(exc)}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI boundary for SDK exceptions.
        print(f"Error: {_safe_error(exc)}", file=sys.stderr)
        return 1

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
