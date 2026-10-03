
"""
Metric Follow-Up Resolver

Detects when a user changes the metric
within an existing conversation.
"""

METRICS = {
    "strike rate": "strike_rate",
    "batting average": "average",
    "average": "average",
    "sixes": "sixes",
    "fours": "fours",
    "wickets": "wickets",
    "economy rate": "economy",
    "economy": "economy",
    "matches played": "matches_played",
    "matches": "matches_played",
}


FOLLOWUP_PATTERNS = [
    "what about",
    "how about",
    "what if",
    "instead",
    "only",
]


def detect_metric_followup(
    question: str
):
    """
    Detect a metric-aware follow-up.

    A metric keyword alone is not enough.
    The message must also contain follow-up wording.
    """

    if not question:
        return {
            "is_metric_followup": False,
            "metric": None,
        }

    normalized_question = (
        question
        .strip()
        .lower()
        .replace("?", "")
        .replace(".", "")
        .replace("!", "")
        .replace(",", "")
    )

    has_followup_pattern = any(
        pattern in normalized_question
        for pattern in FOLLOWUP_PATTERNS
    )

    if not has_followup_pattern:
        return {
            "is_metric_followup": False,
            "metric": None,
        }

    for metric_text, metric_name in METRICS.items():

        if metric_text in normalized_question:
            return {
                "is_metric_followup": True,
                "metric": metric_name,
            }

    return {
        "is_metric_followup": False,
        "metric": None,
    }