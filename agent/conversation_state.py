"""
Conversation State

Stores the current resolved analytical intent.
The canonical question is the primary source
of truth for follow-up rewriting.
"""

from copy import deepcopy


CONTEXT_FIELDS = (
    "season",
    "team",
    "venue",
    "phase",
)


def create_conversation_state():
    """
    Return a new empty conversation state.
    """

    return {
        "canonical_question": None,
        "query_type": None,
        "metric": None,
        "entity_type": None,
        "last_metric": None,
        "top_entity": None,
        "filters": {},
    }


def update_conversation_state(
    old_state,
    question,
    context,
):
    """
    Update conversation state from the latest
    successfully executed analytical question.
    """

    state = deepcopy(
        old_state
        or create_conversation_state()
    )

    state["canonical_question"] = question

    for field in (
        "query_type",
        "metric",
        "entity_type",
        "top_entity",
    ):
        value = context.get(
            field
        )

        if value is not None:
            state[field] = value

    filters = state.setdefault(
        "filters",
        {},
    )

    for field in CONTEXT_FIELDS:
        value = context.get(
            field
        )

        if value is not None:
            filters[field] = value

    return state
