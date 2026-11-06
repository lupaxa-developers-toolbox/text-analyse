"""Guess whether a string looks more like source than prose."""

from __future__ import annotations

import re

from lupaxa.text_analyse.constants import CODE_SYMBOLS

_KEYWORD_RE = re.compile(
    r"\b(if|else|for|while|switch|case|def|class|return|import|from|public|private|"
    r"protected|function|var|let|const|=>|try|catch|finally)\b"
)


def looks_like_code(text: str) -> bool:
    """Return true when the sample contains real code punctuation.

    A code-symbol ratio above 0.03 is enough. Keywords such as ``for``,
    ``from``, and ``if`` are ordinary English, so they count only when
    code symbols are also present (at least five keywords and a symbol
    ratio above 0.01).
    """
    if not text:
        return False
    symbol_count = sum(text.count(character) for character in CODE_SYMBOLS)
    symbol_ratio = symbol_count / len(text)
    if symbol_ratio > 0.03:
        return True
    if symbol_count == 0:
        return False
    keyword_matches = len(_KEYWORD_RE.findall(text))
    return keyword_matches >= 5 and symbol_ratio > 0.01
