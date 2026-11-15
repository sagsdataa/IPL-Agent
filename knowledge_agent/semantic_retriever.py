import json
from pathlib import Path

import numpy as np
from knowledge_agent.embedding_service import (
    generate_embedding,
)

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

INDEX_PATH = ( 
    PROJECT_ROOT / "knowledge_index.json"
)

##############################################################################################
#           load knowledge index jsonfile
########################################################################

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

        knowledge_index = json.load(
            file
        )

    return knowledge_index

##############################################################################################
#           cosine similarity
########################################################################

def cosine_similarity(
    vector_a,
    vector_b,
):

    a = np.array(
        vector_a,
        dtype=np.float32,
    )

    b = np.array(
        vector_b,
        dtype=np.float32,
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

##############################################################################################
#           SEMANTIC SEARCH
##############################################################################################
def semantic_search(
    question: str,
    top_k: int = 3,
    threshold: float = 0.65
):

    if not question or not question.strip():
        return []

    # Load our 208 pre-built chunks
    knowledge_index = load_knowledge_index()

    # Convert the user's question into
    # the same 3072-dimensional vector
    question_embedding = generate_embedding(
        question
    )

    results = []

    # Compare the question with every chunk
    for chunk in knowledge_index:

        similarity = cosine_similarity(
            question_embedding,
            chunk["embedding"],
        )

        results.append(
            {
                "score": similarity,
                "source": chunk["source"],
                "category": chunk["category"],
                "title": chunk["title"],
                "section": chunk["section"],
                "text": chunk["text"],
            }
        )

    # Highest similarity first
    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    qualified_results = [
        result
        for result in results
        if result["score"] >= threshold
    ]


    # Return best matches
    return qualified_results[:top_k]


if __name__ == "__main__":

    question = (
        "Tell me about Ruturaj Gaikwad's playing style?"
    )
        
    results = semantic_search(
        question,
        top_k=3,
    )

    if not results:

        print("\nQUESTION:", question)
        print("NO SEMANTIC MATCH")

    else:
        for rank, result in enumerate(
            results,
            start=1,
        ):

            print(
                rank,
                round(result["score"], 4),
                result["title"],
                result["section"],
            )
           