# cleanup_data.py

import duckdb

conn = duckdb.connect("ipl.db")

conn.execute("""
UPDATE deliveries
SET wicket_fielders = NULL
WHERE LOWER(TRIM(wicket_fielders)) = 'none'
""")

conn.commit()

print("Cleanup completed.")

conn.close()