"""
Result validation layer.

Validates DuckDB query results before
sending them to Context Builder and
Insight Generator.
"""

def validate_result(
    result_df
):
    """
    Validate query result.

    Raises:
        ValueError
            Only when query execution failed.
    """

    # Query execution failed
    if result_df is None:
        raise ValueError(
            "Query execution failed."
        )

    # Result must contain columns
    if len(result_df.columns) == 0:
        raise ValueError(
            "Result contains no columns."
        )

    # Empty result is VALID
    # The UI handles this gracefully.

    return True