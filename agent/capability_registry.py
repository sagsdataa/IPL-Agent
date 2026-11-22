from typing import Any


CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {

    "knowledge_search": {

        "name": "knowledge_search",

        "description": (
            "Retrieves grounded IPL knowledge such as "
            "player profiles, team information, cricket rules, "
            "awards, IPL history, and definitions."
        ),

        "input_schema": {
            "question": "string",
        },

        "output_schema": {
            "answer": "string",
            "sources": "list",
        },

        "constraints": [
            "Use grounded IPL knowledge only.",
            "Use exact retrieval when available.",
            "Use semantic retrieval when exact retrieval is unavailable.",
            "Do not answer quantitative ranking or statistical analysis questions.",
        ],
    },


    "analytics_query": {

        "name": "analytics_query",

        "description": (
            "Answers quantitative IPL questions using "
            "the structured IPL dataset in DuckDB. "
            "Supports rankings, totals, averages, trends, "
            "comparisons, matchups, season analysis, "
            "player analysis, and team analysis."
        ),

        "input_schema": {
            "question": "string",
        },

        "output_schema": {
            "answer": "string",
            "sql": "string",
            "result": "table",
            "context": "object",
        },

        "constraints": [
            "Use only the available IPL analytics dataset.",
            "Generate read-only SQL.",
            "SQL must pass the SQL safety validator.",
            "Do not use this capability for definitions or general IPL knowledge.",
        ],
    },
}


def get_capability_registry():

    return CAPABILITY_REGISTRY


def get_capability(
    capability_name: str,
):

    return CAPABILITY_REGISTRY.get(
        capability_name
    )


def capability_exists(
    capability_name: str,
) -> bool:

    return (
        capability_name
        in CAPABILITY_REGISTRY
    )
