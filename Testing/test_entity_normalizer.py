
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from agent.entity_normalizer import normalize_entity

def test_team_alias():

    assert (
        normalize_entity("srh")
        ==
        "Sunrisers Hyderabad"
    )


def test_team_typo():

    assert (
        normalize_entity(
            "mumbai indains"
        )
        ==
        "Mumbai Indians"
    )


def test_player_typo():

    assert (
        normalize_entity(
            "virat kohhli"
        )
        ==
        "Virat Kohli"
    )


def test_venue_typo():

    assert (
        normalize_entity(
            "wankhede statium"
        )
        ==
        "Wankhede Stadium"
    )