"""
Metric Question Builder

Convert metric-based follow-up questions
into new analytical questions using
previous context.
"""


def build_metric_question(
    metric_result,
    context
):
    """
    Build a new analytical question when
    the user changes the metric.

    Example:

    Previous:
        Who scored the most runs?

    Follow-up:
        What about strike rate?

    Output:
        Who has the highest strike rate?
    """

    if not metric_result:
        return None

    if not context:
        return None

    if not metric_result.get(
        "is_metric_followup"
    ):
        return None

    new_metric = (
        metric_result.get(
            "metric"
        )
    )

    query_type = (
        context.get(
            "query_type"
        )
    )

    entity_type = (
        context.get(
            "entity_type"
        )
    )

    if (
        query_type == "ranking"
        and entity_type == "player"
    ):

        metric_questions = {

            "strike_rate":
                "Who has the highest strike rate?",

            "average":
                "Who has the highest batting average?",

            "sixes":
                "Who hit the most sixes?",

            "fours":
                "Who hit the most fours?",

            "wickets":
                "Who took the most wickets?",

            "economy":
                "Who has the best economy rate?",

            "matches_played":
                "Who played the most matches?"
        }

        return metric_questions.get(
            new_metric,
            f"Who has the highest {new_metric}?"
        )

    return None