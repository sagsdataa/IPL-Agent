from agent.capability_planner import (
    create_capability_plan,
)

from agent.capability_executor import (
    execute_capability_plan,
)


def test_dependent_hybrid_end_to_end():

    question = (
        "Find the highest IPL run scorer "
        "and tell me about that player"
    )

    # ========================================================
    # PLAN
    # ========================================================

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "hybrid"
    assert len(plan.tasks) == 2

    analytics_task = plan.tasks[0]
    knowledge_task = plan.tasks[1]

    assert (
        analytics_task.capability
        == "analytics_query"
    )

    assert (
        knowledge_task.capability
        == "knowledge_search"
    )

    assert (
        knowledge_task.depends_on
        == ["task_1"]
    )

    # Critical dependency contract
    assert (
        "{{task_1.primary_entity}}"
        in knowledge_task.question
    )

    # ========================================================
    # EXECUTE
    # ========================================================

    execution = execute_capability_plan(
        plan
    )

    assert execution["status"] == "success"

    assert (
        execution["successful_tasks"]
        == 2
    )

    analytics_result = (
        execution["task_results"][
            "task_1"
        ]
    )

    knowledge_result = (
        execution["task_results"][
            "task_2"
        ]
    )

    # ========================================================
    # ANALYTICS RESULT
    # ========================================================

    assert (
        analytics_result["status"]
        == "success"
    )

    assert analytics_result["context"]

    discovered_entity = (
        analytics_result["context"].get(
            "primary_entity"
        )
    )

    assert discovered_entity

    # ========================================================
    # DEPENDENCY RESOLUTION
    # ========================================================

    assert (
        knowledge_result["status"]
        == "success"
    )

    assert (
        knowledge_result.get(
            "planned_question"
        )
    )

    assert (
        knowledge_result.get(
            "resolved_question"
        )
    )

    assert (
        discovered_entity.lower()
        in knowledge_result[
            "resolved_question"
        ].lower()
    )

    # The placeholder must be gone.
    assert (
        "{{task_1.primary_entity}}"
        not in knowledge_result[
            "resolved_question"
        ]
    )

    assert knowledge_result["answer"]