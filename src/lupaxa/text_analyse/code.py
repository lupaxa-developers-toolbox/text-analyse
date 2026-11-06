"""Language-agnostic source metrics."""

from __future__ import annotations

import re

from lupaxa.text_analyse.constants import COMMENT_PREFIXES
from lupaxa.text_analyse.text import character_counts, safe_div
from lupaxa.text_analyse.types import CodeAnalysis

_DECISION_RE = re.compile(r"\b(if|for|while|case|elif|else if|catch|when|switch|except)\b")
_BOOL_OPS_RE = re.compile(r"&&|\|\|")
_FUNC_RE = re.compile(r"\b(def|function|fn|class|interface|module)\b")


def analyse_code(text: str) -> CodeAnalysis:
    """Estimate size, comments, and a file-level decision count.

    The complexity figure starts at 1 and adds one for each decision
    keyword, ``&&``, ``||``, and line that contains both ``?`` and ``:``.
    Comment lines are ignored. ``try`` and access modifiers are not counted.
    It is a whole-file heuristic, not a per-function cyclomatic score.
    """
    characters_with_spaces, characters_no_spaces = character_counts(text)
    lines = text.splitlines()
    total_lines = len(lines)
    non_empty_lines = 0
    blank_lines = 0
    comment_lines = 0
    code_lines = 0
    total_length = 0
    max_length = 0
    function_like_blocks = 0
    complexity = 1

    for line in lines:
        length = len(line)
        total_length += length
        if length > max_length:
            max_length = length

        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue

        non_empty_lines += 1
        if stripped.startswith(COMMENT_PREFIXES):
            comment_lines += 1
            continue

        code_lines += 1
        complexity += len(_DECISION_RE.findall(line))
        complexity += len(_BOOL_OPS_RE.findall(line))
        if "?" in line and ":" in line:
            complexity += 1
        if _FUNC_RE.search(line):
            function_like_blocks += 1

    complexity_per_100 = safe_div(complexity, code_lines / 100.0) if code_lines else 0.0
    return {
        "analysis_mode": "code",
        "characters_with_spaces": characters_with_spaces,
        "characters_no_spaces": characters_no_spaces,
        "total_lines": total_lines,
        "non_empty_lines": non_empty_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "comment_density": safe_div(comment_lines, max(code_lines, 1)),
        "average_line_length": safe_div(total_length, total_lines),
        "max_line_length": max_length,
        "estimated_cyclomatic_complexity": complexity,
        "complexity_per_100_lines": complexity_per_100,
        "function_like_blocks": function_like_blocks,
    }
