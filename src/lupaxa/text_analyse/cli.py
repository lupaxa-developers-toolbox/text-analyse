"""Command-line interface for lupaxa.text_analyse."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import cast

from lupaxa.text_analyse import __version__, analyse
from lupaxa.text_analyse.constants import DOC_SUFFIXES
from lupaxa.text_analyse.core import Mode
from lupaxa.text_analyse.exceptions import FetchError
from lupaxa.text_analyse.fetch import fetch
from lupaxa.text_analyse.render import render, render_files
from lupaxa.text_analyse.types import CodeAnalysis, FileSummary, TextAnalysis

_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
    }
)


def build_parser() -> argparse.ArgumentParser:
    """Return the ``text-analyse`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="text-analyse",
        description="Analyse text or code: counts, readability, and rough complexity.",
    )
    parser.add_argument(
        "path",
        nargs="*",
        help=(
            "Files or documentation directories to analyse. "
            "Reads stdin when no path, --file, or --url is given."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path to an input file.",
    )
    parser.add_argument(
        "-u",
        "--url",
        help="URL to fetch and analyse. HTML pages are read as the article.",
    )
    parser.add_argument(
        "--wpm",
        type=_at_least_one,
        default=200,
        help="Reading speed used for the time estimate (default: 200).",
    )
    parser.add_argument(
        "--min-flesch",
        type=float,
        default=None,
        help="Exit 1 when the Flesch Reading Ease score is below this value.",
    )
    parser.add_argument(
        "--max-grade",
        type=float,
        default=None,
        help="Exit 1 when the Flesch–Kincaid grade is above this value.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print only files that fail --min-flesch or --max-grade.",
    )
    parser.add_argument(
        "-F",
        "--format",
        choices=["table", "text", "json"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["auto", "text", "code"],
        default="auto",
        help="Analysis mode (default: auto).",
    )
    parser.add_argument(
        "-R",
        "--reading-age-scheme",
        choices=["uk", "us"],
        default="uk",
        help="Reading-age band scheme for text mode (default: uk).",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"text-analyse {__version__}")
        return 0

    if args.check and args.min_flesch is None and args.max_grade is None:
        print("error: --check needs --min-flesch or --max-grade.", file=sys.stderr)
        return 2

    if args.url and (args.path or args.file):
        print("Please specify only one of a path, --file, or --url.", file=sys.stderr)
        return 1
    if args.file and args.path:
        print("Please specify only one of a path, --file, or --url.", file=sys.stderr)
        return 1

    if args.url:
        return _run_url(args)

    inputs = [*args.path, *([args.file] if args.file else [])]
    if not inputs:
        text = sys.stdin.read()
        if not text.strip():
            print("No text provided.", file=sys.stderr)
            return 1
        return _emit(
            text,
            args,
            mode=cast(Mode, args.mode),
            source=None,
            label="(stdin)",
            summary=args.check,
        )

    try:
        files, walked = _collect_files(inputs)
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1
    if not files:
        print("No files to analyse.", file=sys.stderr)
        return 1

    summary = args.check or walked or len(files) > 1
    if not summary:
        path, label = files[0]
        return _emit_path(path, args, label=label, summary=False)
    return _emit_many(files, args)


def _run_url(args: argparse.Namespace) -> int:
    try:
        page = fetch(args.url)
    except FetchError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not page.text.strip():
        print("No text provided.", file=sys.stderr)
        return 1
    mode = cast(Mode, "text" if args.mode == "auto" and page.is_html else args.mode)
    return _emit(page.text, args, mode=mode, source=None, label=args.url, summary=args.check)


def _emit_path(path: Path, args: argparse.Namespace, *, label: str, summary: bool) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1
    if not text.strip():
        print("No text provided.", file=sys.stderr)
        return 1
    return _emit(
        text,
        args,
        mode=cast(Mode, args.mode),
        source=str(path),
        label=label,
        summary=summary,
    )


def _emit(
    text: str,
    args: argparse.Namespace,
    *,
    mode: Mode,
    source: str | None,
    label: str,
    summary: bool,
) -> int:
    result = analyse(
        text,
        mode=mode,
        source=source,
        reading_age_scheme=args.reading_age_scheme,
        wpm=args.wpm,
    )
    if not summary:
        render(result, fmt=args.format, detected=args.mode == "auto")
        return _readability_status(result, min_flesch=args.min_flesch, max_grade=args.max_grade)

    status, code = _check_status(result, min_flesch=args.min_flesch, max_grade=args.max_grade)
    if code == 1 or not args.check:
        row = _summary_row(label, result, status, detected=args.mode == "auto")
        render_files([row], fmt=args.format)
    if code == 2:
        print("error: --min-flesch and --max-grade apply to text only.", file=sys.stderr)
    return code


def _emit_many(files: list[tuple[Path, str]], args: argparse.Namespace) -> int:
    rows: list[FileSummary] = []
    saw_text = False
    saw_code = False
    failed = False
    checks = args.min_flesch is not None or args.max_grade is not None
    for path, label in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            rows.append(_plain_row(label, "—", "—", f"Error reading file: {exc}"))
            failed = True
            continue
        if not text.strip():
            rows.append(_plain_row(label, "—", "—", "No text provided."))
            failed = True
            continue
        result = analyse(
            text,
            mode=cast(Mode, args.mode),
            source=str(path),
            reading_age_scheme=args.reading_age_scheme,
            wpm=args.wpm,
        )
        status, code = _check_status(result, min_flesch=args.min_flesch, max_grade=args.max_grade)
        if result["analysis_mode"] == "text":
            saw_text = True
        else:
            saw_code = True
        if code == 1:
            failed = True
        rows.append(_summary_row(label, result, status, detected=args.mode == "auto"))

    visible = [row for row in rows if row["check"] not in {"ok", "—"}] if args.check else rows
    if visible:
        render_files(visible, fmt=args.format)
    if failed:
        return 1
    if checks and saw_code and not saw_text:
        print("error: --min-flesch and --max-grade apply to text only.", file=sys.stderr)
        return 2
    return 0


def _collect_files(inputs: list[str]) -> tuple[list[tuple[Path, str]], bool]:
    files: list[tuple[Path, str]] = []
    walked = False
    for item in inputs:
        path = Path(item)
        if not path.exists():
            raise FileNotFoundError(2, "No such file or directory", item)
        if path.is_dir():
            walked = True
            files.extend((found, found.relative_to(path).as_posix()) for found in _iter_docs(path))
        else:
            files.append((path, _display_path(path)))
    return files, walked


def _iter_docs(root: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in _SKIP_DIRS and not name.startswith(".")
        )
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            path = Path(dirpath) / name
            if path.suffix.lower() in DOC_SUFFIXES:
                found.append(path)
    return found


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def _summary_row(
    label: str,
    result: TextAnalysis | CodeAnalysis,
    status: str,
    *,
    detected: bool,
) -> FileSummary:
    how = "auto" if detected else "forced"
    if result["analysis_mode"] == "text":
        return {
            "path": label,
            "mode": f"text · {how}",
            "size": f"{result['words']:,} words",
            "flesch": f"{result['flesch_reading_ease']:.2f}",
            "grade": f"{result['flesch_kincaid_grade']:.2f}",
            "check": status,
        }
    return {
        "path": label,
        "mode": f"code · {how}",
        "size": f"{result['code_lines']:,} lines",
        "flesch": "—",
        "grade": "—",
        "check": status,
    }


def _plain_row(label: str, mode: str, size: str, check: str) -> FileSummary:
    return {"path": label, "mode": mode, "size": size, "flesch": "—", "grade": "—", "check": check}


def _check_status(
    result: TextAnalysis | CodeAnalysis,
    *,
    min_flesch: float | None,
    max_grade: float | None,
) -> tuple[str, int]:
    if min_flesch is None and max_grade is None:
        return "ok", 0
    if result["analysis_mode"] != "text":
        return "—", 2
    failures: list[str] = []
    score = result["flesch_reading_ease"]
    grade = result["flesch_kincaid_grade"]
    if min_flesch is not None and score < min_flesch:
        failures.append(f"Flesch Reading Ease {score:.2f} is below {min_flesch:g}")
    if max_grade is not None and grade > max_grade:
        failures.append(f"Flesch–Kincaid grade {grade:.2f} is above {max_grade:g}")
    if failures:
        return "; ".join(failures), 1
    return "ok", 0


def _readability_status(
    result: TextAnalysis | CodeAnalysis,
    *,
    min_flesch: float | None,
    max_grade: float | None,
) -> int:
    if min_flesch is None and max_grade is None:
        return 0
    if result["analysis_mode"] != "text":
        print("error: --min-flesch and --max-grade apply to text only.", file=sys.stderr)
        return 2
    failed = False
    score = result["flesch_reading_ease"]
    grade = result["flesch_kincaid_grade"]
    if min_flesch is not None and score < min_flesch:
        print(f"Flesch Reading Ease {score:.2f} is below {min_flesch:g}.", file=sys.stderr)
        failed = True
    if max_grade is not None and grade > max_grade:
        print(f"Flesch–Kincaid grade {grade:.2f} is above {max_grade:g}.", file=sys.stderr)
        failed = True
    return 1 if failed else 0


def _at_least_one(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number
