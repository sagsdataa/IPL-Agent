# Testing/test_metric_question_builder.py
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)
from agent.metric_question_builder import (
    build_metric_question,
)


def test_strike_rate_preserves_season():

    metric_result = {
        "is_metric_followup": True,
        "metric": "strike_rate",
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player",
        "metric": "total_runs",
        "season": "2020",
    }

    question = build_metric_question(
        metric_result,
        context,
    )

    assert question == (
        "Who has the highest strike rate "
        "in IPL season 2020?"
    )


def test_strike_rate_without_season():

    metric_result = {
        "is_metric_followup": True,
        "metric": "strike_rate",
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player",
        "metric": "total_runs",
        "season": None,
    }

    question = build_metric_question(
        metric_result,
        context,
    )

    assert question == (
        "Who has the highest strike rate?"
    )