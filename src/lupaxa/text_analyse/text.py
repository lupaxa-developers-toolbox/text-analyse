"""Natural-language counts and readability scores."""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from lupaxa.text_analyse.constants import DEFAULT_WPM, ENGLISH_FUNCTION_WORDS
from lupaxa.text_analyse.types import TextAnalysis

WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)
VOWELS_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_ABBREVIATION_RE = re.compile(
    r"\b(?:e\.g|i\.e|U\.S|U\.K|Mr|Mrs|Ms|Dr|Prof|etc|vs)\.",
    re.IGNORECASE,
)
_MIN_LANGUAGE_WORDS = 8
_ENGLISH_FUNCTION_RATIO = 0.12


def character_counts(text: str) -> tuple[int, int]:
    """Return ``(with whitespace, without whitespace)``."""
    return len(text), len(_WHITESPACE_RE.sub("", text))


def tokenise_words(text: str) -> list[str]:
    """Return word tokens."""
    return WORD_RE.findall(text)


def split_sentences(text: str) -> list[str]:
    """Split on ``.``, ``?``, and ``!`` followed by whitespace.

    Abbreviations such as ``e.g.`` and ``U.S.`` stay inside the sentence.
    """
    stripped = text.strip()
    if not stripped:
        return []
    protected = _ABBREVIATION_RE.sub(lambda match: match.group(0).replace(".", "\u0001"), stripped)
    parts = re.split(r"(?<=[.!?])\s+", protected)
    return [part.replace("\u0001", ".").strip() for part in parts if part.strip()]


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines."""
    stripped = text.strip()
    if not stripped:
        return []
    parts = re.split(r"\n\s*\n", stripped)
    return [part.strip() for part in parts if part.strip()]


def count_syllables_in_word(word: str) -> int:
    """Approximate the syllable count of one word."""
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if not cleaned:
        return 0
    syllables = len(VOWELS_RE.findall(cleaned))
    if cleaned.endswith("e") and syllables > 1:
        syllables -= 1
    return max(1, syllables)


def count_syllables(words: list[str]) -> int:
    """Approximate the syllable count of a word list."""
    return sum(count_syllables_in_word(word) for word in words)


def count_complex_words(words: list[str]) -> int:
    """Count words with three or more estimated syllables."""
    return sum(1 for word in words if count_syllables_in_word(word) >= 3)


def safe_div(numerator: float, denominator: float) -> float:
    """Return ``numerator / denominator``, or ``0.0`` when the divisor is zero."""
    return numerator / denominator if denominator else 0.0


def flesch_reading_ease(words: int, sentences: int, syllables: int) -> float:
    """Flesch Reading Ease. Higher means easier."""
    if words == 0 or sentences == 0:
        return 0.0
    return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)


def flesch_kincaid_grade(words: int, sentences: int, syllables: int) -> float:
    """Flesch–Kincaid grade level."""
    if words == 0 or sentences == 0:
        return 0.0
    return 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59


def gunning_fog_index(words: int, sentences: int, complex_words: int) -> float:
    """Gunning Fog index."""
    if words == 0 or sentences == 0:
        return 0.0
    return 0.4 * ((words / sentences) + 100 * (complex_words / words))


def estimate_reading_age_from_grade(grade: float) -> float:
    """Map a grade level to a rough reading age (grade + 5)."""
    return grade + 5


def detect_language(words: list[str]) -> tuple[Literal["english", "other", "unknown"], str]:
    """Return ``(code, label)`` for whether readability scores apply.

    ``english`` when enough closed-class English words are present.
    ``other`` when they are not. ``unknown`` when the sample is too short.
    """
    if len(words) < _MIN_LANGUAGE_WORDS:
        return "unknown", "Too little text to judge"
    lowered = [word.lower() for word in words]
    hits = sum(1 for word in lowered if word in ENGLISH_FUNCTION_WORDS)
    if hits / len(lowered) >= _ENGLISH_FUNCTION_RATIO:
        return "english", "English"
    return "other", "Not English — scores are a rough guide"


def estimate_reading_time(words: int, wpm: int = DEFAULT_WPM) -> tuple[int, int]:
    """Return ``(minutes, seconds)`` at the given words per minute."""
    if words == 0 or wpm <= 0:
        return 0, 0
    total_seconds = int(round(words / (wpm / 60)))
    minutes, seconds = divmod(total_seconds, 60)
    return minutes, seconds


def describe_flesch_score(score: float) -> str:
    """Short label for a Flesch Reading Ease score."""
    if score >= 90:
        return "Very easy (e.g. comics, simple text)"
    if score >= 80:
        return "Easy"
    if score >= 70:
        return "Fairly easy"
    if score >= 60:
        return "Standard / plain English"
    if score >= 50:
        return "Fairly difficult"
    if score >= 30:
        return "Difficult"
    return "Very confusing / academic"


def reading_age_band(age: float, scheme: str = "uk") -> str:
    """Map a numeric reading age to a UK or US band."""
    if scheme.lower() == "us":
        if age < 6:
            return "Pre-school / Kindergarten"
        if age < 8:
            return "Early elementary (Grades 1–2)"
        if age < 11:
            return "Upper elementary (Grades 3–5)"
        if age < 14:
            return "Middle school (Grades 6–8)"
        if age < 18:
            return "High school (Grades 9–12)"
        if age < 22:
            return "College / Undergraduate"
        return "Adult / Professional"
    if age < 7:
        return "Key Stage 1 (Infant)"
    if age < 11:
        return "Key Stage 2 (Primary)"
    if age < 14:
        return "Key Stage 3 (Lower secondary)"
    if age < 16:
        return "GCSE (Upper secondary)"
    if age < 18:
        return "A-level / College"
    return "Adult / Professional / Academic"


def analyse_text(
    text: str,
    *,
    reading_age_scheme: str = "uk",
    wpm: int = DEFAULT_WPM,
) -> TextAnalysis:
    """Analyse natural-language text.

    Readability labels are part of the result. ``reading_age_scheme`` is
    ``uk`` or ``us``. ``wpm`` is the reading speed used for the time estimate.
    """
    if wpm < 1:
        raise ValueError("wpm must be at least 1")
    scheme = reading_age_scheme.lower()
    if scheme not in {"uk", "us"}:
        raise ValueError("reading_age_scheme must be 'uk' or 'us'")

    characters_with_spaces, characters_no_spaces = character_counts(text)
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    words_all = tokenise_words(text)

    num_paragraphs = len(paragraphs)
    num_sentences = len(sentences)
    num_words = len(words_all)

    syllables = count_syllables(words_all)
    complex_words = count_complex_words(words_all)
    flesch = flesch_reading_ease(num_words, num_sentences, syllables)
    grade = flesch_kincaid_grade(num_words, num_sentences, syllables)
    age = estimate_reading_age_from_grade(grade)
    minutes, seconds = estimate_reading_time(num_words, wpm)
    language, language_label = detect_language(words_all)
    unique_words = len(Counter(word.lower() for word in words_all))

    return {
        "analysis_mode": "text",
        "characters_with_spaces": characters_with_spaces,
        "characters_no_spaces": characters_no_spaces,
        "paragraphs": num_paragraphs,
        "sentences": num_sentences,
        "words": num_words,
        "average_word_length": safe_div(characters_no_spaces, num_words),
        "average_sentence_length": safe_div(num_words, num_sentences),
        "syllables": syllables,
        "complex_words": complex_words,
        "flesch_reading_ease": flesch,
        "flesch_kincaid_grade": grade,
        "gunning_fog_index": gunning_fog_index(num_words, num_sentences, complex_words),
        "flesch_reading_ease_description": describe_flesch_score(flesch),
        "estimated_reading_age": age,
        "reading_age_band_scheme": scheme,
        "reading_age_band_label": reading_age_band(age, scheme),
        "estimated_reading_time_minutes": minutes,
        "estimated_reading_time_seconds": seconds,
        "reading_words_per_minute": wpm,
        "unique_words": unique_words,
        "type_token_ratio": safe_div(unique_words, num_words),
        "language": language,
        "language_label": language_label,
    }
