"""
Entity Normalizer

Normalizes IPL player names,
team names and venue names.
"""

from difflib import get_close_matches


TEAMS = [
    "Chennai Super Kings",
    "Mumbai Indians",
    "Sunrisers Hyderabad",
    "Royal Challengers Bangalore",
    "Kolkata Knight Riders",
    "Rajasthan Royals",
    "Delhi Capitals",
    "Punjab Kings",
    "Lucknow Super Giants",
    "Gujarat Titans",
]

TEAM_ALIASES = {
    "csk": "Chennai Super Kings",
    "mi": "Mumbai Indians",
    "srh": "Sunrisers Hyderabad",
    "rcb": "Royal Challengers Bangalore",
    "kkr": "Kolkata Knight Riders",
    "rr": "Rajasthan Royals",
    "dc": "Delhi Capitals",
    "pbks": "Punjab Kings",
    "lsg": "Lucknow Super Giants",
    "gt": "Gujarat Titans",
}

PLAYERS = [
    "Virat Kohli",
    "Rohit Sharma",
    "MS Dhoni",
    "KL Rahul",
    "Jasprit Bumrah",
    "Abhishek Sharma",
    "Travis Head",
    "David Warner",
]

VENUES = [
    "Wankhede Stadium",
    "Eden Gardens",
    "M Chinnaswamy Stadium",
    "MA Chidambaram Stadium",
]


def normalize_entity(
    text: str
):
    """
    Return the best matching IPL entity.
    """

    if not text:
        return text

    cleaned = text.strip()

    #
    # Team aliases
    #
    alias = TEAM_ALIASES.get(
        cleaned.lower()
    )

    if alias:
        return alias

    candidates = (
        TEAMS
        + PLAYERS
        + VENUES
    )

    matches = get_close_matches(
        cleaned,
        candidates,
        n=1,
        cutoff=0.7,
    )

    if matches:
        return matches[0]

    return text