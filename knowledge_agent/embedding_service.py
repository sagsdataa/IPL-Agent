from google import genai
import streamlit as st


client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


def generate_embedding(text: str):

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )

    return response.embeddings[0].values

if __name__ == "__main__":

    sample_text = """
    MS Dhoni is known for his leadership,
    wicketkeeping and finishing ability.
    """

    embedding = generate_embedding(
        sample_text
    )

    print(
        "Embedding dimensions:",
        len(embedding)
    )

    print(
        "First 10 values:",
        embedding[:10]
    )