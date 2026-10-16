"""
Metric Question Builder

Changes the metric while preserving as much
previous analytical context as possible.
"""


def _get_state_value(
    state,
    keys,
):

    for key in keys:

        value = state.get(key)

        if value:
            return value

    return None


def build_metric_question(
    metric_result,
    conversation_state,
):

    if not metric_result:
        return None

    metric = metric_result.get(
        "metric"
    )

    if not metric:
        return None

    state = conversation_state or {}

    player = _get_state_value(
        state,
        (
            "player",
            "batter",
            "bowler",
            "primary_entity",
            "entity",
        ),
    )

    team = _get_state_value(
        state,
        (
            "team",
            "batting_team",
            "bowling_team",
        ),
    )

    season = _get_state_value(
        state,
        (
            "season",
            "year",
            "time_value",
        ),
    )

    previous_question = _get_state_value(
        state,
        (
            "last_question",
            "question",
            "previous_question",
        ),
    )

    if player:

        rewritten = (
            f"Show the {metric} for {player}"
        )

    elif team:

        rewritten = (
            f"Show the {metric} for {team}"
        )

    elif previous_question:

        rewritten = (
            f"{previous_question.rstrip('?.!')}. "
            f"Now show the {metric} for the same "
            f"player, team, or result entity"
        )

    else:

        return None

    if season:

        rewritten += (
            f" in IPL season {season}"
        )

    return rewritten.rstrip(
        "?.!"
    ) + "?"
