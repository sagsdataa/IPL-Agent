from unittest.mock import patch

from agent.capability_planner_models import (
    CapabilityPlan,
    PlannedTask,
)

from agent.capability_executor import (
    execute_capability_plan,
)


# ============================================================
# 1. KNOWLEDGE-ONLY EXECUTION
# ============================================================

def test_knowledge_only_execution():

    plan = CapabilityPlan(
        route="knowledge",
        original_question="What is Powerplay?",
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="knowledge_search",
                question="What is Powerplay?",
            )
        ],
    )

    result = execute_capability_plan(
        plan
    )

    assert result["status"] == "success"
    assert result["total_tasks"] == 1
    assert result["successful_tasks"] == 1

    task_result = result[
        "task_results"
    ]["task_1"]

    assert task_result["status"] == "success"
    assert task_result["answer"]


# ============================================================
# 2. ANALYTICS-ONLY EXECUTION
# ============================================================

def test_analytics_only_execution():

    plan = CapabilityPlan(
        route="analytics",
        original_question=(
            "Who scored the most runs in IPL?"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="analytics_query",
                question=(
                    "Who scored the most runs in IPL?"
                ),
            )
        ],
    )

    result = execute_capability_plan(
        plan
    )

    assert result["status"] == "success"
    assert result["successful_tasks"] == 1

    task_result = result[
        "task_results"
    ]["task_1"]

    assert task_result["status"] == "success"
    assert task_result["sql"]
    assert task_result["result"] is not None
    assert task_result["answer"]


# ============================================================
# 3. INDEPENDENT HYBRID EXECUTION
# ============================================================

def test_independent_hybrid_execution():

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

    result = execute_capability_plan(
        plan
    )

    assert result["status"] == "success"

    assert result["total_tasks"] == 2
    assert result["successful_tasks"] == 2

    assert (
        result["task_results"]
        ["task_1"]["status"]
        == "success"
    )

    assert (
        result["task_results"]
        ["task_2"]["status"]
        == "success"
    )


# ============================================================
# 4. FAILED DEPENDENCY BLOCKS NEXT TASK
# ============================================================

def test_failed_dependency_blocks_task():

    plan = CapabilityPlan(
        route="hybrid",
        original_question=(
            "Find the highest IPL run scorer "
            "and tell me about that player"
        ),
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="analytics_query",
                question=(
                    "Find the highest IPL "
                    "run scorer"
                ),
            ),
            PlannedTask(
                task_id="task_2",
                capability="knowledge_search",
                question=(
                    "Tell me about the player "
                    "identified in task_1"
                ),
                depends_on=[
                    "task_1"
                ],
            ),
        ],
    )

    fake_failure = {
        "task_id": "task_1",
        "capability": "analytics_query",
        "status": "failed",
        "question": (
            "Find the highest IPL run scorer"
        ),
        "answer": None,
        "error": "Simulated failure",
    }

    with patch(
        "agent.capability_executor."
        "execute_task"
    ) as mock_execute:

        mock_execute.return_value = (
            fake_failure
        )

        result = execute_capability_plan(
            plan
        )

    assert (
        result["task_results"]
        ["task_1"]["status"]
        == "failed"
    )

    assert (
        result["task_results"]
        ["task_2"]["status"]
        == "blocked"
    )

    assert result["failed_tasks"] == 1
    assert result["blocked_tasks"] == 1
    assert result["status"] == "failed"


# ============================================================
# 5. UNSUPPORTED PLAN
# ============================================================

def test_unsupported_plan():

    plan = CapabilityPlan(
        route="unsupported",
        original_question=(
            "How does quantum computing work?"
        ),
        tasks=[],
        unsupported_reason=(
            "Request is outside the available "
            "IPL capabilities."
        ),
    )

    result = execute_capability_plan(
        plan
    )

    assert result["status"] == "unsupported"
    assert result["total_tasks"] == 0

    assert result["successful_tasks"] == 0
    assert result["failed_tasks"] == 0
    assert result["blocked_tasks"] == 0

    assert result["task_results"] == {}

    assert result[
        "unsupported_reason"
    ]


# ============================================================
# 6. PARTIAL SUCCESS
# ============================================================

def test_partial_success():

    plan = CapabilityPlan(
        route="hybrid",
        original_question="Hybrid test",
        tasks=[
            PlannedTask(
                task_id="task_1",
                capability="knowledge_search",
                question="Explain Powerplay",
            ),
            PlannedTask(
                task_id="task_2",
                capability="analytics_query",
                question=(
                    "Show the best "
                    "Powerplay batters"
                ),
            ),
        ],
    )

    fake_results = {
        "task_1": {
            "task_id": "task_1",
            "capability": "knowledge_search",
            "status": "success",
            "question": "Explain Powerplay",
            "answer": "Powerplay explanation",
            "error": None,
        },
        "task_2": {
            "task_id": "task_2",
            "capability": "analytics_query",
            "status": "failed",
            "question": (
                "Show the best "
                "Powerplay batters"
            ),
            "answer": None,
            "error": "Simulated failure",
        },
    }

    def fake_execute(
        task,
        completed_tasks,
    ):
        return fake_results[
            task.task_id
        ]

    with patch(
        "agent.capability_executor."
        "execute_task",
        side_effect=fake_execute,
    ):

        result = execute_capability_plan(
            plan
        )

    assert (
        result["status"]
        == "partial_success"
    )

    assert result["successful_tasks"] == 1
    assert result["failed_tasks"] == 1