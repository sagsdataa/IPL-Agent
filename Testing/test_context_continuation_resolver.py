# tests/test_context_continuation_resolver.py
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

# tests/test_context_continuation_resolver.py

from agent.context_continuation_resolver import (
    detect_context_continuation
)


# --------------------------------------------------
# High-confidence fragments
# --------------------------------------------------

def test_in_2019():

    result = detect_context_continuation(
        "In 2019?"
    )

    assert result["is_context_continuation"] is True
    assert result["confidence"] >= 0.60


def test_for_srh():

    result = detect_context_continuation(
        "For SRH?"
    )

    assert result["is_context_continuation"] is True
    assert result["confidence"] >= 0.60


def test_at_wankhede():

    result = detect_context_continuation(
        "At Wankhede?"
    )

    assert result["is_context_continuation"] is True
    assert result["confidence"] >= 0.60


def test_season_2019():

    result = detect_context_continuation(
        "Season 2019?"
    )

    assert result["is_context_continuation"] is True
    assert result["confidence"] >= 0.60


def test_only_playoffs():

    result = detect_context_continuation(
        "Only playoffs?"
    )

    assert result["is_context_continuation"] is True
    assert result["confidence"] >= 0.60


# --------------------------------------------------
# Continuation chaining examples
# --------------------------------------------------

def test_for_mumbai_indians():

    result = detect_context_continuation(
        "For Mumbai Indians?"
    )

    assert result["is_context_continuation"] is True


def test_against_csk():

    result = detect_context_continuation(
        "Against CSK?"
    )

    assert result["is_context_continuation"] is True


def test_during_powerplay():

    result = detect_context_continuation(
        "During powerplay?"
    )

    assert result["is_context_continuation"] is True


# --------------------------------------------------
# Standalone analytical questions
# --------------------------------------------------

def test_who_scored_most_runs():

    result = detect_context_continuation(
        "Who scored the most runs?"
    )

    assert result["is_context_continuation"] is False


def test_who_took_most_wickets():

    result = detect_context_continuation(
        "Who took the most wickets?"
    )

    assert result["is_context_continuation"] is False


def test_best_batter_in_2019():

    result = detect_context_continuation(
        "Who was the best batter in 2019?"
    )

    assert result["is_context_continuation"] is False


# --------------------------------------------------
# Metric follow-ups should not become
# context continuations
# --------------------------------------------------

def test_strike_rate_metric():

    result = detect_context_continuation(
        "What about strike rate?"
    )

    assert result["is_context_continuation"] is False


# --------------------------------------------------
# Entity follow-ups should not become
# context continuations
# --------------------------------------------------

def test_why_not_dhoni():

    result = detect_context_continuation(
        "Why not Dhoni?"
    )

    assert result["is_context_continuation"] is False


def test_what_about_rohit():

    result = detect_context_continuation(
        "What about Rohit Sharma?"
    )

    assert result["is_context_continuation"] is False


# --------------------------------------------------
# Edge cases
# --------------------------------------------------

def test_empty_string():

    result = detect_context_continuation("")

    assert result["is_context_continuation"] is False
    assert result["confidence"] == 0.0


def test_none_like_text():

    result = detect_context_continuation(
        "?"
    )

    assert isinstance(
        result["is_context_continuation"],
        bool
    )


def test_confidence_range():

    result = detect_context_continuation(
        "For SRH?"
    )

    assert (
        0.0
        <= result["confidence"]
        <= 1.0
    )