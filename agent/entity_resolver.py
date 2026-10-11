from agent.entity_normalizer import normalize_entity

"""
Entity Resolver

Detect entity-aware follow-up questions.
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
    "finals",
}


def detect_entity_followup(
    question: str
):
    """
    Detect whether a follow-up introduces
    a new entity.

    Examples:
        Why not Bumrah?
        What about Dhoni?
        How about Rohit Sharma?
        Compare with Kohli?
    """

    if not question:

        return {
            "is_entity_followup": False,
            "entity": None,
            "intent": None,
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

        r"vs (.+)",
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

        #
        # Reject years
        #
        if re.fullmatch(
            r"20\d{2}",
            entity
        ):

            return {
                "is_entity_followup": False,
                "entity": None,
                "intent": None,
            }

        #
        # Reject generic cricket concepts
        #
        if entity in COMMON_CRICKET_TERMS:

            return {
                "is_entity_followup": False,
                "entity": None,
                "intent": None,
            }

        #
        # Normalize entity
        #
        normalized_entity = (
            normalize_entity(
                entity
            )
        )

        return {
            "is_entity_followup": True,
            "entity": normalized_entity,
            "intent": "entity_followup",
        }

    return {
        "is_entity_followup": False,
        "entity": None,
        "intent": None,
    }