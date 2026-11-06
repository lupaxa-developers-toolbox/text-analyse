"""Tests for prose metrics."""

from __future__ import annotations

import pytest

from lupaxa.text_analyse import analyse_text
from lupaxa.text_analyse.text import count_syllables_in_word, split_sentences

PASSAGE = "The cat sat on the mat."


def test_known_passage_scores() -> None:
    result = analyse_text(PASSAGE)
    assert result["analysis_mode"] == "text"
    assert result["words"] == 6
    assert result["sentences"] == 1
    assert result["paragraphs"] == 1
    assert result["syllables"] == 6
    assert result["complex_words"] == 0
    assert result["characters_with_spaces"] == len(PASSAGE)
    assert result["flesch_reading_ease"] == pytest.approx(116.145)
    assert result["flesch_kincaid_grade"] == pytest.approx(-1.45)
    assert result["gunning_fog_index"] == pytest.approx(2.4)
    assert result["estimated_reading_age"] == pytest.approx(3.55)
    assert result["reading_age_band_scheme"] == "uk"
    assert result["reading_age_band_label"] == "Key Stage 1 (Infant)"
    assert result["flesch_reading_ease_description"].startswith("Very easy")
    assert result["estimated_reading_time_minutes"] == 0
    assert result["estimated_reading_time_seconds"] == 2
    assert result["unique_words"] == 5
    assert result["type_token_ratio"] == pytest.approx(5 / 6)
    assert result["reading_words_per_minute"] == 200
    assert result["language"] == "unknown"
    assert "most_common_words" not in result


def test_us_reading_age_band() -> None:
    result = analyse_text(PASSAGE, reading_age_scheme="US")
    assert result["reading_age_band_scheme"] == "us"
    assert result["reading_age_band_label"] == "Pre-school / Kindergarten"


def test_syllable_heuristics() -> None:
    assert count_syllables_in_word("the") == 1
    assert count_syllables_in_word("make") == 1
    assert count_syllables_in_word("beautiful") == 3
    assert count_syllables_in_word("") == 0


def test_complex_word_and_paragraphs() -> None:
    result = analyse_text("A beautiful day.\n\nIt ended.")
    assert result["paragraphs"] == 2
    assert result["sentences"] == 2
    assert result["complex_words"] == 1


def test_abbreviations_stay_inside_the_sentence() -> None:
    sentences = split_sentences("We use e.g. cats and U.S. English. Done!")
    assert sentences == ["We use e.g. cats and U.S. English.", "Done!"]


def test_language_judgement() -> None:
    english = (
        "The project is a community of independent developers and contributors "
        "building useful software for people who value clean tools."
    )
    other = (
        "Le projet est une communaute de developpeurs qui construit des outils "
        "utiles pour tout le monde chaque jour vraiment sans pause."
    )
    assert analyse_text(english)["language_label"] == "English"
    assert analyse_text(other)["language"] == "other"
    assert "rough guide" in analyse_text(other)["language_label"]


def test_custom_reading_speed() -> None:
    result = analyse_text(PASSAGE, wpm=100)
    assert result["reading_words_per_minute"] == 100
    assert result["estimated_reading_time_seconds"] == 4


def test_tabs_are_not_counted_as_characters() -> None:
    result = analyse_text("a\tb")
    assert result["characters_with_spaces"] == 3
    assert result["characters_no_spaces"] == 2


def test_empty_text_is_zeroed() -> None:
    result = analyse_text("   ")
    assert result["words"] == 0
    assert result["flesch_reading_ease"] == 0.0
    assert result["language"] == "unknown"


def test_rejects_bad_scheme_and_wpm() -> None:
    with pytest.raises(ValueError, match="reading_age_scheme"):
        analyse_text("Hello.", reading_age_scheme="fr")
    with pytest.raises(ValueError, match="wpm"):
        analyse_text("Hello.", wpm=0)
