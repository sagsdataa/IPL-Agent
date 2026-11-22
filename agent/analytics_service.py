from agent.sql_generator import generate_sql
from database.query_executor import run_query
from agent.context_builder import build_context
from agent.insight_generator import generate_insight

from guardrails.sql_validator import validate_sql
from guardrails.result_validator import validate_result
from guardrails.context_validator import validate_context
from guardrails.answer_validator import validate_answer
from guardrails.hallucination_checker import check_hallucination


def enrich_context_with_result(
    context,
    result,
):

    enriched = dict(
        context or {}
    )

    if result is None or result.empty:
        return enriched

    first_row = result.iloc[0]

    entity_columns = (
        "batter",
        "bowler",
        "player",
        "team",
        "winner",
        "fielder",
        "venue",
    )

    for column in entity_columns:

        if column not in result.columns:
            continue

        value = first_row[column]

        if value is None:
            continue

        enriched[
            "primary_entity"
        ] = value

        if column in {
            "batter",
            "bowler",
            "player",
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

        break

    return enriched


def create_direct_answer(
    question,
    result,
):

    if result is None or result.empty:

        return (
            "The analysis completed successfully, "
            "but no matching IPL records were found."
        )

    if len(result) == 1:

        first_row = result.iloc[0]

        values = [
            (
                f"**{column.replace('_', ' ').title()}:** "
                f"{first_row[column]}"
            )
            for column in result.columns
        ]

        return (
            f"Based on the IPL dataset, the answer to "
            f"“{question}” is:\n\n"
            + "  \n".join(values)
        )

    return (
        f"The analysis returned **{len(result):,} results** "
        f"for the question:\n\n"
        f"**{question}**\n\n"
        "The leading results are shown in the Data tab."
    )


def run_analytics_query(
    question: str,
):

    if not question or not question.strip():

        raise ValueError(
            "Analytics question cannot be empty."
        )

    question = question.strip()

    # --------------------------------------------------------
    # SQL generation
    # --------------------------------------------------------

    generated_sql = generate_sql(
        question
    )

    # --------------------------------------------------------
    # SQL safety
    # --------------------------------------------------------

    validate_sql(
        generated_sql
    )

    # --------------------------------------------------------
    # Query execution
    # --------------------------------------------------------

    query_result = run_query(
        generated_sql
    )

    validate_result(
        query_result
    )

    # --------------------------------------------------------
    # Context construction
    # --------------------------------------------------------

    context = build_context(
        question,
        query_result,
    )

    context = enrich_context_with_result(
        context,
        query_result,
    )

    validate_context(
        context
    )

    # --------------------------------------------------------
    # Answer generation
    # --------------------------------------------------------

    if context.get(
        "needs_insight"
    ):

        try:

            insight = generate_insight(
                question,
                query_result,
                context,
            )

            validate_answer(
                insight
            )

            check_hallucination(
                insight,
                context,
            )

        except Exception:

            insight = create_direct_answer(
                question,
                query_result,
            )

    else:

        insight = create_direct_answer(
            question,
            query_result,
        )

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
    }