"""Choose text or code analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, overload

from lupaxa.text_analyse.code import analyse_code
from lupaxa.text_analyse.constants import DEFAULT_WPM, MARKDOWN_SUFFIXES, PROSE_SUFFIXES
from lupaxa.text_analyse.detect import looks_like_code
from lupaxa.text_analyse.markdown import strip_markdown
from lupaxa.text_analyse.text import analyse_text
from lupaxa.text_analyse.types import CodeAnalysis, TextAnalysis

Mode = Literal["auto", "text", "code"]


@overload
def analyse(
    text: str,
    *,
    mode: Literal["text"],
    source: str | None = None,
    reading_age_scheme: str = ...,
    wpm: int = ...,
) -> TextAnalysis:
    pass


@overload
def analyse(
    text: str,
    *,
    mode: Literal["code"],
    source: str | None = None,
    reading_age_scheme: str = ...,
    wpm: int = ...,
) -> CodeAnalysis:
    pass


@overload
def analyse(
    text: str,
    *,
    mode: Literal["auto"] = ...,
    source: str | None = None,
    reading_age_scheme: str = ...,
    wpm: int = ...,
) -> TextAnalysis | CodeAnalysis:
    pass


def analyse(
    text: str,
    *,
    mode: Mode = "auto",
    source: str | None = None,
    reading_age_scheme: str = "uk",
    wpm: int = DEFAULT_WPM,
) -> TextAnalysis | CodeAnalysis:
    """Analyse ``text`` as prose, as code, or by guessing from the contents.

    ``source`` is a file name or path. Its suffix selects text mode for
    documentation, and Markdown files are scored after markup is removed.
    """
    if mode not in {"auto", "text", "code"}:
        raise ValueError("mode must be 'auto', 'text', or 'code'")
    if wpm < 1:
        raise ValueError("wpm must be at least 1")
    resolved = _resolve_mode(text, mode, source)
    if resolved == "code":
        return analyse_code(text)
    body = strip_markdown(text) if _suffix(source) in MARKDOWN_SUFFIXES else text
    return analyse_text(body, reading_age_scheme=reading_age_scheme, wpm=wpm)


def _resolve_mode(text: str, mode: Mode, source: str | None) -> Literal["text", "code"]:
    if mode == "code":
        return "code"
    if mode == "text":
        return "text"
    if _suffix(source) in PROSE_SUFFIXES:
        return "text"
    if looks_like_code(text):
        return "code"
    return "text"


def _suffix(source: str | None) -> str:
    if not source:
        return ""
    return Path(source).suffix.lower()
