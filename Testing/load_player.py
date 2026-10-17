import duckdb

conn = duckdb.connect("ipl.db")

conn.execute("""
CREATE OR REPLACE TABLE player_dimension AS
SELECT *
FROM read_csv_auto(
    'data/player_dimension.csv'
)
""")

total = conn.execute("""
SELECT COUNT(*)
FROM player_dimension
""").fetchone()[0]

print(
    f"Loaded {total} players"
)

conn.close()