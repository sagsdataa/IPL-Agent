from typing import Any, Callable

from agent.capability_planner_models import (
    CapabilityPlan,
    PlannedTask,
)

from agent.capability_plan_validator import (
    validate_capability_plan,
)

from agent.capability_adapters.knowledge_adapter import (
    execute_knowledge_task,
)

from agent.capability_adapters.analytics_adapter import (
    execute_analytics_task,
)

from agent.dependency_result_resolver import (
    DependencyResolutionError,
    resolve_dependent_task,
)


# ============================================================
# TYPES
# ============================================================

TaskResult = dict[str, Any]

CapabilityExecutor = Callable[
    [
        PlannedTask,
        dict[str, TaskResult],
    ],
    TaskResult,
]


# ============================================================
# EXECUTION ERROR
# ============================================================

class CapabilityExecutionError(
    RuntimeError
):
    pass


# ============================================================
# CAPABILITY EXECUTOR REGISTRY
# ============================================================

EXECUTOR_REGISTRY: dict[
    str,
    CapabilityExecutor,
] = {
    "knowledge_search":
        execute_knowledge_task,

    "analytics_query":
        execute_analytics_task,
}


# ============================================================
# EXECUTOR LOOKUP
# ============================================================

def get_capability_executor(
    capability_name: str,
) -> CapabilityExecutor:

    executor = EXECUTOR_REGISTRY.get(
        capability_name
    )

    if executor is None:

        raise CapabilityExecutionError(
            "No executor is registered for "
            f"capability: {capability_name}"
        )

    return executor


# ============================================================
# DEPENDENCY COMPLETION CHECK
# ============================================================

def dependencies_completed(
    task: PlannedTask,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> bool:

    return all(
        dependency_id
        in completed_tasks
        for dependency_id
        in task.depends_on
    )


# ============================================================
# DEPENDENCY SUCCESS CHECK
# ============================================================

def dependencies_successful(
    task: PlannedTask,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> bool:

    for dependency_id in task.depends_on:

        dependency_result = (
            completed_tasks.get(
                dependency_id
            )
        )

        if dependency_result is None:
            return False

        if (
            dependency_result.get(
                "status"
            )
            != "success"
        ):

            return False

    return True


# ============================================================
# BLOCKED TASK RESULT
# ============================================================

def create_blocked_result(
    task: PlannedTask,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> TaskResult:

    failed_dependencies = []

    for dependency_id in task.depends_on:

        dependency_result = (
            completed_tasks.get(
                dependency_id
            )
        )

        if dependency_result is None:

            failed_dependencies.append(
                dependency_id
            )

            continue

        if (
            dependency_result.get(
                "status"
            )
            != "success"
        ):

            failed_dependencies.append(
                dependency_id
            )

    return {
        "task_id":
            task.task_id,

        "capability":
            task.capability,

        "status":
            "blocked",

        "question":
            task.question,

        "answer":
            None,

        "error": (
            "Task was blocked because one or "
            "more dependencies did not complete "
            "successfully."
        ),

        "failed_dependencies":
            failed_dependencies,
    }


# ============================================================
# DEPENDENCY-RESOLUTION FAILURE RESULT
# ============================================================

def create_resolution_failure_result(
    task: PlannedTask,
    error: Exception,
) -> TaskResult:

    return {
        "task_id":
            task.task_id,

        "capability":
            task.capability,

        "status":
            "failed",

        "question":
            task.question,

        "answer":
            None,

        "error":
            str(error),

        "error_type":
            "dependency_resolution",
    }


# ============================================================
# NORMALIZE ADAPTER RESULT
# ============================================================

def normalize_task_result(
    task: PlannedTask,
    result: TaskResult,
) -> TaskResult:

    normalized = dict(
        result or {}
    )

    normalized.setdefault(
        "task_id",
        task.task_id,
    )

    normalized.setdefault(
        "capability",
        task.capability,
    )

    normalized.setdefault(
        "question",
        task.question,
    )

    normalized.setdefault(
        "status",
        "failed",
    )

    normalized.setdefault(
        "answer",
        None,
    )

    normalized.setdefault(
        "error",
        None,
    )

    return normalized


# ============================================================
# EXECUTE ONE TASK
# ============================================================

def execute_task(
    task: PlannedTask,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> TaskResult:

    executor = get_capability_executor(
        task.capability
    )

    try:

        result = executor(
            task=task,
            completed_tasks=completed_tasks,
        )

        return normalize_task_result(
            task,
            result,
        )

    except Exception as error:

        return {
            "task_id":
                task.task_id,

            "capability":
                task.capability,

            "status":
                "failed",

            "question":
                task.question,

            "answer":
                None,

            "error":
                str(error),

            "error_type":
                "capability_execution",
        }


# ============================================================
# EXECUTION SUMMARY
# ============================================================

def build_execution_summary(
    plan: CapabilityPlan,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> dict[str, Any]:

    task_results = [
        completed_tasks[
            task.task_id
        ]
        for task in plan.tasks
        if task.task_id
        in completed_tasks
    ]

    successful_count = sum(
        1
        for result in task_results
        if (
            result.get("status")
            == "success"
        )
    )

    no_match_count = sum(
        1
        for result in task_results
        if (
            result.get("status")
            == "no_match"
        )
    )

    failed_count = sum(
        1
        for result in task_results
        if (
            result.get("status")
            == "failed"
        )
    )

    blocked_count = sum(
        1
        for result in task_results
        if (
            result.get("status")
            == "blocked"
        )
    )

    total_tasks = len(
        plan.tasks
    )

    completed_count = len(
        task_results
    )

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    if total_tasks == 0:

        if plan.route == "unsupported":

            overall_status = (
                "unsupported"
            )

        else:

            overall_status = (
                "completed"
            )

    elif (
        successful_count
        == total_tasks
    ):

        overall_status = (
            "success"
        )

    elif successful_count > 0:

        overall_status = (
            "partial_success"
        )

    elif (
        no_match_count
        == total_tasks
    ):

        overall_status = (
            "no_match"
        )

    else:

        overall_status = (
            "failed"
        )

    return {
        "route":
            plan.route,

        "original_question":
            plan.original_question,

        "status":
            overall_status,

        "total_tasks":
            total_tasks,

        "completed_tasks":
            completed_count,

        "successful_tasks":
            successful_count,

        "no_match_tasks":
            no_match_count,

        "failed_tasks":
            failed_count,

        "blocked_tasks":
            blocked_count,

        "task_results":
            completed_tasks,

        "unsupported_reason":
            plan.unsupported_reason,
    }


# ============================================================
# EXECUTE COMPLETE PLAN
# ============================================================

def execute_capability_plan(
    plan: CapabilityPlan,
) -> dict[str, Any]:

    # Validate again immediately before execution.
    # The executor must not trust an unvalidated plan.
    validate_capability_plan(
        plan
    )

    # Unsupported requests have no executable tasks.
    if plan.route == "unsupported":

        return build_execution_summary(
            plan=plan,
            completed_tasks={},
        )

    pending_tasks = {
        task.task_id: task
        for task in plan.tasks
    }

    completed_tasks: dict[
        str,
        TaskResult,
    ] = {}

    while pending_tasks:

        # A task becomes executable only after all
        # dependency task IDs have completed.
        executable_tasks = [
            task
            for task in pending_tasks.values()
            if dependencies_completed(
                task,
                completed_tasks,
            )
        ]

        if not executable_tasks:

            unresolved_tasks = list(
                pending_tasks.keys()
            )

            raise CapabilityExecutionError(
                "No executable tasks remain. "
                "The plan may contain unresolved "
                "or circular dependencies. "
                f"Pending tasks: "
                f"{unresolved_tasks}"
            )

        for task in executable_tasks:

            # ------------------------------------------------
            # DEPENDENCY FAILURE
            # ------------------------------------------------

            if not dependencies_successful(
                task,
                completed_tasks,
            ):

                task_result = (
                    create_blocked_result(
                        task,
                        completed_tasks,
                    )
                )

            # ------------------------------------------------
            # RESOLVE AND EXECUTE TASK
            # ------------------------------------------------

            else:

                try:

                    # Independent tasks are returned unchanged.
                    # Dependent tasks have placeholders such as
                    # {{task_1.primary_entity}} resolved here.
                    executable_task = (
                        resolve_dependent_task(
                            task,
                            completed_tasks,
                        )
                    )

                    task_result = execute_task(
                        executable_task,
                        completed_tasks,
                    )

                    # Preserve the original planned question
                    # for traceability when resolution changed
                    # the executable task question.
                    if (
                        executable_task.question
                        != task.question
                    ):

                        task_result[
                            "planned_question"
                        ] = task.question

                        task_result[
                            "resolved_question"
                        ] = (
                            executable_task.question
                        )

                except (
                    DependencyResolutionError
                ) as error:

                    task_result = (
                        create_resolution_failure_result(
                            task,
                            error,
                        )
                    )

            # ------------------------------------------------
            # STORE RESULT
            # ------------------------------------------------

            completed_tasks[
                task.task_id
            ] = task_result

            del pending_tasks[
                task.task_id
            ]

    return build_execution_summary(
        plan=plan,
        completed_tasks=completed_tasks,
    )