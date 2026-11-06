"""Result shapes returned by the analysis functions."""

from __future__ import annotations

from typing import Literal, TypedDict


class TextAnalysis(TypedDict):
    """Readability and count metrics for natural-language text."""

    analysis_mode: Literal["text"]
    characters_with_spaces: int
    characters_no_spaces: int
    paragraphs: int
    sentences: int
    words: int
    average_word_length: float
    average_sentence_length: float
    syllables: int
    complex_words: int
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog_index: float
    flesch_reading_ease_description: str
    estimated_reading_age: float
    reading_age_band_scheme: str
    reading_age_band_label: str
    estimated_reading_time_minutes: int
    estimated_reading_time_seconds: int
    reading_words_per_minute: int
    unique_words: int
    type_token_ratio: float
    language: Literal["english", "other", "unknown"]
    language_label: str


class FileSummary(TypedDict):
    """One row when several files are analysed together."""

    path: str
    mode: str
    size: str
    flesch: str
    grade: str
    check: str


class CodeAnalysis(TypedDict):
    """Rough, language-agnostic metrics for source-like input."""

    analysis_mode: Literal["code"]
    characters_with_spaces: int
    characters_no_spaces: int
    total_lines: int
    non_empty_lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    comment_density: float
    average_line_length: float
    max_line_length: int
    estimated_cyclomatic_complexity: int
    complexity_per_100_lines: float
    function_like_blocks: int
