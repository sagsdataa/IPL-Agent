import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from agent.metric_question_builder import (
    build_metric_question
)


def test_strike_rate_question():

    metric_result = {
        "is_metric_followup": True,
        "metric": "strike_rate"
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player",
        "metric": "total_runs"
    }

    question = (
        build_metric_question(
            metric_result,
            context
        )
    )

    assert (
        question ==
        "Who has the highest strike rate?"
    )


def test_average_question():

    metric_result = {
        "is_metric_followup": True,
        "metric": "average"
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player"
    }

    question = (
        build_metric_question(
            metric_result,
            context
        )
    )

    assert (
        question ==
        "Who has the highest batting average?"
    )


def test_sixes_question():

    metric_result = {
        "is_metric_followup": True,
        "metric": "sixes"
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player"
    }

    question = (
        build_metric_question(
            metric_result,
            context
        )
    )

    assert (
        question ==
        "Who hit the most sixes?"
    )


def test_fours_question():

    metric_result = {
        "is_metric_followup": True,
        "metric": "fours"
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player"
    }

    question = (
        build_metric_question(
            metric_result,
            context
        )
    )

    assert (
        question ==
        "Who hit the most fours?"
    )


def test_invalid_metric():

    metric_result = {
        "is_metric_followup": False,
        "metric": None
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player"
    }

    question = (
        build_metric_question(
            metric_result,
            context
        )
    )

    assert question is None