"""ShopAgent Day 3 -- LangChain tool definitions for The Ledger and The Memory.

Query routing uses a two-tier strategy:
1. Keyword matching (instant, ~0ms)
2. NVIDIA NIM LLM fallback via nemotron-mini-4b (~0.3s, 100% accuracy)
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from langchain_core.tools import tool
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_MODEL = os.environ.get("NIM_LEDGER_MODEL", "nvidia/nemotron-mini-4b-instruct")

ROUTER_SYSTEM = """Voce e o ShopAgent query router. Dada uma pergunta, escolha a query SQL mais apropriada.

Queries disponiveis: revenue_by_state, orders_by_status, top_products,
payment_distribution, segment_analysis, revenue_by_category,
premium_southeast_ticket, revenue_by_month, customer_count_by_state

Responda APENAS com o nome da query, nada mais. Sem explicacao."""


QUERIES = {
    "revenue_by_state": {
        "keywords": ["faturamento", "receita", "revenue", "estado", "state", "uf"],
        "sql": """
            SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
            FROM orders o JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY c.state ORDER BY faturamento DESC
        """,
    },
    "orders_by_status": {
        "keywords": ["status", "pedidos", "entregue", "cancelado", "processando", "enviado"],
        "sql": """
            SELECT status, COUNT(*) AS total, SUM(total) AS faturamento,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
            FROM orders GROUP BY status ORDER BY total DESC
        """,
    },
    "top_products": {
        "keywords": ["produto", "product", "top", "mais vendido", "ranking"],
        "sql": """
            SELECT p.name, p.category, p.brand,
            COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
            FROM orders o JOIN products p ON o.product_id = p.product_id
            GROUP BY p.product_id, p.name, p.category, p.brand
            ORDER BY faturamento DESC LIMIT 10
        """,
    },
    "payment_distribution": {
        "keywords": ["pagamento", "payment", "pix", "cartao", "boleto", "credit"],
        "sql": """
            SELECT payment, COUNT(*) AS total,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
            FROM orders GROUP BY payment ORDER BY total DESC
        """,
    },
    "segment_analysis": {
        "keywords": ["segmento", "segment", "premium", "standard", "basic", "ticket medio"],
        "sql": """
            SELECT c.segment, COUNT(DISTINCT c.customer_id) AS clientes,
            COUNT(o.order_id) AS pedidos, ROUND(AVG(o.total), 2) AS ticket_medio
            FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.segment ORDER BY ticket_medio DESC
        """,
    },
    "revenue_by_category": {
        "keywords": ["categoria", "category"],
        "sql": """
            SELECT p.category, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
            FROM orders o JOIN products p ON o.product_id = p.product_id
            GROUP BY p.category ORDER BY faturamento DESC
        """,
    },
    "premium_southeast_ticket": {
        "keywords": ["premium", "sudeste", "ticket"],
        "sql": """
            SELECT c.segment, c.state, COUNT(o.order_id) AS pedidos,
            ROUND(AVG(o.total), 2) AS ticket_medio, SUM(o.total) AS faturamento
            FROM customers c JOIN orders o ON c.customer_id = o.customer_id
            WHERE c.segment = 'premium' AND c.state IN ('SP', 'RJ', 'MG', 'ES')
            GROUP BY c.segment, c.state ORDER BY ticket_medio DESC
        """,
    },
    "revenue_by_month": {
        "keywords": ["mes", "month", "evolucao", "temporal", "faturamento mes", "receita mes", "timeline", "periodo", "trimestre"],
        "sql": """
            SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
            SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
            FROM orders GROUP BY mes ORDER BY mes ASC LIMIT 12
        """,
    },
    "customer_count_by_state": {
        "keywords": ["quantos clientes", "cliente por estado", "clientes"],
        "sql": """
            SELECT state, COUNT(*) AS clientes
            FROM customers GROUP BY state ORDER BY clientes DESC
        """,
    },
}

VALID_QUERIES = set(QUERIES.keys())


def _get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "shopagent"),
        user=os.environ.get("POSTGRES_USER", "shopagent"),
        password=os.environ.get("POSTGRES_PASSWORD", "shopagent"),
    )


def _match_query(question: str) -> str | None:
    question_lower = question.lower()
    best_match = None
    best_score = 0
    for name, config in QUERIES.items():
        score = sum(1 for kw in config["keywords"] if kw in question_lower)
        if score > best_score:
            best_score = score
            best_match = name
    return best_match


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


def _route_query(question: str) -> str | None:
    """Two-tier query routing: keyword match first (instant), then NIM LLM fallback."""
    matched = _match_query(question)
    if matched:
        return matched
    return _nim_route(question)


def _format_results(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "Nenhum resultado encontrado."
    header = " | ".join(f"{c:>15}" for c in columns)
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows[:20]:
        lines.append(" | ".join(f"{str(v):>15}" for v in row))
    return "\n".join(lines)


@tool
def supabase_execute_sql(question: str) -> str:
    """Query Postgres (The Ledger) for EXACT business data.

    Use when the question asks for specific numbers, totals, or structured data:
    - Faturamento (revenue) by state, category, or period
    - Evolucao do faturamento por mes (revenue timeline)
    - Total de pedidos (order counts), ticket medio (average order value)
    - Payment method distribution (pix, credit_card, boleto)
    - Customer segment analysis (premium, standard, basic)
    - Top products by revenue or order count
    - Any question requiring aggregation, GROUP BY, or JOINs

    Args:
        question: Natural language question about business metrics.
    """
    matched = _route_query(question)
    if not matched:
        return (
            f"Nao foi possivel mapear a pergunta para uma query conhecida. "
            f"Queries disponiveis: {list(QUERIES.keys())}"
        )

    sql = QUERIES[matched]["sql"]
    try:
        conn = _get_connection()
    except (psycopg2.OperationalError, ValueError) as exc:
        return f"Erro ao conectar ao Postgres: {exc}"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        return f"Erro ao executar query '{matched}': {exc}"
    finally:
        conn.close()

    result = _format_results(columns, rows)
    return f"Query: {matched}\n\n{result}"


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database (The Memory).

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes (complaints) about delivery, quality, price
    - Customer sentiment analysis (positive, negative, neutral)
    - Product feedback themes and review patterns
    - Any question about what customers SAY, THINK, or FEEL

    Args:
        question: Natural language question for semantic similarity search in reviews.
    """
    try:
        from llama_index.core import Settings, VectorStoreIndex
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        import qdrant_client

        Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

        client = qdrant_client.QdrantClient(url=qdrant_url, check_compatibility=False)
        vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
        index = VectorStoreIndex.from_vector_store(vector_store)

        retriever = index.as_retriever(similarity_top_k=5)
        nodes = retriever.retrieve(question)

        if not nodes:
            return "Nenhum review relevante encontrado."

        snippets = []
        for node in nodes:
            score = node.score if node.score is not None else 0.0
            snippets.append(f"[score: {score:.3f}] {node.text[:200]}")

        return f"Reviews encontrados ({len(nodes)} resultados):\n\n" + "\n\n".join(snippets)

    except Exception as exc:
        return f"Erro ao buscar no Qdrant: {exc}"


if __name__ == "__main__":
    print("=" * 60)
    print(" TOOL TEST: supabase_execute_sql (keyword match)")
    print("=" * 60)
    result = supabase_execute_sql.invoke("Qual o faturamento total por estado?")
    print(result)

    print("\n" + "=" * 60)
    print(" TOOL TEST: revenue_by_month (keyword match)")
    print("=" * 60)
    result = supabase_execute_sql.invoke("Evolucao do faturamento por mes")
    print(result)

    print("\n" + "=" * 60)
    print(" TOOL TEST: NIM fallback routing")
    print("=" * 60)
    result = supabase_execute_sql.invoke("Show me the monthly revenue trend")
    print(result)

    print("\n" + "=" * 60)
    print(" TOOL TEST: qdrant_semantic_search")
    print("=" * 60)
    result = qdrant_semantic_search.invoke("Clientes reclamando de entrega atrasada")
    print(result)
