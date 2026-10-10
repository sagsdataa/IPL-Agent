"""
Time Question Builder

Applies a time filter while preserving
all existing conversational filters.
"""


METRIC_QUESTIONS = {
    "total_runs": "Who scored the most runs",
    "runs": "Who scored the most runs",
    "total_wickets": "Who took the most wickets",
    "wickets": "Who took the most wickets",
    "strike_rate": "Who has the highest strike rate",
    "average": "Who has the highest batting average",
    "sixes": "Who hit the most sixes",
    "fours": "Who hit the most fours",
    "matches_played": "Who played the most matches",
}


def build_time_question(
    time_result,
    conversation_state,
):
    """
    Apply a time filter while preserving
    all active conversational filters.
    """

    if not time_result:
        return None

    if not conversation_state:
        return None

    if not time_result.get(
        "is_time_followup"
    ):
        return None

    metric = conversation_state.get(
        "metric"
    )

    base_question = (
        METRIC_QUESTIONS.get(
            metric
        )
    )

    if not base_question:
        return None

    filters = conversation_state.get(
        "filters",
        {}
    )

    time_type = time_result.get(
        "time_type"
    )

    time_value = time_result.get(
        "time_value"
    )

    #
    # Override time-related filters
    #
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

    if time_type == "season":
        season = time_value

    elif time_type == "playoffs":
        phase = "playoff"

    clauses = []

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