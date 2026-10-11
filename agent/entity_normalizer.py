"""
Entity Normalizer

Normalizes IPL player names,
team names and venue names
to the names stored in the database.
"""

from difflib import get_close_matches


# --------------------------------------------------
# Teams
# --------------------------------------------------

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


# --------------------------------------------------
# Players
# Normalize to database names
# --------------------------------------------------

PLAYER_ALIASES = {

    # Bumrah

    "bumrah": "JJ Bumrah",
    "jj bumrah": "JJ Bumrah",
    "j bumrah": "JJ Bumrah",
    "jasprit bumrah": "JJ Bumrah",

    # Kohli

    "kohli": "V Kohli",
    "virat": "V Kohli",
    "virat kohli": "V Kohli",

    # Rohit

    "rohit": "RG Sharma",
    "rohit sharma": "RG Sharma",

    # Dhoni

    "dhoni": "MS Dhoni",
    "ms dhoni": "MS Dhoni",

    # Rahul

    "rahul": "KL Rahul",
    "kl rahul": "KL Rahul",

    # Head

    "travis head": "TM Head",
    "head": "TM Head",

    # Abhishek

    "abhishek": "Abhishek Sharma",
    "abhishek sharma": "Abhishek Sharma",
}


# --------------------------------------------------
# Venues
# --------------------------------------------------

VENUES = [
    "Wankhede Stadium",
    "Eden Gardens",
    "M Chinnaswamy Stadium",
    "MA Chidambaram Stadium",
]


# --------------------------------------------------
# Normalize Entity
# --------------------------------------------------

def normalize_entity(text: str):

    """
    Convert user entity
    to the database entity.
    """

    if not text:
        return text

    cleaned = text.strip().lower()

    # Team alias

    if cleaned in TEAM_ALIASES:
        return TEAM_ALIASES[cleaned]

    # Player alias

    if cleaned in PLAYER_ALIASES:
        return PLAYER_ALIASES[cleaned]

    # Fuzzy match teams

    team_matches = get_close_matches(
        cleaned,
        TEAM_ALIASES.keys(),
        n=1,
        cutoff=0.7
    )

    if team_matches:
        return TEAM_ALIASES[
            team_matches[0]
        ]

    # Fuzzy match players

    player_matches = get_close_matches(
        cleaned,
        PLAYER_ALIASES.keys(),
        n=1,
        cutoff=0.7
    )

    if player_matches:
        return PLAYER_ALIASES[
            player_matches[0]
        ]

    return text.strip()