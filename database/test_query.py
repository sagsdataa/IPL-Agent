import duckdb

conn = duckdb.connect("ipl.db")

result = conn.execute("""
SELECT * from player_dimension LIMIT 10
""").fetchdf()

print(result)

conn.close()