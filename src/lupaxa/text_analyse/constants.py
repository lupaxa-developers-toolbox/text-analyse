"""Shared defaults for text and code analysis."""

from __future__ import annotations

DEFAULT_WPM = 200
DEFAULT_TIMEOUT = 10.0
MAX_BODY_BYTES = 2_000_000

CODE_SYMBOLS = "{}[]();#<>="
COMMENT_PREFIXES = ("#", "//", "/*", "*", "--")

MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
PROSE_SUFFIXES = MARKDOWN_SUFFIXES | frozenset({".rst", ".adoc", ".asciidoc"})
DOC_SUFFIXES = PROSE_SUFFIXES | frozenset({".txt"})

# Closed-class English words. Used only to judge whether readability
# scores are being applied to English prose.
ENGLISH_FUNCTION_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "as",
        "by",
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "this",
        "that",
        "these",
        "those",
        "he",
        "she",
        "they",
        "we",
        "you",
        "i",
        "me",
        "him",
        "her",
        "them",
        "us",
        "my",
        "your",
        "their",
        "our",
        "from",
        "up",
        "down",
        "out",
        "about",
        "into",
        "over",
        "after",
        "not",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "can",
        "could",
    }
)
