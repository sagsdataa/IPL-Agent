# test_schema.py

import duckdb

conn = duckdb.connect("ipl.db")

print(
    conn.execute(
        "DESCRIBE deliveries"
    ).fetchdf()

)

conn.close()