
from google import genai
import streamlit as st
from agent.prompt_templates import (
    get_query_type_instructions,
    get_grounding_instructions,
    get_cricket_analyst_style
)

#from config import (
#    GEMINI_API_KEY,
#    MODEL_NAME
#)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_NAME = "gemini-flash-lite-latest"

client = genai.Client(
    api_key=GEMINI_API_KEY
)

# Generate a follow-up insight based on the previous question 
# and the DuckDB query results.

import string

def classify_followup_type(
    followup_question: str
) -> str:
    """
    Classify the follow-up question.
    """

    question = (
        followup_question
        .strip()
        .lower()
        .translate(
            str.maketrans(
                "",
                "",
                string.punctuation
            )
        )
    )

    # Verification
    if any(
        phrase in question
        for phrase in [
            "are you sure",
            "sure",
            "really",
            "confirm",
            "is that correct",
            "is this correct"
        ]
    ):
        return "verification"

    # Challenge
    if any(
        phrase in question
        for phrase in [
            "i disagree",
            "dont agree",
            "do not agree",
            "justify",
            "prove it",
            "evidence"
        ]
    ):
        return "challenge"

    # How
    if (
        question == "how"
        or question.startswith("how ")
    ):
        return "how"

    # Why
    if (
        question == "why"
        or question.startswith("why ")
    ):
        return "why"

    # Elaboration
    if any(
        phrase in question
        for phrase in [
            "explain",
            "explain more",
            "tell me more",
            "elaborate",
            "expand"
        ]
    ):
        return "elaboration"

    return "generic"

def get_followup_instructions(
    followup_question: str
) -> str:
    """
    Return explicit instructions based on
    the follow-up question's intent.
    """

    normalized_question = (
        followup_question
        .strip()
        .lower()
        .translate(
            str.maketrans(
                "",
                "",
                string.punctuation
            )
        )
    )

    # ----------------------------------------
    # Confirmation / Verification
    # ----------------------------------------

    if any(
        phrase in normalized_question
        for phrase in [
            "are you sure",
            "sure",
            "really",
            "is that correct",
            "is this correct",
            "can you confirm",
            "confirm"
        ]
    ):
        return """
FOLLOW-UP TYPE: VERIFICATION

You Must verify the previous answer.

Start with:

"Yes, based on the supplied evidence..."

Then:
1. Restate the supporting metric.
2. Restate the supporting value.
3. Confirm the conclusion.

Do NOT explain methodology.
Do NOT explain reasons.

"""

    # ----------------------------------------
    # Challenge / Disagreement
    # ----------------------------------------

    if any(
        phrase in normalized_question
        for phrase in [
            "i disagree",
            "dont agree",
            "do not agree",
            "prove it",
            "justify",
            "evidence"
        ]
    ):
        return """
This is a challenge to the previous answer.

Defend only the conclusion supported by the supplied evidence.

State:
1. Which metric determined the previous result.
2. The exact supporting value.
3. Any limitation in the evidence.

If the follow-up introduces a player, team or entity that
does not appear in the supplied evidence, do not compare it
or invent statistics.

Instead, state that the current evidence does not contain
that entity and that a fresh comparison would be required.
"""

    # ----------------------------------------
    # How / Method
    # ----------------------------------------

    if (
        normalized_question == "how"
        or normalized_question.startswith("how ")
    ):
        return """

FOLLOW-UP TYPE: HOW

You Must explain how the conclusion was determined or reached.

Focus on:
1. Which matrics were used to determine the conclusion.
2. How that metric was applied or determines ranking.
3. How the supplied value led to the result

Do NOT focus on reasons.
Do NOT simply repeat the result.

"""

    # ----------------------------------------
    # Why / Reason
    # ----------------------------------------

    if (
        normalized_question == "why"
        or normalized_question.startswith("why ")
    ):
        return """

FOLLOW-UP TYPE: WHY

You Must explain the reason behind the conclusion.

Focus on:
1. Why the leader achieved the top position.
2. The evidence supporting the conclusion.

Do NOT explain methodology.
Do NOT verify the answer.
Do NOT repeat the previous answer verbatim.

"""

    # ----------------------------------------
    # Elaboration
    # ----------------------------------------

    if any(
        phrase in normalized_question
        for phrase in [
            "explain",
            "explain more",
            "tell me more",
            "more detail",
            "elaborate",
            "expand"
        ]
    ):
        return """
This is an elaboration follow-up.

Add useful detail to the previous answer while remaining on
the same topic.

Use additional metrics from the supplied results that were not
already emphasized in the previous answer.

Do not repeat the previous answer word for word.
Do not introduce external IPL facts.
"""

    # ----------------------------------------
    # Generic Follow-up
    # ----------------------------------------

    return """
Answer the follow-up directly using the previous question,
previous answer and supplied evidence.

Stay on the same topic.

Do not introduce entities, numbers or claims that are absent
from the supplied evidence.
"""

def generate_followup_insight(
    followup_question,
    previous_question,
    previous_answer,
    result_df,
    context
):
    """
    Generate a grounded follow-up answer using
    the previous question, answer, result and context.
    """

    if result_df is None or result_df.empty:
        return (
            "No supporting records are available "
            "for this follow-up question."
        )

    if context is None:
        return (
            "The previous analytical context is unavailable."
        )

    table_context = result_df.head(5).to_string(
        index=False
    )

    top_result = context.get(
        "top_result"
    )

    second_result = context.get(
        "second_result"
    )

    query_type = context.get(
        "query_type",
        "unknown"
    )

    followup_type = classify_followup_type(
        followup_question
    )

    followup_instructions = (
        get_followup_instructions(
            followup_question
        )
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
ROLE

You are a professional IPL cricket data analyst.

PREVIOUS QUESTION

{previous_question}

PREVIOUS ANSWER

{previous_answer}

CURRENT FOLLOW-UP QUESTION

{followup_question}

FOLLOW-UP TYPE
{followup_type}

ORIGINAL QUERY TYPE

{query_type}

TOP RESULT

{top_result}

SECOND RESULT

{second_result if second_result is not None else "Not supplied"}

SUPPORTING RESULTS

{table_context}

FOLLOW-UP-SPECIFIC INSTRUCTIONS

{followup_instructions}

ORIGINAL QUERY-TYPE INSTRUCTIONS

{query_type_instructions}

{grounding_instructions}

{analyst_style}

IMPORTANT RESPONSE RULES

WHY:
Explain the reason behind the result.

HOW:
Explain the methodology used to determine the result.

VERIFICATION:
Confirm whether the previous answer is still supported.

CHALLENGE:
Explain the limitation of the current evidence and why a fresh comparison may be required.

The response MUST match the FOLLOW-UP TYPE.

WHY, HOW and VERIFICATION responses must sound noticeably different.

Do not give the same answer for all follow-up types.

FINAL TASK

Answer the current follow-up question directly.

Use only the previous question, previous answer and supplied
evidence.

Keep the response on the same topic.

Do not introduce players, teams, venues, seasons, matches,
statistics or events that are absent from the supplied
evidence.

If the follow-up mentions an entity that is absent from the
evidence, clearly state that the current results do not contain
that entity and that a fresh comparison would be required.

Do not add a heading, disclaimer or closing offer.

Return only the final response.
"""

    #st.write("Pre Questions:", previous_question)
    #st.write("Followup Questions:", followup_question)
    #st.write("Top Results:", top_result)
    #st.write("Query Type:", query_type)
    #st.write("table context:", table_context)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        return (
            "An analytical insight could not "
            "be generated from the available data."
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

    table_context = result_df.head(5).to_string(
        index=False
    )

    top_result = context.get("top_result")

    second_result = context.get("second_result")

    query_type = context.get("query_type")

    row_count = context.get("row_count")

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
