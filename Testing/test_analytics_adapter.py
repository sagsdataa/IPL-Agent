from agent.capability_planner_models import (
    PlannedTask,   
)
from agent.capability_adapters.analytics_adapter import (
    execute_analytics_task,
)


def test_player_entity_context_preserved():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question=(
            " strike rate"
            
        ),
        entities=[
            {
                "entity_type": "player",
                "canonical_name": "MS Dhoni",
                "mention": "MS Dhoni",
            }
        ],
    )

    result = execute_analytics_task(
        task
    )

    assert (
        result["status"]
        == "success"
    )

    assert (
        result["entity_context"][
            "player"
        ]
        == "MS Dhoni"
    )

    assert (
        result["context"][
            "player"
        ]
        == "MS Dhoni"
    )

    assert (
        result["context"][
            "primary_entity"
        ]
        == "MS Dhoni"
    )