import pytest

from agent.capability_planner import (
    CapabilityPlannerError,
    create_capability_plan,
)

from agent.capability_executor import (
    execute_capability_plan,
)

from agent.capability_response_composer import (
    compose_capability_response,
)


# ============================================================
# 1. INDEPENDENT HYBRID PIPELINE
#
# Knowledge and Analytics can execute independently.
# ============================================================

def test_independent_hybrid_pipeline():

    question = (
        "Tell me about MS Dhoni "
        "and show his runs by season"
    )

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "hybrid"
    assert len(plan.tasks) == 2

    capabilities = {
        task.capability
        for task in plan.tasks
    }

    assert capabilities == {
        "knowledge_search",
        "analytics_query",
    }

    # Independent hybrid tasks should
    # not depend on each other.
    for task in plan.tasks:

        assert task.depends_on == []

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    execution = execute_capability_plan(
        plan
    )

    assert execution["status"] == "success"

    assert execution["total_tasks"] == 2

    assert (
        execution["successful_tasks"]
        == 2
    )

    # --------------------------------------------------------
    # COMPOSE
    # --------------------------------------------------------

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"
    assert response["route"] == "hybrid"

    assert response["answer"]

    assert len(
        response["sections"]
    ) == 2

    assert response[
        "analytics_artifacts"
    ]

    assert response[
        "knowledge_sources"
    ]

    # Verify both capabilities contributed
    # to the final response.
    section_capabilities = {
        section["capability"]
        for section in response[
            "sections"
        ]
    }

    assert section_capabilities == {
        "knowledge_search",
        "analytics_query",
    }


# ============================================================
# 2. DEPENDENT HYBRID PIPELINE
#
# Analytics discovers the entity.
# Knowledge depends on that output.
# ============================================================

def test_dependent_hybrid_pipeline():

    question = (
        "Find the highest IPL run scorer "
        "and tell me about that player"
    )

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

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
        analytics_task.depends_on
        == []
    )

    assert (
        knowledge_task.depends_on
        == ["task_1"]
    )

    # Critical structured dependency contract
    assert (
        "{{task_1.primary_entity}}"
        in knowledge_task.question
    )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    execution = execute_capability_plan(
        plan
    )

    assert execution["status"] == "success"

    assert (
        execution["successful_tasks"]
        == 2
    )

    analytics_result = (
        execution[
            "task_results"
        ]["task_1"]
    )

    knowledge_result = (
        execution[
            "task_results"
        ]["task_2"]
    )

    assert (
        analytics_result["status"]
        == "success"
    )

    assert (
        knowledge_result["status"]
        == "success"
    )

    # --------------------------------------------------------
    # ENTITY DISCOVERY
    # --------------------------------------------------------

    analytics_context = (
        analytics_result.get(
            "context",
            {}
        )
    )

    discovered_entity = (
        analytics_context.get(
            "primary_entity"
        )
    )

    assert discovered_entity

    # --------------------------------------------------------
    # DEPENDENCY RESOLUTION
    # --------------------------------------------------------

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
        "{{task_1.primary_entity}}"
        in knowledge_result[
            "planned_question"
        ]
    )

    assert (
        "{{task_1.primary_entity}}"
        not in knowledge_result[
            "resolved_question"
        ]
    )

    assert (
        discovered_entity.lower()
        in knowledge_result[
            "resolved_question"
        ].lower()
    )

    # --------------------------------------------------------
    # COMPOSE
    # --------------------------------------------------------

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"
    assert response["route"] == "hybrid"

    assert response["answer"]

    assert len(
        response["sections"]
    ) == 2

    assert response[
        "analytics_artifacts"
    ]

    assert response[
        "knowledge_sources"
    ]

    # Entity discovered by Analytics
    # should appear somewhere in the
    # composed response.
    assert (
        discovered_entity.lower()
        in response[
            "answer"
        ].lower()
    )


# ============================================================
# 3. UNSUPPORTED END-TO-END PIPELINE
# ============================================================

def test_unsupported_pipeline():

    question = (
        "How does quantum computing work?"
    )

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "unsupported"

    assert plan.tasks == []

    execution = execute_capability_plan(
        plan
    )

    assert (
        execution["status"]
        == "unsupported"
    )

    response = compose_capability_response(
        plan,
        execution,
    )

    assert (
        response["status"]
        == "unsupported"
    )

    assert response["answer"]

    assert response["sections"] == []

    assert (
        response[
            "analytics_artifacts"
        ]
        == []
    )


# ============================================================
# 4. ANALYTICS-ONLY PIPELINE
#
# Verifies the generic pipeline is not limited
# to Hybrid plans.
# ============================================================

def test_analytics_only_pipeline():

    question = (
        "Who scored the most runs in IPL?"
    )

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "analytics"

    execution = execute_capability_plan(
        plan
    )

    assert execution["status"] == "success"

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"

    assert response["route"] == "analytics"

    assert response["answer"]

    assert response[
        "analytics_artifacts"
    ]


# ============================================================
# 5. KNOWLEDGE-ONLY PIPELINE
#
# Verifies the same orchestration pipeline
# works for Knowledge-only requests.
# ============================================================

def test_knowledge_only_pipeline():

    question = (
        "What is Powerplay?"
    )

    plan = create_capability_plan(
        question=question,
        conversation_context={},
    )

    assert plan.route == "knowledge"

    execution = execute_capability_plan(
        plan
    )

    assert execution["status"] == "success"

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"

    assert response["route"] == "knowledge"

    assert response["answer"]

    assert response[
        "knowledge_sources"
    ]


# ============================================================
# 6. PLANNER FAILURE SHOULD NOT REACH EXECUTION
# ============================================================

def test_empty_question_rejected():

    with pytest.raises(
        CapabilityPlannerError
    ):

        create_capability_plan(
            question=" ",
            conversation_context={},
        )