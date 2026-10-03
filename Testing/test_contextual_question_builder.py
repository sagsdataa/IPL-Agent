import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from agent.contextual_question_builder import (
    build_contextual_question
)


def test_bumrah_followup():

    entity_result = {

        "is_entity_followup": True,

        "entity": "Bumrah",

        "intent": "entity_followup"
    }

    context = {

        "query_type": "ranking",

        "entity_type": "player",

        "top_entity": "YS Chahal",

        "metric": "total_wickets"
    }

    question = (
        build_contextual_question(
            entity_result,
            context
        )
    )

    assert (
        question ==
        "Compare YS Chahal and Bumrah by total_wickets"
    )