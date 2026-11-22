import pandas as pd
import pytest

from agent.capability_planner_models import (
    PlannedTask,
)

from agent.dependency_result_resolver import (
    DependencyResolutionError,
    resolve_dependent_task,
    resolve_dependency_question,
    resolve_task_result_value,
)


# ============================================================
# SHARED TEST RESULT
# ============================================================

def build_analytics_result():

    return {
        "task_id": "task_1",
        "capability": "analytics_query",
        "status": "success",
        "question": (
            "Who scored the most IPL runs?"
        ),
        "answer": (
            "V Kohli is the leading "
            "IPL run scorer."
        ),
        "result": pd.DataFrame(
            {
                "player": [
                    "V Kohli"
                ],
                "total_runs": [
                    8000
                ],
            }
        ),
        "context": {
            "player":
                "V Kohli",

            "primary_entity":
                "V Kohli",

            "metric":
                "total_runs",
        },
        "error": None,
    }


# ============================================================
# 1. RESOLVE PRIMARY ENTITY FROM CONTEXT
# ============================================================

def test_resolve_primary_entity():

    task_result = (
        build_analytics_result()
    )

    value = resolve_task_result_value(
        task_result,
        "primary_entity",
    )

    assert value == "V Kohli"


# ============================================================
# 2. RESOLVE PLAYER FROM CONTEXT
# ============================================================

def test_resolve_player():

    task_result = (
        build_analytics_result()
    )

    value = resolve_task_result_value(
        task_result,
        "player",
    )

    assert value == "V Kohli"


# ============================================================
# 3. RESOLVE VALUE FROM DATAFRAME
# ============================================================

def test_resolve_dataframe_field():

    task_result = (
        build_analytics_result()
    )

    value = resolve_task_result_value(
        task_result,
        "total_runs",
    )

    assert value == 8000


# ============================================================
# 4. RESOLVE QUESTION PLACEHOLDER
# ============================================================

def test_resolve_question_placeholder():

    completed_tasks = {
        "task_1":
            build_analytics_result()
    }

    resolved_question = (
        resolve_dependency_question(
            (
                "Tell me about "
                "{{task_1.primary_entity}}"
            ),
            completed_tasks,
        )
    )

    assert resolved_question == (
        "Tell me about V Kohli"
    )


# ============================================================
# 5. RESOLVE NESTED CONTEXT PLACEHOLDER
# ============================================================

def test_resolve_nested_context_placeholder():

    completed_tasks = {
        "task_1":
            build_analytics_result()
    }

    resolved_question = (
        resolve_dependency_question(
            (
                "Tell me about "
                "{{task_1.context.player}}"
            ),
            completed_tasks,
        )
    )

    assert resolved_question == (
        "Tell me about V Kohli"
    )


# ============================================================
# 6. RESOLVE COMPLETE DEPENDENT TASK
# ============================================================

def test_resolve_dependent_task():

    task = PlannedTask(
        task_id="task_2",
        capability="knowledge_search",
        question=(
            "Tell me about "
            "{{task_1.primary_entity}}"
        ),
        depends_on=[
            "task_1"
        ],
    )

    completed_tasks = {
        "task_1":
            build_analytics_result()
    }

    resolved_task = (
        resolve_dependent_task(
            task,
            completed_tasks,
        )
    )

    assert (
        resolved_task.question
        == "Tell me about V Kohli"
    )

    assert (
        resolved_task.task_id
        == "task_2"
    )

    assert (
        resolved_task.capability
        == "knowledge_search"
    )

    assert (
        resolved_task.depends_on
        == ["task_1"]
    )


# ============================================================
# 7. ORIGINAL TASK MUST NOT BE MUTATED
# ============================================================

def test_original_task_not_modified():

    original_question = (
        "Tell me about "
        "{{task_1.primary_entity}}"
    )

    task = PlannedTask(
        task_id="task_2",
        capability="knowledge_search",
        question=original_question,
        depends_on=[
            "task_1"
        ],
    )

    completed_tasks = {
        "task_1":
            build_analytics_result()
    }

    resolved_task = (
        resolve_dependent_task(
            task,
            completed_tasks,
        )
    )

    assert (
        task.question
        == original_question
    )

    assert (
        resolved_task.question
        == "Tell me about V Kohli"
    )


# ============================================================
# 8. MISSING DEPENDENCY
# ============================================================

def test_missing_dependency_result():

    task = PlannedTask(
        task_id="task_2",
        capability="knowledge_search",
        question=(
            "Tell me about "
            "{{task_1.primary_entity}}"
        ),
        depends_on=[
            "task_1"
        ],
    )

    with pytest.raises(
        DependencyResolutionError
    ):

        resolve_dependent_task(
            task,
            completed_tasks={},
        )


# ============================================================
# 9. FAILED DEPENDENCY
# ============================================================

def test_failed_dependency_result():

    task = PlannedTask(
        task_id="task_2",
        capability="knowledge_search",
        question=(
            "Tell me about "
            "{{task_1.primary_entity}}"
        ),
        depends_on=[
            "task_1"
        ],
    )

    completed_tasks = {
        "task_1": {
            "task_id":
                "task_1",

            "capability":
                "analytics_query",

            "status":
                "failed",

            "error":
                "Simulated failure",
        }
    }

    with pytest.raises(
        DependencyResolutionError
    ):

        resolve_dependent_task(
            task,
            completed_tasks,
        )


# ============================================================
# 10. UNKNOWN OUTPUT FIELD
# ============================================================

def test_missing_output_field():

    completed_tasks = {
        "task_1":
            build_analytics_result()
    }

    with pytest.raises(
        DependencyResolutionError
    ):

        resolve_dependency_question(
            (
                "Tell me about "
                "{{task_1.unknown_field}}"
            ),
            completed_tasks,
        )


# ============================================================
# 11. INDEPENDENT TASK REMAINS UNCHANGED
# ============================================================

def test_independent_task_unchanged():

    task = PlannedTask(
        task_id="task_1",
        capability="knowledge_search",
        question="Explain Powerplay",
        depends_on=[],
    )

    resolved_task = (
        resolve_dependent_task(
            task,
            completed_tasks={},
        )
    )

    assert resolved_task is task

    assert (
        resolved_task.question
        == "Explain Powerplay"
    )


# ============================================================
# 12. RESOLVE TEAM ENTITY
# ============================================================

def test_resolve_team_entity():

    completed_tasks = {
        "task_1": {
            "task_id":
                "task_1",

            "capability":
                "analytics_query",

            "status":
                "success",

            "result":
                pd.DataFrame(
                    {
                        "team": [
                            "Mumbai Indians"
                        ],
                        "titles": [
                            5
                        ],
                    }
                ),

            "context": {
                "team":
                    "Mumbai Indians",

                "primary_entity":
                    "Mumbai Indians",
            },

            "answer":
                "Mumbai Indians",

            "error":
                None,
        }
    }

    resolved_question = (
        resolve_dependency_question(
            (
                "Tell me about "
                "{{task_1.team}}"
            ),
            completed_tasks,
        )
    )

    assert resolved_question == (
        "Tell me about Mumbai Indians"
    )