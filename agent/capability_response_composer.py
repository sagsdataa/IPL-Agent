from typing import Any

from agent.capability_planner_models import (
    CapabilityPlan,
)


# ============================================================
# TYPES
# ============================================================

TaskResult = dict[str, Any]
ExecutionResult = dict[str, Any]
ComposedResponse = dict[str, Any]


# ============================================================
# COMPOSER ERROR
# ============================================================

class CapabilityResponseComposerError(
    RuntimeError
):
    pass


# ============================================================
# CAPABILITY LABELS
# ============================================================

CAPABILITY_LABELS = {
    "knowledge_search":
        "IPL Knowledge",

    "analytics_query":
        "IPL Analysis",
}


# ============================================================
# STATUS LABELS
# ============================================================

STATUS_MESSAGES = {
    "failed": (
        "This part of the request could not "
        "be completed."
    ),

    "blocked": (
        "This part of the request could not "
        "run because a required earlier task "
        "did not complete successfully."
    ),

    "no_match": (
        "The available IPL knowledge does not "
        "contain enough grounded information "
        "to answer this part of the request."
    ),
}


# ============================================================
# NORMALIZE ANSWER
# ============================================================

def normalize_answer(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# GET TASK RESULT
# ============================================================

def get_task_result(
    execution_result: ExecutionResult,
    task_id: str,
) -> TaskResult | None:

    task_results = execution_result.get(
        "task_results",
        {},
    )

    if not isinstance(
        task_results,
        dict,
    ):
        return None

    return task_results.get(
        task_id
    )


# ============================================================
# BUILD SECTION TITLE
# ============================================================

def build_section_title(
    capability: str,
    task_question: str,
    task_index: int,
) -> str:

    capability_label = (
        CAPABILITY_LABELS.get(
            capability,
            "Result",
        )
    )

    # For plans containing one task, the general
    # capability label is sufficient.
    if task_index == 1:

        return capability_label

    return (
        f"{capability_label} "
        f"{task_index}"
    )


# ============================================================
# BUILD SUCCESS SECTION
# ============================================================

def build_success_section(
    task,
    task_result: TaskResult,
    task_index: int,
) -> dict[str, Any]:

    answer = normalize_answer(
        task_result.get("answer")
    )

    if not answer:

        answer = (
            "The capability completed successfully, "
            "but it did not return a user-facing answer."
        )

    return {
        "task_id":
            task.task_id,

        "capability":
            task.capability,

        "status":
            "success",

        "title":
            build_section_title(
                task.capability,
                task.question,
                task_index,
            ),

        "question":
            task_result.get(
                "resolved_question"
            )
            or task_result.get(
                "question"
            )
            or task.question,

        "content":
            answer,
    }


# ============================================================
# BUILD UNSUCCESSFUL SECTION
# ============================================================

def build_unsuccessful_section(
    task,
    task_result: TaskResult,
    task_index: int,
) -> dict[str, Any]:

    status = task_result.get(
        "status",
        "failed",
    )

    answer = normalize_answer(
        task_result.get("answer")
    )

    if not answer:

        answer = STATUS_MESSAGES.get(
            status,
            STATUS_MESSAGES["failed"],
        )

    return {
        "task_id":
            task.task_id,

        "capability":
            task.capability,

        "status":
            status,

        "title":
            build_section_title(
                task.capability,
                task.question,
                task_index,
            ),

        "question":
            task_result.get(
                "resolved_question"
            )
            or task_result.get(
                "question"
            )
            or task.question,

        "content":
            answer,

        "error":
            task_result.get(
                "error"
            ),
    }


# ============================================================
# BUILD RESPONSE SECTIONS
# ============================================================

def build_response_sections(
    plan: CapabilityPlan,
    execution_result: ExecutionResult,
) -> list[dict[str, Any]]:

    sections = []

    for task_index, task in enumerate(
        plan.tasks,
        start=1,
    ):

        task_result = get_task_result(
            execution_result,
            task.task_id,
        )

        if task_result is None:

            sections.append(
                {
                    "task_id":
                        task.task_id,

                    "capability":
                        task.capability,

                    "status":
                        "failed",

                    "title":
                        build_section_title(
                            task.capability,
                            task.question,
                            task_index,
                        ),

                    "question":
                        task.question,

                    "content": (
                        "No execution result was "
                        "returned for this task."
                    ),

                    "error": (
                        "Missing task result."
                    ),
                }
            )

            continue

        if (
            task_result.get("status")
            == "success"
        ):

            section = (
                build_success_section(
                    task,
                    task_result,
                    task_index,
                )
            )

        else:

            section = (
                build_unsuccessful_section(
                    task,
                    task_result,
                    task_index,
                )
            )

        sections.append(
            section
        )

    return sections


# ============================================================
# RENDER MARKDOWN
# ============================================================

def render_sections_as_markdown(
    sections: list[dict[str, Any]],
    include_failed_sections: bool = True,
) -> str:

    rendered_sections = []

    for section in sections:

        status = section.get(
            "status"
        )

        if (
            not include_failed_sections
            and status != "success"
        ):

            continue

        title = normalize_answer(
            section.get("title")
        )

        content = normalize_answer(
            section.get("content")
        )

        if not content:
            continue

        rendered_sections.append(
            f"### {title}\n\n{content}"
        )

    return "\n\n".join(
        rendered_sections
    ).strip()


# ============================================================
# COLLECT ANALYTICS ARTIFACTS
# ============================================================

def collect_analytics_artifacts(
    plan: CapabilityPlan,
    execution_result: ExecutionResult,
) -> list[dict[str, Any]]:

    artifacts = []

    for task in plan.tasks:

        if (
            task.capability
            != "analytics_query"
        ):
            continue

        task_result = get_task_result(
            execution_result,
            task.task_id,
        )

        if not task_result:
            continue

        if (
            task_result.get("status")
            != "success"
        ):
            continue

        artifacts.append(
            {
                "task_id":
                    task.task_id,

                "question":
                    task_result.get(
                        "resolved_question"
                    )
                    or task_result.get(
                        "question"
                    )
                    or task.question,

                "sql":
                    task_result.get(
                        "sql"
                    ),

                "result":
                    task_result.get(
                        "result"
                    ),

                "context":
                    task_result.get(
                        "context"
                    ),
            }
        )

    return artifacts


# ============================================================
# COLLECT KNOWLEDGE SOURCES
# ============================================================

def collect_knowledge_sources(
    plan: CapabilityPlan,
    execution_result: ExecutionResult,
) -> list[dict[str, Any]]:

    sources = []

    for task in plan.tasks:

        if (
            task.capability
            != "knowledge_search"
        ):
            continue

        task_result = get_task_result(
            execution_result,
            task.task_id,
        )

        if not task_result:
            continue

        task_sources = task_result.get(
            "sources",
            [],
        )

        if not isinstance(
            task_sources,
            list,
        ):
            continue

        for source in task_sources:

            if source not in sources:

                sources.append(
                    source
                )

    return sources


# ============================================================
# COMPOSE UNSUPPORTED RESPONSE
# ============================================================

def compose_unsupported_response(
    plan: CapabilityPlan,
    execution_result: ExecutionResult,
) -> ComposedResponse:

    reason = (
        execution_result.get(
            "unsupported_reason"
        )
        or plan.unsupported_reason
        or (
            "The request cannot be completed "
            "using the available IPL capabilities."
        )
    )

    return {
        "status":
            "unsupported",

        "route":
            plan.route,

        "original_question":
            plan.original_question,

        "answer":
            reason,

        "sections":
            [],

        "analytics_artifacts":
            [],

        "knowledge_sources":
            [],

        "execution_summary":
            execution_result,
    }


# ============================================================
# COMPOSE CAPABILITY RESPONSE
# ============================================================

def compose_capability_response(
    plan: CapabilityPlan,
    execution_result: ExecutionResult,
) -> ComposedResponse:

    if not isinstance(
        plan,
        CapabilityPlan,
    ):

        raise CapabilityResponseComposerError(
            "A valid CapabilityPlan is required."
        )

    if not isinstance(
        execution_result,
        dict,
    ):

        raise CapabilityResponseComposerError(
            "Execution result must be a dictionary."
        )

    execution_route = (
        execution_result.get("route")
    )

    if (
        execution_route
        and execution_route
        != plan.route
    ):

        raise CapabilityResponseComposerError(
            "Execution route does not match "
            "the capability plan route."
        )

    if (
        plan.route == "unsupported"
        or execution_result.get("status")
        == "unsupported"
    ):

        return compose_unsupported_response(
            plan,
            execution_result,
        )

    sections = build_response_sections(
        plan,
        execution_result,
    )

    answer = render_sections_as_markdown(
        sections,
        include_failed_sections=True,
    )

    if not answer:

        answer = (
            "The IPL request was processed, "
            "but no user-facing answer was produced."
        )

    return {
        "status":
            execution_result.get(
                "status",
                "failed",
            ),

        "route":
            plan.route,

        "original_question":
            plan.original_question,

        "answer":
            answer,

        "sections":
            sections,

        "analytics_artifacts":
            collect_analytics_artifacts(
                plan,
                execution_result,
            ),

        "knowledge_sources":
            collect_knowledge_sources(
                plan,
                execution_result,
            ),

        "execution_summary":
            execution_result,
    }