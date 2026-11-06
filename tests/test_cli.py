"""Tests for the text-analyse CLI."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from lupaxa.text_analyse import __version__, analyse
from lupaxa.text_analyse.cli import main
from lupaxa.text_analyse.fetch import Fetched

PASSAGE = "The cat sat on the mat."


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"text-analyse {__version__}"


def test_default_table_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "text · auto" in out
    assert "Text Analysis" in out
    assert "Most Common Words" not in out
    assert "Key Stage 1" in out


def test_json_format(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--format", "json", "--mode", "text"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["analysis_mode"] == "text"
    assert payload["words"] == 6
    assert "most_common_words" not in payload
    assert "Text ·" not in json.dumps(payload)


def test_plain_text_format(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--format", "text"]) == 0
    out = capsys.readouterr().out
    assert "Text Analysis" in out
    assert "╭" not in out
    assert "Most Common Words" not in out


def test_file_and_code_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "sample.py"
    path.write_text("def foo():\n    if x:\n        return 1\n", encoding="utf-8")
    assert main([str(path), "--mode", "code"]) == 0
    out = capsys.readouterr().out
    assert "code · forced" in out
    assert "Source Code Analysis" in out
    assert "Function-like blocks" in out


def test_markdown_file_is_text_in_auto_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "README.md"
    path.write_text("def foo():\n    if x:\n        return 1\n" * 5, encoding="utf-8")
    assert main(["-f", str(path)]) == 0
    assert "text · auto" in capsys.readouterr().out


def test_python_file_is_code_in_auto_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "sample.py"
    path.write_text("def foo():\n    if x:\n        return 1\n", encoding="utf-8")
    assert main([str(path)]) == 0
    assert "code · auto" in capsys.readouterr().out


def test_file_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "note.txt"
    path.write_text(PASSAGE, encoding="utf-8")
    assert main(["--file", str(path), "--format", "text", "--mode", "text"]) == 0
    assert "6" in capsys.readouterr().out


def test_rejects_two_sources(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["note.txt", "--url", "https://example.test"]) == 1
    assert "only one" in capsys.readouterr().err


def test_empty_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO("  \n"))
    assert main([]) == 1
    assert "No text provided." in capsys.readouterr().err


def test_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--file", "does-not-exist-text-analyse.txt"]) == 1
    assert "Error reading file" in capsys.readouterr().err


def test_us_scheme_in_table(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--reading-age-scheme", "us", "--mode", "text"]) == 0
    assert "Kindergarten" in capsys.readouterr().out


def test_html_url_is_text_in_auto_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = "def foo():\n    if x:\n        return 1\n" * 5

    def fake_fetch(_url: str) -> Fetched:
        return Fetched(text=code, is_html=True)

    monkeypatch.setattr("lupaxa.text_analyse.cli.fetch", fake_fetch)
    assert main(["--url", "https://example.test"]) == 0
    assert "text · auto" in capsys.readouterr().out


def test_html_url_can_be_forced_to_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = "def foo():\n    if x:\n        return 1\n"

    def fake_fetch(_url: str) -> Fetched:
        return Fetched(text=code, is_html=True)

    monkeypatch.setattr("lupaxa.text_analyse.cli.fetch", fake_fetch)
    assert main(["--url", "https://example.test", "--mode", "code"]) == 0
    assert "code · forced" in capsys.readouterr().out


def test_min_flesch_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--mode", "text", "--min-flesch", "200"]) == 1
    captured = capsys.readouterr()
    assert "Text Analysis" in captured.out
    assert "below 200" in captured.err


def test_max_grade_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--mode", "text", "--max-grade", "-2"]) == 1
    assert "above -2" in capsys.readouterr().err


def test_readability_check_passes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(PASSAGE))
    assert main(["--mode", "text", "--min-flesch", "50", "--wpm", "100"]) == 0
    assert "Reading time (100 wpm)" in capsys.readouterr().out


def test_readability_check_rejects_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO("def foo():\n    return 1\n"))
    assert main(["--mode", "code", "--min-flesch", "60"]) == 2
    assert "apply to text only" in capsys.readouterr().err


def test_several_files_print_one_row_each(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    easy = tmp_path / "easy.md"
    hard = tmp_path / "hard.md"
    easy.write_text("The cat sat on the mat. The dog sat on the log.\n", encoding="utf-8")
    hard.write_text("A rat sat on the mat. A hen sat on the log.\n", encoding="utf-8")
    assert main([str(easy), str(hard), "--min-flesch", "0"]) == 0
    out = capsys.readouterr().out
    assert "easy.md" in out
    assert "hard.md" in out
    assert "Text Analysis" not in out
    assert "Characters (with spaces)" not in out


def test_check_prints_only_failures(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    easy = tmp_path / "easy.md"
    hard = tmp_path / "hard.md"
    easy_text = "The cat sat on the mat. The dog sat on the log."
    hard_text = (
        "Operationalisation of phenomenological epistemological infrastructures "
        "requires interdisciplinary reconceptualisation."
    )
    easy.write_text(easy_text + "\n", encoding="utf-8")
    hard.write_text(hard_text + "\n", encoding="utf-8")
    easy_score = analyse(easy_text, mode="text")["flesch_reading_ease"]
    hard_score = analyse(hard_text, mode="text")["flesch_reading_ease"]
    threshold = (easy_score + hard_score) / 2
    assert easy_score > threshold > hard_score
    assert main([str(easy), str(hard), "--check", "--min-flesch", str(threshold)]) == 1
    out = capsys.readouterr().out
    assert "hard.md" in out
    assert "easy.md" not in out
    assert "below" in out


def test_check_on_a_passing_file_is_silent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "easy.md"
    path.write_text("The cat sat on the mat.\n", encoding="utf-8")
    assert main([str(path), "--check", "--min-flesch", "0"]) == 0
    assert capsys.readouterr().out == ""


def test_check_needs_a_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--check"]) == 2
    assert "--min-flesch" in capsys.readouterr().err


def test_directory_walks_documentation_and_skips_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs = tmp_path / "docs"
    nested = docs / "nested"
    nested.mkdir(parents=True)
    (docs / "guide.md").write_text(PASSAGE + "\n", encoding="utf-8")
    (nested / "notes.rst").write_text(PASSAGE + "\n", encoding="utf-8")
    (docs / "skip.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    hidden = docs / ".git"
    hidden.mkdir()
    (hidden / "hidden.md").write_text(PASSAGE + "\n", encoding="utf-8")
    assert main([str(docs)]) == 0
    out = capsys.readouterr().out
    assert "guide.md" in out
    assert "notes.rst" in out
    assert "skip.py" not in out
    assert "hidden.md" not in out


def test_checks_on_code_files_only_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "sample.py"
    path.write_text("def foo():\n    return 1\n", encoding="utf-8")
    other = tmp_path / "other.py"
    other.write_text("x = 1\n", encoding="utf-8")
    assert main([str(path), str(other), "--min-flesch", "60"]) == 2
    assert "apply to text only" in capsys.readouterr().err
