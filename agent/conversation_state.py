"""
Conversation State

Stores the latest analytical question and
accumulated structured context.
"""

def create_conversation_state():

    return {
        "last_question": None,
        "intent": None,
        "metric": None,
        "player": None,
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": None,
    }


def _first_context_value(
    context,
    keys,
):

    for key in keys:

        value = context.get(key)

        if value is not None:
            return value

    return None


def update_conversation_state(
    current_state,
    question,
    context,
):
    """
    Replace the previous analytical state with the context
    from the latest successful analysis.

    This prevents stale players, teams, seasons and other
    filters from leaking into unrelated new questions.
    """

    # Start with a clean analytical state.
    state = create_conversation_state()

    state["last_question"] = question

    if not context:
        return state

    intent = _first_context_value(
        context,
        (
            "intent",
            "query_type",
            "analysis_type",
        ),
    )

    metric = _first_context_value(
        context,
        (
            "metric",
            "metric_name",
            "primary_metric",
        ),
    )

    primary_entity = _first_context_value(
        context,
        (
            "primary_entity",
            "leading_entity",
            "top_entity",
            "result_entity",
        ),
    )

    player = _first_context_value(
        context,
        (
            "player",
            "batter",
            "bowler",
        ),
    )

    team = _first_context_value(
        context,
        (
            "team",
            "batting_team",
            "bowling_team",
        ),
    )

    season = _first_context_value(
        context,
        (
            "season",
            "year",
            "time_value",
        ),
    )

    venue = _first_context_value(
        context,
        (
            "venue",
            "stadium",
        ),
    )

    phase = _first_context_value(
        context,
        (
            "phase",
            "match_phase",
        ),
    )

    state.update(
        {
            "intent": intent,
            "metric": metric,
            "player": player,
            "team": team,
            "season": season,
            "venue": venue,
            "phase": phase,
            "primary_entity": primary_entity,
        }
    )

    print("=" * 80)
    print("UPDATED CONVERSATION STATE")
    print(state)
    print("=" * 80)

    return state