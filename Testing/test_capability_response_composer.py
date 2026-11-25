import pandas as pd
import pytest

from agent.capability_planner_models import (
    CapabilityPlan,
    PlannedTask,
)

from agent.capability_response_composer import (
    CapabilityResponseComposerError,
    compose_capability_response,
)


# ============================================================
# 1. KNOWLEDGE-ONLY RESPONSE
# ============================================================

def test_knowledge_only_response():

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

    execution = {
        "route": "knowledge",
        "status": "success",
        "task_results": {
            "task_1": {
                "task_id": "task_1",
                "capability": "knowledge_search",
                "status": "success",
                "question": "What is Powerplay?",
                "answer": (
                    "Powerplay is the opening phase "
                    "of an IPL innings."
                ),
                "sources": [
                    {
                        "document": "PowerPlay"
                    }
                ],
                "error": None,
            }
        },
        "unsupported_reason": None,
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"
    assert response["route"] == "knowledge"

    assert "Powerplay" in response["answer"]

    assert len(
        response["sections"]
    ) == 1

    assert response[
        "knowledge_sources"
    ]

    assert (
        response["analytics_artifacts"]
        == []
    )


# ============================================================
# 2. ANALYTICS-ONLY RESPONSE
# ============================================================

def test_analytics_only_response():

    dataframe = pd.DataFrame(
        {
            "player": ["V Kohli"],
            "total_runs": [9050],
        }
    )

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

    execution = {
        "route": "analytics",
        "status": "success",
        "task_results": {
            "task_1": {
                "task_id": "task_1",
                "capability": "analytics_query",
                "status": "success",
                "question": (
                    "Who scored the most runs in IPL?"
                ),
                "answer": (
                    "V Kohli is the highest "
                    "IPL run scorer."
                ),
                "sql": "SELECT ...",
                "result": dataframe,
                "context": {
                    "primary_entity": "V Kohli",
                    "player": "V Kohli",
                    "metric": "total_runs",
                },
                "error": None,
            }
        },
        "unsupported_reason": None,
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"
    assert response["route"] == "analytics"

    assert "V Kohli" in response["answer"]

    assert len(
        response["analytics_artifacts"]
    ) == 1

    artifact = response[
        "analytics_artifacts"
    ][0]

    assert artifact["sql"] == "SELECT ..."

    assert (
        artifact["result"]
        is dataframe
    )


# ============================================================
# 3. INDEPENDENT HYBRID RESPONSE
# ============================================================

def test_independent_hybrid_response():

    dataframe = pd.DataFrame(
        {
            "season": [2023, 2024],
            "runs": [350, 400],
        }
    )

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
                question="Tell me about MS Dhoni",
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

    execution = {
        "route": "hybrid",
        "status": "success",
        "task_results": {
            "task_1": {
                "task_id": "task_1",
                "capability": "knowledge_search",
                "status": "success",
                "question": "Tell me about MS Dhoni",
                "answer": (
                    "MS Dhoni is an IPL player "
                    "and long-time Chennai leader."
                ),
                "sources": [
                    {
                        "document": "ms_dhoni"
                    }
                ],
                "error": None,
            },
            "task_2": {
                "task_id": "task_2",
                "capability": "analytics_query",
                "status": "success",
                "question": (
                    "Show MS Dhoni's IPL "
                    "runs by season"
                ),
                "answer": (
                    "The season-by-season "
                    "analysis was completed."
                ),
                "sql": "SELECT season, runs ...",
                "result": dataframe,
                "context": {
                    "player": "MS Dhoni",
                    "metric": "total_runs",
                },
                "error": None,
            },
        },
        "unsupported_reason": None,
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"
    assert response["route"] == "hybrid"

    assert "MS Dhoni" in response["answer"]

    assert (
        "season-by-season"
        in response["answer"]
    )

    assert len(
        response["sections"]
    ) == 2

    assert len(
        response["analytics_artifacts"]
    ) == 1

    assert response[
        "knowledge_sources"
    ]


# ============================================================
# 4. DEPENDENT HYBRID RESPONSE
# ============================================================

def test_dependent_hybrid_response():

    dataframe = pd.DataFrame(
        {
            "player": ["V Kohli"],
            "total_runs": [9050],
        }
    )

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
                    "Tell me about "
                    "{{task_1.primary_entity}}"
                ),
                depends_on=["task_1"],
            ),
        ],
    )

    execution = {
        "route": "hybrid",
        "status": "success",
        "task_results": {
            "task_1": {
                "task_id": "task_1",
                "capability": "analytics_query",
                "status": "success",
                "question": (
                    "Find the highest IPL "
                    "run scorer"
                ),
                "answer": (
                    "V Kohli is the highest "
                    "IPL run scorer."
                ),
                "sql": "SELECT ...",
                "result": dataframe,
                "context": {
                    "primary_entity": "V Kohli",
                    "player": "V Kohli",
                },
                "error": None,
            },
            "task_2": {
                "task_id": "task_2",
                "capability": "knowledge_search",
                "status": "success",
                "question": "Tell me about V Kohli",
                "planned_question": (
                    "Tell me about "
                    "{{task_1.primary_entity}}"
                ),
                "resolved_question": (
                    "Tell me about V Kohli"
                ),
                "answer": (
                    "V Kohli is one of the "
                    "prominent IPL batters."
                ),
                "sources": [
                    {
                        "document": "virat_kohli"
                    }
                ],
                "error": None,
            },
        },
        "unsupported_reason": None,
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert response["status"] == "success"

    assert (
        "V Kohli is the highest"
        in response["answer"]
    )

    assert (
        "prominent IPL batters"
        in response["answer"]
    )

    assert len(
        response["sections"]
    ) == 2

    assert (
        response["sections"][1][
            "question"
        ]
        == "Tell me about V Kohli"
    )


# ============================================================
# 5. PARTIAL SUCCESS
# ============================================================

def test_partial_success_response():

    plan = CapabilityPlan(
        route="hybrid",
        original_question=(
            "Explain Powerplay and show "
            "the best Powerplay batters"
        ),
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

    execution = {
        "route": "hybrid",
        "status": "partial_success",
        "task_results": {
            "task_1": {
                "task_id": "task_1",
                "capability": "knowledge_search",
                "status": "success",
                "answer": (
                    "Powerplay is the opening "
                    "phase of an innings."
                ),
                "sources": [],
                "error": None,
            },
            "task_2": {
                "task_id": "task_2",
                "capability": "analytics_query",
                "status": "failed",
                "answer": None,
                "error": "Simulated analytics failure",
            },
        },
        "unsupported_reason": None,
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert (
        response["status"]
        == "partial_success"
    )

    assert "Powerplay" in response["answer"]

    assert (
        "could not be completed"
        in response["answer"]
    )

    assert len(
        response["sections"]
    ) == 2


# ============================================================
# 6. UNSUPPORTED RESPONSE
# ============================================================

def test_unsupported_response():

    plan = CapabilityPlan(
        route="unsupported",
        original_question=(
            "How does quantum computing work?"
        ),
        tasks=[],
        unsupported_reason=(
            "The request is outside the "
            "available IPL capabilities."
        ),
    )

    execution = {
        "route": "unsupported",
        "status": "unsupported",
        "task_results": {},
        "unsupported_reason": (
            "The request is outside the "
            "available IPL capabilities."
        ),
    }

    response = compose_capability_response(
        plan,
        execution,
    )

    assert (
        response["status"]
        == "unsupported"
    )

    assert (
        response["route"]
        == "unsupported"
    )

    assert (
        "outside"
        in response["answer"].lower()
    )

    assert response["sections"] == []

    assert (
        response["analytics_artifacts"]
        == []
    )


# ============================================================
# 7. ROUTE MISMATCH
# ============================================================

def test_route_mismatch_raises_error():

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

    execution = {
        "route": "analytics",
        "status": "success",
        "task_results": {},
    }

    with pytest.raises(
        CapabilityResponseComposerError
    ):

        compose_capability_response(
            plan,
            execution,
        )