import json
import time
from pathlib import Path

from knowledge_agent.knowledge_indexer import (
    build_knowledge_chunks,
)

from knowledge_agent.embedding_service import (
    generate_embedding,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_PATH = (
    PROJECT_ROOT
    / "knowledge_index.json"
)


def build_embedding_index():

    chunks = build_knowledge_chunks()

    print(
        "Total chunks:",
        len(chunks)
    )

    embedded_chunks = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        text_for_embedding = f"""
Title: {chunk["title"]}
Category: {chunk["category"]}
Section: {chunk["section"]}

{chunk["text"]}
"""

        try:

            embedding = generate_embedding(
                text_for_embedding
            )

        except Exception as error:

            print(
                f"\nEmbedding failed "
                f"at chunk {index}"
            )

            print(
                "Error:",
                error
            )

            print(
                "\nWaiting 20 seconds "
                "before retrying..."
            )

            time.sleep(20)

            embedding = generate_embedding(
                text_for_embedding
            )

        chunk["embedding"] = embedding

        embedded_chunks.append(
            chunk
        )

        print("=" * 60)

        print(
            f"CHUNK {index}/{len(chunks)}"
        )

        print(
            "TITLE:",
            chunk["title"]
        )

        print(
            "SECTION:",
            chunk["section"]
        )

        print(
            "VECTOR SIZE:",
            len(embedding)
        )

        # Small delay to avoid hitting
        # the free-tier request limit.
        time.sleep(0.7)

    # Save only after all chunks complete

    with open(
        INDEX_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            embedded_chunks,
            file,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)

    print(
        "Semantic index created successfully."
    )

    print(
        "Total indexed chunks:",
        len(embedded_chunks)
    )

    print(
        "Index saved to:",
        INDEX_PATH
    )

    return embedded_chunks


if __name__ == "__main__":

    build_embedding_index()