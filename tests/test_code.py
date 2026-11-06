"""Tests for code metrics and mode detection."""

from __future__ import annotations

import pytest

from lupaxa.text_analyse import analyse, analyse_code, looks_like_code

FUNCTION = "def foo():\n    if x:\n        return 1\n"
COMMENTS = "# comment\nx = 1\n\ny = 2\n"


def test_function_metrics() -> None:
    result = analyse_code(FUNCTION)
    assert result["analysis_mode"] == "code"
    assert result["total_lines"] == 3
    assert result["blank_lines"] == 0
    assert result["comment_lines"] == 0
    assert result["code_lines"] == 3
    assert result["function_like_blocks"] == 1
    assert result["estimated_cyclomatic_complexity"] == 2
    assert result["max_line_length"] == len("        return 1")
    assert result["average_line_length"] == pytest.approx(35 / 3)
    assert result["complexity_per_100_lines"] == pytest.approx(2 / 0.03)


def test_comment_and_blank_lines() -> None:
    result = analyse_code(COMMENTS)
    assert result["total_lines"] == 4
    assert result["blank_lines"] == 1
    assert result["comment_lines"] == 1
    assert result["code_lines"] == 2
    assert result["comment_density"] == pytest.approx(0.5)
    assert result["estimated_cyclomatic_complexity"] == 1
    assert result["complexity_per_100_lines"] == pytest.approx(50)


def test_boolean_and_ternary_add_complexity() -> None:
    result = analyse_code("a && b ? c : d\n")
    assert result["estimated_cyclomatic_complexity"] == 3
    assert result["function_like_blocks"] == 0


def test_comments_try_and_access_modifiers_do_not_count() -> None:
    commented = analyse_code("# if for while\n// if (x)\nx = 1\n")
    assert commented["estimated_cyclomatic_complexity"] == 1
    declared = analyse_code("public void run() {\n    try {\n        return 1;\n    }\n}\n")
    assert declared["function_like_blocks"] == 0
    assert declared["estimated_cyclomatic_complexity"] == 1


def test_tabs_are_excluded_from_the_no_space_count() -> None:
    result = analyse_code("a\tb\n")
    assert result["characters_no_spaces"] == 2


def test_detection_thresholds() -> None:
    prose = (
        "Projects are shaped for developers. Ideas come from the freedom "
        "to create. We return to the work if the class of problem is "
        "practical, and an open community can import nothing from a "
        "private company."
    )
    assert looks_like_code("") is False
    assert looks_like_code("I wonder if the cat sat on the mat.") is False
    assert looks_like_code(prose) is False
    assert looks_like_code(FUNCTION) is True
    assert looks_like_code("{" * 4 + "a" * 100) is True


def test_auto_mode_follows_detection() -> None:
    assert analyse("The cat sat on the mat.")["analysis_mode"] == "text"
    assert analyse(FUNCTION)["analysis_mode"] == "code"
    forced = analyse(FUNCTION, mode="text")
    assert forced["analysis_mode"] == "text"


MARKDOWN = (
    "# Title\n\n"
    "The cat sat on the mat.\n\n"
    "```python\n"
    "def foo():\n"
    "    if x:\n"
    "        return 1\n"
    "```\n\n"
    "See the [docs](https://example.com/very/long/path) today.\n\n"
    '<p align="center">ignored</p>\n'
)


def test_markdown_source_scores_the_prose_only() -> None:
    result = analyse(MARKDOWN, source="README.md")
    assert result["analysis_mode"] == "text"
    assert result["words"] == 12
    assert analyse(MARKDOWN, mode="text")["words"] > result["words"]


def test_tilde_fences_are_dropped_for_markdown() -> None:
    sample = "Hello there friend.\n\n~~~\ndef foo():\n    if x:\n        return 1\n~~~\n"
    result = analyse(sample, source="guide.markdown")
    assert result["analysis_mode"] == "text"
    assert result["words"] == 3


def test_markdown_suffix_forces_text_and_code_suffix_does_not() -> None:
    code = FUNCTION * 5
    assert analyse(code, source="README.md")["analysis_mode"] == "text"
    assert analyse(code, source="sample.py")["analysis_mode"] == "code"


def test_rst_is_text_but_keeps_fenced_blocks() -> None:
    sample = "Hello.\n\n```\ndef foo():\n    if x:\n        return 1\n```\n"
    as_rst = analyse(sample, source="notes.rst")
    as_text = analyse(sample, mode="text")
    assert as_rst["analysis_mode"] == "text"
    assert as_rst["words"] == as_text["words"]


def test_forced_code_keeps_a_markdown_file_intact() -> None:
    result = analyse(MARKDOWN, mode="code", source="README.md")
    assert result["analysis_mode"] == "code"
    assert result["estimated_cyclomatic_complexity"] > 1


def test_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode"):
        analyse("Hello.", mode="poem")  # type: ignore[call-overload]
