# agent/context_continuation_builder.py

"""
Context Continuation Builder

Builds a complete analytical question
from a continuation fragment while
replacing filters already present
in the canonical question.
"""

import re

from agent.entity_normalizer import (
    normalize_entity
)


def build_context_continuation_question(
    continuation_result,
    conversation_state,
):
    """
    Example

    Base:
        Who scored the most runs in IPL
        for SRH?

    Follow-up:
        for Mumbai Indians?

    Output:
        Who scored the most runs in IPL
        for Mumbai Indians?
    """

    if not continuation_result:
        return None

    if not conversation_state:
        return None

    if not continuation_result.get(
        "is_context_continuation"
    ):
        return None

    base_question = (
        conversation_state.get(
            "canonical_question"
        )
    )

    if not base_question:
        return None

    fragment = (
        continuation_result.get(
            "fragment"
        )
    )

    if not fragment:
        return None

    #
    # Normalize fragment
    #
    fragment = fragment.strip()

    #
    # Team replacement
    #
    if fragment.lower().startswith(
        "for "
    ):

        entity = fragment[4:].strip()

        entity = normalize_entity(
            entity
        )

        #
        # Remove existing team clause
        #
        base_question = re.sub(
            r"\s+for\s+[^?]+",
            "",
            base_question,
            flags=re.IGNORECASE
        )

        return (
            f"{base_question.rstrip('?')} "
            f"for {entity}?"
        )

    #
    # Venue replacement
    #
    if fragment.lower().startswith(
        "at "
    ):

        venue = fragment[3:].strip()

        venue = normalize_entity(
            venue
        )

        base_question = re.sub(
            r"\s+at\s+[^?]+",
            "",
            base_question,
            flags=re.IGNORECASE
        )

        return (
            f"{base_question.rstrip('?')} "
            f"at {venue}?"
        )

    #
    # Season replacement
    #
    season_match = re.search(
        r"20\d{2}",
        fragment
    )

    if season_match:

        season = season_match.group()

        base_question = re.sub(
            r"in IPL season \d{4}",
            "",
            base_question,
            flags=re.IGNORECASE
        )

        return (
            f"{base_question.rstrip('?')} "
            f"in IPL season {season}?"
        )

    #
    # Pure entity continuation
    #
    if len(fragment.split()) <= 3:

        normalized_entity = normalize_entity(
        fragment
        )

        base_question = re.sub(
        r"\s+for\s+[^?]+",
        "",
        base_question,
        flags=re.IGNORECASE
        )

        return (
        f"{base_question.rstrip('?')} "
        f"for {normalized_entity}?"
        )

    #
    # Fallback
    #
    return (
        f"{base_question.rstrip('?')} "
        f"{fragment}?"
    )