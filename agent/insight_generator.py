
from google import genai
import streamlit as st
from agent.prompt_templates import (
    get_query_type_instructions,
    get_grounding_instructions,
    get_cricket_analyst_style
)

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
    previous_answer,
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
    
    query_type_instructions = (
        get_query_type_instructions(
        query_type
        )
    )
    
    grounding_instructions = (
        get_grounding_instructions()
    )

    analyst_style = (
        get_cricket_analyst_style()
    )
    
    prompt = f"""
You are an IPL cricket analyst.
Previous Question:
{previous_question}

Previous Answer:
{previous_answer}

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

QUERY-TYPE INSTRUCTIONS:
{query_type_instructions}

{grounding_instructions}

{analyst_style}

1. The first row is the top performer.
2. Mention names and values exactly as provided.
3. If a second result is available, compare the top performer with it.
4. If only one result is available, describe the achievement naturally.
5. If the user asks:
    - Why -> explain the reasoning behind the answer using only the supplied data.
    - How -> explain the statistics.
    - Are you sure -> defend the answer using only the supplied data.
    - I disageer -> defend the answer using only the supplied data.
6. Never say or mention:
    - comparison availability
    - missing competitors
    - lack of data
    - no second player available
    - insufficient data to compare
7. Keep the response under 120 words.
8. Write naturally like a cricket analyst.
9. Focus on the top performers and their statistics.
10. Do not mention SQL,
    - database operations,
    - sorting,
    - ranking algorithms,
    - or any other technical details.
    - calculations.
    
FINAL TASK
Answer the follow-up question directly.

Use ONLY:
- Previous Question
- Previous Answer
- Top Result
- Second Result
- Results Table

Stay on the same topic as the previous answer.
Do not introduce new players,
teams, venues, seasons,
matches or statistics unless
they appear above.

Return only the final answer.

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

    query_type_instructions = (
        get_query_type_instructions(
            query_type
        )
    )

    grounding_instructions = (
        get_grounding_instructions()
    )

    analyst_style = (
        get_cricket_analyst_style()
    )

    prompt = f"""

ROLE
You are a professional IPL cricket data analyst.

USER QUESTION:
{question}

QUERY TYPE:
{query_type}

NUMBER OF RETURNED ROWS:
{row_count}

TOP RESULT:
{top_result}

SECOND RESULT:
{second_result if second_result is not None else "Not supplied"}

RESULTS TABLE:
{table_context}

QUERY-TYPE INSTRUCTIONS:
{query_type_instructions}
{grounding_instructions}
{analyst_style}

FINAL TASK

Answer the user's question directly using only the supplied
evidence.

Do not add a heading, preamble, disclaimer or closing offer.
Return only the final analytical response.

"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()
