import json
from typing import Any

import streamlit as st
from google import genai
from google.genai import types
from pydantic import ValidationError

from agent.capability_planner_models import (
    CapabilityPlan,
)

from agent.capability_registry import (
    get_capability_registry,
)

from agent.capability_plan_validator import (
    CapabilityPlanValidationError,
    validate_capability_plan,
)


# ============================================================
# CONFIGURATION
# ============================================================

PLANNER_MODEL = (
    "models/gemini-3.5-flash-lite"
)


client = genai.Client(
    api_key=st.secrets[
        "GEMINI_API_KEY"
    ]
)


# ============================================================
# PLANNER ERROR
# ============================================================

class CapabilityPlannerError(
    RuntimeError
):
    pass


# ============================================================
# PREPARE CAPABILITY CONTRACTS
# ============================================================

def build_capability_context() -> str:

    registry = (
        get_capability_registry()
    )

    capability_context = []

    for (
        capability_name,
        capability,
    ) in registry.items():

        capability_context.append(
            {
                "name":
                    capability_name,

                "description":
                    capability.get(
                        "description",
                        "",
                    ),

                "input_schema":
                    capability.get(
                        "input_schema",
                        {},
                    ),

                "output_schema":
                    capability.get(
                        "output_schema",
                        {},
                    ),

                "constraints":
                    capability.get(
                        "constraints",
                        [],
                    ),
            }
        )

    return json.dumps(
        capability_context,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# BUILD PLANNER PROMPT
# ============================================================

def build_planner_prompt(
    question: str,
    conversation_context: (
        dict[str, Any] | None
    ) = None,
) -> str:

    capability_context = (
        build_capability_context()
    )

    conversation_context = (
        conversation_context
        or {}
    )

    serialized_conversation_context = (
        json.dumps(
            conversation_context,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    return f"""
You are the capability planner for an IPL intelligence system.

Your responsibility is to determine which registered capabilities
are required to satisfy the user's request.

You must produce a structured execution plan only.

Do not answer the user's question.
Do not generate SQL.
Do not retrieve knowledge.
Do not execute capabilities.
Do not invent capabilities.

AVAILABLE CAPABILITIES:

{capability_context}

CURRENT CONVERSATION CONTEXT:

{serialized_conversation_context}

USER REQUEST:

{question}


PLANNING PRINCIPLE:

Select capabilities according to the authoritative source required
to produce the answer, not according to whether the final answer
sounds like a factual statement.

Use analytics_query when the answer should be derived from
structured IPL match or delivery data.

This includes:

- statistics
- rankings
- totals
- averages
- trends
- comparisons
- matchups
- match results
- team results
- season outcomes
- season winners
- player performance
- team performance

Use knowledge_search for authored IPL knowledge.

This includes:

- rules
- definitions
- historical explanations
- player profiles
- team profiles
- awards
- explanatory information


PLANNING RULES:

1. Use route "knowledge" when only knowledge_search is required.

2. Use route "analytics" when only analytics_query is required.

3. Use route "hybrid" only when satisfying the complete request
   requires both knowledge_search and analytics_query.

4. Use route "unsupported" when none of the registered
   capabilities can satisfy the request.

5. Split compound requests into separate executable tasks.

6. Every task question must be complete enough for the selected
   capability to execute it.

7. Resolve pronouns and indirect references immediately when
   the referenced entity is already known from the user's request
   or conversation context.

   Example:

   User:
   Tell me about MS Dhoni and show his runs by season.

   Good analytics task:

   Show MS Dhoni's IPL runs by season.

   Bad analytics task:

   Show his runs by season.

8. If an entity or value is NOT known until another task executes,
   do not guess or invent the value.

   Instead, create a dependency and use a structured dependency
   output placeholder.

9. Use dependencies only when one task genuinely requires the
   output produced by another task.

10. Independent tasks must have an empty depends_on list.

11. Do not classify a single analytical request as hybrid merely
    because it uses wording such as "who is".

    Example:

    Who is the best Powerplay batter?

    This is analytics only because the user requests a statistical
    ranking, not a definition of Powerplay.

12. A hybrid plan must contain at least one knowledge_search task
    and at least one analytics_query task.

13. An unsupported plan must contain no executable tasks and
    must include an unsupported_reason.

14. Use sequential task IDs:

    task_1
    task_2
    task_3

15. Preserve known IPL entities in canonical form when possible.

16. Do not assign a descriptive unknown value as a canonical
    entity.

    Bad:

    canonical_name = "highest IPL run scorer"

    when the player's actual identity has not yet been discovered.

17. Questions asking for season winners, match winners, rankings,
    records, statistics, or other results derived from structured
    IPL data require analytics_query.


DEPENDENT TASK OUTPUT REFERENCES:

When a task requires an entity or value produced by another task,
the dependent task MUST reference that output using this exact
placeholder syntax:

{{{{task_id.field_name}}}}

Common structured output fields include:

{{{{task_1.primary_entity}}}}

{{{{task_1.player}}}}

{{{{task_1.team}}}}

{{{{task_1.venue}}}}

{{{{task_1.top_value}}}}


DEPENDENT TASK EXAMPLE:

User request:

Find the highest IPL run scorer and tell me about that player.

Required plan:

task_1:

capability = analytics_query

question = Find the highest IPL run scorer

depends_on = []


task_2:

capability = knowledge_search

question = Tell me about {{{{task_1.primary_entity}}}}

depends_on = ["task_1"]


IMPORTANT:

The task_2 question MUST contain the structured placeholder.

Do not replace the placeholder with an entity that has not yet
been discovered.

Do not use unresolved natural-language references such as:

- that player
- that team
- that bowler
- that batter
- that franchise
- the player returned by task_1
- the player identified by task_1
- the player who is the highest IPL run scorer
- the team identified earlier
- the result returned by task_1

Use structured dependency placeholders instead.

Return only the structured plan matching the required schema.
""".strip()


# ============================================================
# PARSE RAW PLANNER RESPONSE
# ============================================================

def parse_capability_plan(
    raw_response: str,
) -> CapabilityPlan:

    if not raw_response:

        raise CapabilityPlannerError(
            "Planner returned an empty "
            "response."
        )

    cleaned_response = (
        raw_response.strip()
    )

    # Defensive fallback if the model
    # returns fenced JSON.
    if cleaned_response.startswith(
        "```"
    ):

        cleaned_response = (
            cleaned_response
            .replace(
                "```json",
                "",
                1,
            )
            .replace(
                "```",
                "",
            )
            .strip()
        )

    try:

        return (
            CapabilityPlan
            .model_validate_json(
                cleaned_response
            )
        )

    except ValidationError as error:

        raise CapabilityPlannerError(
            "Planner response did not "
            "match the CapabilityPlan "
            "schema."
        ) from error


# ============================================================
# BUILD AND VALIDATE PLAN
# ============================================================

def create_capability_plan(
    question: str,
    conversation_context: (
        dict[str, Any] | None
    ) = None,
) -> CapabilityPlan:

    if (
        not question
        or not question.strip()
    ):

        raise CapabilityPlannerError(
            "Question cannot be empty."
        )

    normalized_question = (
        question.strip()
    )

    planner_prompt = (
        build_planner_prompt(
            question=(
                normalized_question
            ),
            conversation_context=(
                conversation_context
            ),
        )
    )

    try:

        response = (
            client.models.generate_content(
                model=PLANNER_MODEL,
                contents=planner_prompt,
                config=(
                    types
                    .GenerateContentConfig(
                        temperature=0,
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            CapabilityPlan
                        ),
                    )
                ),
            )
        )

    except Exception as error:

        raise CapabilityPlannerError(
            "Capability planner model "
            "call failed. "
            f"{type(error).__name__}: "
            f"{error}"
        ) from error


    # ========================================================
    # PREFER STRUCTURED PARSED RESPONSE
    # ========================================================

    parsed_response = getattr(
        response,
        "parsed",
        None,
    )

    if parsed_response is not None:

        try:

            if isinstance(
                parsed_response,
                CapabilityPlan,
            ):

                plan = (
                    parsed_response
                )

            else:

                plan = (
                    CapabilityPlan
                    .model_validate(
                        parsed_response
                    )
                )

        except ValidationError as error:

            raise CapabilityPlannerError(
                "Planner structured output "
                "did not match the "
                "CapabilityPlan schema."
            ) from error

    else:

        if not response.text:

            raise CapabilityPlannerError(
                "Capability planner returned "
                "no structured output."
            )

        plan = parse_capability_plan(
            response.text
        )


    # ========================================================
    # PRESERVE ORIGINAL USER QUESTION
    # ========================================================

    plan.original_question = (
        normalized_question
    )


    # ========================================================
    # DETERMINISTIC PLAN VALIDATION
    # ========================================================

    try:

        validate_capability_plan(
            plan
        )

    except (
        CapabilityPlanValidationError
    ) as error:

        raise CapabilityPlannerError(
            "Generated capability plan "
            f"is invalid: {error}"
        ) from error

    return plan


# ============================================================
# PRINT PLAN
# ============================================================

def print_capability_plan(
    plan: CapabilityPlan,
):

    print(
        "\n" + "=" * 80
    )

    print(
        "ORIGINAL QUESTION:",
        plan.original_question,
    )

    print(
        "ROUTE:",
        plan.route,
    )

    if plan.unsupported_reason:

        print(
            "UNSUPPORTED REASON:",
            plan.unsupported_reason,
        )

    print(
        "PLAN ENTITIES:"
    )

    if not plan.entities:

        print(
            "- None"
        )

    for entity in plan.entities:

        print(
            f"- {entity.entity_type}: "
            f"{entity.canonical_name} "
            f"(mention: "
            f"{entity.mention})"
        )

    print(
        "TASKS:"
    )

    if not plan.tasks:

        print(
            "- None"
        )

    for task in plan.tasks:

        print(
            "\n" + "-" * 60
        )

        print(
            "TASK ID:",
            task.task_id,
        )

        print(
            "CAPABILITY:",
            task.capability,
        )

        print(
            "QUESTION:",
            task.question,
        )

        print(
            "DEPENDS ON:",
            task.depends_on,
        )

        print(
            "ENTITIES:"
        )

        if not task.entities:

            print(
                "- None"
            )

        for entity in task.entities:

            print(
                f"- {entity.entity_type}: "
                f"{entity.canonical_name} "
                f"(mention: "
                f"{entity.mention})"
            )

    print(
        "=" * 80
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    # Keep the local test deliberately small
    # because your Gemini tier has experienced
    # temporary 429/503 limits.

    test_questions = (

        # Dependent Hybrid
        (
            "Find the highest IPL run "
            "scorer and tell me about "
            "that player"
        ),

    )

    for test_question in test_questions:

        try:

            capability_plan = (
                create_capability_plan(
                    question=(
                        test_question
                    ),
                    conversation_context={},
                )
            )

            print_capability_plan(
                capability_plan
            )

        except (
            CapabilityPlannerError
        ) as error:

            print(
                "\n" + "=" * 80
            )

            print(
                "QUESTION:",
                test_question,
            )

            print(
                "PLANNER ERROR:",
                error,
            )

            print(
                "=" * 80
            )