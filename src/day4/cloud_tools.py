"""ShopAgent Cloud Tools — Lightweight tool functions for Render deployment.

No crewai/langchain dependency. Plain functions + OpenAI tool definitions
for use with NVIDIA NIM direct tool calling.
"""

import json
import os
import unicodedata
from pathlib import Path

import psycopg2
import qdrant_client
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_is_cloud = os.environ.get("ENVIRONMENT", "local") == "cloud"

_sb_rest_client = None


def _get_sb_rest_client():
    global _sb_rest_client
    if _sb_rest_client is None and _is_cloud:
        try:
            from supabase import create_client as _create_client
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
            if url and key and not key.startswith("eyJ_your"):
                _sb_rest_client = _create_client(url, key)
        except ImportError:
            pass
    return _sb_rest_client


NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_MODEL = os.environ.get("NIM_LEDGER_MODEL", "meta/llama-3.1-70b-instruct")
NIM_ROUTER_MODEL = os.environ.get("NIM_ROUTER_MODEL", "nvidia/nemotron-mini-4b-instruct")
NIM_EMBED_MODEL = os.environ.get("NIM_EMBED_MODEL", "nvidia/llama-nemotron-embed-1b-v2")

ROUTER_SYSTEM = """Voce e o ShopAgent query router. Dada uma pergunta do usuario, escolha a query SQL mais apropriada.

Queries disponiveis:
- revenue_by_month_state: faturamento, pedidos e ticket_medio agrupados por estado E mes. Use quando a pergunta menciona um estado + periodo temporal (mes, evolucao, mes a mes, etc.)
- revenue_by_month: faturamento, pedidos e ticket_medio por mes (geral, sem estado). Use para evolucao temporal sem estado especifico.
- revenue_by_state: faturamento e pedidos por estado (visao geral, sem temporal). Use para comparar estados.
- orders_by_status: pedidos por status (entregue, cancelado, processando, enviado).
- top_products: top 10 produtos por faturamento.
- payment_distribution: pedidos por forma de pagamento (pix, cartao, boleto).
- segment_analysis: clientes, pedidos e ticket_medio por segmento (premium, standard, basic).
- revenue_by_category: faturamento e ticket_medio por categoria de produto.
- customer_count_by_state: quantidade de clientes por estado.
- satisfaction_by_region: faturamento e ticket_medio por estado e segmento.
- premium_southeast_ticket: ticket_medio de clientes premium no sudeste (SP, RJ, MG, ES).
- cross_store_review_join: ticket_medio, pedidos e faturamento por estado APENAS para pedidos que vieram de reviews do Qdrant. Use quando o usuario pergunta sobre ticket/reclamacao/regiao, combinando resultado do search_memory com o banco SQL.

REGRAS:
- Se menciona estado (sigla ou nome) + mes/evolucao/mensal/temporal, use revenue_by_month_state
- Se menciona evolucao/temporal sem estado, use revenue_by_month
- Se menciona estado sem temporal, use revenue_by_state
- "vendas" e "faturamento" sao sinonimos
- Se a pergunta menciona AO MESMO TEMPO opiniao/reclamacao (Qdrant) E dados numericos (faturamento/ticket), use cross_store_review_join

Responda APENAS com o nome da query, nada mais."""


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


SAFE_QUERIES: dict[str, dict] = {
    "revenue_by_state": {
        "keywords": ["faturamento por estado", "receita por estado", "revenue by state", "vendas por estado"],
        "sql": """
SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.state ORDER BY faturamento DESC
""",
    },
    "orders_by_status": {
        "keywords": ["pedidos por status", "status do pedido", "entregue cancelado", "pedido entregue"],
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
SELECT p.category, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento,
ROUND(AVG(o.total), 2) AS ticket_medio
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
        "keywords": ["faturamento por mes", "faturamento mensal", "vendas por mes", "evolucao geral"],
        "sql": """
SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
SUM(total) AS faturamento, ROUND(AVG(total), 2) AS ticket_medio
FROM orders GROUP BY mes ORDER BY mes ASC LIMIT 12
""",
    },
    "revenue_by_month_state": {
        "keywords": ["vendas por mes estado", "faturamento mes estado", "evolucao estado"],
        "sql": """
SELECT c.state, TO_CHAR(o.created_at, 'YYYY-MM') AS mes, COUNT(o.order_id) AS pedidos,
SUM(o.total) AS faturamento, ROUND(AVG(o.total), 2) AS ticket_medio
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.state, mes ORDER BY c.state, mes ASC
""",
    },
    "satisfaction_by_region": {
        "keywords": ["satisfacao", "regiao", "satisfaction", "region"],
        "sql": """
SELECT c.state, c.segment, COUNT(o.order_id) AS pedidos,
SUM(o.total) AS faturamento, ROUND(AVG(o.total), 2) AS ticket_medio
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.state, c.segment ORDER BY c.state, faturamento DESC
""",
    },
    "customer_count_by_state": {
        "keywords": ["quantos clientes por estado", "clientes por estado"],
        "sql": """
SELECT state, COUNT(*) AS clientes
FROM customers GROUP BY state ORDER BY clientes DESC
""",
    },
    "cross_store_review_join": {
        "keywords": ["reclamacao", "reclama", "nordeste", "ticket medio", "atraso", "review join"],
        "sql": """
SELECT c.state,
       COUNT(DISTINCT o.order_id) AS pedidos,
       ROUND(AVG(o.total), 2) AS ticket_medio,
       SUM(o.total) AS faturamento
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_id = ANY(%(order_ids)s::uuid[])
GROUP BY c.state
ORDER BY ticket_medio DESC
""",
    },
}

VALID_QUERIES = set(SAFE_QUERIES.keys())


def _match_query(question: str) -> str | None:
    """Keyword-based fallback for when NIM router is unavailable."""
    question_norm = _normalize(question)
    best_match = None
    best_score = 0
    for name, config in SAFE_QUERIES.items():
        score = sum(1 for kw in config["keywords"] if _normalize(kw) in question_norm)
        if score > best_score:
            best_score = score
            best_match = name
    return best_match


def _nim_route(question: str) -> str | None:
    if not NIM_API_KEY:
        return None
    try:
        client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)
        completion = client.chat.completions.create(
            model=NIM_ROUTER_MODEL,
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
    # Prefer LLM router — it understands natural language.
    # Fall back to keyword matching only if NIM is unavailable.
    nim_result = _nim_route(question)
    if nim_result:
        return nim_result
    return _match_query(question)


def _get_postgres_connection():
    if _is_cloud:
        db_url = os.environ.get("SUPABASE_DB_URL", "")
        if db_url and "xxxxx" not in db_url and db_url.startswith("postgresql"):
            try:
                return psycopg2.connect(db_url)
            except (psycopg2.OperationalError, OSError):
                pass
        raise psycopg2.OperationalError("Cloud mode: direct DB failed, use RPC fallback")
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "shopagent"),
        user=os.environ.get("POSTGRES_USER", "shopagent"),
        password=os.environ.get("POSTGRES_PASSWORD", "shopagent"),
    )


def _exec_query_rpc(query_key: str) -> str | None:
    import requests as _req
    supabase_url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_KEY", "")
    if not supabase_url or not anon_key:
        return None
    try:
        resp = _req.post(
            f"{supabase_url}/rest/v1/rpc/exec_shopagent_query",
            json={"query_name": query_key},
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
        return None
    except Exception:
        return None


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


def _get_embedding(text: str) -> list[float]:
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5", providers=["CPUExecutionProvider"])
        return list(model.embed(text))[0].tolist()
    except ImportError:
        pass
    if not NIM_API_KEY:
        raise RuntimeError("NVIDIA_NIM_API_KEY required for embedding (or install fastembed)")
    client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)
    resp = client.embeddings.create(
        model=NIM_EMBED_MODEL,
        input=[text],
        extra_body={"input_type": "query"},
    )
    return resp.data[0].embedding


# --- Public tool functions ---

def query_ledger(question: str, memory_context: str | None = None) -> str:
    """Query Postgres (The Ledger) for exact business data.

    Use when the question asks for specific numbers, totals, or structured data:
    - Faturamento (revenue) by state, category, or period
    - Evolucao do faturamento por mes (revenue timeline)
    - Total de pedidos, ticket medio, payment distribution, segment analysis

    Args:
        question: Natural language question about business metrics.
        memory_context: Optional raw output from search_memory for cross-store queries.
    """
    matched = _route_query(question)
    if not matched:
        return f"Nao foi possivel mapear a pergunta. Queries disponiveis: {list(SAFE_QUERIES.keys())}"

    sql = SAFE_QUERIES[matched]["sql"]

    order_ids = []
    if memory_context and matched == "cross_store_review_join":
        import re as _re
        for m in _re.finditer(r'"order_id":\s*"([^"]+)"', memory_context):
            oid = m.group(1)
            if oid and oid not in order_ids:
                order_ids.append(oid)

    try:
        conn = _get_postgres_connection()
    except (psycopg2.OperationalError, ValueError) as exc:
        if _is_cloud:
            rpc_result = _exec_query_rpc(matched)
            if rpc_result is not None:
                return f"Query: {matched}\n\n{rpc_result}"
        return f"Erro ao conectar ao Postgres: {exc}"

    try:
        with conn.cursor() as cur:
            params = {}
            if order_ids:
                params["order_ids"] = order_ids
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        return f"Erro ao executar query '{matched}': {exc}"
    finally:
        conn.close()

    if not rows:
        return f"Query: {matched}\n\nNenhum resultado encontrado."

    results = []
    for row in rows[:20]:
        record = {}
        for col, val in zip(columns, row):
            if hasattr(val, "__float__"):
                record[col] = float(val)
            else:
                record[col] = str(val) if val is not None else None
        results.append(record)

    result_str = json.dumps(results, ensure_ascii=False, indent=2)
    return f"Query: {matched}\n\n{result_str}"


def search_memory(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database.

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes about delivery, quality, price
    - Customer sentiment analysis (positive, negative, neutral)
    - Product feedback themes and review patterns

    Args:
        question: Natural language question for semantic similarity search in reviews.
    """
    try:
        query_embedding = _get_embedding(question)

        qdrant_url = _get_qdrant_url()
        api_key = _get_qdrant_api_key()
        collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

        client_kwargs: dict = {"url": qdrant_url, "prefer_grpc": False}
        if api_key:
            client_kwargs["api_key"] = api_key
        client = qdrant_client.QdrantClient(**client_kwargs)

        results = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=5,
            with_payload=True,
        )

        sources = []
        for point in results.points:
            text = point.payload.get("text", "")
            rating = point.payload.get("rating")
            sentiment = point.payload.get("sentiment")
            if not text:
                node_content = point.payload.get("_node_content", "")
                if node_content:
                    try:
                        node = json.loads(node_content)
                        raw_text = node.get("text", "")
                        try:
                            to_parse = raw_text.strip()
                            if not to_parse.startswith("{"):
                                to_parse = "{" + to_parse
                            open_braces = to_parse.count("{") - to_parse.count("}")
                            if open_braces > 0:
                                to_parse += "}" * open_braces
                            review = json.loads(to_parse)
                            text = review.get("comment", raw_text)
                            rating = rating or review.get("rating")
                            sentiment = sentiment or review.get("sentiment")
                        except (ValueError, TypeError):
                            text = raw_text
                    except (ValueError, TypeError):
                        pass

            label = f"[score: {point.score:.3f}"
            if rating:
                label += f", rating: {rating}"
            if sentiment:
                label += f", {sentiment}"
            label += "]"
            sources.append(f"{label} {text[:200]}")

        if not sources:
            return "Nenhum review relevante encontrado."

        return f"Reviews encontrados ({len(sources)} resultados):\n\n" + "\n\n".join(sources)

    except Exception as exc:
        return f"Erro ao buscar no Qdrant: {exc}"


# --- OpenAI tool definitions for NIM ---

def get_tools_definitions() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "query_ledger",
                "description": (
                    "Query Postgres for EXACT business data: revenue, order counts, "
                    "payment distribution, segment analysis, monthly trends. "
                    "Use for questions asking for specific numbers or metrics."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Natural language question about business metrics (e.g. 'faturamento por estado', 'evolucao do faturamento mensal')",
                        },
                        "memory_context": {
                            "type": "string",
                            "description": "Optional raw output from a previous search_memory call. The system will extract order_ids from it to use in the query. Pass this when the user asks to combine review data with business metrics.",
                        },
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": (
                    "Search customer reviews by MEANING for opinions, complaints, sentiment. "
                    "Use for questions about what customers SAY, THINK, or FEEL."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Natural language question for semantic search in reviews (e.g. 'clientes reclamando de entrega atrasada')",
                        },
                    },
                    "required": ["question"],
                },
            },
        },
    ]
