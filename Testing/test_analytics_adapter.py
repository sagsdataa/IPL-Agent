from unittest.mock import patch

import pandas as pd

from agent.capability_planner_models import (
    PlannedTask,
)

from agent.capability_adapters.analytics_adapter import (
    execute_analytics_task,
)


# ============================================================
# 1. BASIC ANALYTICS TASK
# ============================================================

def test_basic_analytics_task():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question="Who scored the most runs in IPL?",
    )

    result = execute_analytics_task(
        task
    )

    assert result["task_id"] == "task_1"
    assert result["capability"] == "analytics_query"
    assert result["status"] == "success"

    assert result["question"]
    assert result["answer"]
    assert result["sql"]

    assert result["result"] is not None
    assert not result["result"].empty

    assert result["context"] is not None
    assert result["error"] is None


# ============================================================
# 2. SEASON ANALYTICS TASK
# ============================================================

def test_season_analytics_task():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question="Which team won IPL 2015?",
    )

    result = execute_analytics_task(
        task
    )

    assert result["status"] == "success"

    assert result["sql"]

    assert result["result"] is not None
    assert not result["result"].empty

    assert result["answer"]
    assert result["context"]

    assert result["error"] is None


# ============================================================
# 3. POWERPLAY ANALYTICS TASK
# ============================================================

def test_powerplay_analytics_task():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question="Who is the best Powerplay batter?",
    )

    result = execute_analytics_task(
        task
    )

    assert result["status"] == "success"

    assert result["sql"]

    assert result["result"] is not None
    assert not result["result"].empty

    assert result["answer"]
    assert result["context"]

    assert result["error"] is None


# ============================================================
# 4. EMPTY QUESTION
# ============================================================

def test_empty_analytics_question():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question=" ",
    )

    result = execute_analytics_task(
        task
    )

    assert result["task_id"] == "task_1"
    assert result["capability"] == "analytics_query"

    assert result["status"] == "failed"

    assert result["answer"] is None
    assert result["sql"] is None
    assert result["result"] is None
    assert result["context"] is None

    assert result["error"] is not None


# ============================================================
# 5. ANALYTICS SERVICE FAILURE
# ============================================================

def test_analytics_service_failure():

    task = PlannedTask(
        task_id="task_1",
        capability="analytics_query",
        question="Who scored the most runs in IPL?",
    )

    with patch(
        "agent.capability_adapters.analytics_adapter."
        "run_analytics_query"
    ) as mock_query:

        mock_query.side_effect = RuntimeError(
            "Simulated analytics failure"
        )

        result = execute_analytics_task(
            task
        )

    assert result["status"] == "failed"

    assert result["answer"] is None
    assert result["sql"] is None
    assert result["result"] is None
    assert result["context"] is None

    assert (
        result["error"]
        == "Simulated analytics failure"
    )


# ============================================================
# 6. STANDARD OUTPUT CONTRACT
# ============================================================

def test_analytics_adapter_output_contract():

    fake_result = pd.DataFrame(
        {
            "player": ["V Kohli"],
            "total_runs": [8000],
        }
    )

    fake_context = {
        "intent": "ranking",
        "metric": "total_runs",
        "player": "V Kohli",
        "primary_entity": "V Kohli",
    }

    task = PlannedTask(
        task_id="task_99",
        capability="analytics_query",
        question="Who scored the most runs in IPL?",
    )

    with patch(
        "agent.capability_adapters.analytics_adapter."
        "run_analytics_query"
    ) as mock_query:

        mock_query.return_value = {
            "question":
                task.question,

            "sql":
                "SELECT ...",

            "result":
                fake_result,

            "answer":
                "V Kohli is the leading run scorer.",

            "context":
                fake_context,
        }

        result = execute_analytics_task(
            task
        )

    expected_keys = {
        "task_id",
        "capability",
        "status",
        "question",
        "answer",
        "sql",
        "result",
        "context",
        "error",
    }

    assert set(result.keys()) == expected_keys

    assert result["task_id"] == "task_99"
    assert result["capability"] == "analytics_query"
    assert result["status"] == "success"
    assert result["error"] is None