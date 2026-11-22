from agent.capability_planner_models import (
    PlannedTask,
)

from agent.capability_adapters.knowledge_adapter import (
    execute_knowledge_task,
)


def test_exact_knowledge():

    task = PlannedTask(
        task_id="task_1",
        capability="knowledge_search",
        question="What is Powerplay?",
    )

    result = execute_knowledge_task(
        task
    )

    assert result["status"] == "success"
    assert result["retrieval_mode"] == "exact"
    assert result["answer"]


def test_semantic_knowledge():

    task = PlannedTask(
        task_id="task_1",
        capability="knowledge_search",
        question=(
            "What restrictions apply "
            "during the opening overs?"
        ),
    )

    result = execute_knowledge_task(
        task
    )

    assert result["status"] == "success"
    assert result["retrieval_mode"] == "semantic"
    assert result["answer"]
    assert result["sources"]


def test_missing_player_knowledge():

    task = PlannedTask(
        task_id="task_1",
        capability="knowledge_search",
        question=(
            "Tell me about Ruturaj "
            "Gaikwad's playing style"
        ),
    )

    result = execute_knowledge_task(
        task
    )

    assert result["status"] == "no_match"


def test_empty_question():

    task = PlannedTask(
        task_id="task_1",
        capability="knowledge_search",
        question=" ",
    )

    result = execute_knowledge_task(
        task
    )

    assert result["status"] == "failed"