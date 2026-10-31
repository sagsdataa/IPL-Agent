# knowledge_router.py

def detect_knowledge_intent(
        question: str
            
):      
        """
        Detect whether the user is asking for descriptive knowledge rather
        than statistical analysis.
        """
      
        if not question:
            return False

        cleaned = (
                question
                .lower()
                .strip()
        )

        knowledge_patterns = (

            "who is ",
            "tell me about ",
            "about ",
            "what is ",
            "what are ",
            "history of ",
            "explain ",
            "describe ",
            "profile of ",
            "meaning of ",
            "ipl history ",
            "IPL history ",
            

        )

        return cleaned.startswith(
            knowledge_patterns
        )