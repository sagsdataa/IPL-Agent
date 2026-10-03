"""
Contextual Question Builder

Convert conversational follow-up questions
into richer analytical questions using
stored context.
"""


def build_contextual_question(
    entity_result,
    context
):
    """
    Build a contextual analytical question.

    Example:

    Previous:
        Best bowler = YS Chahal

    Follow-up:
        Why not Bumrah?

    Output:
        Compare YS Chahal and Bumrah
        by total_wickets
    """

    if not entity_result:

        return None

    if not context:

        return None

    if not entity_result.get(
        "is_entity_followup"
    ):

        return None

    new_entity = (
        entity_result.get("entity")
    )

    current_entity = (
        context.get("top_entity")
    )

    metric = (
        context.get("metric")
    )

    query_type = (
        context.get("query_type")
    )

    entity_type = (
        context.get("entity_type")
    )

    if (
        query_type == "ranking"
        and current_entity
        and new_entity
        and metric
    ):

        return (
            f"Compare "
            f"{current_entity} "
            f"and {new_entity} "
            f"by {metric}"
        )

    return None