from agent.metric_resolver import (
    detect_metric_followup,
)

from agent.metric_question_builder import (
    build_metric_question,
)


def test_ms_dhoni_strike_rate_followup():

    question = "strike rate"

    conversation_state = {
        "last_question": (
            "Show MS Dhoni's IPL runs by season"
        ),
        "intent": "trend",
        "metric": "total_runs",
        "player": "MS Dhoni",
        "team": None,
        "season": None,
        "venue": None,
        "phase": None,
        "primary_entity": "MS Dhoni",
    }

    metric_result = (
        detect_metric_followup(
            question
        )
    )

    print(
        "METRIC RESULT:",
        metric_result,
    )

    assert (
        metric_result.get(
            "is_metric_followup"
        )
        is True
    )

    assert (
        metric_result.get(
            "metric"
        )
        in {
            "strike rate",
            "strike_rate",
        }
    )

    rewritten_question = (
        build_metric_question(
            metric_result,
            conversation_state,
        )
    )

    print(
        "REWRITTEN QUESTION:",
        rewritten_question,
    )

    assert rewritten_question

    assert (
        "MS Dhoni"
        in rewritten_question
    )

    normalized = (
        rewritten_question
        .lower()
        .replace("_", " ")
    )

    assert (
        "strike rate"
        in normalized
    )