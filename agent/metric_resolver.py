"""
Metric Follow-Up Resolver

Detects short metric-only follow-ups such as:

- Strike rate?
- Economy?
- Average?
- Wickets?
- Sixes?
"""

import re


METRIC_ALIASES = {
    "run": "runs",
    "runs": "runs",
    "total runs": "runs",

    "wicket": "wickets",
    "wickets": "wickets",
    "total wickets": "wickets",

    "strike rate": "strike rate",
    "batting strike rate": "strike rate",

    "economy": "economy rate",
    "economy rate": "economy rate",
    "bowling economy": "economy rate",

    "average": "average",
    "batting average": "batting average",
    "bowling average": "bowling average",

    "six": "sixes",
    "sixes": "sixes",

    "four": "fours",
    "fours": "fours",

    "dot ball": "dot balls",
    "dot balls": "dot balls",

    "catch": "catches",
    "catches": "catches",

    "win percentage": "win percentage",
    "wins": "wins",
}


def _empty_result():

    return {
        "is_metric_followup": False,
        "metric": None,
    }


def detect_metric_followup(question: str):

    if not question or not question.strip():
        return _empty_result()

    cleaned = question.lower().strip()

    cleaned = re.sub(
        r"[?.,!]+$",
        "",
        cleaned,
    ).strip()

    # Only treat short metric phrases as follow-ups.
    # A complete question such as
    # "Who has the highest strike rate?"
    # must remain a standalone analytical question.

    words = cleaned.split()

    if len(words) > 4:
        return _empty_result()

    metric = METRIC_ALIASES.get(
        cleaned
    )

    if not metric:
        return _empty_result()

    return {
        "is_metric_followup": True,
        "metric": metric,
    }