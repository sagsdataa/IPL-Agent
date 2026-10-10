# agent/context_continuation_resolver.py
"""
Fragment Detector

Goal:
Determine whether the user's message
is likely an incomplete continuation
of the previous analytical question.
"""

import re


QUESTION_WORDS = {
    "who",
    "what",
    "which",
    "when",
    "where",
    "why",
    "how"
}


CONTINUATION_STARTERS = {
    "in",
    "for",
    "at",
    "during",
    "season",
    "only",
    "against",
    "with"
}


STANDALONE_ANALYTICAL_WORDS = {
    "scored",
    "score",
    "runs",
    "wickets",
    "won",
    "win",
    "took",
    "take",
    "highest",
    "lowest",
    "best",
    "most",
    "player",
    "venue"
}


def detect_context_continuation(
    question: str
):
    """
    Returns:

    {
        "is_context_continuation": bool,
        "confidence": float,
        "fragment": str,
        "reasons": []
    }
    """

    if not question:

        return {
            "is_context_continuation": False,
            "confidence": 0.0,
            "fragment": None,
            "reasons": []
        }

    normalized = (
        question
        .strip()
        .lower()
        .replace("?", "")
    )

    words = normalized.split()

    score = 0.0
    reasons = []

    # ----------------------------------
    # Very short messages
    # ----------------------------------

    if len(words) <= 4:

        score += 0.30
        reasons.append(
            "short_fragment"
        )

    # ----------------------------------
    # Starts like a continuation
    # ----------------------------------

    if (
        words
        and words[0]
        in CONTINUATION_STARTERS
    ):

        score += 0.25
        reasons.append(
            "continuation_starter"
        )

    # ----------------------------------
    # Contains a year
    # ----------------------------------

    if re.search(
        r"20\d{2}",
        normalized
    ):

        score += 0.20
        reasons.append(
            "contains_year"
        )

    # ----------------------------------
    # Does not look like a question
    # ----------------------------------

    if (
        words
        and words[0]
        not in QUESTION_WORDS
    ):

        score += 0.10
        reasons.append(
            "not_question_style"
        )

    # ----------------------------------
    # Lacks analytical structure
    # ----------------------------------

    analytical_terms_found = any(
        word in STANDALONE_ANALYTICAL_WORDS
        for word in words
    )

    if not analytical_terms_found:

        score += 0.15
        reasons.append(
            "not_standalone"
        )

    confidence = min(
        score,
        1.0
    )

    return {
        "is_context_continuation":
            confidence >= 0.60,

        "confidence":
            round(confidence, 2),

        "fragment":
            question,

        "reasons":
            reasons
    }