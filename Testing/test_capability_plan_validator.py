import pytest

from agent.capability_planner_models import (
    CapabilityPlan,
    PlannedTask,
)

from agent.capability_plan_validator import (
    CapabilityPlanValidationError,
    validate_capability_plan,
)


def test_valid_knowledge_plan():

    plan = CapabilityPlan(
        route="knowledge",
        original_question=(
            "What is Powerplay?"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="knowledge_search",
                question=(
                    "What is Powerplay?"
                ),
            )
        ],
    )

    assert (
        validate_capability_plan(plan)
        is True
    )


def test_valid_analytics_plan():

    plan = CapabilityPlan(
        route="analytics",
        original_question=(
            "Who scored the most IPL runs?"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="analytics_query",
                question=(
                    "Who scored the most IPL runs?"
                ),
            )
        ],
    )

    assert (
        validate_capability_plan(plan)
        is True
    )


def test_valid_hybrid_plan():

    plan = CapabilityPlan(
        route="hybrid",
        original_question=(
            "Tell me about MS Dhoni "
            "and show his runs by season"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="knowledge_search",
                question=(
                    "Tell me about MS Dhoni"
                ),
            ),
            PlannedTask(
                task_id="task_2",
                capability="analytics_query",
                question=(
                    "Show MS Dhoni's IPL "
                    "runs by season"
                ),
            ),
        ],
    )

    assert (
        validate_capability_plan(plan)
        is True
    )


def test_invalid_hybrid_with_one_capability():

    plan = CapabilityPlan(
        route="hybrid",
        original_question=(
            "Tell me about MS Dhoni"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="knowledge_search",
                question=(
                    "Tell me about MS Dhoni"
                ),
            )
        ],
    )

    with pytest.raises(
        CapabilityPlanValidationError
    ):

        validate_capability_plan(
            plan
        )


def test_invalid_dependency():

    plan = CapabilityPlan(
        route="hybrid",
        original_question="Test",
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="analytics_query",
                question="Find player",
            ),
            PlannedTask(
                task_id="task_2",
                capability="knowledge_search",
                question="Find profile",
                depends_on=[
                    "task_99"
                ],
            ),
        ],
    )

    with pytest.raises(
        CapabilityPlanValidationError
    ):

        validate_capability_plan(
            plan
        )


def test_circular_dependency():

    plan = CapabilityPlan(
        route="hybrid",
        original_question="Test",
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="analytics_query",
                question="Task 1",
                depends_on=[
                    "task_2"
                ],
            ),
            PlannedTask(
                task_id="task_2",
                capability="knowledge_search",
                question="Task 2",
                depends_on=[
                    "task_1"
                ],
            ),
        ],
    )

    with pytest.raises(
        CapabilityPlanValidationError
    ):

        validate_capability_plan(
            plan
        )