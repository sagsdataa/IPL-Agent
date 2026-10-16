"""
Time Follow-Up Resolver

Detects short time-filter follow-ups such as:

- In 2020?
- From 2020 onward?
- Since 2018?
- From 2020 to 2024?

A complete question such as "Who won IPL 2020?"
must not be classified as a time follow-up.
"""

import re


TIME_FOLLOWUP_PREFIXES = (
    "in ",
    "from ",
    "during ",
    "after ",
    "before ",
    "since ",
    "until ",
    "between ",
)


def _empty_result():

    return {
        "is_time_followup": False,
        "time_type": None,
        "time_value": None,
        "start_year": None,
        "end_year": None,
    }


def detect_time_followup(question: str):

    if not question or not question.strip():
        return _empty_result()

    cleaned = question.lower().strip()

    cleaned = re.sub(
        r"[?.,!]+$",
        "",
        cleaned,
    ).strip()

    # A complete analytical question containing a year
    # is not automatically a time follow-up.
    #
    # Examples that should return False:
    # - Who won IPL 2020?
    # - IPL 2020 winner
    # - Top run scorer in IPL 2020

    if not cleaned.startswith(
        TIME_FOLLOWUP_PREFIXES
    ):
        return _empty_result()

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        cleaned,
    )

    if not years:
        return _empty_result()

    # From 2020 to 2024
    # Between 2020 and 2024

    if len(years) >= 2:

        return {
            "is_time_followup": True,
            "time_type": "range",
            "time_value": years,
            "start_year": years[0],
            "end_year": years[1],
        }

    year = years[0]

    # From 2020 onward
    # Since 2020
    # After 2020

    if (
        cleaned.startswith("from ")
        or cleaned.startswith("since ")
        or cleaned.startswith("after ")
        or "onward" in cleaned
        or "onwards" in cleaned
        or "later" in cleaned
    ):

        return {
            "is_time_followup": True,
            "time_type": "start_year",
            "time_value": year,
            "start_year": year,
            "end_year": None,
        }

    # Before 2020
    # Until 2020

    if (
        cleaned.startswith("before ")
        or cleaned.startswith("until ")
    ):

        return {
            "is_time_followup": True,
            "time_type": "end_year",
            "time_value": year,
            "start_year": None,
            "end_year": year,
        }

    # In 2020
    # During 2020

    return {
        "is_time_followup": True,
        "time_type": "season",
        "time_value": year,
        "start_year": None,
        "end_year": None,
    }