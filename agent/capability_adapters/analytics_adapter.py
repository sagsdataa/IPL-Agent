from typing import Any

from agent.capability_planner_models import (
    PlannedTask,
)

from agent.analytics_service import (
    run_analytics_query,
)


def execute_analytics_task(
    task: PlannedTask,
    completed_tasks: dict[str, Any] | None = None,
):

    completed_tasks = (
        completed_tasks or {}
    )

    question = (
        task.question
        .strip()
    )

    if not question:

        return {
            "task_id":
                task.task_id,

            "capability":
                task.capability,

            "status":
                "failed",

            "question":
                task.question,

            "answer":
                None,

            "sql":
                None,

            "result":
                None,

            "context":
                None,

            "error":
                (
                    "Analytics task question "
                    "cannot be empty."
                ),
        }

    try:

        analytics_result = (
            run_analytics_query(
                question
            )
        )

        return {
            "task_id":
                task.task_id,

            "capability":
                task.capability,

            "status":
                "success",

            "question":
                question,

            "answer":
                analytics_result[
                    "answer"
                ],

            "sql":
                analytics_result[
                    "sql"
                ],

            "result":
                analytics_result[
                    "result"
                ],

            "context":
                analytics_result[
                    "context"
                ],

            "error":
                None,
        }

    except Exception as error:

        return {
            "task_id":
                task.task_id,

            "capability":
                task.capability,

            "status":
                "failed",

            "question":
                question,

            "answer":
                None,

            "sql":
                None,

            "result":
                None,

            "context":
                None,

            "error":
                str(error),
        }