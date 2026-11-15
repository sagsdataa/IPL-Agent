from knowledge_agent.semantic_retriever import (
    extract_requested_player,
    normalize_entity_name,
    player_entity_matches,
    semantic_search,
)


def test_normalize_player_filename():

    assert normalize_entity_name(
        "ms_dhoni"
    ) == "ms dhoni"


def test_extract_dhoni_from_possessive_question():

    player = extract_requested_player(
        "Describe Dhoni's playing style"
    )

    assert player == "dhoni"


def test_extract_ruturaj_from_profile_question():

    player = extract_requested_player(
        "Tell me about Ruturaj Gaikwad's playing style"
    )

    assert player == "ruturaj gaikwad"


def test_short_name_matches_full_player_title():

    assert player_entity_matches(
        "dhoni",
        "ms_dhoni",
    )


def test_different_players_do_not_match():

    assert not player_entity_matches(
        "ruturaj gaikwad",
        "kl_rahul",
    )


def test_known_player_retrieval_succeeds():

    results = semantic_search(
        question="Describe Dhoni's playing style",
        top_k=3,
        threshold=0.65,
    )

    assert results
    assert results[0]["title"] == "ms_dhoni"
    assert results[0]["section"] == "Playing Style"


def test_missing_player_profile_returns_no_match():

    results = semantic_search(
        question=(
            "Tell me about Ruturaj "
            "Gaikwad's playing style"
        ),
        top_k=3,
        threshold=0.65,
    )

    assert results == []