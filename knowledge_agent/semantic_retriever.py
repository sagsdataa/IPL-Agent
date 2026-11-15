import json
import re
from pathlib import Path

import numpy as np

from knowledge_agent.embedding_service import (
    generate_embedding,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

INDEX_PATH = (
    PROJECT_ROOT
    / "knowledge_index.json"
)


# ============================================================
# LOAD KNOWLEDGE INDEX
# ============================================================

def load_knowledge_index():

    if not INDEX_PATH.exists():

        raise FileNotFoundError(
            f"Knowledge index not found: "
            f"{INDEX_PATH}"
        )

    with open(
        INDEX_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        knowledge_index = json.load(file)

    return knowledge_index


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(
    vector_a,
    vector_b,
):

    a = np.asarray(
        vector_a,
        dtype=np.float32,
    )

    b = np.asarray(
        vector_b,
        dtype=np.float32,
    )

    if a.shape != b.shape:

        raise ValueError(
            "Embedding dimensions do not match: "
            f"{a.shape} vs {b.shape}"
        )

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    similarity = (
        np.dot(a, b)
        / denominator
    )

    return float(similarity)


# ============================================================
# NORMALIZE ENTITY NAME
# ============================================================

def normalize_entity_name(
    value: str,
) -> str:

    if not value:
        return ""

    normalized = (
        str(value)
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )

    normalized = re.sub(
        r"[^a-z0-9\s]",
        "",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


# ============================================================
# EXTRACT PLAYER FROM PLAYER-SPECIFIC QUESTIONS
# ============================================================

def extract_requested_player(
    question: str,
):

    if not question:
        return None

    normalized_question = (
        question
        .lower()
        .strip()
    )

    player_patterns = (

        # Tell me about Ruturaj Gaikwad's playing style
        # Tell me about Rohit Sharma's batting style
        (
            r"tell\s+me\s+about\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"(?:playing|batting|bowling)\s+style"
        ),

        # Tell me about Ruturaj Gaikwad playing style
        (
            r"tell\s+me\s+about\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"\s+(?:playing|batting|bowling)\s+style"
        ),

        # Describe Dhoni's playing style
        (
            r"describe\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"(?:playing|batting|bowling)\s+style"
        ),

        # Describe Dhoni playing style
        (
            r"describe\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"\s+(?:playing|batting|bowling)\s+style"
        ),

        # What makes Rashid Khan's bowling distinctive?
        (
            r"what\s+makes\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"(?:playing|batting|bowling)"
        ),

        # What are Dhoni's major achievements?
        (
            r"what\s+are\s+"
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"(?:major\s+)?achievements?"
        ),

        # Dhoni's playing style
        # Rashid Khan's bowling style
        (
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"(?:playing|batting|bowling)\s+style"
        ),

        # Dhoni playing style
        (
            r"^(?P<name>[a-z][a-z\s._-]+?)"
            r"\s+(?:playing|batting|bowling)\s+style$"
        ),

        # Dhoni's career summary
        (
            r"(?P<name>[a-z][a-z\s._-]+?)"
            r"['’]s\s+"
            r"career\s+summary"
        ),
    )

    for pattern in player_patterns:

        match = re.search(
            pattern,
            normalized_question,
        )

        if not match:
            continue

        player_name = normalize_entity_name(
            match.group("name")
        )

        if player_name:
            return player_name

    return None


# ============================================================
# PLAYER ENTITY MATCHING
# ============================================================

def player_entity_matches(
    requested_player: str,
    retrieved_title: str,
) -> bool:

    requested = normalize_entity_name(
        requested_player
    )

    retrieved = normalize_entity_name(
        retrieved_title
    )

    if not requested or not retrieved:
        return False

    # Exact normalized match
    if requested == retrieved:
        return True

    # Supports short-name matching:
    # dhoni -> ms dhoni
    # kohli -> virat kohli
    # bumrah -> jasprit bumrah
    if requested in retrieved:
        return True

    if retrieved in requested:
        return True

    requested_tokens = set(
        requested.split()
    )

    retrieved_tokens = set(
        retrieved.split()
    )

    # Ignore initials and very short words.
    requested_significant = {
        token
        for token in requested_tokens
        if len(token) >= 4
    }

    retrieved_significant = {
        token
        for token in retrieved_tokens
        if len(token) >= 4
    }

    common_tokens = (
        requested_significant
        & retrieved_significant
    )

    return bool(common_tokens)


# ============================================================
# CHECK PLAYER CATEGORY
# ============================================================

def is_player_result(
    result,
) -> bool:

    category = normalize_entity_name(
        result.get("category")
    )

    return category in {
        "player",
        "players",
    }


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(
    question: str,
    top_k: int = 3,
    threshold: float = 0.65,
    entity_aware: bool = True,
):

    if not question or not question.strip():
        return []

    if top_k <= 0:
        return []

    knowledge_index = (
        load_knowledge_index()
    )

    if not knowledge_index:
        return []

    # Generate only one embedding for the question.
    question_embedding = (
        generate_embedding(
            question.strip()
        )
    )

    requested_player = None

    if entity_aware:

        requested_player = (
            extract_requested_player(
                question
            )
        )

    results = []

    # Compare question embedding against
    # every stored chunk embedding.
    for chunk in knowledge_index:

        chunk_embedding = chunk.get(
            "embedding"
        )

        if not chunk_embedding:
            continue

        similarity = cosine_similarity(
            question_embedding,
            chunk_embedding,
        )

        results.append(
            {
                "score": similarity,
                "source": chunk.get(
                    "source",
                    "",
                ),
                "category": chunk.get(
                    "category",
                    "",
                ),
                "title": chunk.get(
                    "title",
                    "",
                ),
                "section": chunk.get(
                    "section",
                    "",
                ),
                "text": chunk.get(
                    "text",
                    "",
                ),
            }
        )

    # Highest similarity first.
    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Keep only results that pass
    # the similarity threshold.
    qualified_results = [
        result
        for result in results
        if result["score"] >= threshold
    ]

    # ========================================================
    # ENTITY-AWARE PLAYER VALIDATION
    # ========================================================

    if requested_player:

        matching_player_results = [
            result
            for result in qualified_results
            if (
                is_player_result(result)
                and player_entity_matches(
                    requested_player,
                    result["title"],
                )
            )
        ]

        # A specific player was requested, but the
        # index does not contain a matching profile.
        #
        # Example:
        # Requested: Ruturaj Gaikwad
        # Retrieved: KL Rahul
        #
        # Return no match rather than providing
        # another player's information.
        if not matching_player_results:
            return []

        return matching_player_results[:top_k]

    return qualified_results[:top_k]


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_questions = (
        "Describe Dhoni's playing style",
        (
            "Tell me about Ruturaj "
            "Gaikwad's playing style"
        ),
        "How did the IPL begin?",
        "How does quantum computing work?",
    )

    for test_question in test_questions:

        print("\n" + "=" * 80)

        print(
            "QUESTION:",
            test_question,
        )

        requested_player = (
            extract_requested_player(
                test_question
            )
        )

        print(
            "REQUESTED PLAYER:",
            requested_player,
        )

        search_results = semantic_search(
            question=test_question,
            top_k=3,
            threshold=0.65,
            entity_aware=True,
        )

        if not search_results:

            print(
                "RESULT: NO SEMANTIC MATCH"
            )

            continue

        for rank, result in enumerate(
            search_results,
            start=1,
        ):

            print(
                f'{rank}. '
                f'{result["title"]} | '
                f'{result["section"]} | '
                f'{result["score"]:.4f}'
            )