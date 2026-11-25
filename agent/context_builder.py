"""
Context Builder

Converts query results into a rich,
structured analytical context.
"""

import re


# ============================================================
# QUERY TYPE
# ============================================================

def detect_query_type(
    question: str,
):

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


# ============================================================
# SEASON
# ============================================================

def detect_season(
    question: str,
):

    if not question:
        return None

    match = re.search(
        r"\b20\d{2}\b",
        question,
    )

    if match:
        return match.group(0)

    return None


# ============================================================
# TEAM
# ============================================================

def detect_team(
    question: str,
):

    if not question:
        return None

    q = question.lower()

    team_map = {

        # Aliases
        "srh":
            "Sunrisers Hyderabad",

        "csk":
            "Chennai Super Kings",

        "mi":
            "Mumbai Indians",

        "rcb":
            "Royal Challengers Bangalore",

        "kkr":
            "Kolkata Knight Riders",

        "rr":
            "Rajasthan Royals",

        "dc":
            "Delhi Capitals",

        "pbks":
            "Punjab Kings",

        # Full names
        "sunrisers hyderabad":
            "Sunrisers Hyderabad",

        "chennai super kings":
            "Chennai Super Kings",

        "mumbai indians":
            "Mumbai Indians",

        "royal challengers bangalore":
            "Royal Challengers Bangalore",

        "kolkata knight riders":
            "Kolkata Knight Riders",

        "rajasthan royals":
            "Rajasthan Royals",

        "delhi capitals":
            "Delhi Capitals",

        "punjab kings":
            "Punjab Kings",
    }

    # Prefer longest match first.
    for key in sorted(
        team_map,
        key=len,
        reverse=True,
    ):

        if key in q:
            return team_map[key]

    return None


# ============================================================
# VENUE
# ============================================================

def detect_venue(
    question: str,
):

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


# ============================================================
# PHASE
# ============================================================

def detect_phase(
    question: str,
):

    if not question:
        return None

    q = question.lower()

    if (
        "powerplay" in q
        or "power play" in q
    ):
        return "powerplay"

    if "death" in q:
        return "death"

    if "playoff" in q:
        return "playoff"

    return None


# ============================================================
# ENTITY COLUMN
# ============================================================

def detect_entity_column(
    df,
):

    candidates = [
        "player",
        "batter",
        "bowler",
        "player_name",
        "batter_name",
        "bowler_name",
        "team",
        "winner",
        "venue",
        "fielder",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None


# ============================================================
# METRIC COLUMN
# ============================================================

def detect_metric_column(
    df,
):

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
        "economy_rate",
        "economy",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    return None


# ============================================================
# ENTITY TYPE
# ============================================================

def detect_entity_type(
    entity_column,
):

    if entity_column in {
        "player",
        "batter",
        "bowler",
        "player_name",
        "batter_name",
        "bowler_name",
        "fielder",
    }:
        return "player"

    if entity_column in {
        "team",
        "winner",
    }:
        return "team"

    if entity_column == "venue":
        return "venue"

    return None


# ============================================================
# NORMALIZE PLANNER ENTITY CONTEXT
# ============================================================

def normalize_entity_context(
    entity_context,
):

    if not entity_context:

        return {
            "player": None,
            "team": None,
            "venue": None,
        }

    return {
        "player":
            entity_context.get(
                "player"
            ),

        "team":
            entity_context.get(
                "team"
            ),

        "venue":
            entity_context.get(
                "venue"
            ),
    }


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    question,
    result_df,
    entity_context=None,
):

    """
    Build structured analytical context.

    Entity precedence:

    1. Entity discovered from the analytics result
    2. Entity supplied by planner/task context
    3. Entity detected directly from the question

    The planner/task entity is especially important
    for aggregation and trend queries where the
    result DataFrame may not repeat the filtered
    player/team in every row.
    """

    # --------------------------------------------------------
    # QUESTION-DERIVED CONTEXT
    # --------------------------------------------------------

    season = detect_season(
        question
    )

    question_team = detect_team(
        question
    )

    question_venue = detect_venue(
        question
    )

    phase = detect_phase(
        question
    )


    # --------------------------------------------------------
    # PLANNER / TASK ENTITY CONTEXT
    # --------------------------------------------------------

    known_entities = (
        normalize_entity_context(
            entity_context
        )
    )

    player = (
        known_entities.get(
            "player"
        )
    )

    team = (
        question_team
        or known_entities.get(
            "team"
        )
    )

    venue = (
        question_venue
        or known_entities.get(
            "venue"
        )
    )


    # --------------------------------------------------------
    # EMPTY RESULT
    # --------------------------------------------------------

    if (
        result_df is None
        or result_df.empty
    ):

        primary_entity = (
            player
            or team
            or venue
        )

        return {
            "question":
                question,

            "query_type":
                detect_query_type(
                    question
                ),

            "season":
                season,

            "player":
                player,

            "team":
                team,

            "venue":
                venue,

            "phase":
                phase,

            "primary_entity":
                primary_entity,

            "row_count":
                0,

            "needs_insight":
                False,

            "top_result":
                None,

            "second_result":
                None,

            "entity_column":
                None,

            "entity_type":
                None,

            "metric":
                None,

            "top_entity":
                None,

            "second_entity":
                None,

            "top_value":
                None,

            "second_value":
                None,

            "gap":
                None,

            "entities":
                [],
        }


    # --------------------------------------------------------
    # RESULT SHAPE
    # --------------------------------------------------------

    row_count = len(
        result_df
    )

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


    # --------------------------------------------------------
    # RESULT ENTITY
    # --------------------------------------------------------

    entity_column = (
        detect_entity_column(
            result_df
        )
    )

    entity_type = (
        detect_entity_type(
            entity_column
        )
    )


    # --------------------------------------------------------
    # RESULT METRIC
    # --------------------------------------------------------

    metric_column = (
        detect_metric_column(
            result_df
        )
    )


    # --------------------------------------------------------
    # TOP ENTITIES
    # --------------------------------------------------------

    top_entity = None
    second_entity = None

    if entity_column:

        top_entity = (
            top_result.get(
                entity_column
            )
        )

        if second_result:

            second_entity = (
                second_result.get(
                    entity_column
                )
            )


    # --------------------------------------------------------
    # MERGE RESULT ENTITY INTO CONTEXT
    # --------------------------------------------------------

    if entity_type == "player":

        player = (
            top_entity
            or player
        )

    elif entity_type == "team":

        team = (
            top_entity
            or team
        )

    elif entity_type == "venue":

        venue = (
            top_entity
            or venue
        )


    # --------------------------------------------------------
    # METRIC VALUES
    # --------------------------------------------------------

    top_value = None
    second_value = None

    if metric_column:

        top_value = (
            top_result.get(
                metric_column
            )
        )

        if second_result:

            second_value = (
                second_result.get(
                    metric_column
                )
            )


    # --------------------------------------------------------
    # GAP
    # --------------------------------------------------------

    gap = None

    if (
        isinstance(
            top_value,
            (int, float),
        )
        and isinstance(
            second_value,
            (int, float),
        )
    ):

        gap = (
            top_value
            - second_value
        )


    # --------------------------------------------------------
    # PRIMARY ENTITY
    # --------------------------------------------------------

    primary_entity = (
        top_entity
        or player
        or team
        or venue
    )


    # --------------------------------------------------------
    # STRUCTURED ENTITY LIST
    # --------------------------------------------------------

    context_entities = []

    for entity in [
        top_entity,
        second_entity,
        player,
        team,
        venue,
    ]:

        if (
            entity is not None
            and entity
            not in context_entities
        ):

            context_entities.append(
                entity
            )


    # --------------------------------------------------------
    # FINAL CONTEXT
    # --------------------------------------------------------

    return {
        "question":
            question,

        "query_type":
            detect_query_type(
                question
            ),

        "season":
            season,

        "player":
            player,

        "team":
            team,

        "venue":
            venue,

        "phase":
            phase,

        "primary_entity":
            primary_entity,

        "row_count":
            row_count,

        "needs_insight":
            True,

        "top_result":
            top_result,

        "second_result":
            second_result,

        "entity_column":
            entity_column,

        "entity_type":
            entity_type,

        "metric":
            metric_column,

        "top_entity":
            top_entity,

        "second_entity":
            second_entity,

        "top_value":
            top_value,

        "second_value":
            second_value,

        "gap":
            gap,

        "entities":
            context_entities,
    }