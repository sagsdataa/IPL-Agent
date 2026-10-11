# Context Builder for the Agent
# Analyze the questions and result shape
# Analyze the structured context
# Decide whether insights are needed

# agent/context_builder.py

"""
Context Builder

Converts query results into a rich,
structured analytical context.
"""

import re


def detect_query_type(
    question: str
):
    """
    Detect analytical query type.
    """

    if not question:
        return "unknown"

    question = question.lower()

    if any(
        keyword in question
        for keyword in [
            "compare",
            "vs",
            "versus",
            "difference between",
        ]
    ):
        return "comparison"

    if any(
        keyword in question
        for keyword in [
            "trend",
            "over time",
            "by season",
            "season wise",
            "year wise",
        ]
    ):
        return "trend"

    if any(
        keyword in question
        for keyword in [
            "best",
            "top",
            "highest",
            "most",
            "leading",
        ]
    ):
        return "ranking"

    if any(
        keyword in question
        for keyword in [
            "total",
            "sum",
            "average",
            "avg",
            "count",
            "how many",
        ]
    ):
        return "aggregation"

    if any(
        keyword in question
        for keyword in [
            "why",
            "how",
            "explain",
        ]
    ):
        return "explanation"

    return "unknown"


def detect_season(
    question: str
):
    """
    Extract IPL season.
    """

    if not question:
        return None

    match = re.search(
        r"20\d{2}",
        question
    )

    if match:
        return match.group(0)

    return None


def detect_team(
    question: str
):
    """
    Detect IPL team from question.
    """

    if not question:
        return None

    q = question.lower()

    TEAM_MAP = {
        # aliases
        "srh": "Sunrisers Hyderabad",
        "csk": "Chennai Super Kings",
        "mi": "Mumbai Indians",
        "rcb": "Royal Challengers Bangalore",
        "kkr": "Kolkata Knight Riders",
        "rr": "Rajasthan Royals",
        "dc": "Delhi Capitals",
        "pbks": "Punjab Kings",

        # full names
        "sunrisers hyderabad": "Sunrisers Hyderabad",
        "chennai super kings": "Chennai Super Kings",
        "mumbai indians": "Mumbai Indians",
        "royal challengers bangalore": "Royal Challengers Bangalore",
        "kolkata knight riders": "Kolkata Knight Riders",
        "rajasthan royals": "Rajasthan Royals",
        "delhi capitals": "Delhi Capitals",
        "punjab kings": "Punjab Kings",
    }

    #
    # Prefer longest match first
    #
    for key in sorted(
        TEAM_MAP,
        key=len,
        reverse=True
    ):

        if key in q:
            return TEAM_MAP[key]

    return None

def detect_venue(
    question: str
):
    """
    Lightweight venue extraction.
    Replace later with fuzzy matching.
    """

    if not question:
        return None

    venues = [
        "Wankhede Stadium",
        "Eden Gardens",
        "MA Chidambaram Stadium",
        "M Chinnaswamy Stadium",
    ]

    q = question.lower()

    for venue in venues:

        if venue.lower() in q:
            return venue

    return None


def detect_phase(
    question: str
):
    """
    Detect IPL phase.
    """

    if not question:
        return None

    q = question.lower()

    if "powerplay" in q:
        return "powerplay"

    if "death" in q:
        return "death"

    if "playoff" in q:
        return "playoff"

    return None


def detect_entity_column(
    df
):
    """
    Detect entity column.
    """

    candidates = [
        "player",
        "batter",
        "bowler",
        "player_name",
        "batter_name",
        "bowler_name",
        "team",
        "venue",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None


def detect_metric_column(
    df
):
    """
    Detect primary metric.
    """

    candidates = [
        "total_runs",
        "runs",
        "total_wickets",
        "wickets",
        "strike_rate",
        "average",
        "sixes",
        "fours",
        "matches_played",
        "matches",
        "wins",
        "economy",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None


def detect_entity_type(
    entity_column
):
    """
    Convert entity column into high-level type.
    """

    if entity_column in {
        "player",
        "batter",
        "bowler",
        "player_name",
        "batter_name",
        "bowler_name",
    }:
        return "player"

    if entity_column == "team":
        return "team"

    if entity_column == "venue":
        return "venue"

    return None


def build_context(
    question,
    result_df,
):
    """
    Build analytical context.
    """

    season = detect_season(
        question
    )

    team = detect_team(
        question
    )

    venue = detect_venue(
        question
    )

    phase = detect_phase(
        question
    )

    if (
        result_df is None
        or result_df.empty
    ):
        return {
            "question": question,
            "query_type": detect_query_type(question),

            "season": season,
            "team": team,
            "venue": venue,
            "phase": phase,

            "row_count": 0,
            "needs_insight": False,

            "top_result": None,
            "second_result": None,

            "entity_column": None,
            "entity_type": None,

            "metric": None,

            "top_entity": None,
            "second_entity": None,

            "top_value": None,
            "second_value": None,

            "gap": None,
            "entities": [],
        }

    row_count = len(result_df)

    top_result = (
        result_df.iloc[0].to_dict()
        if row_count >= 1
        else None
    )

    second_result = (
        result_df.iloc[1].to_dict()
        if row_count >= 2
        else None
    )

    entity_column = detect_entity_column(
        result_df
    )

    entity_type = detect_entity_type(
        entity_column
    )

    metric_column = detect_metric_column(
        result_df
    )

    top_entity = None
    second_entity = None

    top_value = None
    second_value = None

    if entity_column:

        top_entity = top_result.get(
            entity_column
        )

        if second_result:

            second_entity = second_result.get(
                entity_column
            )

    if metric_column:

        top_value = top_result.get(
            metric_column
        )

        if second_result:

            second_value = second_result.get(
                metric_column
            )

    gap = None

    if (
        isinstance(top_value, (int, float))
        and isinstance(second_value, (int, float))
    ):
        gap = top_value - second_value

    return {
        "question": question,

        "query_type": detect_query_type(
            question
        ),

        "season": season,
        "team": team,
        "venue": venue,
        "phase": phase,

        "row_count": row_count,
        "needs_insight": True,

        "top_result": top_result,
        "second_result": second_result,

        "entity_column": entity_column,
        "entity_type": entity_type,

        "metric": metric_column,

        "top_entity": top_entity,
        "second_entity": second_entity,

        "top_value": top_value,
        "second_value": second_value,

        "gap": gap,

        "entities": [
            entity
            for entity in [
                top_entity,
                second_entity,
            ]
            if entity is not None
        ],
    }