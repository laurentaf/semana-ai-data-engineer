"""ShopAgent Cloud Migration — Docker local -> Supabase REST + Qdrant Cloud.

Steps:
1. Read local Postgres data
2. Create Supabase tables via SQL Editor RPC (or manual SQL pasted in Dashboard)
3. Insert data into Supabase via REST API (bypasses IPv6-only direct DB)
4. Re-ingest reviews into Qdrant Cloud (already done if collection exists)
5. Toggle ENVIRONMENT=cloud

Usage:
    python migrate_to_cloud.py --dry-run   # preview what will migrate
    python migrate_to_cloud.py             # full migration
    python migrate_to_cloud.py --create-tables  # only create tables via RPC
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _local_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "shopagent"),
        user=os.environ.get("POSTGRES_USER", "shopagent"),
        password=os.environ.get("POSTGRES_PASSWORD", "shopagent"),
    )


def _sb_client(use_service_role=False):
    url = os.environ.get("SUPABASE_URL", "")
    if use_service_role:
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not key or key.startswith("eyJ_your"):
            key = os.environ.get("SUPABASE_KEY", "")
    else:
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("[ERROR] SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    return create_client(url, key)


def _count_local():
    conn = _local_conn()
    counts = {}
    try:
        with conn.cursor() as cur:
            for table in ["customers", "products", "orders"]:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
    finally:
        conn.close()
    return counts


def _count_cloud(sb):
    counts = {}
    for table in ["customers", "products", "orders"]:
        try:
            resp = sb.table(table).select("id", count="exact").limit(0).execute()
            counts[table] = resp.count
        except Exception:
            counts[table] = "table not found"
    return counts


CREATE_TABLES_SQL = """-- ShopAgent tables for Supabase
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

-- Enable RLS with permissive policies for service_role
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON customers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON orders FOR ALL USING (true) WITH CHECK (true);

-- RPC function for predefined SQL queries (REST API fallback for IPv6-only hosts)
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
        WHEN 'revenue_by_month_state' THEN
            SELECT json_agg(row_to_json(t)) INTO result FROM (
                SELECT c.state, TO_CHAR(o.created_at, 'YYYY-MM') AS mes, COUNT(o.order_id) AS pedidos,
                SUM(o.total) AS faturamento, ROUND(AVG(o.total), 2) AS ticket_medio
                FROM orders o JOIN customers c ON o.customer_id = c.customer_id
                GROUP BY c.state, mes ORDER BY c.state, mes ASC
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
                print(f"  {table}: first failing record: {batch[0]}")

    status = f"{inserted}/{len(records)} rows"
    if errors:
        status += f" ({errors} batch errors)"
    print(f"  {table}: {status}")
    return inserted


TABLE_COLUMNS = {
    "customers": ["customer_id", "name", "email", "city", "state", "segment"],
    "products": ["product_id", "name", "category", "price", "brand"],
    "orders": ["order_id", "customer_id", "product_id", "qty", "total", "status", "payment", "created_at"],
}


def _ingest_qdrant_cloud():
    import qdrant_client
    from qdrant_client.http.models import PointStruct

    cloud_url = os.environ.get("QDRANT_CLOUD_URL", "")
    api_key = os.environ.get("QDRANT_CLOUD_API_KEY", "")
    if not cloud_url or "xxxxx" in cloud_url:
        print("[ERROR] QDRANT_CLOUD_URL not configured in .env")
        return False

    nim_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
    collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

    review_dir = PROJECT_ROOT / "gen" / "data" / "reviews"
    jsonl_files = sorted(review_dir.glob("*.jsonl"))
    if not jsonl_files:
        print("[ERROR] No review JSONL files found in gen/data/reviews/")
        return False

    reviews = []
    for f in jsonl_files:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        reviews.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    if not reviews:
        print("[WARN] No reviews found in JSONL files")
        return False

    print(f"\n[QDRANT] Ingesting {len(reviews)} reviews into Qdrant Cloud...")

    client = qdrant_client.QdrantClient(url=cloud_url, api_key=api_key)

    # Use NIM embedding API (lightweight) or fallback to local fastembed
    texts = [r.get("comment", r.get("text", "")) for r in reviews]
    if nim_key:
        from openai import OpenAI
        nim_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nim_key)
        embed_model_name = os.environ.get("NIM_EMBED_MODEL", "baai/bge-m3")
        embeddings = []
        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = nim_client.embeddings.create(model=embed_model_name, input=batch)
            embeddings.extend([d.embedding for d in resp.data])
            print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} reviews")
    else:
        try:
            from fastembed import TextEmbedding
            embed_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
            embeddings = list(embed_model.embed(texts))
            embeddings = [e.tolist() if hasattr(e, 'tolist') else e for e in embeddings]
        except ImportError:
            print("[ERROR] No embedding source available. Set NVIDIA_NIM_API_KEY or install fastembed.")
            return False

    texts = [r.get("comment", r.get("text", "")) for r in reviews]
    embeddings = list(embed_model.embed(texts))

    points = []
    for review, embedding in zip(reviews, embeddings):
        text = review.get("comment", review.get("text", ""))
        if not text:
            continue
        points.append(PointStruct(
            id=review.get("review_id", str(uuid.uuid4())),
            vector=embedding.tolist(),
            payload={
                "text": text,
                "review_id": review.get("review_id", ""),
                "order_id": review.get("order_id", ""),
                "rating": review.get("rating"),
                "sentiment": review.get("sentiment", ""),
            },
        ))

    if not points:
        print("[WARN] No valid points to insert")
        return False

    batch_size = 100
    upserted = 0
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        upserted += len(batch)

    print(f"  {upserted} reviews indexed in Qdrant Cloud")
    return True


def create_tables(sb):
    print("\n[TABLES] Creating tables in Supabase...")
    print("Paste the following SQL in Supabase Dashboard > SQL Editor:")
    print("-" * 60)
    print(CREATE_TABLES_SQL)
    print("-" * 60)

    try:
        result = sb.rpc("exec_sql", {"query": CREATE_TABLES_SQL}).execute()
        print("Tables created via RPC!")
    except Exception:
        print("\n[RPC] Supabase RPC not available. Use the SQL Editor method above.")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Click 'SQL Editor' in the sidebar")
        print("4. Paste the SQL above and click 'Run'")


def migrate(dry_run: bool = False):
    env_mode = os.environ.get("ENVIRONMENT", "local")
    print("=" * 60)
    print("  ShopAgent Cloud Migration (REST API)")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print(f"  Current ENVIRONMENT: {env_mode}")
    print("=" * 60)

    # Step 1: Count local data
    print("\n[1/4] Counting local Docker data...")
    try:
        local_counts = _count_local()
        for table, count in local_counts.items():
            print(f"  {table}: {count} rows")
    except Exception as exc:
        print(f"[ERROR] Cannot connect to local Postgres: {exc}")
        print("Make sure Docker containers are running: docker compose up -d")
        return

    # Step 2: Check Supabase REST API
    print("\n[2/4] Checking Supabase cloud via REST API...")
    sb = _sb_client(use_service_role=True)
    cloud_counts = _count_cloud(sb)
    for table, count in cloud_counts.items():
        print(f"  {table}: {count} rows (existing in cloud)")

    has_tables = all(isinstance(c, int) for c in cloud_counts.values())

    if not has_tables:
        print("\n[ACTION REQUIRED] Tables don't exist in Supabase yet.")
        print("Create them with: python migrate_to_cloud.py --create-tables")
        if not dry_run:
            print("\nAttempting auto-create via Supabase Dashboard SQL...")
            create_tables(sb)
        return

    if dry_run:
        print("\n[DRY RUN] No data will be modified.")
        print("To run the migration: python migrate_to_cloud.py")
        return

    # Step 3: Migrate Postgres data via REST
    print("\n[3/4] Migrating Postgres -> Supabase (REST API)...")
    local = _local_conn()
    try:
        local_cur = local.cursor()
        total_migrated = 0
        for table, columns in TABLE_COLUMNS.items():
            count = _migrate_table_rest(sb, local_cur, table, columns)
            total_migrated += count
        print(f"\n  Total: {total_migrated} rows migrated to Supabase")
    except Exception as exc:
        print(f"\n[ERROR] Migration failed: {exc}")
    finally:
        local.close()

    # Step 4: Qdrant Cloud (skip if already populated)
    print("\n[4/4] Checking Qdrant Cloud...")
    try:
        import qdrant_client
        qdrant_url = os.environ.get("QDRANT_CLOUD_URL", "")
        qdrant_key = os.environ.get("QDRANT_CLOUD_API_KEY", "")
        client = qdrant_client.QdrantClient(url=qdrant_url, api_key=qdrant_key)
        collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")
        info = client.get_collection(collection_name)
        count = info.points_count
        print(f"  Qdrant Cloud: {count} reviews already indexed")
        if count < 10:
            print("  Low count — re-ingesting...")
            _ingest_qdrant_cloud()
        else:
            print("  Skipping re-ingestion (already populated)")
    except Exception as exc:
        print(f"  Qdrant collection not found or error: {exc}")
        print("  Attempting to ingest...")
        _ingest_qdrant_cloud()

    # Final
    print("\n" + "=" * 60)
    print("  Migration complete!")
    print("  To switch to cloud mode, set in .env:")
    print("  ENVIRONMENT=cloud")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShopAgent Cloud Migration (REST API)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying cloud")
    parser.add_argument("--create-tables", action="store_true", help="Print SQL to create Supabase tables")
    args = parser.parse_args()

    if args.create_tables:
        load_dotenv(PROJECT_ROOT / ".env")
        sb = _sb_client(use_service_role=True)
        create_tables(sb)
    else:
        migrate(dry_run=args.dry_run)
