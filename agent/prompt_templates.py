

"""
Query-type prompt templates for the IPL Intelligence Agent.

This module provides focused instructions for different
analytical question types. It does not call Gemini directly.
"""


QUERY_TYPE_INSTRUCTIONS = {
    "ranking": """
The user is asking for a ranking or leading performer.

Your response must:

1. Identify the top-ranked entity directly.
2. State the exact metric and value supporting the ranking.
3. Explain that the entity leads based on the measured metric.
4. If a second result is provided, compare the leader with
   the second-ranked entity using exact supplied values.
5. Do not claim overall superiority beyond the supplied metric.
6. Do not mention missing second results.
7. Only compare against second place when second-place data is explicitly required for the explanation.
8. Do not infer consistency, longevity, dominance or quality
   unless those factors are explicitly present in the data.
9. Mention the metric value.
10. Mention the top result.

Recommended structure:

- State the leader and leading value.
- Add one concise evidence-based comparison or interpretation.
""",

    "comparison": """
The user is asking for a comparison between entities.

Your response must:

1. Compare both supplied entities using the available metrics.
2. Clearly identify where each entity leads.
3. Use the exact names and values from the supplied data.
4. Focus on meaningful differences rather than listing every
   value mechanically.
5. State an overall conclusion only when the supplied metrics
   support that conclusion.
6. Do not describe the first row as better overall merely
   because the result is ordered by one metric.
7. Do not invent reasons for any performance difference.

Recommended structure:

- Begin with the most important difference.
- Explain the strengths of each entity.
- End with a balanced, metric-based conclusion.
""",

    "aggregation": """
The user is asking for an aggregated statistic such as an
average, total, percentage, count or rate.

Your response must:

1. State the aggregate result directly.
2. Explain exactly what the returned number measures.
3. Use the exact value supplied in the result.
4. Keep the interpretation proportional to the available data.
5. Do not infer causes, conditions or external explanations.
6. Do not make comparisons unless comparison data is supplied.
7. Do not describe pitch behavior, pressure, consistency,
   playing style or match conditions unless explicitly
   supported by the data.

Recommended structure:

- State the aggregate value.
- Briefly explain what was aggregated.
""",

    "trend": """
The user is asking about a trend over seasons, years, matches
or another ordered period.

Your response must:

1. Describe the direction of the trend.
2. Mention the relevant periods and exact values.
3. Identify meaningful increases, decreases, peaks or declines.
4. Distinguish temporary changes from a visible sustained
   pattern only when sufficient periods are supplied.
5. Do not infer reasons for the trend.
6. Do not introduce external events, injuries, venues, players
   or match conditions not included in the supplied data.

Recommended structure:

- Summarize the overall direction.
- Support it with two or three important data points.
- Mention any visible turning point or peak.
""",

    "explanation": """
The user is asking for an explanation of a result.

Your response must:

1. Answer why or how the result was reached.
2. Use only the evidence supplied in the structured context.
3. Connect the conclusion to the relevant metric and value.
4. Avoid merely repeating the original conclusion.
5. Do not introduce external cricket knowledge.
6. Do not discuss SQL, databases, sorting or application logic.
7. If the evidence supports only a limited conclusion, state
   that conclusion without expanding it.

Recommended structure:

- State the reason.
- Support it with the relevant statistics.
""",

    "retrieval": """
The user is asking to retrieve records rather than receive
an analytical interpretation.

Your response must:

1. Briefly confirm what records were returned.
2. Do not create a detailed analytical narrative.
3. Direct the user to the displayed data when multiple rows
   are available.
4. Do not add conclusions that were not requested.

Recommended structure:

- One short confirmation sentence.
""",
}


DEFAULT_INSTRUCTIONS = """
Answer the user's IPL question using only the supplied data.

Your response must:

1. State the most relevant result directly.
2. Use exact names and values from the supplied data.
3. Avoid unsupported assumptions or external cricket facts.
4. Remain concise, clear and evidence-based.
"""


COMMON_GROUNDING_INSTRUCTIONS = """
GROUNDING RULES

1. Use only facts contained in:
   - the question,
   - the structured context,
   - the top result,
   - the second result,
   - and the supplied results table.

2. Do not use general cricket knowledge.

3. Do not invent or introduce:
   - players,
   - teams,
   - venues,
   - seasons,
   - match events,
   - statistics,
   - records,
   - awards,
   - dates,
   - playing styles,
   - pitch conditions,
   - or performance explanations.

4. Every name and numeric value in the response must appear
   in the supplied question or evidence.

5. Do not claim that a player or team is consistent, dominant,
   aggressive, successful under pressure or historically great
   unless the supplied data directly measures that claim.

6. Do not mention:
   - SQL,
   - database operations,
   - sorting,
   - prompts,
   - context builders,
   - ranking algorithms,
   - or internal application logic.

7. If the supplied evidence cannot support a requested
   conclusion, state the supported result without adding an
   unsupported explanation.
"""


CRICKET_ANALYST_STYLE = """
WRITING STYLE

1. Write like a professional IPL data analyst.
2. Lead with the answer, not with a generic introduction.
3. Use concise, natural cricket language.
4. Interpret the supplied statistics without overstating them.
5. Avoid phrases such as:
   - "As an IPL cricket analyst",
   - "Looking at the provided data",
   - "Based on the official IPL data",
   - "It is important to note",
   - "The data clearly proves".

6. Avoid excessive praise or dramatic adjectives such as:
   - remarkable,
   - legendary,
   - extraordinary,
   - massive,
   - incredible,
   - dominant.

7. Prefer precise wording such as:
   - leads by,
   - ranks first by,
   - records,
   - averages,
   - edges ahead in,
   - trails by,
   - is higher based on.

8. Use one or two short paragraphs.
9. Keep the response under 120 words.
"""


def get_query_type_instructions(
    query_type: str,
) -> str:
    """
    Return prompt instructions for the supplied query type.
    """

    if not query_type:
        return DEFAULT_INSTRUCTIONS

    normalized_query_type = (
        query_type
        .strip()
        .lower()
    )

    return QUERY_TYPE_INSTRUCTIONS.get(
        normalized_query_type,
        DEFAULT_INSTRUCTIONS,
    )


def get_grounding_instructions() -> str:
    """
    Return common grounding rules for insight generation.
    """

    return COMMON_GROUNDING_INSTRUCTIONS


def get_cricket_analyst_style() -> str:
    """
    Return the writing guidance for cricket analysis.
    """

    return CRICKET_ANALYST_STYLE