# tests/test_entity_resolver.py
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)
from agent.entity_resolver import (
    detect_entity_followup
)


# -------------------------------------------
# Valid Entity Follow-Ups
# -------------------------------------------

def test_why_not_dhoni():

    result = detect_entity_followup(
        "Why not Dhoni?"
    )

    assert result["is_entity_followup"] is True
    assert result["entity"] == "Dhoni"
    assert result["intent"] == "entity_followup"


def test_what_about_rohit():

    result = detect_entity_followup(
        "What about Rohit Sharma?"
    )

    assert result["is_entity_followup"] is True
    assert result["entity"] == "Rohit Sharma"
    assert result["intent"] == "entity_followup"


def test_how_about_bumrah():

    result = detect_entity_followup(
        "How about Bumrah?"
    )

    assert result["is_entity_followup"] is True
    assert result["entity"] == "Bumrah"
    assert result["intent"] == "entity_followup"


def test_compare_with_kohli():

    result = detect_entity_followup(
        "Compare with Kohli"
    )

    assert result["is_entity_followup"] is True
    assert result["entity"] == "Kohli"
    assert result["intent"] == "entity_followup"


# -------------------------------------------
# Time Follow-Up (should NOT be entity)
# -------------------------------------------

def test_reject_2020():

    result = detect_entity_followup(
        "What about 2020?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


def test_reject_2024():

    result = detect_entity_followup(
        "What about 2024?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


# -------------------------------------------
# Context Continuation / Role Terms
# -------------------------------------------

def test_reject_bowler():

    result = detect_entity_followup(
        "What about bowler?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


def test_reject_team():

    result = detect_entity_followup(
        "What about team?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


def test_reject_venue():

    result = detect_entity_followup(
        "What about venue?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


def test_reject_matches():

    result = detect_entity_followup(
        "What about matches?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


# -------------------------------------------
# Non Follow-Up Questions
# -------------------------------------------

def test_normal_question():

    result = detect_entity_followup(
        "Who scored the most runs?"
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None


def test_empty_question():

    result = detect_entity_followup(
        ""
    )

    assert result["is_entity_followup"] is False
    assert result["entity"] is None
    assert result["intent"] is None