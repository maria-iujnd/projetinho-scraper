
#!/usr/bin/env python3
"""
Test schema versioning (state_store as source of truth).
"""
import os
import sqlite3
import state_store

# Clean up
db_path = "test_schema.db"
if os.path.exists(db_path):
    os.remove(db_path)

print("=== Test 1: Create new DB ===")
state_store.setup_database(db_path)
print("✓ DB created")

# Check version (schema_meta é controlado pelo state_store)
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT version FROM schema_meta")
row = cursor.fetchone()
assert row is not None, "schema_meta row missing"

EXPECTED_VERSION = state_store.SCHEMA_VERSION
print(f"Schema version in DB: {row[0]}")
assert row[0] == EXPECTED_VERSION, f"Should be version {EXPECTED_VERSION}"

# Check tables expected in schema v4
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {r[0] for r in cursor.fetchall()}
expected_tables = {
    "schema_meta",
    "route_date_state",
    "announcements",
    "rt_price_history",
}

missing = expected_tables - tables
assert not missing, f"Missing tables: {missing}"

conn.close()

print("\n=== Test 2: Re-init same DB (should not duplicate schema) ===")
state_store.setup_database(db_path)
print("✓ DB re-opened")

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT COUNT(*) FROM schema_meta")
count = cursor.fetchone()[0]
assert count == 1, "schema_meta should have exactly 1 row"
conn.close()

print("\n=== Test 3: Check function consistency ===")
state_store.mark_announced("test_hash_123", db_path=db_path, trip_type="OW")
print("✓ mark_announced() works")

conn = sqlite3.connect(db_path)
cursor = conn.execute(
    "SELECT trip_type FROM announcements WHERE offer_hash='test_hash_123'"
)
row = cursor.fetchone()
assert row is not None, "offer_hash not found"
assert row[0] in ("OW", "RT"), f"unexpected trip_type: {row[0]}"
conn.close()

print("\n✅ All schema versioning tests passed!")

# Cleanup
import gc
gc.collect()
import time
for _ in range(3):
    try:
        os.remove(db_path)
        break
    except PermissionError:
        time.sleep(0.5)
for ext in ("-wal", "-shm"):
    if os.path.exists(db_path + ext):
        try:
            os.remove(db_path + ext)
        except PermissionError:
            time.sleep(0.5)
            os.remove(db_path + ext)
