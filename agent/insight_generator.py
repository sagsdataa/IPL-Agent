from google import genai

from config import (
    GEMINI_API_KEY,
    MODEL_NAME
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_insight(
    question: str,
    result_df
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

    context = result_df.head(10).to_string(
        index=False
    )

    top_result = result_df.iloc[0].to_dict()

    second_result = None

    if len(result_df) > 1:
        second_result = result_df.iloc[1].to_dict()

    prompt = f"""
You are an IPL Cricket Analyst.

Question:
{question}

Top Result:
{top_result}

Second Result:
{second_result}

Top Results Table:
{context}

Instructions:

1. Use ONLY the supplied data.
2. Do NOT invent statistics.
3. Do NOT add external cricket facts.
4. The first row is the top performer.
5. Mention names and values exactly as provided.
6. If a second result is available, compare the top performer with it.
7. If a second result is NOT available, explain why the top performer leads using only the available metric.
8. Never say:
   - "comparison is unavailable"
   - "no second player available"
   - "insufficient data to compare"
9. Keep the response under 120 words.
10. Write naturally like a cricket analyst.

Response Format:

Direct Answer:
<short paragraph>

Key Insight:
<short paragraph>
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()