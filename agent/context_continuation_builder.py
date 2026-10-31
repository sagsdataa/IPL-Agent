"""
Context Continuation Builder

Builds a complete analytical question
from a continuation fragment while
preserving the previous analytical
entity, metric, and filters.
"""

import re

from agent.entity_normalizer import (
    normalize_entity
)


def build_context_continuation_question(
    continuation_result,
    conversation_state,
):

    if not continuation_result:
        return None

    if not conversation_state:
        return None

    if not continuation_result.get(
        "is_context_continuation",
        False,
    ):
        return None

    # -----------------------------------------
    # Previous analytical context
    # -----------------------------------------

    base_question = conversation_state.get(
        "last_question"
    )

    if not base_question:
        return None

    fragment = continuation_result.get(
        "fragment"
    )

    if not fragment:
        return None

    fragment = (
        fragment
        .strip()
        .rstrip("?.!")
    )

    fragment_lower = fragment.lower()

    player = (
        conversation_state.get("player")
        or conversation_state.get(
            "primary_entity"
        )
    )

    metric = conversation_state.get(
        "metric"
    )

    # ==================================================
    # AGAINST WHICH TEAM
    # ==================================================

    if fragment_lower in {
        "against which team",
        "against what team",
        "against whom",
        "which opposition",
    }:

        if not player:
            return None

        # Previous analysis was wickets
        if metric == "total_wickets":

            return (
                f"Against which batting team did "
                f"{player} take the most "
                f"bowler-attributed wickets?"
            )

        # Previous analysis was runs
        if metric == "total_runs":

            return (
                f"Against which bowling team did "
                f"{player} score the most runs?"
            )

        # Previous analysis was sixes
        if metric == "sixes":

            return (
                f"Against which bowling team did "
                f"{player} hit the most sixes?"
            )

        # Previous analysis was fours
        if metric == "fours":

            return (
                f"Against which bowling team did "
                f"{player} hit the most fours?"
            )

        # Generic player fallback
        return (
            f"{base_question.rstrip('?')} "
            f"against which team?"
        )

    # ==================================================
    # TEAM REPLACEMENT
    # Example:
    # For CSK?
    # ==================================================

    if fragment_lower.startswith("for "):

        entity = fragment[4:].strip()

        entity = normalize_entity(
            entity
        )

        base_question = re.sub(
            r"\s+for\s+[^?]+",
            "",
            base_question,
            flags=re.IGNORECASE,
        )

        return (
            f"{base_question.rstrip('?')} "
            f"for {entity}?"
        )

    # ==================================================
    # VENUE REPLACEMENT
    # Example:
    # At Wankhede?
    # ==================================================

    if fragment_lower.startswith("at "):

        venue = fragment[3:].strip()

        venue = normalize_entity(
            venue
        )

        base_question = re.sub(
            r"\s+at\s+[^?]+",
            "",
            base_question,
            flags=re.IGNORECASE,
        )

        return (
            f"{base_question.rstrip('?')} "
            f"at {venue}?"
        )

    # ==================================================
    # SEASON REPLACEMENT
    # ==================================================

    season_match = re.search(
        r"\b20\d{2}\b",
        fragment
    )

    if season_match:

        season = season_match.group()

        base_question = re.sub(
            r"\s+in\s+IPL\s+season\s+\d{4}",
            "",
            base_question,
            flags=re.IGNORECASE,
        )

        return (
            f"{base_question.rstrip('?')} "
            f"in IPL season {season}?"
        )

    # ==================================================
    # PURE ENTITY CONTINUATION
    # ==================================================

    normalized_entity = normalize_entity(
        fragment
    )

    # Only use the entity branch if normalization
    # actually identified a player/team alias.
    if (
        normalized_entity
        and normalized_entity.lower()
        != fragment.lower()
    ):

        base_question = re.sub(
            r"\s+for\s+[^?]+",
            "",
            base_question,
            flags=re.IGNORECASE,
        )

        return (
            f"{base_question.rstrip('?')} "
            f"for {normalized_entity}?"
        )

    # ==================================================
    # GENERIC CONTINUATION
    # ==================================================

    return (
        f"{base_question.rstrip('?')}. "
        f"Follow-up request: {fragment}?"
    )