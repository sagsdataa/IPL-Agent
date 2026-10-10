"""
Contextual Question Builder

Builds entity-aware comparison questions while
preserving all active conversational filters.
"""


def build_contextual_question(
    entity_result,
    conversation_state,
):
    """
    Build an entity comparison question.

    Example

    Conversation State:

    {
        "top_entity": "KL Rahul",
        "metric": "total_runs",

        "filters": {
            "season": "2020",
            "team": "Punjab Kings"
        }
    }

    Follow-Up:

        Why not Dhoni?

    Output:

        Compare KL Rahul and Dhoni
        by total_runs
        in IPL season 2020
        for Punjab Kings.
    """

    if not entity_result:
        return None

    if not conversation_state:
        return None

    if not entity_result.get(
        "is_entity_followup"
    ):
        return None

    new_entity = entity_result.get(
        "entity"
    )

    current_entity = conversation_state.get(
        "top_entity"
    )

    metric = conversation_state.get(
        "metric"
    )

    query_type = conversation_state.get(
        "query_type"
    )

    if not new_entity:
        return None

    if not current_entity:
        return None

    if not metric:
        return None

    if query_type not in {
        "ranking",
        "comparison",
    }:
        return None

    filters = conversation_state.get(
        "filters",
        {}
    )

    season = filters.get(
        "season"
    )

    team = filters.get(
        "team"
    )

    venue = filters.get(
        "venue"
    )

    phase = filters.get(
        "phase"
    )

    clauses = []

    if season:
        clauses.append(
            f"in IPL season {season}"
        )

    if team:
        clauses.append(
            f"for {team}"
        )

    if venue:
        clauses.append(
            f"at {venue}"
        )

    if phase:
        clauses.append(
            f"during {phase}"
        )

    question = (
        f"Compare {current_entity} "
        f"and {new_entity} "
        f"by {metric}"
    )

    if clauses:
        question += (
            " "
            + " ".join(clauses)
        )

    return f"{question}."