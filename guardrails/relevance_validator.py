
from agent.ontology_detector import (
    detect_ontology_elements
)

def is_ipl_relevant(question):

    ontology = (
        detect_ontology_elements(
            question
        )
    )

    return any(
        ontology.values()
    )

    if not is_relevant:

        raise ValueError(
            "I couldn't identify any IPL concept, metric, season, match, venue, player, or team reference in your question."
        )