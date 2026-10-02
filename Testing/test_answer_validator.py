import pytest
from pathlib import Path
import sys

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from guardrails.answer_validator import (
    validate_answer
)


def test_none_answer():

    with pytest.raises(
        ValueError,
        match="Answer was not generated"
    ):
        validate_answer(None)


def test_empty_answer():

    with pytest.raises(
        ValueError,
        match="Answer is empty"
    ):
        validate_answer("")


def test_spaces_only_answer():

    with pytest.raises(
        ValueError,
        match="Answer is empty"
    ):
        validate_answer("     ")


def test_short_answer():

    with pytest.raises(
        ValueError,
        match="Answer is too short"
    ):
        validate_answer("Kohli")


def test_valid_answer():

    answer = (
        "YS Chahal leads all bowlers "
        "with 228 wickets."
    )

    assert validate_answer(
        answer
    ) is True