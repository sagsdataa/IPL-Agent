# Context Builder for the Agent
# Analyze the questions and result shape
# Analyze the structured context
# Decide whether insights are needed

# agent/context_builder.py


"""
Context Builder

Converts query results into a rich,
structured analytical context.
"""

import pandas as pd

def detect_query_type(
    question: str
):
    """
    Detect the analytical query type.
    """

    if not question:
        return "unknown"

    question = question.lower()

    # -------------------------
    # Comparison
    # -------------------------

    comparison_keywords = [
        "compare",
        "vs",
        "versus",
        "difference between"
    ]

    if any(
        keyword in question
        for keyword in comparison_keywords
    ):
        return "comparison"

    # -------------------------
    # Trend
    # -------------------------

    trend_keywords = [
        "trend",
        "over time",
        "by season",
        "season wise",
        "year wise"
    ]

    if any(
        keyword in question
        for keyword in trend_keywords
    ):
        return "trend"

    # -------------------------
    # Ranking
    # -------------------------

    ranking_keywords = [
        "best",
        "top",
        "highest",
        "most",
        "leading"
    ]

    if any(
        keyword in question
        for keyword in ranking_keywords
    ):
        return "ranking"

    # -------------------------
    # Aggregation
    # -------------------------

    aggregation_keywords = [
        "total",
        "sum",
        "average",
        "avg",
        "count",
        "how many"
    ]

    if any(
        keyword in question
        for keyword in aggregation_keywords
    ):
        return "aggregation"

    # -------------------------
    # Explanation
    # -------------------------

    explanation_keywords = [
        "why",
        "how",
        "explain"
    ]

    if any(
        keyword in question
        for keyword in explanation_keywords
    ):
        return "explanation"

    return "unknown"

def detect_entity_column(df):
    """
    Detect the entity column.
    """

    candidates = [
        "player",
        "batter",
        "bowler",
        "batter_name",
        "bowler_name",
        "team",
        "venue"
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None


def detect_metric_column(df):
    """
    Detect the metric column.
    """

    candidates = [
        "total_runs",
        "runs",
        "total_wickets",
        "wickets",
        "strike_rate",
        "average",
        "matches",
        "wins"
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None

def build_context(
    question,
    result_df
):
    """
    Build analytical context for
    insight generation and future
    conversational follow-ups.
    """

    if result_df is None or result_df.empty:

        return {
            "question": question,
            "query_type": "unknown",
            "row_count": 0,
            "needs_insight": False,
            "top_result": None,
            "second_result": None,
            "top_entity": None,
            "second_entity": None,
            "top_value": None,
            "second_value": None,
            "metric": None,
            "gap": None,
            "entities": []
        }

    row_count = len(result_df)

    top_result = (
        result_df.iloc[0].to_dict()
        if row_count >= 1
        else None
    )

    second_result = (
        result_df.iloc[1].to_dict()
        if row_count >= 2
        else None
    )

    entity_column = detect_entity_column(
        result_df
    )

    metric_column = detect_metric_column(
        result_df
    )

    entity_type = None

    if entity_column in [
        "batter",
        "bowler",
        "player",
        "player_name",
        "batter_name",
        "bowler_name"
    ]:
        entity_type = "player"

    elif entity_column == "team":
        entity_type = "team"

    elif entity_column == "venue":
        entity_type = "venue"

    top_entity = None
    second_entity = None
    top_value = None
    second_value = None

    if entity_column:

        top_entity = (
            top_result.get(entity_column)
        )

        if second_result:
            second_entity = (
                second_result.get(
                    entity_column
                )
            )

    if metric_column:

        top_value = (
            top_result.get(metric_column)
        )

        if second_result:
            second_value = (
                second_result.get(
                    metric_column
                )
            )

    gap = None

    if (
        isinstance(top_value, (int, float))
        and isinstance(
            second_value,
            (int, float)
        )
    ):
        gap = (
            top_value - second_value
        )

    context = {

        "question": question,

        "query_type": detect_query_type(
            question
        ),

        "row_count": row_count,

        "needs_insight": True,

        "top_result": top_result,

        "second_result": second_result,

        "entity_column": entity_column,

        "entity_type": entity_type,

        "metric": metric_column,

        "top_entity": top_entity,

        "second_entity": second_entity,

        "top_value": top_value,

        "second_value": second_value,

        "gap": gap,

        "entities": [
            entity
            for entity in [
                top_entity,
                second_entity
            ]
            if entity
        ]
    }

    return context