"""ShopAgent Day 4 — Supabase cloud setup via REST API.

Creates tables + RPC function in Supabase and migrates data
from local Docker Postgres using the REST API (bypasses IPv6-only DB host).

Usage:
    1. Set SUPABASE_SERVICE_KEY in .env (from Dashboard > Settings > API)
    2. Run:  python -m day4.setup_supabase
    3. Or:   python -m day4.setup_supabase --dry-run
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _local_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "shopagent"),
        user=os.environ.get("POSTGRES_USER", "shopagent"),
        password=os.environ.get("POSTGRES_PASSWORD", "shopagent"),
    )


def _sb_client():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("[ERROR] Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)
    if key.startswith("eyJ_your"):
        print("[ERROR] SUPABASE_SERVICE_KEY not configured. Get it from:")
        print("  Supabase Dashboard > Settings > API > service_role secret")
        sys.exit(1)
    return create_client(url, key)


CREATE_TABLES_RPC_SQL = """-- ShopAgent: tables + RPC for SQL queries
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state CHAR(2),
    segment VARCHAR(20) CHECK (segment IN ('premium', 'standard', 'basic'))
);

CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    brand VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    qty INTEGER CHECK (qty BETWEEN 1 AND 10),
    total DECIMAL(10,2) CHECK (total >= 0),
    status VARCHAR(20) CHECK (status IN ('delivered', 'shipped', 'processing', 'cancelled')),
    payment VARCHAR(20) CHECK (payment IN ('pix', 'credit_card', 'boleto')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_payment ON orders(payment);
CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(state);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON customers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON orders FOR ALL USING (true) WITH CHECK (true);

CREATE OR REPLACE FUNCTION exec_shopagent_query(query_name TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    CASE query_name
        WHEN 'revenue_by_state' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
                FROM orders o JOIN customers c ON o.customer_id = c.customer_id
                GROUP BY c.state ORDER BY faturamento DESC
            ) t;
        WHEN 'orders_by_status' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT status, COUNT(*) AS total, SUM(total) AS faturamento,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
                FROM orders GROUP BY status ORDER BY total DESC
            ) t;
        WHEN 'top_products' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT p.name, p.category, p.brand,
                COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
                FROM orders o JOIN products p ON o.product_id = p.product_id
                GROUP BY p.product_id, p.name, p.category, p.brand
                ORDER BY faturamento DESC LIMIT 10
            ) t;
        WHEN 'payment_distribution' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT payment, COUNT(*) AS total,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
                FROM orders GROUP BY payment ORDER BY total DESC
            ) t;
        WHEN 'segment_analysis' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT c.segment, COUNT(DISTINCT c.customer_id) AS clientes,
                COUNT(o.order_id) AS pedidos, ROUND(AVG(o.total), 2) AS ticket_medio
                FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id
                GROUP BY c.segment ORDER BY ticket_medio DESC
            ) t;
        WHEN 'revenue_by_category' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT p.category, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento,
                ROUND(AVG(o.total), 2) AS ticket_medio
                FROM orders o JOIN products p ON o.product_id = p.product_id
                GROUP BY p.category ORDER BY faturamento DESC
            ) t;
        WHEN 'customer_count_by_state' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT state, COUNT(*) AS clientes
                FROM customers GROUP BY state ORDER BY clientes DESC
            ) t;
        WHEN 'orders_by_month' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
                SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
                FROM orders GROUP BY mes ORDER BY mes DESC LIMIT 12
            ) t;
        WHEN 'revenue_by_month' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
                SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
                FROM orders GROUP BY mes ORDER BY mes ASC LIMIT 12
            ) t;
        WHEN 'satisfaction_by_region' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT c.state, c.segment, COUNT(o.order_id) AS pedidos,
                SUM(o.total) AS faturamento, ROUND(AVG(o.total), 2) AS ticket_medio
                FROM orders o JOIN customers c ON o.customer_id = c.customer_id
                GROUP BY c.state, c.segment ORDER BY c.state, faturamento DESC
            ) t;
        ELSE
            result := json_build_object('error', 'Unknown query: ' || query_name);
    END CASE;
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""


def _row_to_dict(row, columns):
    d = {}
    for col, val in zip(columns, row):
        if isinstance(val, uuid.UUID):
            d[col] = str(val)
        elif isinstance(val, datetime):
            d[col] = val.isoformat()
        elif val is None:
            d[col] = None
        elif hasattr(val, "__float__"):
            d[col] = float(val)
        else:
            d[col] = str(val) if not isinstance(val, (int, float, bool)) else val
    return d


TABLE_COLUMNS = {
    "customers": ["customer_id", "name", "email", "city", "state", "segment"],
    "products": ["product_id", "name", "category", "price", "brand"],
    "orders": ["order_id", "customer_id", "product_id", "qty", "total", "status", "payment", "created_at"],
}


def _migrate_table_rest(sb, local_cur, table: str, columns: list[str]) -> int:
    col_list = ", ".join(columns)
    local_cur.execute(f"SELECT {col_list} FROM {table}")
    rows = local_cur.fetchall()
    if not rows:
        print(f"  {table}: 0 rows (skipped)")
        return 0

    records = [_row_to_dict(row, columns) for row in rows]

    batch_size = 100
    inserted = 0
    errors = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            resp = sb.table(table).insert(batch).execute()
            inserted += len(batch)
        except Exception as exc:
            errors += 1
            if errors == 1:
                print(f"  {table}: insert error: {exc}")

    status = f"{inserted}/{len(records)} rows"
    if errors:
        status += f" ({errors} batch errors)"
    print(f"  {table}: {status}")
    return inserted


def migrate(dry_run: bool = False):
    print("=" * 60)
    print("  ShopAgent Supabase Migration (REST API)")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print("=" * 60)

    # Step 1: Check local data
    print("\n[1/3] Counting local Docker data...")
    try:
        local = _local_conn()
        with local.cursor() as cur:
            for table in TABLE_COLUMNS:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count} rows")
        local.close()
    except Exception as exc:
        print(f"[ERROR] Cannot connect to local Postgres: {exc}")
        return

    # Step 2: Check Supabase (tables must exist first — created via Dashboard SQL)
    print("\n[2/3] Checking Supabase cloud...")
    sb = _sb_client()

    tables_exist = True
    for table in TABLE_COLUMNS:
        try:
            resp = sb.table(table).select("*").limit(0).execute()
            print(f"  {table}: exists")
        except Exception:
            print(f"  {table}: NOT FOUND")
            tables_exist = False

    if not tables_exist:
        print("\n[ACTION REQUIRED] Tables not found in Supabase.")
        print("Paste the SQL below into Supabase Dashboard > SQL Editor:\n")
        print(CREATE_TABLES_RPC_SQL)
        print("\nAfter creating tables, re-run: python -m day4.setup_supabase")
        return

    if dry_run:
        print("\n[DRY RUN] Tables exist. No data will be modified.")
        return

    # Step 3: Migrate data via REST
    print("\n[3/3] Migrating data via REST API...")
    local = _local_conn()
    try:
        local_cur = local.cursor()
        total = 0
        for table, columns in TABLE_COLUMNS.items():
            count = _migrate_table_rest(sb, local_cur, table, columns)
            total += count
        print(f"\n  Total: {total} rows migrated to Supabase")
    except Exception as exc:
        print(f"\n[ERROR] Migration failed: {exc}")
    finally:
        local.close()

    # Verify RPC
    print("\nVerifying RPC function...")
    try:
        resp = sb.rpc("exec_shopagent_query", {"query_name": "revenue_by_state"}).execute()
        if resp.data:
            print(f"  exec_shopagent_query('revenue_by_state'): {len(resp.data)} rows returned")
        else:
            print("  RPC returned no data")
    except Exception as exc:
        print(f"  RPC not available: {exc}")
        print("  Create it by pasting the SQL into Dashboard > SQL Editor")

    print("\nDone! Set ENVIRONMENT=cloud in .env to use Supabase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShopAgent Supabase Setup (REST API)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
