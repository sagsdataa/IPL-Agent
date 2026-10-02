import pytest
import sys
from pathlib import Path
import pandas as pd
import pathlib
sys.path.append(
        str(pathlib.Path(__file__).resolve().parent.parent)  
)

from guardrails.result_validator import validate_result


def test_none_result():

    with pytest.raises(
        ValueError,
        match="Query returned no result"
    ):
        validate_result(None)


def test_empty_dataframe():

    df = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="No matching records found"
    ):
        validate_result(df)


def test_valid_dataframe():

    df = pd.DataFrame(
        {
            "player": ["V Kohli"],
            "runs": [9050]
        }
    )

    assert validate_result(df) is True