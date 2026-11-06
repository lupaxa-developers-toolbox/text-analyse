"""lupaxa.text_analyse — readability scores and rough code metrics.

``analyse(text)`` picks prose or code. ``analyse_text`` and ``analyse_code``
force a mode. ``fetch_text`` downloads a URL and extracts readable text.
"""

from __future__ import annotations

from lupaxa.text_analyse.code import analyse_code
from lupaxa.text_analyse.core import analyse
from lupaxa.text_analyse.detect import looks_like_code
from lupaxa.text_analyse.exceptions import FetchError, TextAnalyseError
from lupaxa.text_analyse.fetch import fetch_text
from lupaxa.text_analyse.text import analyse_text, describe_flesch_score, reading_age_band
from lupaxa.text_analyse.version import __version__, get_version

__all__ = [
    "FetchError",
    "TextAnalyseError",
    "__version__",
    "analyse",
    "analyse_code",
    "analyse_text",
    "describe_flesch_score",
    "fetch_text",
    "get_version",
    "looks_like_code",
    "reading_age_band",
]
