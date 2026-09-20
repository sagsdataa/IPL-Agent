from pathlib import Path
import duckdb
import pandas as pd


# --------------------------------------------------
# DATABASE PATH
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "ipl.db"


# --------------------------------------------------
# SQL SAFETY VALIDATION
# --------------------------------------------------

def validate_sql(sql: str) -> bool:
    """
    Allow only read-only SQL queries.
    """

    sql_upper = sql.upper()

    blocked_keywords = [
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
        "EXPORT",
        "IMPORT",
        "CALL",
    ]

    for keyword in blocked_keywords:
        if keyword in sql_upper:
            raise ValueError(
                f"Blocked SQL command detected: {keyword}"
            )

    return True


# --------------------------------------------------
# QUERY EXECUTION
# --------------------------------------------------

def run_query(sql: str) -> pd.DataFrame:
    """
    Execute SQL against DuckDB and return DataFrame.
    """

    validate_sql(sql)

    connection = duckdb.connect(
        str(DB_PATH),
        read_only=True
    )

    try:

        result = connection.execute(
            sql
        ).fetchdf()

        return result

    finally:
        connection.close()


# --------------------------------------------------
# REUSABLE PREDEFINED QUERIES
# --------------------------------------------------

def get_top_batters(limit: int = 10):

    sql = f"""
    SELECT
        batter,
        SUM(batter_runs) AS total_runs
    FROM deliveries
    GROUP BY batter
    ORDER BY total_runs DESC
    LIMIT {limit}
    """

    return run_query(sql)


def get_top_bowlers(limit: int = 10):

    sql = f"""
    SELECT
        bowler,
        SUM(is_wicket) AS total_wickets
    FROM deliveries
    GROUP BY bowler
    ORDER BY total_wickets DESC
    LIMIT {limit}
    """

    return run_query(sql)


def get_top_six_hitters(limit: int = 10):

    sql = f"""
    SELECT
        batter,
        SUM(is_boundary_6) AS sixes
    FROM deliveries
    GROUP BY batter
    ORDER BY sixes DESC
    LIMIT {limit}
    """

    return run_query(sql)


def get_best_death_over_batters(limit: int = 10):

    sql = f"""
    SELECT
        batter,
        SUM(batter_runs) AS runs
    FROM deliveries
    WHERE is_death_overs = 1
    GROUP BY batter
    ORDER BY runs DESC
    LIMIT {limit}
    """

    return run_query(sql)


# --------------------------------------------------
# LOCAL TESTING
# --------------------------------------------------

if __name__ == "__main__":

    print("\nTOP BATTERS\n")

    print(
        get_top_batters()
    )
