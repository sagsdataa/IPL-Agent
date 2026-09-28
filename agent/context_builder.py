# Context Builder for the Agent
# Analyze the questions and result shape
# Analyze the structured context
# Decide whether insights are needed

# agent/context_builder.py


def classify_query(question: str):
    """
    Classify the user's question into a query type.
    """

    question = question.lower().strip()

    if any(
        phrase in question
        for phrase in [
            "compare",
            "versus",
            "vs",
            "difference",
        ]
    ):
        return "comparison"

    if any(
        phrase in question
        for phrase in [
            "trend",
            "over time",
            "season wise",
            "season-wise",
            "year wise",
            "year-wise",
        ]
    ):
        return "trend"

    if any(
        phrase in question
        for phrase in [
            "why",
            "explain",
            "reason",
            "justify",
            "prove",
        ]
    ):
        return "explanation"

    if any(
        phrase in question
        for phrase in [
            "average",
            "avg",
            "sum",
            "total",
            "percentage",
            "rate",
        ]
    ):
        return "aggregation"

    return "ranking"


def determine_insight_need(
    question: str,
    query_type: str,
    row_count: int,
):
    """
    Decide whether Gemini insight generation
    is required.
    """

    question = question.lower()

    if query_type in [
        "comparison",
        "trend",
        "explanation",
        "aggregation",
     ]:
        return True

    if query_type == "ranking":

        if any(
            keyword in question
            for keyword in [
                "best",
                "highest",
                "most",
                "leading",
                "top performer",
            ]
        ):
            return True

        if row_count <= 5:
            return True

    return False


def build_context(
    question,
    result_df,
):
    """
    Build a structured context object from
    the query and DuckDB results.
    """

    query_type = classify_query(question)

    context = {
        "question": question,
        "query_type": query_type,
        "needs_insight": False,
        "row_count": 0,
        "columns": [],
        "top_result": None,
        "second_result": None,
    }

    if result_df is None or result_df.empty:

        context["needs_insight"] = (
            determine_insight_need(
            question,
            query_type,
            0,
            )
        )
        return context

    context["row_count"] = len(result_df)

    context["columns"] = list(
        result_df.columns
    )

    context["top_result"] = (
        result_df.iloc[0].to_dict()
    )

    if len(result_df) > 1:
        context["second_result"] = (
            result_df.iloc[1].to_dict()
        )

    context["needs_insight"] = (
        determine_insight_need(
            question,
            query_type,
            len(result_df),
        )
    )

    return context