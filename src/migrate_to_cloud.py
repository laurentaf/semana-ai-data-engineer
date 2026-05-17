"""ShopAgent Cloud Migration — Docker local -> Supabase + Qdrant Cloud.

Steps:
1. Dump local Postgres data
2. Insert into Supabase (via SUPABASE_DB_URL)
3. Re-ingest reviews into Qdrant Cloud
4. Toggle ENVIRONMENT=cloud

Usage:
  python migrate_to_cloud.py --dry-run    # preview what will migrate
  python migrate_to_cloud.py              # full migration
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

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


def _cloud_conn():
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url or "xxxxx" in db_url:
        print("[ERROR] SUPABASE_DB_URL not configured in .env")
        print("        Get it from: Supabase Dashboard > Settings > Database > Connection string")
        sys.exit(1)
    return psycopg2.connect(db_url)


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


def _count_cloud():
    try:
        conn = _cloud_conn()
    except Exception as exc:
        print(f"[WARN] Cannot connect to Supabase: {exc}")
        return {"customers": "?", "products": "?", "orders": "?"}

    counts = {}
    try:
        with conn.cursor() as cur:
            for table in ["customers", "products", "orders"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cur.fetchone()[0]
                except psycopg2.Error:
                    counts[table] = "table not found"
    finally:
        conn.close()
    return counts


def _ensure_schema(cloud_cur):
    """Create tables in Supabase if they don't exist."""
    init_sql = (PROJECT_ROOT / "gen" / "init.sql").read_text(encoding="utf-8")
    # Split on semicolons and execute each statement
    for statement in init_sql.split(";"):
        stmt = statement.strip()
        if stmt and not stmt.startswith("--"):
            try:
                cloud_cur.execute(stmt + ";")
            except psycopg2.Error as exc:
                if "already exists" in str(exc):
                    pass  # OK — table already there
                else:
                    print(f"  Schema error: {exc}")


def _migrate_table(local_cur, cloud_cur, table: str, columns: list[str]):
    """Copy all rows from local Postgres to Supabase."""
    col_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    local_cur.execute(f"SELECT {col_list} FROM {table}")
    rows = local_cur.fetchall()
    if not rows:
        print(f"  {table}: 0 rows (skipped)")
        return 0

    # Clear existing data in cloud (idempotent)
    cloud_cur.execute(f"DELETE FROM {table}")

    # Insert in batches
    batch_size = 500
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        cloud_cur.executemany(
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
            batch,
        )
        inserted += len(batch)

    print(f"  {table}: {inserted} rows migrated")
    return inserted


def _ingest_qdrant_cloud():
    """Re-ingest reviews into Qdrant Cloud."""
    try:
        from llama_index.core import Settings, VectorStoreIndex, StorageContext
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        from llama_index.readers.json import JSONReader
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        import qdrant_client
    except ImportError:
        print("[ERROR] llama_index not installed. Run: pip install llama-index-core llama-index-vector-stores-qdrant")
        return False

    cloud_url = os.environ.get("QDRANT_CLOUD_URL", "")
    api_key = os.environ.get("QDRANT_CLOUD_API_KEY", "")
    if not cloud_url or "xxxxx" in cloud_url:
        print("[ERROR] QDRANT_CLOUD_URL not configured in .env")
        return False

    reviews_path = PROJECT_ROOT / "gen" / "data" / "reviews" / "reviews.jsonl"
    if not reviews_path.exists():
        # Try consolidated reviews
        reviews_path = PROJECT_ROOT / "gen" / "data" / "reviews" / "consolidated_reviews.jsonl"
    if not reviews_path.exists():
        # Find any jsonl in reviews dir
        review_dir = PROJECT_ROOT / "gen" / "data" / "reviews"
        jsonl_files = list(review_dir.glob("*.jsonl"))
        if jsonl_files:
            reviews_path = jsonl_files[0]
        else:
            print("[ERROR] No review JSONL files found in gen/data/reviews/")
            return False

    print(f"\n[QDRANT] Ingesting reviews from: {reviews_path.name}")

    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

    client = qdrant_client.QdrantClient(url=cloud_url, api_key=api_key)
    collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Load reviews as documents
    documents = []
    with open(reviews_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                review = json.loads(line)
                text = review.get("comment", review.get("text", ""))
                if text:
                    from llama_index.core import Document
                    documents.append(Document(
                        text=text,
                        metadata={
                            "review_id": review.get("review_id", ""),
                            "order_id": review.get("order_id", ""),
                            "rating": review.get("rating", ""),
                            "sentiment": review.get("sentiment", ""),
                        },
                    ))

    if not documents:
        print("[WARN] No review documents to ingest")
        return False

    print(f"  Ingesting {len(documents)} reviews into Qdrant Cloud...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    print(f"  Done! {len(documents)} reviews indexed in Qdrant Cloud")
    return True


def migrate(dry_run: bool = False):
    env_mode = os.environ.get("ENVIRONMENT", "local")
    print("=" * 60)
    print("  ShopAgent Cloud Migration")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print(f"  Current ENVIRONMENT: {env_mode}")
    print("=" * 60)

    # Step 1: Count local data
    print("\n[1/4] Counting local Docker data...")
    local_counts = _count_local()
    for table, count in local_counts.items():
        print(f"  {table}: {count} rows")

    # Step 2: Check cloud connectivity
    print("\n[2/4] Checking Supabase cloud connectivity...")
    cloud_counts = _count_cloud()
    for table, count in cloud_counts.items():
        print(f"  {table}: {count} rows (existing in cloud)")

    if dry_run:
        print("\n[DRY RUN] No data will be modified.")
        print("To run the migration: python migrate_to_cloud.py")
        return

    # Step 3: Migrate Postgres data
    print("\n[3/4] Migrating Postgres -> Supabase...")
    local = _local_conn()
    cloud = _cloud_conn()

    try:
        local_cur = local.cursor()
        cloud_cur = cloud.cursor()

        _ensure_schema(cloud_cur)

        # Migrate in dependency order (customers, products first, then orders)
        table_columns = {
            "customers": ["customer_id", "name", "email", "city", "state", "segment"],
            "products": ["product_id", "name", "category", "price", "brand"],
            "orders": ["order_id", "customer_id", "product_id", "qty", "total", "status", "payment", "created_at"],
        }

        total_migrated = 0
        for table, columns in table_columns.items():
            count = _migrate_table(local_cur, cloud_cur, table, columns)
            total_migrated += count

        cloud.commit()
        print(f"\n  Total: {total_migrated} rows migrated to Supabase")

    except Exception as exc:
        cloud.rollback()
        print(f"\n[ERROR] Migration failed: {exc}")
        print("  Cloud DB rolled back. Local data untouched.")
    finally:
        local.close()
        cloud.close()

    # Step 4: Ingest reviews into Qdrant Cloud
    print("\n[4/4] Ingesting reviews into Qdrant Cloud...")
    _ingest_qdrant_cloud()

    # Final: Toggle env
    print("\n" + "=" * 60)
    print("  Migration complete!")
    print("  To switch to cloud mode, set in .env:")
    print("  ENVIRONMENT=cloud")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShopAgent Cloud Migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying cloud")
    args = parser.parse_args()

    migrate(dry_run=args.dry_run)
