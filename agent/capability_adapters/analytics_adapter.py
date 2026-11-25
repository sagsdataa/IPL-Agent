from typing import Any

from agent.capability_planner_models import (
    PlannedTask,
)

from agent.analytics_service import (
    run_analytics_query,
)


# ============================================================
# BUILD ENTITY CONTEXT
# ============================================================

def build_entity_context(
    task: PlannedTask,
) -> dict[str, Any]:

    """
    Convert planner EntityReference objects into
    structured context for the Analytics Service.

    Example:

    task.entities:
        player -> MS Dhoni

    becomes:

    {
        "player": "MS Dhoni"
    }
    """

    entity_context = {}

    for entity in task.entities:

        entity_type = (
            entity.entity_type
            .strip()
            .lower()
        )

        canonical_name = (
            entity.canonical_name
            .strip()
        )

        if not canonical_name:
            continue

        # Only pass entity types understood by
        # the analytical Context Builder.
        if entity_type in {
            "player",
            "team",
            "venue",
        }:

            entity_context[
                entity_type
            ] = canonical_name

    return entity_context


# ============================================================
# EXECUTE ANALYTICS TASK
# ============================================================

def execute_analytics_task(
    task: PlannedTask,
    completed_tasks: (
        dict[str, Any] | None
    ) = None,
):

    completed_tasks = (
        completed_tasks
        or {}
    )

    question = (
        task.question.strip()
    )

    # --------------------------------------------------------
    # EMPTY QUESTION
    # --------------------------------------------------------

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

            "entity_context":
                {},

            "error": (
                "Analytics task question "
                "cannot be empty."
            ),
        }


    # --------------------------------------------------------
    # PLANNER ENTITY CONTEXT
    # --------------------------------------------------------

    entity_context = (
        build_entity_context(
            task
        )
    )


    # --------------------------------------------------------
    # EXECUTE ANALYTICS SERVICE
    # --------------------------------------------------------

    try:

        analytics_result = (
            run_analytics_query(
                question,
                entity_context=(
                    entity_context
                ),
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

            "entity_context":
                entity_context,

            "error":
                None,
        }


    # --------------------------------------------------------
    # FAILURE
    # --------------------------------------------------------

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

            "entity_context":
                entity_context,

            "error":
                str(error),
        }