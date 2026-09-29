
from google import genai
import streamlit as st

from config import (
    GEMINI_API_KEY,
    MODEL_NAME
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)

# Generate a follow-up insight based on the previous question 
# and the DuckDB query results.

def generate_followup_insight(
    followup_question,
    previous_question,
    result_df,
    context
):
    """
    Generate a follow-up insight based on the previous question
    and the DuckDB query results and structured context.
    """

    if result_df is None or result_df.empty:
        return (
            "No matching or supporting records were found "
            "for this follow-up question."
        )
    
    table_context = result_df.head(10).to_string(
        index=False
    )
    top_result = context.get(
        "top_result",
        None
    )
    second_result = context.get(
        "second_result",
        None
    )
    query_type = context.get(
        "query_type",
        None
    )
    
    prompt = f"""
You are an IPL cricket analyst.

Previous Question:
{previous_question}

User follow-up Question:
{followup_question}

Query Type:
{query_type}

Top Result:
{top_result}

Second Result:
{second_result}

Results:
{table_context}

1. Use ONLY the supplied data.
2. Do NOT invent statistics.
3. Do NOT add external cricket facts.
4. The first row is the top performer.
5. Mention names and values exactly as provided.
6. If a second result is available, compare the top performer with it.
7. If only one result is available, describe the achievement naturally.
8. If the user asks:
    - Why -> explain the reasoning behind the answer using only the supplied data.
    - How -> explain the statistics.
    - Are you sure -> defend the answer using only the supplied data.
    - I disagee -> defend the answer using only the supplied data.
9. Never say or mention:
    - comparison availability
    - missing competitors
    - lack of data
    - no second player available
    - insufficient data to compare
10. Keep the response under 120 words.
11. Write naturally like a cricket analyst.
12. Focus on the top performers and their statistics.
13. Do not mention SQL,
    - database operations,
    - sorting,
    - ranking algorithms,
    - or any other technical details.
    - calculations.
"""
    st.write("Pre Questions:", previous_question)
    st.write("Followup Questions:", followup_question)
    st.write("Top Results:", top_result)
    st.write("Query Type:", query_type)
    st.write("table context:", table_context)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


# Generate a grounded cricket insight based ONLY on DuckDB query results.

def generate_insight(
    question: str,
    result_df,
    context
):
    """
    Generate a grounded cricket insight
    based ONLY on DuckDB query results.
    """

    if result_df is None or result_df.empty:
        return (
            "No matching records were found "
            "for this question."
        )

    table_context = result_df.head(10).to_string(
        index=False
    )

    top_result = context["top_result"]

    second_result = context["second_result"]

    query_type = context["query_type"]

    row_count = context["row_count"]

    prompt = f"""
You are an IPL Cricket Analyst.

Question:
{question}

Top Result:
{top_result}

Second Result:
{second_result}

Top Results Table:
{table_context}

Query Type:
{query_type}

Row Count:
{row_count}

Instructions:

1. Use ONLY the supplied data.
2. Do NOT invent statistics.
3. Do NOT add external cricket facts.
4. The first row is the top performer.
5. Mention names and values exactly as provided.
6. If a second result is available, compare the top performer with it.
7. If only one result is available , describe the achievement naturally.
8. Never say or mention:
   - comparison availability
   - missing competitors
   - lack of data
   - no second player available
   - insufficient data to compare
9. Keep the response under 120 words.
10. Write naturally like a cricket analyst.

Response Format:

<short paragraph>

<short paragraph>
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()