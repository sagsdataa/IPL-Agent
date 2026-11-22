import re
from copy import deepcopy
from typing import Any

import pandas as pd

from agent.capability_planner_models import (
    PlannedTask,
)


# ============================================================
# TYPES
# ============================================================

TaskResult = dict[str, Any]


# ============================================================
# RESOLUTION ERROR
# ============================================================

class DependencyResolutionError(
    RuntimeError
):
    pass


# ============================================================
# PLACEHOLDER PATTERN
#
# Examples:
# {{task_1.primary_entity}}
# {{task_1.context.player}}
# {{task_1.result.player}}
# ============================================================

PLACEHOLDER_PATTERN = re.compile(
    r"\{\{\s*"
    r"(?P<task_id>[A-Za-z0-9_-]+)"
    r"\."
    r"(?P<field_path>[A-Za-z0-9_.-]+)"
    r"\s*\}\}"
)


# ============================================================
# SIMPLE VALUE CHECK
# ============================================================

def is_usable_value(
    value: Any,
) -> bool:

    if value is None:
        return False

    if isinstance(value, str):

        return bool(
            value.strip()
        )

    return True


# ============================================================
# GET NESTED VALUE
# ============================================================

def get_nested_value(
    source: Any,
    field_path: str,
) -> Any:

    current = source

    for field_name in field_path.split("."):

        if isinstance(current, dict):

            if field_name not in current:
                return None

            current = current[
                field_name
            ]

        else:

            return None

    return current


# ============================================================
# EXTRACT VALUE FROM DATAFRAME
# ============================================================

def get_dataframe_value(
    dataframe: pd.DataFrame,
    field_name: str,
) -> Any:

    if dataframe is None:
        return None

    if dataframe.empty:
        return None

    if field_name not in dataframe.columns:
        return None

    value = dataframe.iloc[0][
        field_name
    ]

    if pd.isna(value):
        return None

    return value


# ============================================================
# ENTITY FIELD ALIASES
#
# These are generic output fields, not question-specific rules.
# ============================================================

ENTITY_FIELD_ALIASES = {
    "primary_entity": (
        "primary_entity",
        "player",
        "team",
        "winner",
        "batter",
        "bowler",
        "fielder",
        "venue",
    ),

    "player": (
        "player",
        "batter",
        "bowler",
        "fielder",
        "primary_entity",
    ),

    "team": (
        "team",
        "winner",
        "batting_team",
        "bowling_team",
        "primary_entity",
    ),

    "venue": (
        "venue",
        "primary_entity",
    ),
}


# ============================================================
# RESOLVE VALUE FROM ONE TASK RESULT
# ============================================================

def resolve_task_result_value(
    task_result: TaskResult,
    field_path: str,
) -> Any:

    if not task_result:

        return None

    # --------------------------------------------------------
    # 1. Explicit nested path
    #
    # Examples:
    # context.player
    # context.primary_entity
    # --------------------------------------------------------

    if "." in field_path:

        value = get_nested_value(
            task_result,
            field_path,
        )

        if is_usable_value(value):
            return value

    # --------------------------------------------------------
    # 2. Top-level task-result field
    # --------------------------------------------------------

    direct_value = task_result.get(
        field_path
    )

    if is_usable_value(
        direct_value
    ):

        return direct_value

    # --------------------------------------------------------
    # 3. Context field
    # --------------------------------------------------------

    context = task_result.get(
        "context"
    )

    if isinstance(context, dict):

        context_value = context.get(
            field_path
        )

        if is_usable_value(
            context_value
        ):

            return context_value

    # --------------------------------------------------------
    # 4. DataFrame field
    # --------------------------------------------------------

    result = task_result.get(
        "result"
    )

    if isinstance(
        result,
        pd.DataFrame,
    ):

        dataframe_value = (
            get_dataframe_value(
                result,
                field_path,
            )
        )

        if is_usable_value(
            dataframe_value
        ):

            return dataframe_value

    # --------------------------------------------------------
    # 5. Generic entity aliases
    # --------------------------------------------------------

    aliases = ENTITY_FIELD_ALIASES.get(
        field_path,
        (),
    )

    for alias in aliases:

        if isinstance(context, dict):

            context_value = context.get(
                alias
            )

            if is_usable_value(
                context_value
            ):

                return context_value

        if isinstance(
            result,
            pd.DataFrame,
        ):

            dataframe_value = (
                get_dataframe_value(
                    result,
                    alias,
                )
            )

            if is_usable_value(
                dataframe_value
            ):

                return dataframe_value

    return None


# ============================================================
# RESOLVE PLACEHOLDER
# ============================================================

def resolve_placeholder(
    match: re.Match,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> str:

    task_id = match.group(
        "task_id"
    )

    field_path = match.group(
        "field_path"
    )

    task_result = completed_tasks.get(
        task_id
    )

    if task_result is None:

        raise DependencyResolutionError(
            f"Dependency result not found: "
            f"{task_id}"
        )

    if (
        task_result.get("status")
        != "success"
    ):

        raise DependencyResolutionError(
            f"Dependency task {task_id} "
            f"did not complete successfully."
        )

    value = resolve_task_result_value(
        task_result,
        field_path,
    )

    if not is_usable_value(value):

        raise DependencyResolutionError(
            f"Unable to resolve "
            f"{{{{{task_id}.{field_path}}}}} "
            f"from dependency output."
        )

    return str(value)


# ============================================================
# RESOLVE QUESTION
# ============================================================

def resolve_dependency_question(
    question: str,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> str:

    if not question:
        return ""

    resolved_question = (
        PLACEHOLDER_PATTERN.sub(
            lambda match: resolve_placeholder(
                match,
                completed_tasks,
            ),
            question,
        )
    )

    unresolved_placeholders = (
        PLACEHOLDER_PATTERN.findall(
            resolved_question
        )
    )

    if unresolved_placeholders:

        raise DependencyResolutionError(
            "Dependent task question still "
            "contains unresolved placeholders."
        )

    return resolved_question.strip()


# ============================================================
# RESOLVE PLANNED TASK
# ============================================================

def resolve_dependent_task(
    task: PlannedTask,
    completed_tasks: dict[
        str,
        TaskResult,
    ],
) -> PlannedTask:

    if not task.depends_on:

        return task

    for dependency_id in task.depends_on:

        dependency_result = (
            completed_tasks.get(
                dependency_id
            )
        )

        if dependency_result is None:

            raise DependencyResolutionError(
                f"Task {task.task_id} depends "
                f"on missing task "
                f"{dependency_id}."
            )

        if (
            dependency_result.get("status")
            != "success"
        ):

            raise DependencyResolutionError(
                f"Task {task.task_id} cannot "
                f"resolve dependency "
                f"{dependency_id} because it "
                f"did not succeed."
            )

    resolved_question = (
        resolve_dependency_question(
            task.question,
            completed_tasks,
        )
    )

    resolved_task = deepcopy(
        task
    )

    resolved_task.question = (
        resolved_question
    )

    return resolved_task