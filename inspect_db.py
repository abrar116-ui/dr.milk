import sqlite3
import os

db_path = 'instance/drmilk.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

for table in tables:
    name = table[0]
    print(f"\n--- {name} ---")
    c.execute(f'PRAGMA table_info("{name}")')
    print(c.fetchall())

conn.close()
