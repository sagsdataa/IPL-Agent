from knowledge_agent.semantic_retriever import (
    semantic_search,
)

from knowledge_agent.knowledge_agent import (
    generate_knowledge_answer,
)


def generate_semantic_knowledge_answer(
    question: str,
    top_k: int = 3,
    threshold: float = 0.65,
):

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    # --------------------------------------------------
    # STEP 1
    # Retrieve semantically relevant chunks
    # --------------------------------------------------

    results = semantic_search(
        question=question,
        top_k=top_k,
        threshold=threshold,
    )

    # --------------------------------------------------
    # STEP 2
    # No trustworthy semantic match
    # --------------------------------------------------

    if not results:

        return {
            "answer": (
                "The retrieved knowledge does not contain "
                "enough information to answer this question."
            ),
            "sources": [],
        }

    # --------------------------------------------------
    # STEP 3
    # Build grounded context
    # --------------------------------------------------

    context_parts = []

    for result in results:

        context_part = f"""
Title: {result["title"]}
Section: {result["section"]}
Source: {result["source"]}
Similarity Score: {result["score"]:.4f}

{result["text"]}
"""

        context_parts.append(
            context_part.strip()
        )

    retrieved_context = "\n\n---\n\n".join(
        context_parts
    )

    # --------------------------------------------------
    # STEP 4
    # Send only retrieved knowledge to Gemini
    # --------------------------------------------------

    answer = generate_knowledge_answer(
        question,
        retrieved_context,
    )

    # --------------------------------------------------
    # STEP 5
    # Preserve source information
    # --------------------------------------------------

    sources = []

    for result in results:

        sources.append(
            {
                "title": result["title"],
                "section": result["section"],
                "source": result["source"],
                "score": result["score"],
            }
        )

    return {
        "answer": answer,
        "sources": sources,
    }


# ======================================================
# LOCAL TEST
# ======================================================

if __name__ == "__main__":

    question = (
        "Tell me about Ruturaj Gaikwad's playing style?"
    )

    response = (
        generate_semantic_knowledge_answer(
            question
        )
    )

    print("\n" + "=" * 70)
    print("QUESTION:")
    print(question)

    print("\nANSWER:")
    print(response["answer"])

    print("\nSOURCES:")

    if not response["sources"]:

        print("No semantic source found.")

    else:

        for source in response["sources"]:

            print(
                f'- {source["title"]} | '
                f'{source["section"]} | '
                f'{source["score"]:.4f}'
            )

    print("=" * 70)