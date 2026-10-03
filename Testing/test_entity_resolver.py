import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from agent.entity_resolver import (
    detect_entity_followup
)


def test_why_not_bumrah():

    result = detect_entity_followup(
        "Why not Bumrah?"
    )

    assert (
        result["is_entity_followup"]
        is True
    )

    assert (
        result["entity"]
        == "Bumrah"
    )


def test_what_about_dhoni():

    result = detect_entity_followup(
        "What about Dhoni?"
    )

    assert (
        result["entity"]
        == "Dhoni"
    )


def test_how_about_rohit():

    result = detect_entity_followup(
        "How about Rohit?"
    )

    assert (
        result["entity"]
        == "Rohit"
    )


def test_normal_why():

    result = detect_entity_followup(
        "Why?"
    )

    assert (
        result["is_entity_followup"]
        is False
    )


def test_are_you_sure():

    result = detect_entity_followup(
        "Are you sure?"
    )

    assert (
        result["is_entity_followup"]
        is False
    )