
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)


from agent.time_resolver import (
    detect_time_followup
)


def test_year_followup():

    result = detect_time_followup(
        "What about 2024?"
    )

    assert result["is_time_followup"] is True
    assert result["time_filter"] == "2024"


def test_playoffs_followup():

    result = detect_time_followup(
        "What about playoffs?"
    )

    assert result["is_time_followup"] is True
    assert result["time_filter"] == "playoffs"


def test_last_5_seasons():

    result = detect_time_followup(
        "What about last 5 seasons?"
    )

    assert result["is_time_followup"] is True


def test_normal_question():

    result = detect_time_followup(
        "Who scored the most runs?"
    )

    assert result["is_time_followup"] is False