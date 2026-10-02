"""
Context validation layer.
"""


def validate_context(context):
    """
    Validate Context Builder output.
    """

    if context is None:
        raise ValueError(
            "Context was not generated."
        )

    required_fields = [
        "query_type",
        "needs_insight",
        "row_count",
        "top_result",
    ]

    for field in required_fields:

        if field not in context:

            raise ValueError(
                f"Missing context field: {field}"
            )

    if context["row_count"] < 0:

        raise ValueError(
            "Invalid row count."
        )

    if (
        context["needs_insight"]
        and context["top_result"] is None
    ):
        raise ValueError(
            "Missing top result."
        )

    return True