
import re

from agent.ipl_ontology import IPL_ONTOLOGY

def detect_ontology_elements(question: str):

    question = question.lower().strip()

    detected = {

        "metric": False,
        "phase": False,
        "concept": False,
        "role": False,
        "season": False,
        "question": False
    }

    #
    # Metrics
    #

    for metric in IPL_ONTOLOGY["metrics"]:

        if metric in question:

            detected["metric"] = True
            break

    #
    # Phases
    #

    for phase in IPL_ONTOLOGY["phases"]:

        if phase in question:

            detected["phase"] = True
            break

    #
    # Concepts
    #

    for concept in IPL_ONTOLOGY["concepts"]:

        if concept in question:

            detected["concept"] = True
            break

    for word in IPL_ONTOLOGY["question_words"]:

        if word in question:

            detected["question"] = True
            break
    #
    # Roles
    #

    for role in IPL_ONTOLOGY["roles"]:

        if role in question:

            detected["role"] = True
            break

    #
    # Season Detection
    #

    if re.search(
        r"\b20\d{2}\b",
        question
    ):
        detected["season"] = True

    return detected
