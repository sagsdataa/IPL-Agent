from agent.conversation_state import (
    create_conversation_state,
    update_conversation_state,
)


# ============================================================
# TEST 1
# Metric follow-up must replace previous metric
#
# Flow:
# Who scored the most runs in IPL?
# -> Strike rate?
# ============================================================

def test_metric_followup_preserves_player_and_updates_metric():

    state = create_conversation_state()

    # First analytical question
    first_context = {
        "intent": "ranking",
        "metric": "total_runs",
        "player": "V Kohli",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "V Kohli",
    }

    state = update_conversation_state(
        state,
        "Who scored the most runs in IPL?",
        first_context,
    )

    assert state["player"] == "V Kohli"
    assert state["metric"] == "total_runs"
    assert state["primary_entity"] == "V Kohli"

    # Simulate the enriched context produced
    # by the metric follow-up branch
    followup_context = {
        "intent": "metric_lookup",
        "metric": "strike_rate",
        "player": "V Kohli",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "V Kohli",
    }

    state = update_conversation_state(
        state,
        "Show the strike rate for V Kohli?",
        followup_context,
    )

    assert state["intent"] == "metric_lookup"
    assert state["metric"] == "strike_rate"
    assert state["player"] == "V Kohli"
    assert state["primary_entity"] == "V Kohli"


# ============================================================
# TEST 2
# Context continuation must preserve player + metric
#
# Flow:
# Most wickets by left-arm pacers
# -> Against which team?
# ============================================================

def test_context_continuation_preserves_player_and_metric():

    state = create_conversation_state()

    first_context = {
        "intent": "ranking",
        "metric": "total_wickets",
        "player": "JD Unadkat",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "JD Unadkat",
    }

    state = update_conversation_state(
        state,
        "Most wickets by left-arm pacers",
        first_context,
    )

    assert state["intent"] == "ranking"
    assert state["metric"] == "total_wickets"
    assert state["player"] == "JD Unadkat"
    assert state["primary_entity"] == "JD Unadkat"

    # Simulates the context AFTER your continuation
    # branch has enriched it with previous state.
    continuation_context = {
        "intent": "ranking",
        "metric": "total_wickets",
        "player": "JD Unadkat",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "JD Unadkat",

        # Result-specific fields can safely coexist
        "row_count": 1,
        "top_result": {
            "batting_team": "Mumbai Indians",
            "total_wickets": 17,
        },
    }

    state = update_conversation_state(
        state,
        (
            "Against which batting team did JD Unadkat "
            "take the most bowler-attributed wickets?"
        ),
        continuation_context,
    )

    assert state["intent"] == "ranking"
    assert state["metric"] == "total_wickets"
    assert state["player"] == "JD Unadkat"
    assert state["primary_entity"] == "JD Unadkat"