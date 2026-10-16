"""
Contextual Question Builder

Builds entity-aware follow-up questions
while preserving conversational context.
"""


def build_contextual_question(
    entity_result,
    conversation_state,
):
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

    if not new_entity:
        return None

    previous_question = (
        conversation_state.get(
            "last_question"
        )
    )

    if not previous_question:
        return None

    previous_question = (
        previous_question
        .rstrip("?.!")
    )

    print("=" * 80)
    print("CONTEXTUAL BUILDER")
    print("PREVIOUS QUESTION:", previous_question)
    print("NEW ENTITY:", new_entity)
    print("=" * 80)

    return (
        f"{previous_question} "
        f"for {new_entity}"
    )