# agent/context_continuation_builder.py

"""
Context Continuation Builder

Combines the latest canonical analytical question
with an incomplete conversational fragment.
"""

def clean_clause(
    text: str,
):
    """
    Remove terminal punctuation and normalize spacing.
    """

    if not text:
        return ""

    return " ".join(
        text
        .strip()
        .rstrip("?.!")
        .split()
    )


def build_context_continuation_question(
    continuation_result,
    conversation_state,
):
    """
    Extend the latest canonical analytical question
    using the detected continuation fragment.
    """

    if not continuation_result:
        return None

    if not conversation_state:
        return None

    if not continuation_result.get(
        "is_context_continuation"
    ):
        return None

    previous_question = clean_clause(
        conversation_state.get(
            "canonical_question"
        )
    )

    fragment = clean_clause(
        continuation_result.get(
            "fragment"
        )
    )

    if not previous_question:
        return None

    if not fragment:
        return None

    return (
        f"{previous_question} "
        f"{fragment}?"
    )