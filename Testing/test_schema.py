# test_schema.py

import duckdb

conn = duckdb.connect("ipl.db")

conn.execute("""
copy(SELECT DISTINCT batter AS player from deliveries

union

SELECT DISTINCT bowler AS player from deliveries
order by player
) TO 'D:/players.csv' (HEADER,DELIMITER ',')
""")

conn.close()