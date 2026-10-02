"""
Answer validation layer.

Validates generated answers before
showing them to the user.
"""


def validate_answer(answer):
    """
    Validate generated answer.

    Raises:
        ValueError
            If answer is invalid.
    """

    # None check
    if answer is None:
        raise ValueError(
            "Answer was not generated."
        )

    # Empty string
    if not answer.strip():
        raise ValueError(
            "Answer is empty."
        )

    # Very short response
    if len(answer.strip()) < 10:
        raise ValueError(
            "Answer is too short."
        )

    return True