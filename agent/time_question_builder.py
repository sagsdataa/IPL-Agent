"""
Time Question Builder

Applies a new season or year range to the
previous analytical question.
"""


def _get_previous_question(
    conversation_state
):

    if not conversation_state:
        return None

    candidate_keys = (
        "last_question",
        "question",
        "previous_question",
        "current_question",
        "original_question",
    )

    for key in candidate_keys:

        value = conversation_state.get(
            key
        )

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _remove_existing_time_phrase(
    question: str
):
    """
    Keep this conservative.

    For now, the SQL generator receives both the
    prior analytical question and the new explicit
    time instruction.
    """

    return question.strip().rstrip(
        "?.!"
    )


def build_time_question(
    time_result,
    conversation_state,
):

    if not time_result:
        return None

    if not time_result.get(
        "is_time_followup",
        False,
    ):
        return None

    previous_question = (
        _get_previous_question(
            conversation_state
        )
    )

    print("=" * 30)
    print("TIME BUILDER")
    print("conversation state", conversation_state)
    print("previous question", previous_question)
    print("=" * 30)

    if not previous_question:
        print(
            "time builder failed: "
            "No previous question found"
        )

        return None

    previous_question = (
        _remove_existing_time_phrase(
            previous_question
        )
    )

    time_type = time_result.get(
        "time_type"
    )

    if time_type == "season":

        season = time_result.get(
            "time_value"
        )

        if not season:
            return None

        return (
            f"{previous_question} "
            f"in IPL season {season}?"
        )

    if time_type == "start_year":

        start_year = time_result.get(
            "start_year"
        )

        if not start_year:
            return None

        return (
            f"{previous_question} "
            f"from IPL season {start_year} onward?"
        )

    if time_type == "end_year":

        end_year = time_result.get(
            "end_year"
        )

        if not end_year:
            return None

        return (
            f"{previous_question} "
            f"through IPL season {end_year}?"
        )

    if time_type == "range":

        start_year = time_result.get(
            "start_year"
        )

        end_year = time_result.get(
            "end_year"
        )

        if not start_year or not end_year:
            return None

        return (
            f"{previous_question} "
            f"from IPL season {start_year} "
            f"through IPL season {end_year}?"
        )

    return None