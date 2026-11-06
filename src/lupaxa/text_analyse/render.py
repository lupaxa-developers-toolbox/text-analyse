"""Format analysis results for the terminal."""

from __future__ import annotations

import json
import sys
from typing import TextIO

from rich import box
from rich.console import Console
from rich.table import Table

from lupaxa.text_analyse.types import CodeAnalysis, FileSummary, TextAnalysis

Group = list[tuple[str, str]]
Report = TextAnalysis | CodeAnalysis


def render(
    result: Report,
    *,
    fmt: str = "table",
    detected: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Write ``result`` as a table, plain text, or JSON."""
    output = stream if stream is not None else sys.stdout
    if fmt == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False), file=output)
        return
    if fmt == "text":
        _render_plain(result, detected=detected, stream=output)
        return
    if fmt != "table":
        raise ValueError("format must be 'table', 'text', or 'json'")
    _render_table(result, detected=detected, stream=output)


def render_files(
    rows: list[FileSummary],
    *,
    fmt: str = "table",
    stream: TextIO | None = None,
) -> None:
    """Write one row per file as a table, plain text, or JSON."""
    output = stream if stream is not None else sys.stdout
    if fmt == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False), file=output)
        return
    if fmt == "text":
        _render_file_plain(rows, stream=output)
        return
    if fmt != "table":
        raise ValueError("format must be 'table', 'text', or 'json'")
    _render_file_table(rows, stream=output)


def _render_file_table(rows: list[FileSummary], *, stream: TextIO) -> None:
    console = Console(file=stream, highlight=False)
    table = Table(
        title="Files",
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        pad_edge=True,
        expand=False,
    )
    table.add_column("File", no_wrap=True)
    table.add_column("Mode", no_wrap=True)
    table.add_column("Size", justify="right", no_wrap=True)
    table.add_column("Flesch", justify="right", no_wrap=True)
    table.add_column("Grade", justify="right", no_wrap=True)
    table.add_column("Check", overflow="fold", max_width=42)
    for row in rows:
        table.add_row(
            row["path"],
            row["mode"],
            row["size"],
            row["flesch"],
            row["grade"],
            row["check"],
        )
    console.print(table)


def _render_file_plain(rows: list[FileSummary], *, stream: TextIO) -> None:
    print("Files", file=stream)
    for row in rows:
        print(
            f"  {row['path']}  {row['mode']}  {row['size']}  "
            f"Flesch {row['flesch']}  grade {row['grade']}  {row['check']}",
            file=stream,
        )


def _render_table(result: Report, *, detected: bool, stream: TextIO) -> None:
    console = Console(file=stream, highlight=False)
    table = Table(
        title=_title(result),
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        pad_edge=True,
        expand=False,
    )
    table.add_column("Metric", no_wrap=True, overflow="ellipsis")
    table.add_column("Value", justify="right", overflow="fold", max_width=42)
    first = True
    for rows in _groups(result, detected=detected):
        if not first:
            table.add_section()
        first = False
        for metric, value in rows:
            table.add_row(metric, value)
    console.print(table)


def _render_plain(result: Report, *, detected: bool, stream: TextIO) -> None:
    print(_title(result), file=stream)
    for rows in _groups(result, detected=detected):
        print(file=stream)
        width = max(len(metric) for metric, _value in rows)
        for metric, value in rows:
            print(f"  {metric:<{width}}  {value}", file=stream)


def _title(result: Report) -> str:
    if result["analysis_mode"] == "code":
        return "Source Code Analysis"
    return "Text Analysis"


def _groups(result: Report, *, detected: bool) -> list[Group]:
    how = "auto" if detected else "forced"
    mode_row: Group = [("Mode", f"{result['analysis_mode']} · {how}")]
    if result["analysis_mode"] == "code":
        return [mode_row, *_code_groups(result)]
    return [mode_row, *_text_groups(result)]


def _text_groups(result: TextAnalysis) -> list[Group]:
    minutes = result["estimated_reading_time_minutes"]
    seconds = result["estimated_reading_time_seconds"]
    if minutes == 0 and seconds == 0:
        reading_time = "Too little text to estimate"
    else:
        reading_time = f"{minutes} min {seconds} sec"
    return [
        [
            ("Characters (with spaces)", _int(result["characters_with_spaces"])),
            ("Characters (no spaces)", _int(result["characters_no_spaces"])),
            ("Words", _int(result["words"])),
            ("Sentences", _int(result["sentences"])),
            ("Paragraphs", _int(result["paragraphs"])),
        ],
        [
            ("Average word length", f"{result['average_word_length']:.2f}"),
            ("Average sentence length", f"{result['average_sentence_length']:.2f}"),
        ],
        [
            ("Unique words", _int(result["unique_words"])),
            ("Type–token ratio", f"{result['type_token_ratio']:.3f}"),
            ("Language", result["language_label"]),
        ],
        [
            ("Syllables (estimated)", _int(result["syllables"])),
            ("Complex words (3+ syllables)", _int(result["complex_words"])),
            ("Flesch Reading Ease", f"{result['flesch_reading_ease']:.2f}"),
            ("Flesch description", result["flesch_reading_ease_description"]),
            ("Flesch–Kincaid grade", f"{result['flesch_kincaid_grade']:.2f}"),
            ("Gunning Fog index", f"{result['gunning_fog_index']:.2f}"),
            ("Reading age (years)", f"{result['estimated_reading_age']:.1f}"),
            (
                f"Reading age band ({result['reading_age_band_scheme'].upper()})",
                result["reading_age_band_label"],
            ),
        ],
        [
            (f"Reading time ({result['reading_words_per_minute']} wpm)", reading_time),
        ],
    ]


def _code_groups(result: CodeAnalysis) -> list[Group]:
    return [
        [
            ("Characters (with spaces)", _int(result["characters_with_spaces"])),
            ("Characters (no spaces)", _int(result["characters_no_spaces"])),
            ("Total lines", _int(result["total_lines"])),
            ("Non-empty lines", _int(result["non_empty_lines"])),
            ("Blank lines", _int(result["blank_lines"])),
            ("Comment lines", _int(result["comment_lines"])),
            ("Code lines", _int(result["code_lines"])),
        ],
        [
            ("Comment density", f"{result['comment_density']:.3f}"),
            ("Average line length", f"{result['average_line_length']:.2f}"),
            ("Max line length", _int(result["max_line_length"])),
            ("Function-like blocks", _int(result["function_like_blocks"])),
        ],
        [
            ("Estimated cyclomatic complexity", _int(result["estimated_cyclomatic_complexity"])),
            ("Complexity per 100 code lines", f"{result['complexity_per_100_lines']:.2f}"),
        ],
    ]


def _int(value: int) -> str:
    return f"{value:,}"
