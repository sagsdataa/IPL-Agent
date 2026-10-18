# test_knowledge.py
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from knowledge_agent.knowledge_router import KnowledgeRouter
from knowledge_agent.knowledge_retriever import KnowledgeRetriever

router = KnowledgeRouter()

retriever = KnowledgeRetriever()

question = "Who is MS Dhoni?"

if router.is_knowledge_query(question):

    content = retriever.load_document(question)

    print(content)

else:

    print(
        "Not a knowledge query"
    )