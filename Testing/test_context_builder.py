

# Testing/test_context_builder.py
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)
import pandas as pd

from agent.context_builder import (
    build_context,
    detect_season,
)


def test_detect_season_2020():

    season = detect_season(
        "Who scored the most runs "
        "in IPL season 2020?"
    )

    assert season == "2020"


def test_no_season():

    season = detect_season(
        "Who scored the most runs?"
    )

    assert season is None


def test_context_stores_season():

    result_df = pd.DataFrame(
        [
            {
                "batter": "KL Rahul",
                "total_runs": 676.0,
            }
        ]
    )

    context = build_context(
        (
            "Who scored the most runs "
            "in IPL season 2020?"
        ),
        result_df,
    )

    assert context["season"] == "2020"
    assert context["metric"] == "total_runs"
    assert context["top_entity"] == "KL Rahul"