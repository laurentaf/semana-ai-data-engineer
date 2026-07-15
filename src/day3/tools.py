"""ShopAgent Day 3 -- LangChain tool definitions for The Ledger and The Memory.

The LLM generates SQL queries directly for maximum flexibility.
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import psycopg2
import qdrant_client
from dotenv import load_dotenv
from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

_is_cloud = os.environ.get("ENVIRONMENT", "local") == "cloud"


def _get_postgres_connection():
    if _is_cloud:
        db_url = os.environ.get("SUPABASE_DB_URL", "")
        if db_url and "xxxxx" not in db_url and db_url.startswith("postgresql"):
            try:
                return psycopg2.connect(db_url)
            except (psycopg2.OperationalError, OSError):
                pass
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


def _get_embedding(text: str) -> list[float]:
    """Get embedding via FastEmbed (local, no API key needed)."""
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    return list(model.embed(text))[0].tolist()


def _format_results(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "Nenhum resultado encontrado."
    header = " | ".join(f"{c:>15}" for c in columns)
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows[:20]:
        lines.append(" | ".join(f"{str(v):>15}" for v in row))
    return "\n".join(lines)


CHART_DIR = Path(tempfile.gettempdir()) / "shopagent_charts"
CHART_DIR.mkdir(exist_ok=True)


@tool
def render_plotly_chart(data_json: str, chart_type: str, title: str, x_label: str = "", y_label: str = "") -> str:
    """Render an INTERACTIVE Plotly chart in the user's browser.

    CRITICAL: This is the ONLY way to generate visual charts. NEVER create ASCII art.

    Call this tool whenever user asks for: grafico, graph, chart, visualizacao, evolucao, trend, comparacao, distribuicao, plotar, desenhar.

    After calling this tool, the chart will appear INTERACTIVELY in the chat.
    Do NOT also generate ASCII art or text-based representations.

    Args:
        data_json: JSON array. For bar/line/area/scatter: [{"x":"label","y":number},...]
                   For pie: [{"label":"name","value":number},...]
        chart_type: bar, line, pie, scatter, area
        title: Chart title in Portuguese
        x_label: X-axis label
        y_label: Y-axis label
    """
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
    except json.JSONDecodeError as e:
        return f"Erro ao interpretar dados: {e}"

    if not data:
        return "Nenhum dado fornecido para o grafico."

    df = pd.DataFrame(data)

    is_currency = any(
        kw in title.lower() for kw in ("faturamento", "receita", "revenue")
    ) or y_label.lower() in ("faturamento", "receita", "total", "revenue")
    if is_currency:
        label_tmpl = "%{y:.4s}"
        hover_tmpl = "R$ %{y:,.2f}"
        tick_fmt = ".4s"
    else:
        label_tmpl = "%{y:.4s}"
        hover_tmpl = "%{y:,.0f}"
        tick_fmt = ".4s"

    fig = None
    if chart_type == "pie":
        label_col = [c for c in df.columns if c in ("label", "name", "category")][0]
        value_col = [c for c in df.columns if c in ("value", "y", "total", "count")][0]
        fig = px.pie(df, names=label_col, values=value_col, title=title)
        pie_tmpl = f"%{{value:.4s}}" if not is_currency else "R$ %{value:.4s}"
        fig.update_traces(
            texttemplate=f"%{{label}}<br>{pie_tmpl}<br>(%{{percent}})",
            textposition="inside",
            hovertemplate=f"%{{label}}: {hover_tmpl}<extra></extra>",
        )
    elif chart_type == "line":
        x_col = [c for c in df.columns if c in ("x", "mes", "date", "month", "label")][0]
        y_col = [c for c in df.columns if c in ("y", "value", "total", "faturamento", "count")][0]
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
        fig.update_traces(
            texttemplate=label_tmpl, textposition="top center",
            hovertemplate=f"%{{x}}<br>{hover_tmpl}<extra></extra>",
        )
        fig.update_layout(xaxis_title=x_label or x_col, yaxis_title=y_label or y_col)
        fig.update_yaxes(tickformat=tick_fmt)
    elif chart_type == "area":
        x_col = [c for c in df.columns if c in ("x", "mes", "date", "month", "label")][0]
        y_col = [c for c in df.columns if c in ("y", "value", "total", "faturamento", "count")][0]
        fig = px.area(df, x=x_col, y=y_col, title=title)
        fig.update_traces(hovertemplate=f"%{{x}}<br>{hover_tmpl}<extra></extra>")
        fig.update_layout(xaxis_title=x_label or x_col, yaxis_title=y_label or y_col)
        fig.update_yaxes(tickformat=tick_fmt)
    else:
        x_col = [c for c in df.columns if c in ("x", "label", "state", "name", "category", "mes")][0]
        y_col = [c for c in df.columns if c in ("y", "value", "total", "faturamento", "count", "pedidos")][0]
        color_col = next((c for c in df.columns if c not in (x_col, y_col)), None)
        if chart_type == "scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title, color=color_col)
            fig.update_traces(hovertemplate=f"%{{x}}<br>{hover_tmpl}<extra></extra>")
            fig.update_yaxes(tickformat=tick_fmt)
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title, color=color_col, text_auto=False)
            fig.update_traces(
                texttemplate=label_tmpl, textposition="outside",
                hovertemplate=f"%{{x}}<br>{hover_tmpl}<extra></extra>",
            )
            fig.update_yaxes(tickformat=tick_fmt)
        fig.update_layout(xaxis_title=x_label or x_col, yaxis_title=y_label or y_col)

    if fig is None:
        return "Nao foi possivel gerar o grafico."

    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        font=dict(family="Inter, sans-serif", size=13),
        hoverlabel=dict(font_size=13),
    )

    chart_id = str(uuid.uuid4())[:8]
    fig_json = fig.to_json()
    chart_file = CHART_DIR / f"{chart_id}.json"
    chart_file.write_text(fig_json, encoding="utf-8")

    return f"Grafico '{title}' gerado (ID: {chart_id}). Tipo: {chart_type}."


@tool
def execute_sql(sql: str) -> str:
    """Execute a SELECT SQL query on The Ledger (Postgres) e-commerce database.

    Use this for any business metric: revenue, orders, products, customers.
    Write SQL with WHERE clauses for filtering by date, state, category, etc.

    SCHEMA:
    - customers: customer_id, name, email, city, state, segment
    - products: product_id, name, category, price, brand
    - orders: order_id, customer_id (FK), product_id (FK), qty, total, status, payment, created_at

    IMPORTANT: Use TO_CHAR(created_at, 'YYYY-MM') for month formatting.
    Filter by date range: WHERE created_at >= '2026-04-01' AND created_at < '2026-05-01'
    Use LIKE for text searches on name, category, state, brand.

    Args:
        sql: The SELECT SQL query to execute. Must start with SELECT.
    """
    sql_stripped = sql.strip()
    if not sql_stripped.upper().startswith("SELECT"):
        return "Apenas queries SELECT sao permitidas."

    try:
        conn = _get_postgres_connection()
    except (psycopg2.OperationalError, ValueError) as exc:
        return f"Erro ao conectar ao Postgres: {exc}"

    try:
        with conn.cursor() as cur:
            cur.execute(sql_stripped)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        return f"Erro SQL: {exc}"
    finally:
        conn.close()

    return _format_results(columns, rows)


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database (The Memory).

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes (complaints) about delivery, quality, price
    - Customer sentiment analysis (positive, negative, neutral)
    - Product feedback themes and review patterns
    - Any question about what customers SAY, THINK, or FEEL
    - **Evolucao temporal do sentimento** (reviews have created_at field)

    Each review has: comment, rating (1-5), sentiment (positive/neutral/negative),
    created_at (ISO date), product_id, customer_state.

    For temporal analysis, mention the period in the question
    (e.g., "reclamacoes em 2025" or "sentimento em junho 2026").
    The tool will automatically filter by the mentioned date range.

    Args:
        question: Natural language question for semantic similarity search in reviews.
    """
    try:
        import re as _re
        qdrant_url = _get_qdrant_url()
        qdrant_api_key = _get_qdrant_api_key()
        collection_name = os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")
        client_kwargs = {"url": qdrant_url}
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        client = qdrant_client.QdrantClient(**client_kwargs)

        import unicodedata
        def _norm(t):
            return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))

        import unicodedata as _ud
        def _norm(t):
            return "".join(c for c in _ud.normalize("NFKD", t.lower()) if not _ud.combining(c))

        import requests as _req
        _base = qdrant_url.rstrip("/")
        def _qcnt(qfilter: dict | None = None):
            body = {"exact": True}
            if qfilter: body["filter"] = qfilter
            r = _req.post(f"{_base}/collections/{collection_name}/points/count", json=body)
            return r.json()["result"]["count"]

        # Semantic search: use score_threshold instead of arbitrary limit
        _grand_total = _qcnt()
        query_embedding = _get_embedding(question)
        results = client.query_points(
            collection_name=collection_name, query=query_embedding,
            limit=min(2000, _grand_total), score_threshold=0.4, with_payload=True,
        )

        snippets = []
        for point in results.points:
            text = point.payload.get("text", "")
            rating = point.payload.get("rating")
            sentiment = point.payload.get("sentiment")
            created_at = point.payload.get("created_at", "")
            date_str = created_at[:10] if created_at else ""
            if not text:
                nc = point.payload.get("_node_content", "")
                if nc:
                    import json as _json
                    try:
                        node = _json.loads(nc)
                        raw = node.get("text", "")
                        try:
                            to_parse = raw.strip()
                            if not to_parse.startswith("{"): to_parse = "{" + to_parse
                            ob = to_parse.count("{") - to_parse.count("}")
                            if ob > 0: to_parse += "}" * ob
                            review = _json.loads(to_parse)
                            text = review.get("comment", raw)
                            rating = rating or review.get("rating")
                            sentiment = sentiment or review.get("sentiment")
                        except (ValueError, TypeError):
                            text = raw
                    except (ValueError, TypeError):
                        pass
            ctx = f"[{date_str} | score: {point.score:.3f}"
            if rating: ctx += f", rating: {rating}"
            if sentiment: ctx += f", {sentiment}"
            ctx += "]"
            snippets.append(f"{ctx} {text[:200]}")

        if not snippets:
            return "Nenhum review relevante encontrado."

        sent_found = {"positive": 0, "neutral": 0, "negative": 0}
        ratings_found = []
        for s in snippets:
            for k in sent_found:
                if f", {k}]" in s: sent_found[k] += 1
            rm = _re.search(r"rating: (\d)", s)
            if rm: ratings_found.append(float(rm.group(1)))

        total_topic = len(snippets)
        pct = {k: f"{100*v/total_topic:.1f}%" for k, v in sent_found.items()}
        result = f"Distribuicao nos {total_topic} reviews sobre o tema:\n"
        result += f"  Positivos: {sent_found['positive']} ({pct['positive']})\n"
        result += f"  Neutros:   {sent_found['neutral']} ({pct['neutral']})\n"
        result += f"  Negativos: {sent_found['negative']} ({pct['negative']})\n"
        if ratings_found:
            result += f"  Rating medio: {sum(ratings_found)/len(ratings_found):.1f}\n"
        result += f"\n(Total geral na base: {_grand_total} reviews)\n"

        months = {}
        for s in snippets:
            m = _re.search(r"\[(\d{4}-\d{2})", s)
            if m:
                ym = m.group(1)
                if ym not in months:
                    months[ym] = {"positive": 0, "neutral": 0, "negative": 0, "ratings": []}
                for k in ("positive", "neutral", "negative"):
                    if f", {k}]" in s:
                        months[ym][k] += 1
                rm = _re.search(r"rating: (\d)", s)
                if rm: months[ym]["ratings"].append(float(rm.group(1)))

        # Build the raw sample for LLM qualitative reading (30 reviews: 10 each sentiment)
        sample_pool = {"positive": [], "neutral": [], "negative": []}
        for point in results.points:
            s = point.payload.get("sentiment", "neutral")
            if len(sample_pool[s]) < 10:
                raw_text = point.payload.get("text", "")[:300]
                rating = point.payload.get("rating", "?")
                created_at = point.payload.get("created_at", "")[:10]
                sample_pool[s].append(f"  [{created_at} | nota {rating}] {raw_text}")

        result += "\n--- AMOSTRA PARA LEITURA (30 reviews, 10 de cada sentimento) ---\n\n"
        for sentiment, label in [("positive", "POSITIVOS"), ("neutral", "NEUTROS"), ("negative", "NEGATIVOS")]:
            if sample_pool[sentiment]:
                result += f"[{label}]\n"
                result += "\n".join(sample_pool[sentiment]) + "\n\n"

        if months:
            result += "Distribuicao mensal:\n"
            result += "Mes       | Total | Pos | Neu | Neg | Rating\n"
            result += "----------|-------|-----|-----|-----|-------\n"
            for ym in sorted(months):
                m = months[ym]
                total_m = sum(m[k] for k in ("positive", "neutral", "negative"))
                avg_r = sum(m["ratings"]) / len(m["ratings"]) if m["ratings"] else 0
                result += f"{ym} | {total_m:>5} | {m['positive']:>3} | {m['neutral']:>3} | {m['negative']:>3} | {avg_r:.1f}\n"

        return result
    except Exception as exc:
        return f"Erro ao buscar no Qdrant: {exc}"


if __name__ == "__main__":
    test = execute_sql.invoke("SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.created_at >= '2026-04-01' AND o.created_at < '2026-05-01' GROUP BY c.state ORDER BY faturamento DESC")
    print(test)
