"""
Time Follow-Up Resolver

Detects when the user applies a time or season
filter to the previous analytical question.
"""

import re


FOLLOWUP_PATTERNS = [
    "what about",
    "how about",
    "what if",
    "instead",
    "only",
]


def detect_time_followup(
    question: str
):
    """
    Detect a time-aware follow-up.

    Examples:
        What about 2024?
        How about 2019?
        What about last 5 seasons?
        What about playoffs?
    """

    if not question:

        return {
            "is_time_followup": False,
            "time_type": None,
            "time_value": None,
        }

    normalized_question = (
        question
        .strip()
        .lower()
        .replace("?", "")
        .replace(".", "")
        .replace("!", "")
        .replace(",", "")
    )

    has_followup_pattern = any(
        pattern in normalized_question
        for pattern in FOLLOWUP_PATTERNS
    )

    if not has_followup_pattern:

        return {
            "is_time_followup": False,
            "time_type": None,
            "time_value": None,
        }

    year_match = re.search(
        r"\b(20(?:0[8-9]|1[0-9]|2[0-9]))\b",
        normalized_question,
    )

    if year_match:

        return {
            "is_time_followup": True,
            "time_type": "season",
            "time_value": year_match.group(1),
        }

    last_seasons_match = re.search(
        r"\blast\s+(\d+)\s+seasons?\b",
        normalized_question,
    )

    if last_seasons_match:

        return {
            "is_time_followup": True,
            "time_type": "last_n_seasons",
            "time_value": int(
                last_seasons_match.group(1)
            ),
        }

    if "playoff" in normalized_question:

        return {
            "is_time_followup": True,
            "time_type": "playoffs",
            "time_value": "playoffs",
        }

    return {
        "is_time_followup": False,
        "time_type": None,
        "time_value": None,
    }