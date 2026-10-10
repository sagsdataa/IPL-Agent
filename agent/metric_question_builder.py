"""
Metric Question Builder

Changes the analytical metric while preserving
all active conversational filters.
"""

METRIC_QUESTIONS = {
    "strike_rate": "Who has the highest strike rate",
    "average": "Who has the highest batting average",
    "sixes": "Who hit the most sixes",
    "fours": "Who hit the most fours",
    "wickets": "Who took the most wickets",
    "total_wickets": "Who took the most wickets",
    "economy": "Who has the best economy rate",
    "matches_played": "Who played the most matches",
    "total_runs": "Who scored the most runs",
    "runs": "Who scored the most runs",
}


def build_metric_question(
    metric_result,
    conversation_state,
):
    """
    Build a fresh analytical question using
    the requested metric while preserving
    conversational filters.

    Example

    Conversation State:

    {
        "query_type": "ranking",
        "entity_type": "player",
        "filters": {
            "season": "2019",
            "team": "Sunrisers Hyderabad",
            "venue": "Wankhede Stadium"
        }
    }

    Follow-up:

        What about strike rate?

    Output:

        Who has the highest strike rate
        in IPL season 2019
        for Sunrisers Hyderabad
        at Wankhede Stadium?
    """

    if not metric_result:
        return None

    if not conversation_state:
        return None

    if not metric_result.get(
        "is_metric_followup"
    ):
        return None

    new_metric = metric_result.get(
        "metric"
    )

    query_type = conversation_state.get(
        "query_type"
    )

    entity_type = conversation_state.get(
        "entity_type"
    )

    if query_type not in {
        "ranking",
        "comparison",
    }:
        return None

    if entity_type != "player":
        return None

    base_question = (
        METRIC_QUESTIONS.get(
            new_metric
        )
    )

    if not base_question:
        return None

    filters = conversation_state.get(
        "filters",
        {}
    )

    clauses = []

    season = filters.get(
        "season"
    )

    team = filters.get(
        "team"
    )

    venue = filters.get(
        "venue"
    )

    phase = filters.get(
        "phase"
    )

    if season:
        clauses.append(
            f"in IPL season {season}"
        )

    if team:
        clauses.append(
            f"for {team}"
        )

    if venue:
        clauses.append(
            f"at {venue}"
        )

    if phase:
        clauses.append(
            f"during {phase}"
        )

    question = base_question

    if clauses:
        question += (
            " "
            + " ".join(clauses)
        )

    return f"{question}?"