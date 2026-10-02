"""
Hallucination Checker V1

Purpose:
Detect unsupported cricket entities in
generated answers.

V1 validates entities only.

Future V2:
- Entity validation
- Number validation
- Metric validation
"""

import re


IGNORE_WORDS = {
    "ipl",
    "player",
    "players",
    "bowler",
    "bowlers",
    "batter",
    "batters",
    "team",
    "teams",
    "runs",
    "wickets",
    "average",
    "strike",
    "rate",
    "season",
    "performance",
    "best",
    "top",
    "highest",
    "lowest",
    "leads",
    "lead",
    "with",
    "based",
    "according",
    "all",
    "the",
}


def extract_evidence(context):
    """
    Convert context into searchable text.
    """

    evidence_parts = []

    if context.get("top_result"):
        evidence_parts.append(
            str(context["top_result"])
        )

    if context.get("second_result"):
        evidence_parts.append(
            str(context["second_result"])
        )

    return " ".join(
        evidence_parts
    ).lower()


def check_hallucination(
    answer: str,
    context: dict
):
    """
    Check whether answer contains
    unsupported entities.

    Returns:

    {
        "grounded": bool,
        "unsupported_entities": list
    }
    """

    if not answer:

        return {
            "grounded": False,
            "unsupported_entities": []
        }

    evidence = extract_evidence(
        context
    )

    answer_lower = answer.lower()

    # Known IPL entities to monitor
    monitored_entities = [
        "kohli",
        "rohit",
        "dhoni",
        "bumrah",
        "chahal",
        "warner",
        "gayle",
        "abd",
        "de villiers",
        "jadeja",
        "yadav",
        "sharma",
    ]

    unsupported_entities = []

    for entity in monitored_entities:

        if (
            entity in answer_lower
            and entity not in evidence
        ):
            unsupported_entities.append(
                entity
            )

    return {
        "grounded":
            len(
                unsupported_entities
            ) == 0,

        "unsupported_entities":
            unsupported_entities
    }