# knowledge_retriever.py

import os


class KnowledgeRetriever:

    def __init__(self):

        self.base_path = "knowledge"

        self.entity_map = {

            # Players
            "ms dhoni": "players/ms_dhoni.md",
            "virat kohli": "players/virat_kohli.md",
            "rohit sharma": "players/rohit_sharma.md",
            "jasprit bumrah": "players/jasprit_bumrah.md",
            "rashid khan": "players/rashid_khan.md",
            "kl rahul": "players/kl_rahul.md",
            "ab de villiers": "players/ab_de_villiers.md",
            "hardik pandya": "players/hardik_pandya.md",
            "ravindra jadeja": "players/ravindra_jadeja.md",
            "shikhar dhawan": "players/shikhar_dhawan.md",            

            # Teams
            "csk": "teams/csk.md",
            "chennai super kings": "teams/csk.md",

            "mi": "teams/mi.md",
            "mumbai indians": "teams/mi.md",

            "rcb": "teams/rcb.md",
            "royal challengers bangalore": "teams/rcb.md",

            "kkr": "teams/kkr.md",
            "Kolkata Knight Riders": "teams/kkr.md",

            "gt": "teams/gt.md",
            "Gujarat Titans": "teams/gt.md",

            "dc": "teams/dc.md",
            "Delhi Capitals": "teams/dc.md",

            "lsg": "teams/lsg.md",
            "Lucknow Super Giants": "teams/lsg.md",

            "rr": "teams/rr.md",
            "Rajasthan Royals": "teams/rr.md",

            "srh": "teams/srh.md",
            "Sunrisers Hyderabad": "teams/srh.md",

            "pbks": "teams/PBKS.md",
            "Punjab Kings": "teams/PBKS.md",

            # Rules
            "powerplay": "rules/powerplay.md",
            "power play": "rules/powerplay.md",
            "powerply": "rules/powerplay.md",
            "impact player": "rules/impact_player.md",
            "orange cap": "rules/orange_cap.md",
            "purple cap": "rules/purple_cap.md",
            "dls": "rules/dls.md",
            "duckworth lewis": "rules/dls.md",
            "super over": "rules/super_over.md",
            "superover": "rules/super_over.md",

            # History
            "ipl history": "history/ipl_history.md",
            "history of the ipl": "history/ipl_history.md",
            "how did the ipl begin": "history/ipl_history.md",
            "origin of ipl": "history/ipl_history.md",
            "history ipl": "history/ipl_history.md",
            "finals history": "history/ipl_finals_history.md",
            "evolution of ipl": "history/evolution_of_ipl.md",
            "greatest ipl records": "history/greatest_ipl_records.md"
        }

    def find_document(self, question):

        question = question.lower()

        for entity, file_path in self.entity_map.items():

            if entity in question:

                return file_path

        return None

    def load_document(self, question):

        file_path = self.find_document(question)

        if not file_path:
            return None

        full_path = os.path.join(
            self.base_path,
            file_path
        )

        try:

            with open(
                full_path,
                "r",
                encoding="utf-8"
            ) as f:

                return f.read()

        except Exception as e:

            print(
                f"Error reading file: {e}"
            )

            return None