import pandas as pd

from agent.insight_generator import (
    generate_insight
)

data = {
    "fielder": [
        "MS Dhoni",
        "KD Karthik",
        "AB de Villiers"
    ],
    "total_dismissals": [
        221,
        191,
        134
    ]
}

df = pd.DataFrame(data)

question = """
Who is the best fielder in IPL history?
"""

insight = generate_insight(
    question,
    df
)

print(insight)