from typing import Any

from agent.capability_planner_models import (
    PlannedTask,
)

from knowledge_agent.knowledge_retriever import (
    KnowledgeRetriever,
)

from knowledge_agent.knowledge_agent import (
    generate_knowledge_answer,
)

from knowledge_agent.semantic_knowledge_service import (
    generate_semantic_knowledge_answer,
)


retriever = KnowledgeRetriever()


def execute_knowledge_task(
    task: PlannedTask,
    completed_tasks: dict[str, Any] | None = None,
):

    completed_tasks = (
        completed_tasks or {}
    )

    question = task.question.strip()

    if not question:

        return {
            "task_id": task.task_id,
            "capability": task.capability,
            "status": "failed",
            "question": task.question,
            "answer": None,
            "sources": [],
            "error": (
                "Knowledge task question "
                "cannot be empty."
            ),
        }

    try:

        # ====================================================
        # EXACT KNOWLEDGE
        # ====================================================

        knowledge_document = (
            retriever.find_document(
                question
            )
        )

        if knowledge_document:

            knowledge_content = (
                retriever.load_document(
                    question
                )
            )

            if knowledge_content:

                answer = (
                    generate_knowledge_answer(
                        question,
                        knowledge_content,
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
                        answer,

                    "retrieval_mode":
                        "exact",

                    "sources": [
                        {
                            "document":
                                knowledge_document
                        }
                    ],

                    "error":
                        None,
                }

        # ====================================================
        # SEMANTIC KNOWLEDGE FALLBACK
        # ====================================================

        semantic_response = (
            generate_semantic_knowledge_answer(
                question=question,
                top_k=3,
                threshold=0.65,
            )
        )

        answer = semantic_response.get(
            "answer"
        )

        sources = semantic_response.get(
            "sources",
            [],
        )

        if not sources:

            return {
                "task_id":
                    task.task_id,

                "capability":
                    task.capability,

                "status":
                    "no_match",

                "question":
                    question,

                "answer":
                    answer,

                "retrieval_mode":
                    "semantic",

                "sources":
                    [],

                "error":
                    None,
            }

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
                answer,

            "retrieval_mode":
                "semantic",

            "sources":
                sources,

            "error":
                None,
        }

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

            "retrieval_mode":
                None,

            "sources":
                [],

            "error":
                str(error),
        }