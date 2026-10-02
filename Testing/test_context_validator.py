import pytest
import sys
from pathlib import Path
import pandas as pd
import pathlib
sys.path.append(
        str(pathlib.Path(__file__).resolve().parent.parent)  
)

from guardrails.context_validator import validate_context

def test_valid_context():

    context = {
        "query_type": "ranking",
        "needs_insight": True,
        "row_count": 5,
        "top_result": {
            "player": "V Kohli"
        }
    }

    assert validate_context(
        context
    ) is True

def test_missing_field():

    context = {
        "query_type": "ranking",
        "needs_insight": True,
        "row_count": 5
        
    }

    with pytest.raises(
        ValueError,
        match="Missing context field: top_result"
    ):
        validate_context(context)
