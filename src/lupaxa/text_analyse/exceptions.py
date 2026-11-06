"""Errors raised by lupaxa.text_analyse."""

from __future__ import annotations


class TextAnalyseError(Exception):
    """Base error for the text_analyse package."""


class FetchError(TextAnalyseError):
    """Raised when a URL cannot be fetched or the body is too large."""
