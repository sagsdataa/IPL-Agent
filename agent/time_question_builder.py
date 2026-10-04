"""
Time Question Builder

Builds a fresh analytical question using
the previous metric and a new time filter.
"""


def build_time_question(
    time_result,
    context,
):
    """
    Build a time-filtered analytical question.
    """

    if not time_result:
        return None

    if not context:
        return None

    if not time_result.get(
        "is_time_followup"
    ):
        return None

    time_type = time_result.get(
        "time_type"
    )

    time_value = time_result.get(
        "time_value"
    )

    metric = context.get(
        "metric"
    )

    entity_column = context.get(
        "entity_column"
    )

    query_type = context.get(
        "query_type"
    )

    if query_type != "ranking":
        return None

    metric_questions = {
        "total_runs": (
            "Who scored the most runs"
        ),
        "runs": (
            "Who scored the most runs"
        ),
        "total_wickets": (
            "Who took the most wickets"
        ),
        "wickets": (
            "Who took the most wickets"
        ),
        "strike_rate": (
            "Who has the highest strike rate"
        ),
        "average": (
            "Who has the highest batting average"
        ),
        "sixes": (
            "Who hit the most sixes"
        ),
        "fours": (
            "Who hit the most fours"
        ),
        "matches_played": (
            "Who played the most matches"
        ),
    }

    base_question = metric_questions.get(
        metric
    )

    if not base_question:

        if entity_column == "bowler":
            base_question = (
                f"Who has the highest {metric}"
            )
        else:
            base_question = (
                f"Who has the highest {metric}"
            )

    if time_type == "season":

        return (
            f"{base_question} "
            f"in IPL season {time_value}?"
        )

    if time_type == "last_n_seasons":

        return (
            f"{base_question} "
            f"in the last {time_value} "
            f"IPL seasons?"
        )

    if time_type == "playoffs":

        return (
            f"{base_question} "
            f"in IPL playoff matches?"
        )

    return None