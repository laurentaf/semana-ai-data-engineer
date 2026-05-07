#!/usr/bin/env python3
"""
Verify Postgres data for ShopAgent Day 1
Connects to local Postgres and runs verification queries
"""

import psycopg2
from tabulate import tabulate

# Connection settings
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "shopagent",
    "user": "shopagent",
    "password": "shopagent"
}

conn = None
try:
    # Connect to Postgres
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("=== ShopAgent Postgres Verification ===\n")

    # 1. Count of rows in each table
    print("1. Row Counts:")
    tables = ["customers", "products", "orders"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count:,} rows")

    # 2. Sample 5 customers
    print("\n2. Sample Customers:")
    cursor.execute("""
        SELECT name, state, segment
        FROM customers
        LIMIT 5
    """)
    customers = cursor.fetchall()
    print(tabulate(customers, headers=["Name", "State", "Segment"], tablefmt="grid"))

    # 3. Sample 5 orders
    print("\n3. Sample Orders:")
    cursor.execute("""
        SELECT total, status, payment
        FROM orders
        LIMIT 5
    """)
    orders = cursor.fetchall()
    print(tabulate(orders, headers=["Total", "Status", "Payment"], tablefmt="grid"))

    # 4. Distribution of orders by status
    print("\n4. Orders Distribution by Status:")
    cursor.execute("""
        SELECT
            status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM orders
        GROUP BY status
        ORDER BY count DESC
    """)
    status_dist = cursor.fetchall()
    print(tabulate(status_dist, headers=["Status", "Count", "%"], tablefmt="grid"))

    # 5. Distribution of customers by state
    print("\n5. Customers Distribution by State:")
    cursor.execute("""
        SELECT
            state,
            COUNT(*) as count
        FROM customers
        GROUP BY state
        ORDER BY count DESC
    """)
    state_dist = cursor.fetchall()
    print(tabulate(state_dist, headers=["State", "Count"], tablefmt="grid"))

    cursor.close()

except psycopg2.OperationalError as e:
    print(f"Error connecting to Postgres: {e}")
    print("\nMake sure to run 'cd gen && docker compose up' first!")
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
