"""
Entity Resolver

Detect entity-aware follow-up questions.

Examples:

Why not Bumrah?
What about Dhoni?
How about Rohit Sharma?
Compare with Kohli.

Reject:

What about 2020?
What about bowler?
What about team?
What about season?
"""

import re


COMMON_CRICKET_TERMS = {
    "bowler",
    "bowlers",
    "batter",
    "batters",
    "batsman",
    "batsmen",
    "player",
    "players",
    "captain",
    "captains",
    "team",
    "teams",
    "venue",
    "venues",
    "stadium",
    "ground",
    "season",
    "seasons",
    "match",
    "matches",
    "playoff",
    "playoffs",
    "final",
    "finals"
}


def detect_entity_followup(
    question: str
):
    """
    Detect whether a follow-up introduces
    a new player entity.

    Returns:

    {
        "is_entity_followup": bool,
        "entity": str | None,
        "intent": str | None
    }
    """

    if not question:

        return {
            "is_entity_followup": False,
            "entity": None,
            "intent": None
        }

    question_clean = (
        question.strip()
        .replace("?", "")
    )

    question_lower = (
        question_clean.lower()
    )

    patterns = [

        r"why not (.+)",
        r"what about (.+)",
        r"how about (.+)",
        r"compare with (.+)",
        r"versus (.+)",
        r"vs (.+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question_lower
        )

        if not match:
            continue

        entity = (
            match.group(1)
            .strip()
        )

        # ---------------------------------
        # Reject years
        # ---------------------------------

        if re.fullmatch(
            r"20\d{2}",
            entity
        ):

            return {
                "is_entity_followup": False,
                "entity": None,
                "intent": None
            }

        # ---------------------------------
        # Reject generic cricket concepts
        # ---------------------------------

        if entity in COMMON_CRICKET_TERMS:

            return {
                "is_entity_followup": False,
                "entity": None,
                "intent": None
            }

        # ---------------------------------
        # Valid entity
        # ---------------------------------

        return {
            "is_entity_followup": True,
            "entity": entity.title(),
            "intent": "entity_followup"
        }

    return {
        "is_entity_followup": False,
        "entity": None,
        "intent": None
    }