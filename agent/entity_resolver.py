"""
Entity Follow-Up Resolver

Examples:

For CSK?
For MI?
What about Bumrah?
How about Kohli?
"""

import re

from agent.entity_normalizer import (
    normalize_entity,
)


ENTITY_FOLLOWUP_PREFIXES = (
    "for ",
    "what about ",
    "how about ",
    "and ",
)


def _empty_result():

    return {
        "is_entity_followup": False,
        "entity": None,
        "intent": None,
    }


def detect_entity_followup(question: str):

    if not question or not question.strip():
        return _empty_result()

    cleaned = (
        question
        .strip()
        .lower()
    )

    cleaned = re.sub(
        r"[?.,!]+$",
        "",
        cleaned
    ).strip()

    matched_prefix = None
    entity_text = None

    for prefix in ENTITY_FOLLOWUP_PREFIXES:

        if cleaned.startswith(prefix):

            matched_prefix = prefix.strip()

            entity_text = (
                cleaned[len(prefix):]
                .strip()
            )

            break

    if not entity_text:
        return _empty_result()

    normalized_entity = normalize_entity(
        entity_text
    )

    print(
        "ENTITY FOLLOWUP:",
        entity_text,
        "→",
        normalized_entity
    )

    if not normalized_entity:
        return _empty_result()

    return {
        "is_entity_followup": True,
        "entity": normalized_entity,
        "intent": matched_prefix,
    }