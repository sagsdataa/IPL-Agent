
"""
SQL safety and validation layer.

Validates SQL before execution.
Only read-only analytical queries are allowed.
"""

import re

# --------------------------------------------------
# BLOCKED COMMANDS
# --------------------------------------------------

BLOCKED_COMMANDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "COPY",
    "PRAGMA",
    "CALL",
    "EXEC",
]


# --------------------------------------------------
# VALIDATE SQL
# --------------------------------------------------

def validate_sql(sql: str):
    """
    Validate generated SQL before execution.

    Raises:
        ValueError
            If SQL violates safety rules.
    """

    if not sql:
        raise ValueError(
            "Empty SQL query generated."
        )

    sql_upper = sql.upper().strip()

    # ------------------------------------------
    # Rule 1
    # Only SELECT / WITH queries allowed
    # ------------------------------------------

    if not (
        sql_upper.startswith("SELECT")
        or sql_upper.startswith("WITH")
    ):
        raise ValueError(
            "Blocked SQL command. "
            "Only SELECT and WITH statements "
            "are allowed."
        )

    # ------------------------------------------
    # Rule 2
    # Block Dangerous Commands
    # ------------------------------------------

    for command in BLOCKED_COMMANDS:

        pattern = rf"\b{command}\b"

        if re.search(
            pattern,
            sql_upper,
        ):
            raise ValueError(
                f"Blocked SQL command detected: "
                f"{command}"
            )

    # ------------------------------------------
    # Rule 3
    # Single Statement Only
    # ------------------------------------------

    sql_no_spaces = sql.strip()

    if ";" in sql_no_spaces[:-1]:
        raise ValueError(
            "Multiple SQL statements "
            "are not allowed."
        )

    return True
