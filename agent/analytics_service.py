from agent.sql_generator import (
    generate_sql,
)

from database.query_executor import (
    run_query,
)

from agent.context_builder import (
    build_context,
)

from agent.insight_generator import (
    generate_insight,
)

from guardrails.sql_validator import (
    validate_sql,
)

from guardrails.result_validator import (
    validate_result,
)

from guardrails.context_validator import (
    validate_context,
)

from guardrails.answer_validator import (
    validate_answer,
)

from guardrails.hallucination_checker import (
    check_hallucination,
)


# ============================================================
# DIRECT ANSWER
# ============================================================

def create_direct_answer(
    question,
    result,
):

    if (
        result is None
        or result.empty
    ):

        return (
            "The analysis completed successfully, "
            "but no matching IPL records were found."
        )

    if len(result) == 1:

        first_row = (
            result.iloc[0]
        )

        values = [
            (
                f"**{column.replace('_', ' ').title()}:** "
                f"{first_row[column]}"
            )
            for column in result.columns
        ]

        return (
            f"Based on the IPL dataset, "
            f"the answer to “{question}” is:\n\n"
            + "  \n".join(values)
        )

    return (
        f"The analysis returned "
        f"**{len(result):,} results** "
        f"for the question:\n\n"
        f"**{question}**\n\n"
        "The leading results are shown "
        "in the Data tab."
    )


# ============================================================
# ENRICH CONTEXT FROM RESULT
# ============================================================

def enrich_context_with_result(
    context,
    result,
):

    enriched = dict(
        context or {}
    )

    if (
        result is None
        or result.empty
    ):

        return enriched

    first_row = (
        result.iloc[0]
    )

    entity_columns = (
        "player",
        "batter",
        "bowler",
        "team",
        "winner",
        "fielder",
        "venue",
    )

    for column in entity_columns:

        if column not in result.columns:
            continue

        value = (
            first_row[column]
        )

        if value is None:
            continue

        enriched[
            "primary_entity"
        ] = value

        if column in {
            "player",
            "batter",
            "bowler",
            "fielder",
        }:

            enriched[
                "player"
            ] = value

        elif column in {
            "team",
            "winner",
        }:

            enriched[
                "team"
            ] = value

        elif column == "venue":

            enriched[
                "venue"
            ] = value

        break

    return enriched


# ============================================================
# RUN ANALYTICS QUERY
# ============================================================

def run_analytics_query(
    question: str,
    entity_context=None,
):

    if (
        not question
        or not question.strip()
    ):

        raise ValueError(
            "Analytics question "
            "cannot be empty."
        )

    question = (
        question.strip()
    )

    entity_context = (
        entity_context or {}
    )


    # ========================================================
    # SQL GENERATION
    # ========================================================

    generated_sql = (
        generate_sql(
            question
        )
    )


    # ========================================================
    # SQL VALIDATION
    # ========================================================

    validate_sql(
        generated_sql
    )


    # ========================================================
    # QUERY EXECUTION
    # ========================================================

    query_result = (
        run_query(
            generated_sql
        )
    )


    # ========================================================
    # RESULT VALIDATION
    # ========================================================

    validate_result(
        query_result
    )


    # ========================================================
    # CONTEXT BUILDING
    # ========================================================

    context = build_context(
        question,
        query_result,
        entity_context=entity_context,
    )


    # ========================================================
    # RESULT-DERIVED ENTITY ENRICHMENT
    #
    # This remains useful for ranking queries where the entity
    # is discovered by Analytics rather than supplied by the
    # planner.
    # ========================================================

    context = (
        enrich_context_with_result(
            context,
            query_result,
        )
    )


    # ========================================================
    # CONTEXT VALIDATION
    # ========================================================

    validate_context(
        context
    )


    # ========================================================
    # ANSWER GENERATION
    # ========================================================

    if context.get(
        "needs_insight"
    ):

        try:

            insight = (
                generate_insight(
                    question,
                    query_result,
                    context,
                )
            )

            validate_answer(
                insight
            )

            check_hallucination(
                insight,
                context,
            )

        except Exception:

            insight = (
                create_direct_answer(
                    question,
                    query_result,
                )
            )

    else:

        insight = (
            create_direct_answer(
                question,
                query_result,
            )
        )


    # ========================================================
    # STANDARD ANALYTICS RESULT
    # ========================================================

    return {
        "question":
            question,

        "sql":
            generated_sql,

        "result":
            query_result,

        "answer":
            insight,

        "context":
            context,

        "entity_context":
            entity_context,
    }