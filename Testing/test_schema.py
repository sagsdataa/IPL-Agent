# test_schema.py

import duckdb

conn = duckdb.connect("ipl.db")

result = conn.execute("""
SELECT
    date,
    team1,
    team2,
    winner
FROM matches
WHERE TRY_CAST(
    SUBSTRING(season, 1, 4)
    AS INTEGER
) = 2020
ORDER BY date DESC
limit 10;
""").fetchdf()
print(result)

conn.close()