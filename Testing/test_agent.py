# test_agent.py

from agent.sql_generator import generate_sql
from database.query_executor import run_query


def clean_sql(sql_response: str) -> str:
    """
    Remove markdown code fences returned by Gemini.
    """

    sql_response = sql_response.replace("```sql", "")
    sql_response = sql_response.replace("```", "")

    return sql_response.strip()


def main():

    # Test Question
    question = """
    Top 5 death-over batters between 2020 and 2026 by strike rate with at least 200 balls faced?
    """

    print("\n" + "=" * 60)
    print("QUESTION")
    print("=" * 60)
    print(question)

    # Step 1 - Agent
    sql = generate_sql(question)

    sql = clean_sql(sql)

    print("\n" + "=" * 60)
    print("GENERATED SQL")
    print("=" * 60)
    print(sql)

    # Step 2 - Tool
    result = run_query(sql)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()