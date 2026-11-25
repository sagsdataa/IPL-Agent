from agent.capability_planner import (
    create_capability_plan,
)

from agent.capability_executor import (
    execute_capability_plan,
)


# ============================================================
# MS DHONI HYBRID ENTITY-CONTEXT REGRESSION
# ============================================================

def test_ms_dhoni_entity_preserved_in_hybrid_analytics():

    question = (
        "strike rate "
        
    )

    # --------------------------------------------------------
    # 1. PLAN
    # --------------------------------------------------------

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "hybrid"
    assert len(plan.tasks) == 2

    analytics_tasks = [
        task
        for task in plan.tasks
        if task.capability
        == "analytics_query"
    ]

    assert len(
        analytics_tasks
    ) == 1

    analytics_task = (
        analytics_tasks[0]
    )

    # --------------------------------------------------------
    # 2. PLANNER ENTITY
    # --------------------------------------------------------

    player_entities = [
        entity
        for entity in analytics_task.entities
        if entity.entity_type
        == "player"
    ]

    assert len(
        player_entities
    ) >= 1

    assert (
        player_entities[0]
        .canonical_name
        == "MS Dhoni"
    )

    # --------------------------------------------------------
    # 3. EXECUTE COMPLETE HYBRID PLAN
    # --------------------------------------------------------

    execution = (
        execute_capability_plan(
            plan
        )
    )

    assert (
        execution["status"]
        == "success"
    )

    # --------------------------------------------------------
    # 4. FIND ANALYTICS RESULT
    # --------------------------------------------------------

    analytics_result = None

    for task_id, task_result in (
        execution[
            "task_results"
        ].items()
    ):

        if (
            task_result.get(
                "capability"
            )
            == "analytics_query"
        ):

            analytics_result = (
                task_result
            )

            break

    assert (
        analytics_result
        is not None
    )

    assert (
        analytics_result["status"]
        == "success"
    )

    # --------------------------------------------------------
    # 5. VERIFY ADAPTER ENTITY CONTEXT
    # --------------------------------------------------------

    entity_context = (
        analytics_result.get(
            "entity_context",
            {},
        )
    )

    assert (
        entity_context.get(
            "player"
        )
        == "MS Dhoni"
    )

    # --------------------------------------------------------
    # 6. VERIFY ANALYTICS CONTEXT
    # --------------------------------------------------------

    context = (
        analytics_result.get(
            "context"
        )
    )

    assert context

    assert (
        context.get(
            "query_type"
        )
        == "trend"
    )

    assert (
        context.get(
            "metric"
        )
        == "total_runs"
    )

    assert (
        context.get(
            "player"
        )
        == "MS Dhoni"
    )

    assert (
        context.get(
            "primary_entity"
        )
        == "MS Dhoni"
    )