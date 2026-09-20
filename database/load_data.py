import duckdb

# Connect to database
conn = duckdb.connect("ipl.db")

# Drop existing tables
conn.execute("DROP TABLE IF EXISTS matches")
conn.execute("DROP TABLE IF EXISTS deliveries")

# Load matches data
conn.execute("""
CREATE TABLE matches AS
SELECT *
FROM read_csv_auto(
    'data/ipl_matches_clean.csv',
    HEADER = TRUE,
    sample_size = -1,
    types = {
        'season':'VARCHAR'
    }
)
""")

# Load deliveries data
conn.execute("""
CREATE TABLE deliveries AS
SELECT *
FROM read_csv_auto(
    'data/ipl_ball_by_ball_clean.csv',
    HEADER = TRUE,
    sample_size = -1,
    types = {
        'season':'VARCHAR'
    }
)
""")

# Verify row counts
matches = conn.execute(
    "SELECT COUNT(*) FROM matches"
).fetchone()[0]

deliveries = conn.execute(
    "SELECT COUNT(*) FROM deliveries"
).fetchone()[0]

print(f"✅ Matches Loaded : {matches:,}")
print(f"✅ Deliveries Loaded : {deliveries:,}")

conn.close()