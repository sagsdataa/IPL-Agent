import duckdb

conn = duckdb.connect("ipl.db")

result = conn.execute("""
SELECT
    batter,
    SUM(batter_runs) AS runs
FROM deliveries
GROUP BY batter
ORDER BY runs DESC
LIMIT 10
""").fetchdf()

print(result)

conn.close()