
from pathlib import Path
import re

KNOWLEDGE_PATH = Path("knowledge")

def split_markdown_file(file_path: Path):

    content = file_path.read_text(
        encoding="utf-8"
    )

    # Get main document title
    title_match = re.search(
        r"^#\s+(.+)$",
        content,
        re.MULTILINE,
    )

    title = (
        title_match.group(1).strip()
        if title_match
        else file_path.stem
    )

    # Split document using ## headings
    sections = re.split(
        r"^##\s+(.+)$",
        content,
        flags=re.MULTILINE,
    )

    chunks = []

    # sections format:
    # [intro, heading1, text1, heading2, text2...]

    for i in range(1, len(sections), 2):

        section_name = sections[i].strip()
        section_text = sections[i + 1].strip()

        if not section_text:
            continue

        chunks.append(
            {
                "source": str(file_path),
                "category": file_path.parent.name,
                "title": title,
                "section": section_name,
                "text": section_text,
                "embedding": [3072] , # Placeholder for embedding values
            }
        )

    return chunks

def build_knowledge_chunks():

    all_chunks = []

    for file_path in KNOWLEDGE_PATH.rglob(
        "*.md"
    ):

        file_chunks = split_markdown_file(
            file_path
        )

        all_chunks.extend(
            file_chunks
        )

    return all_chunks

if __name__ == "__main__":

    chunks = build_knowledge_chunks()

    print(
        f"Total chunks: {len(chunks)}"
    )

    for chunk in chunks[:5]:

        print("\n" + "=" * 60)

        print(
            "SOURCE:",
            chunk["source"]
        )

        print(
            "CATEGORY:",
            chunk["category"]
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
            "TEXT:",
            chunk["text"][:300]
        )
