from agent.capability_planner_models import (
    CapabilityPlan,
)

from agent.capability_registry import (
    capability_exists,
)


# ============================================================
# PLAN VALIDATION ERROR
# ============================================================

class CapabilityPlanValidationError(
    ValueError
):
    pass


# ============================================================
# VALIDATE TASK IDS
# ============================================================

def validate_task_ids(
    plan: CapabilityPlan,
):

    task_ids = [
        task.task_id
        for task in plan.tasks
    ]

    if len(task_ids) != len(set(task_ids)):

        raise CapabilityPlanValidationError(
            "Capability plan contains "
            "duplicate task IDs."
        )


# ============================================================
# VALIDATE REGISTERED CAPABILITIES
# ============================================================

def validate_capabilities(
    plan: CapabilityPlan,
):

    for task in plan.tasks:

        if not capability_exists(
            task.capability
        ):

            raise CapabilityPlanValidationError(
                f"Unknown capability: "
                f"{task.capability}"
            )


# ============================================================
# VALIDATE TASK QUESTIONS
# ============================================================

def validate_task_questions(
    plan: CapabilityPlan,
):

    for task in plan.tasks:

        if not task.question.strip():

            raise CapabilityPlanValidationError(
                f"Task {task.task_id} "
                f"contains an empty question."
            )


# ============================================================
# VALIDATE ROUTE CONSISTENCY
# ============================================================

def validate_route_consistency(
    plan: CapabilityPlan,
):

    capabilities = {
        task.capability
        for task in plan.tasks
    }

    # --------------------------------------------------------
    # KNOWLEDGE
    # --------------------------------------------------------

    if plan.route == "knowledge":

        if not plan.tasks:

            raise CapabilityPlanValidationError(
                "Knowledge route must contain "
                "at least one task."
            )

        if capabilities != {
            "knowledge_search"
        }:

            raise CapabilityPlanValidationError(
                "Knowledge route can contain "
                "only knowledge_search tasks."
            )

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------

    elif plan.route == "analytics":

        if not plan.tasks:

            raise CapabilityPlanValidationError(
                "Analytics route must contain "
                "at least one task."
            )

        if capabilities != {
            "analytics_query"
        }:

            raise CapabilityPlanValidationError(
                "Analytics route can contain "
                "only analytics_query tasks."
            )

    # --------------------------------------------------------
    # HYBRID
    # --------------------------------------------------------

    elif plan.route == "hybrid":

        required_capabilities = {
            "knowledge_search",
            "analytics_query",
        }

        if not required_capabilities.issubset(
            capabilities
        ):

            raise CapabilityPlanValidationError(
                "Hybrid route must contain "
                "both knowledge_search and "
                "analytics_query capabilities."
            )

    # --------------------------------------------------------
    # UNSUPPORTED
    # --------------------------------------------------------

    elif plan.route == "unsupported":

        if plan.tasks:

            raise CapabilityPlanValidationError(
                "Unsupported route cannot "
                "contain executable tasks."
            )

        if not plan.unsupported_reason:

            raise CapabilityPlanValidationError(
                "Unsupported route must include "
                "an unsupported_reason."
            )


# ============================================================
# VALIDATE DEPENDENCIES
# ============================================================

def validate_dependencies(
    plan: CapabilityPlan,
):

    task_ids = {
        task.task_id
        for task in plan.tasks
    }

    for task in plan.tasks:

        for dependency in task.depends_on:

            if dependency not in task_ids:

                raise CapabilityPlanValidationError(
                    f"Task {task.task_id} "
                    f"depends on unknown task "
                    f"{dependency}."
                )

            if dependency == task.task_id:

                raise CapabilityPlanValidationError(
                    f"Task {task.task_id} "
                    f"cannot depend on itself."
                )


# ============================================================
# DETECT CIRCULAR DEPENDENCIES
# ============================================================

def validate_no_dependency_cycles(
    plan: CapabilityPlan,
):

    dependency_graph = {
        task.task_id: set(
            task.depends_on
        )
        for task in plan.tasks
    }

    visiting = set()
    visited = set()

    def visit(task_id):

        if task_id in visiting:

            raise CapabilityPlanValidationError(
                "Capability plan contains "
                "a circular dependency."
            )

        if task_id in visited:
            return

        visiting.add(task_id)

        for dependency in (
            dependency_graph.get(
                task_id,
                set(),
            )
        ):

            visit(dependency)

        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependency_graph:

        visit(task_id)


# ============================================================
# VALIDATE ENTITY REFERENCES
# ============================================================

def validate_entities(
    plan: CapabilityPlan,
):

    for entity in plan.entities:

        if not entity.entity_type.strip():

            raise CapabilityPlanValidationError(
                "Plan contains an entity "
                "without entity_type."
            )

        if not entity.canonical_name.strip():

            raise CapabilityPlanValidationError(
                "Plan contains an entity "
                "without canonical_name."
            )

    for task in plan.tasks:

        for entity in task.entities:

            if not entity.entity_type.strip():

                raise CapabilityPlanValidationError(
                    f"Task {task.task_id} "
                    f"contains an entity without "
                    f"entity_type."
                )

            if not entity.canonical_name.strip():

                raise CapabilityPlanValidationError(
                    f"Task {task.task_id} "
                    f"contains an entity without "
                    f"canonical_name."
                )


# ============================================================
# MASTER VALIDATOR
# ============================================================

def validate_capability_plan(
    plan: CapabilityPlan,
):

    validate_task_ids(
        plan
    )

    validate_capabilities(
        plan
    )

    validate_task_questions(
        plan
    )

    validate_route_consistency(
        plan
    )

    validate_dependencies(
        plan
    )

    validate_no_dependency_cycles(
        plan
    )

    validate_entities(
        plan
    )

    return True