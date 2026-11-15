from agent.metric_question_builder import (
    build_metric_question,
)

from agent.context_continuation_builder import (
    build_context_continuation_question,
)


def test_strike_rate_followup_rewrite():

    state = {
        "last_question":
            "Who scored the most runs in IPL?",

        "intent": "ranking",
        "metric": "total_runs",
        "player": "V Kohli",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "V Kohli",
    }

    metric_result = {
        "is_metric_followup": True,
        "metric": "strike rate",
    }

    rewritten = build_metric_question(
        metric_result,
        state,
    )

    assert rewritten == (
        "Show the strike rate for V Kohli?"
    )


def test_against_which_team_rewrite():

    state = {
        "last_question":
            "Most wickets by left-arm pacers",

        "intent": "ranking",
        "metric": "total_wickets",
        "player": "JD Unadkat",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "JD Unadkat",
    }

    continuation_result = {
        "is_context_continuation": True,
        "confidence": 1.0,
        "fragment": "against which team",
        "reasons": [
            "contextual_analytical_followup"
        ],
    }

    rewritten = (
        build_context_continuation_question(
            continuation_result,
            state,
        )
    )

    assert rewritten == (
        "Against which batting team did JD Unadkat "
        "take the most bowler-attributed wickets?"
    )