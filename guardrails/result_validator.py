"""
Result validation layer.

Validates DuckDB query results before
sending them to Context Builder and
Insight Generator.
"""


def validate_result(result_df):
    """
    Validate query result.

    Raises:
        ValueError
            If result is invalid.
    """

    # Query failed completely
    if result_df is None:
        raise ValueError(
            "Query returned no result."
        )

    # Query executed but returned no rows
    if result_df.empty:
        raise ValueError(
            "No matching records found."
        )

    # Query returned no columns
    if len(result_df.columns) == 0:
        raise ValueError(
            "Result contains no columns."
        )

    return True