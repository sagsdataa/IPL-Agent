import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

# Testing/test_contextual_question_builder.py

from agent.contextual_question_builder import (
    build_contextual_question,
)


def test_entity_comparison_preserves_season():

    entity_result = {
        "is_entity_followup": True,
        "entity": "Dhoni",
        "intent": "entity_followup",
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player",
        "metric": "total_runs",
        "season": "2020",
        "top_entity": "KL Rahul",
    }

    question = build_contextual_question(
        entity_result,
        context,
    )

    assert question == (
        "Compare KL Rahul and Dhoni "
        "by total_runs in IPL season 2020."
    )


def test_entity_comparison_without_season():

    entity_result = {
        "is_entity_followup": True,
        "entity": "Rohit Sharma",
        "intent": "entity_followup",
    }

    context = {
        "query_type": "ranking",
        "entity_type": "player",
        "metric": "total_runs",
        "season": None,
        "top_entity": "V Kohli",
    }

    question = build_contextual_question(
        entity_result,
        context,
    )

    assert question == (
        "Compare V Kohli and Rohit Sharma "
        "by total_runs."
    )