# agent/incomplete_query_detector.py

import re

from agent.entity_normalizer import normalize_entity


ANALYTICAL_TERMS = {
    "winner",
    "won",
    "runs",
    "run",
    "scorer",
    "scored",
    "wickets",
    "wicket",
    "wins",
    "win",
    "strike rate",
    "economy",
    "average",
    "sixes",
    "six",
    "fours",
    "four",
    "catches",
    "catch",
    "top",
    "best",
    "highest",
    "lowest",
    "most",
    "compare",
    "comparison",
    "performance",
    "statistics",
    "statistic",
    "stats",
    "took",
    "hit",
    "bowled",
    "hosted",
    "total",
    "leading",
    "lead"
}


FOLLOWUP_PREFIXES = (
    "in ",
    "from ",
    "during ",
    "after ",
    "before ",
    "since ",
    "until ",
    "for ",
    "between "
)


STANDALONE_CONCEPTS = {
    "ipl",
    "powerplay",
    "middle overs",
    "death overs",
    "final",
    "playoff",
    "playoffs",
    "venue",
    "match",
    "chasing",
    "toss"
}


def _empty_result():

    return {
        "is_incomplete": False,
        "type": None,
        "value": None
    }


def detect_incomplete_ipl_query(question: str):
    """
    Detect an IPL subject that lacks analytical intent.

    Incomplete:
        Kohli
        CSK
        IPL 2020
        Powerplay
        Final

    Complete:
        Who won IPL 2020?
        IPL 2020 winner
        Top run scorer in IPL 2020
        Best powerplay batter

    Follow-up:
        In 2020?
        From 2020 onward?
        For MI?
    """
    
    if not question or not question.strip():
        return _empty_result()

    original = question.strip()

    cleaned = original.lower()

    cleaned = re.sub(
        r"[^\w\s/]",
        " ",
        cleaned
    )

    cleaned = " ".join(
        cleaned.split()
    )

    if not cleaned:
        return _empty_result()

    # Follow-up fragments must be processed
    # by the follow-up routers.

    if cleaned.startswith(FOLLOWUP_PREFIXES):
        return _empty_result()

    # A metric or analytical action makes
    # the question complete enough to analyze.

    has_analytical_intent = any(
        term in cleaned
        for term in ANALYTICAL_TERMS
    )

    if has_analytical_intent:
        return _empty_result()

    # Entity-only input.

    normalized_entity = normalize_entity(
        original
    )

    if (
        normalized_entity
        and normalized_entity.lower()
        != original.lower()
    ):

        return {
            "is_incomplete": True,
            "type": "entity",
            "value": normalized_entity
            
        }

    # Season-only input.

    season_match = re.search(
        r"\b(?:19|20)\d{2}\b",
        cleaned
    )

    if season_match:

        remaining_text = re.sub(
            r"\bipl\b",
            " ",
            cleaned
        )

        remaining_text = re.sub(
            r"\b(?:19|20)\d{2}\b",
            " ",
            remaining_text
        )

        remaining_text = " ".join(
            remaining_text.split()
        )

        if not remaining_text:

            return {
                "is_incomplete": True,
                "type": "season",
                "value": season_match.group(0)
            }

    # Concept-only input.

    if cleaned in STANDALONE_CONCEPTS:

        return {
            "is_incomplete": True,
            "type": "concept",
            "value": cleaned
        }

    return _empty_result()