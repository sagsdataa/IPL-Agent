# knowledge_router.py

class KnowledgeRouter:

    def __init__(self):

        self.knowledge_patterns = [

            "who is",
            "tell me about",
            "about",
            "what is",
            "what are",
            "history of",
            "explain",
            "describe"
        ]

    def is_knowledge_query(
        self,
        question
    ):

        question = question.lower()

        return any(
            pattern in question
            for pattern in self.knowledge_patterns
        )