"""Migrate data from Supabase Cloud to local OCI Postgres via REST API."""

import json
import os

import psycopg2
import requests as req
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

conn = psycopg2.connect(
    host="localhost", port=5432, dbname="shopagent",
    user="shopagent", password="shopagent",
)
cur = conn.cursor()

tables = ["customers", "products", "orders"]

for table in tables:
    print(f"Exporting {table}...")
    offset = 0
    total = 0
    while True:
        resp = req.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            params={"select": "*", "limit": 1000, "offset": offset},
        )
        if resp.status_code != 200:
            print(f"  Error: {resp.status_code} - {resp.text[:100]}")
            break
        rows = resp.json()
        if not rows:
            break
        for row in rows:
            cols = ", ".join(row.keys())
            vals = ", ".join(f"%({k})s" for k in row)
            cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals}) ON CONFLICT DO NOTHING", row)
        conn.commit()
        total += len(rows)
        offset += len(rows)
        print(f"  {total} rows imported...")
    print(f"  Done: {total} rows in {table}")

cur.close()
conn.close()
print("\nMigration complete!")
