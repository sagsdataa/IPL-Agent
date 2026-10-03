"""
Entity Resolver

Detect entity-aware follow-up questions.

Examples:

Why not Bumrah?
What about Dhoni?
How does Rohit compare?
Compare with Kohli.
"""

import re


def detect_entity_followup(
    question: str
):
    """
    Detect whether a follow-up introduces
    a new entity.

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

        if match:

            entity = (
                match.group(1)
                .strip()
                .title()
            )

            return {
                "is_entity_followup": True,
                "entity": entity,
                "intent": "entity_followup"
            }

    return {
        "is_entity_followup": False,
        "entity": None,
        "intent": None
    }