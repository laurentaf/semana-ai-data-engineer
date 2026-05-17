"""ShopAgent Day 4 — CrewAI tool wrappers for The Ledger and The Memory.

ENVIRONMENT-aware: set ENVIRONMENT=cloud to use Supabase/Qdrant cloud,
or ENVIRONMENT=local (default) for Docker endpoints. Zero code changes.

Query routing: keyword match -> NIM nemotron-mini-4b fallback (~0.3s, 100% acc)
"""

import json
import os
from pathlib import Path

import psycopg2
import qdrant_client
from crewai.tools import tool
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.qdrant import QdrantVectorStore
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_is_cloud = os.environ.get("ENVIRONMENT", "local") == "cloud"

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_MODEL = os.environ.get("NIM_LEDGER_MODEL", "nvidia/nemotron-mini-4b-instruct")

ROUTER_SYSTEM = """Voce e o ShopAgent query router. Dada uma pergunta, escolha a query SQL mais apropriada.

Queries disponiveis: revenue_by_state, orders_by_status, top_products,
payment_distribution, segment_analysis, revenue_by_category,
customer_count_by_state, orders_by_month, revenue_by_month,
satisfaction_by_region

Responda APENAS com o nome da query, nada mais. Sem explicacao."""


def _get_postgres_connection():
    if _is_cloud:
        db_url = os.environ.get("SUPABASE_DB_URL")
        if db_url:
            return psycopg2.connect(db_url)
    supabase_url = os.environ.get("SUPABASE_URL")
    if supabase_url and not supabase_url.startswith("https://xxxxx"):
        return psycopg2.connect(supabase_url)
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "shopagent"),
        user=os.environ.get("POSTGRES_USER", "shopagent"),
        password=os.environ.get("POSTGRES_PASSWORD", "shopagent"),
    )


def _get_qdrant_url() -> str:
    if _is_cloud:
        cloud_url = os.environ.get("QDRANT_CLOUD_URL", "")
        if cloud_url and not cloud_url.startswith("https://xxxxx"):
            return cloud_url
    return os.environ.get("QDRANT_URL", "http://localhost:6333")


def _get_qdrant_api_key() -> str | None:
    if _is_cloud:
        return os.environ.get("QDRANT_CLOUD_API_KEY")
    return None


_llama_settings_initialized = False


def _configure_llama_settings() -> None:
    global _llama_settings_initialized
    if _llama_settings_initialized:
        return
    Settings.llm = Anthropic(model="claude-sonnet-4-20250514")
    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
    _llama_settings_initialized = True


SAFE_QUERIES: dict[str, str] = {
    "revenue_by_state": """
        SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.state ORDER BY faturamento DESC
    """,
    "orders_by_status": """
        SELECT status, COUNT(*) AS total, SUM(total) AS faturamento,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
        FROM orders GROUP BY status ORDER BY total DESC
    """,
    "top_products": """
        SELECT p.name, p.category, p.brand,
        COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
        FROM orders o JOIN products p ON o.product_id = p.product_id
        GROUP BY p.product_id, p.name, p.category, p.brand
        ORDER BY faturamento DESC LIMIT 10
    """,
    "payment_distribution": """
        SELECT payment, COUNT(*) AS total,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
        FROM orders GROUP BY payment ORDER BY total DESC
    """,
    "segment_analysis": """
        SELECT c.segment, COUNT(DISTINCT c.customer_id) AS clientes,
        COUNT(o.order_id) AS pedidos, ROUND(AVG(o.total), 2) AS ticket_medio
        FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.segment ORDER BY ticket_medio DESC
    """,
    "revenue_by_category": """
        SELECT p.category, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento,
        ROUND(AVG(o.total), 2) AS ticket_medio
        FROM orders o JOIN products p ON o.product_id = p.product_id
        GROUP BY p.category ORDER BY faturamento DESC
    """,
    "customer_count_by_state": """
        SELECT state, COUNT(*) AS clientes
        FROM customers GROUP BY state ORDER BY clientes DESC
    """,
    "orders_by_month": """
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
        SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
        FROM orders GROUP BY mes ORDER BY mes DESC LIMIT 12
    """,
    "revenue_by_month": """
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
        SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
        FROM orders GROUP BY mes ORDER BY mes ASC LIMIT 12
    """,
    "satisfaction_by_region": """
        SELECT c.state, c.segment, COUNT(o.order_id) AS pedidos,
        SUM(o.total) AS faturamento, ROUND(AVG(o.total), 2) AS ticket_medio
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.state, c.segment ORDER BY c.state, faturamento DESC
    """,
}

VALID_QUERIES = set(SAFE_QUERIES.keys())


def _nim_route(question: str) -> str | None:
    """Use NVIDIA NIM nemotron-mini-4b for query routing (~0.3s)."""
    if not NIM_API_KEY:
        return None
    try:
        client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)
        completion = client.chat.completions.create(
            model=NIM_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=30,
        )
        response = completion.choices[0].message.content.strip().lower()
        response_clean = response.replace(" ", "_").replace("-", "_").strip(".")
        if response_clean in VALID_QUERIES:
            return response_clean
        return None
    except Exception:
        return None


@tool("Supabase SQL Executor")
def supabase_execute_sql(query: str) -> str:
    """Execute a predefined SQL query against Supabase Postgres for EXACT data.

    Use when the question asks for specific numbers, totals, or structured data:
    - Faturamento (revenue) by state, category, or period
    - Evolucao do faturamento por mes (revenue timeline / monthly trend)
    - Total de pedidos (order counts), ticket medio (average order value)
    - Payment method distribution, customer segment analysis
    - Any question requiring aggregation, GROUP BY, or JOINs

    The query parameter must be one of the predefined safe query names:
    revenue_by_state, orders_by_status, top_products, payment_distribution,
    segment_analysis, revenue_by_category, customer_count_by_state,
    orders_by_month, revenue_by_month, satisfaction_by_region.
    If a natural language question is passed, the NIM router will map it.

    Args:
        query: Query name or natural language question about business metrics.
    """
    query_key = query.strip().lower().replace(" ", "_").replace("-", "_")

    # Try direct query name lookup first
    sql = SAFE_QUERIES.get(query_key)

    # If not a direct name, try NIM routing
    if sql is None and NIM_API_KEY:
        routed = _nim_route(query)
        if routed:
            sql = SAFE_QUERIES.get(routed)
            query_key = routed

    if sql is None:
        available = ", ".join(sorted(SAFE_QUERIES.keys()))
        return (
            f"Unknown query '{query}'. "
            f"Available predefined queries: {available}. "
            f"Pass one of these names as the query parameter."
        )

    try:
        conn = _get_postgres_connection()
    except (psycopg2.OperationalError, ValueError) as exc:
        return f"Database connection failed: {exc}"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            results = []
            for row in rows:
                record = {}
                for col, val in zip(columns, row):
                    if hasattr(val, "__float__"):
                        record[col] = float(val)
                    else:
                        record[col] = str(val) if val is not None else None
                results.append(record)

            return json.dumps(results, ensure_ascii=False, indent=2)
    except psycopg2.Error as exc:
        return f"Query execution failed: {exc}"
    finally:
        conn.close()


@tool("Qdrant Semantic Search")
def qdrant_semantic_search(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database.

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes (complaints) about delivery, quality, price
    - Customer sentiment analysis (positive, negative, neutral)
    - Product feedback themes and review patterns
    - Any question about what customers SAY, THINK, or FEEL

    Args:
        question: Natural language question for semantic similarity search in reviews.
    """
    _configure_llama_settings()

    qdrant_url = _get_qdrant_url()
    api_key = _get_qdrant_api_key()
    collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

    try:
        client_kwargs: dict = {"url": qdrant_url}
        if api_key:
            client_kwargs["api_key"] = api_key
        client = qdrant_client.QdrantClient(**client_kwargs)

        vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
        index = VectorStoreIndex.from_vector_store(vector_store)
        engine = index.as_query_engine(similarity_top_k=5)
        response = engine.query(question)

        sources = []
        for node in response.source_nodes:
            sources.append({
                "score": round(node.score, 3),
                "text": node.text[:200],
            })

        result = {
            "answer": str(response.response),
            "sources": sources,
            "total_sources": len(response.source_nodes),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Qdrant search failed: {exc}"


def _print_env_status() -> None:
    mode = "CLOUD" if _is_cloud else "LOCAL (Docker)"
    pg_host = "Supabase Cloud" if _is_cloud else os.environ.get("POSTGRES_HOST", "localhost")
    qdrant_host = _get_qdrant_url()
    nim_status = f"enabled ({NIM_MODEL})" if NIM_API_KEY else "disabled (no NVIDIA_NIM_API_KEY)"
    print(f" ENVIRONMENT={os.environ.get('ENVIRONMENT', 'local')} -> mode: {mode}")
    print(f" Postgres: {pg_host}")
    print(f" Qdrant: {qdrant_host}")
    print(f" NIM Router: {nim_status}")
    print(f" LangFuse: {'enabled' if os.environ.get('LANGFUSE_SECRET_KEY', '').strip() and not os.environ.get('LANGFUSE_SECRET_KEY', '').startswith('sk-lf-') else 'disabled'}")


if __name__ == "__main__":
    print("=" * 60)
    print(" ShopAgent Day 4 Tools — Environment Status")
    print("=" * 60)
    _print_env_status()

    print()
    print("=" * 60)
    print(" Testing supabase_execute_sql (direct name)")
    print("=" * 60)
    print(supabase_execute_sql.run("revenue_by_state"))

    print()
    print("=" * 60)
    print(" Testing supabase_execute_sql (NIM routing)")
    print("=" * 60)
    print(supabase_execute_sql.run("evolucao do faturamento por mes"))

    print()
    print("=" * 60)
    print(" Testing qdrant_semantic_search")
    print("=" * 60)
    print(qdrant_semantic_search.run("Clientes reclamando de entrega atrasada"))
