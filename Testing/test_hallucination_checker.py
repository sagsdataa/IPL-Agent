import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from guardrails.hallucination_checker import (
    check_hallucination
)


# ======================================
# GROUNDED ANSWER
# ======================================

def test_grounded_answer():

    context = {
        "top_result": {
            "bowler": "YS Chahal",
            "wickets": 228
        }
    }

    answer = (
        "YS Chahal leads all bowlers "
        "with 228 wickets."
    )

    result = check_hallucination(
        answer,
        context
    )

    assert result["grounded"] is True
    assert len(
        result["unsupported_entities"]
    ) == 0


# ======================================
# HALLUCINATED PLAYER
# ======================================

def test_hallucinated_player():

    context = {
        "top_result": {
            "bowler": "YS Chahal",
            "wickets": 228
        }
    }

    answer = (
        "Jasprit Bumrah is the best bowler."
    )

    result = check_hallucination(
        answer,
        context
    )

    assert result["grounded"] is False


# ======================================
# UNSUPPORTED ENTITY
# ======================================

def test_detect_unsupported_entity():

    context = {
        "top_result": {
            "bowler": "YS Chahal"
        }
    }

    answer = (
        "Bumrah leads the tournament."
    )

    result = check_hallucination(
        answer,
        context
    )

    assert (
        "bumrah"
        in result["unsupported_entities"]
    )


# ======================================
# SECOND RESULT SUPPORTED
# ======================================

def test_second_result_supported():

    context = {
        "top_result": {
            "player": "V Kohli"
        },
        "second_result": {
            "player": "RG Sharma"
        }
    }

    answer = (
        "V Kohli leads RG Sharma "
        "in total runs."
    )

    result = check_hallucination(
        answer,
        context
    )

    assert result["grounded"] is True


# ======================================
# EMPTY ANSWER
# ======================================

def test_empty_answer():

    result = check_hallucination(
        "",
        {
            "top_result": {
                "player": "V Kohli"
            }
        }
    )

    assert result["grounded"] is False


# ======================================
# NONE ANSWER
# ======================================

def test_none_answer():

    result = check_hallucination(
        None,
        {
            "top_result": {
                "player": "V Kohli"
            }
        }
    )

    assert result["grounded"] is False