
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from agent.metric_resolver import (
    detect_metric_followup
)

def test_strike_rate():

    result = detect_metric_followup(
        "What about strike rate?"
    )

    assert (
        result["is_metric_followup"]
        is True
    )

    assert (
        result["metric"]
        == "strike_rate"
    )