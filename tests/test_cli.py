from __future__ import annotations

import json
import logging

import pytest

from rag_foundations import cli
from rag_foundations.constants import UNSUPPORTED_ANSWER
from rag_foundations.errors import RAGFoundationsError
from rag_foundations.pipeline import PipelineResult
from rag_foundations.schemas import (
    AllToneResult,
    Citation,
    GroundedAnswerResult,
    ToneName,
    ToneResult,
)


def citation() -> Citation:
    return Citation(
        citation_id="citation-1-chunk-1",
        chunk_id="chunk-1",
        document_id="policy-remote-work",
        title="Remote Work Policy",
        section_heading="5. Maximum Remote Days and Office Attendance",
        source_path="data/documents_v2_1/flexible_work_workplace_access_policy.md",
    )


def result(
    *,
    tone: ToneName | None = None,
    all_tones: bool = False,
    answerable: bool = True,
) -> PipelineResult:
    grounded = GroundedAnswerResult(
        answer=(
            "Eligible employees may work remotely up to 2 working days per week."
            if answerable
            else UNSUPPORTED_ANSWER
        ),
        is_answerable=answerable,
        citations=[citation()] if answerable else [],
    )
    tone_result = (
        ToneResult(tone=tone, output=f"{tone.value} output", citations=grounded.citations)
        if tone is not None
        else None
    )
    all_tone_result = None
    if all_tones:
        all_tone_result = AllToneResult(
            original_answer=grounded.answer,
            variations=[
                ToneResult(tone=item, output=f"{item.value} output", citations=grounded.citations)
                for item in ToneName
            ],
        )
    return PipelineResult(
        question="How many remote days?",
        grounded_result=grounded,
        tone_result=tone_result,
        all_tone_result=all_tone_result,
        metadata={"mode": "test"},
    )


def test_grounded_only_command(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "run_question", lambda *args, **kwargs: result())

    exit_code = cli.main(["ask", "How many remote days?"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Answer:" in captured.out
    assert "Answerable status: true" in captured.out


@pytest.mark.parametrize(
    "tone",
    [
        ToneName.FORMAL_REPORT_SUMMARY,
        ToneName.CASUAL_MESSAGE,
        ToneName.CONCISE_EXECUTIVE_BRIEFING,
    ],
)
def test_valid_tone_commands(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tone: ToneName,
) -> None:
    def fake_run_question(question: str, **kwargs: object) -> PipelineResult:
        assert kwargs["tone"] == tone.value
        return result(tone=tone)

    monkeypatch.setattr(cli, "run_question", fake_run_question)

    exit_code = cli.main(["ask", "How many remote days?", "--tone", tone.value])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert tone.value in captured.out
    assert f"{tone.value} output" in captured.out


def test_all_tones_command(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fake_run_question(question: str, **kwargs: object) -> PipelineResult:
        assert kwargs["all_tones"] is True
        return result(all_tones=True)

    monkeypatch.setattr(cli, "run_question", fake_run_question)

    exit_code = cli.main(["ask", "How many remote days?", "--all-tones"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Formal report summary" in captured.out
    assert "Casual message" in captured.out
    assert "Concise executive briefing" in captured.out


def test_json_output_parses_successfully(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "run_question", lambda *args, **kwargs: result(all_tones=True))

    exit_code = cli.main(["ask", "How many remote days?", "--all-tones", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)

    assert exit_code == 0
    assert parsed["grounded_result"]["is_answerable"] is True
    assert len(parsed["all_tone_result"]["variations"]) == 3


def test_json_output_remains_parseable_when_debug_logging_enabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    def noisy_run_question(*args: object, **kwargs: object) -> PipelineResult:
        logging.getLogger("rag_foundations.cli").debug("diagnostic without secrets")
        return result()

    monkeypatch.setattr(cli, "run_question", noisy_run_question)

    exit_code = cli.main(["ask", "How many remote days?", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)

    assert exit_code == 0
    assert parsed["grounded_result"]["is_answerable"] is True
    assert "diagnostic without secrets" in captured.err
    assert "diagnostic without secrets" not in captured.out


def test_cli_logging_configuration_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    calls = {"count": 0}

    def noisy_run_question(*args: object, **kwargs: object) -> PipelineResult:
        calls["count"] += 1
        logging.getLogger("rag_foundations.cli").debug("one project diagnostic")
        return result()

    monkeypatch.setattr(cli, "run_question", noisy_run_question)

    assert cli.main(["ask", "How many remote days?", "--json"]) == 0
    first = capsys.readouterr()
    assert cli.main(["ask", "How many remote days?", "--json"]) == 0
    second = capsys.readouterr()

    assert calls["count"] == 2
    assert first.err.count("one project diagnostic") == 1
    assert second.err.count("one project diagnostic") == 1


def test_cli_logging_does_not_reset_root_or_third_party_loggers(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    root_logger = logging.getLogger()
    third_party_logger = logging.getLogger("httpx")
    original_root_level = root_logger.level
    original_root_handlers = list(root_logger.handlers)
    original_httpx_level = third_party_logger.level

    def noisy_run_question(*args: object, **kwargs: object) -> PipelineResult:
        logging.getLogger("rag_foundations.cli").debug("project debug visible")
        logging.getLogger("httpx").debug("third party debug hidden")
        return result()

    monkeypatch.setattr(cli, "run_question", noisy_run_question)

    assert cli.main(["ask", "How many remote days?", "--json"]) == 0
    captured = capsys.readouterr()

    assert root_logger.level == original_root_level
    assert root_logger.handlers == original_root_handlers
    assert third_party_logger.level == original_httpx_level
    assert "project debug visible" in captured.err
    assert "third party debug hidden" not in captured.err


def test_cli_help_does_not_instantiate_watsonx_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_run_question(*args: object, **kwargs: object) -> PipelineResult:
        raise AssertionError("run_question must not be called for help")

    monkeypatch.delenv("WATSONX_URL", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)
    monkeypatch.delenv("WATSONX_API_KEY", raising=False)
    monkeypatch.setattr(cli, "run_question", fail_run_question)

    exit_code = cli.main(["ask", "--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out


def test_human_readable_output_includes_answer_and_sources(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "run_question", lambda *args, **kwargs: result())

    exit_code = cli.main(["ask", "How many remote days?"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Eligible employees may work remotely" in captured.out
    assert "Remote Work Policy" in captured.out
    assert "data/documents_v2_1/flexible_work_workplace_access_policy.md" in captured.out


def test_tone_and_all_tones_conflict(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(
        [
            "ask",
            "How many remote days?",
            "--tone",
            "formal_report_summary",
            "--all-tones",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "not allowed with argument" in captured.err


def test_blank_question_returns_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["ask", "   "])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "question must not be blank" in captured.err


def test_invalid_tone_returns_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["ask", "How many remote days?", "--tone", "pirate"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "invalid choice" in captured.err


def test_typed_pipeline_failure_is_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_run_question(*args: object, **kwargs: object) -> PipelineResult:
        raise RAGFoundationsError("generation failed api_key=secret")

    monkeypatch.setattr(cli, "run_question", broken_run_question)

    exit_code = cli.main(["ask", "How many remote days?"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "super-secret-token" not in captured.err
    assert "api_key= <redacted>" in captured.err
    assert "Traceback" not in captured.err


def test_third_party_stderr_is_suppressed_before_safe_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def noisy_run_question(*args: object, **kwargs: object) -> PipelineResult:
        print("raw sdk stderr api_key=secret", file=cli.sys.stderr)
        raise RAGFoundationsError("generation failed api_key=secret")

    monkeypatch.setattr(cli, "run_question", noisy_run_question)

    exit_code = cli.main(["ask", "How many remote days?"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "raw sdk stderr" not in captured.err
    assert "super-secret-token" not in captured.err
    assert "api_key= <redacted>" in captured.err
