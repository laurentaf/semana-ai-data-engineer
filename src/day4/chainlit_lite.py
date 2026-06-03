"""ShopAgent Lite — Single-agent Chainlit app (no crewai).

Built for Render free-tier deployment (512MB RAM).
LLM: OpenRouter owl-alpha (free, tool calling, Portuguese)
Embeddings: NIM nv-embedqa-e5-v5 (for Qdrant search)
Charts: Plotly (auto-render for chartable data)
Memory: Last 5 exchanges per session
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day4.cloud_tools import query_ledger, search_memory, get_tools_definitions

# Build version from git short SHA (for deploy tracking)
try:
    _build = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL,
    ).decode().strip()
except Exception:
    _build = os.environ.get("RENDER_GIT_COMMIT", "dev")[:7]

# LLM via OpenRouter (free, stable Portuguese + tool calling)
OPENROUTER_API_KEY = os.environ.get("OPEN_ROUTER_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "openrouter/owl-alpha")
LLM_BASE_URL = "https://openrouter.ai/api/v1"

MAX_HISTORY = 5  # max past exchanges to keep in conversation memory

SYSTEM_PROMPT = """Voce e o ShopAgent, um assistente de analise de e-commerce.

Voce tem acesso a 2 ferramentas:
1. query_ledger — Para dados EXATOS do banco (faturamento, pedidos, ticket medio, etc.)
2. search_memory — Para OPINIOES e SENTIMENTO dos clientes (reclamacoes, elogios, feedback)

DADOS DISPONIVEIS no query_ledger:
- revenue_by_month: faturamento, pedidos E ticket_medio por mes (12 meses)
- revenue_by_state: faturamento e pedidos por estado
- revenue_by_category: faturamento, pedidos e ticket_medio por categoria
- revenue_by_month_state: faturamento, pedidos e ticket_medio por mes E estado
- orders_by_status: pedidos por status
- payment_distribution: pedidos por forma de pagamento
- segment_analysis: clientes, pedidos e ticket_medio por segmento
- top_products: top 10 produtos por faturamento

REGRAS:
- SEMPRE use uma ferramenta antes de responder. Nunca invente numeros.
- Para perguntas sobre ticket_medio mensal, use revenue_by_month (ja traz ticket_medio).
- Para perguntas sobre ticket_medio mensal por estado, use revenue_by_month_state.
- Use search_memory para perguntas sobre opinioes, reclamacoes, sentimento.
- Se a pergunta cruza dados numericos com opinioes, chame as DUAS ferramentas em sequencia.
- Chame NO MAXIMO UMA ferramenta por vez. Nunca chame duas ferramentas na mesma mensagem.
- Se ja tem dados suficientes para responder, NAO chame mais ferramentas. Responda direto.
- Antes de dizer que um dado nao existe, verifique se ele ja esta em uma das queries acima.
- Responda em portugues com dados especificos.
- Inclua numeros exatos nos seus relatorios.
- Quando os dados tiverem multiplas linhas/periodos/estados, formate em TABELA MARKDOWN com colunas |---|.
- NAO resuma dados mensais em um unico total. Liste cada periodo separadamente.
- NAO repita os dados brutos em JSON. Formate como tabela markdown legivel para o usuario.

LIMITACOES (guiderails):
- Voce so conhece os dados disponiveis nas ferramentas. Se a pergunta pede um dado que nao existe em NENHUMA query (ex: custo de compra, margem de lucro, desconto, custo logistico, imposto), diga claramente que esse dado NAO esta disponivel no sistema. NAO invente nem estime valores.
- Se uma query retorna dados parciais, apresente o que tem e diga o que falta.
- Nunca faca calculos com dados inventados. So calcule com numeros retornados pelas ferramentas."""


def _wants_chart(text: str) -> bool:
    words = _normalize(text)
    return any(kw in words for kw in [
        "grafico", "chart", "plot", "curva", "linha do tempo",
        "evolucao", "mes a mes", "comparacao", "mensal", "timeline",
        "linha",
    ])


def _wants_line(text: str) -> bool:
    words = _normalize(text)
    return any(kw in words for kw in ["linha", "line", "curva", "evolucao", "timeline"])


def _pick_y_key(first: dict, user_msg: str) -> str:
    """Pick the best Y axis based on what user asked about."""
    words = _normalize(user_msg)
    if "ticket" in words and "ticket_medio" in first:
        return "ticket_medio"
    if "pedido" in words and "pedidos" in first:
        return "pedidos"
    if "faturamento" in words and "faturamento" in first:
        return "faturamento"
    # Default: faturamento if available, else first numeric key
    if "faturamento" in first:
        return "faturamento"
    for k in ("pedidos", "ticket_medio", "total", "clientes"):
        if k in first:
            return k
    return list(first.keys())[-1]


def _should_auto_chart(tool_result: str) -> bool:
    """Auto-detect if data is chartable (time-series, by state/category) — show chart."""
    json_match = re.search(r"\[.*\]", tool_result, re.DOTALL)
    if not json_match:
        return False
    try:
        rows = json.loads(json_match.group())
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(rows, list) or len(rows) < 2:
        return False
    first = rows[0]
    return any(k in first for k in ("mes", "state", "category", "status", "payment", "segment"))


def _normalize(text: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _fmt_brl(val: float) -> str:
    """Format number as Brazilian currency: R$ 207.750,11"""
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_month(iso: str) -> str:
    """Convert 2025-06 → Jun/2025 in Portuguese."""
    months = {
        "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
        "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
    }
    parts = iso.split("-")
    if len(parts) == 2 and parts[1] in months:
        return f"{months[parts[1]]}/{parts[0]}"
    return iso


def _bar_layout(title: str, x_title: str, y_title: str, is_currency: bool) -> dict:
    """Common layout with BR formatting for all bar charts."""
    layout = dict(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        height=420,
        margin=dict(l=60, r=30, t=50, b=50),
        font=dict(family="Inter, sans-serif", size=13),
    )
    if is_currency:
        layout["yaxis"] = dict(
            tickprefix="R$ ",
            tickformat=",.",
            separatethousands=".",
            decimals=",",
        )
    return layout


def _build_chart_from_tool_result(tool_result: str, user_msg: str = "", line_chart: bool = False):
    """Parse query_ledger result and build a Plotly Figure if data is chartable."""
    import plotly.graph_objects as go

    json_match = re.search(r"\[.*\]", tool_result, re.DOTALL)
    if not json_match:
        return None

    try:
        rows = json.loads(json_match.group())
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(rows, list) or len(rows) < 2:
        return None

    first = rows[0]
    y_key = _pick_y_key(first, user_msg)
    is_currency = y_key in ("faturamento", "ticket_medio")

    if "mes" in first:
        x = [_fmt_month(r["mes"]) for r in rows]
        y = [float(r[y_key]) for r in rows]
        text_labels = [_fmt_brl(v) if is_currency else f"{v:,.0f}" for v in y]

        if line_chart:
            fig = go.Figure(go.Scatter(
                x=x, y=y, mode="lines+markers+text",
                line=dict(color="#4f46e5", width=2.5),
                marker=dict(size=8, color="#4f46e5"),
                text=text_labels, textposition="top center",
                textfont=dict(size=11),
            ))
        else:
            fig = go.Figure(go.Bar(
                x=x, y=y, marker_color="#4f46e5",
                text=text_labels, textposition="outside",
                textfont=dict(size=11),
            ))
        fig.update_layout(**_bar_layout(
            f"{y_key.replace('_', ' ').capitalize()} por Mes", "Mes",
            y_key.replace('_', ' ').capitalize(), is_currency,
        ))
        fig.update_xaxes(tickangle=-45)
        return fig

    if "state" in first:
        x = [r["state"] for r in rows]
        y = [float(r[y_key]) for r in rows]
        text_labels = [_fmt_brl(v) if is_currency else f"{v:,.0f}" for v in y]
        fig = go.Figure(go.Bar(
            x=x, y=y, marker_color="#4f46e5",
            text=text_labels, textposition="outside",
            textfont=dict(size=11),
        ))
        fig.update_layout(**_bar_layout(
            f"{y_key.replace('_', ' ').capitalize()} por Estado", "Estado",
            y_key.replace('_', ' ').capitalize(), is_currency,
        ))
        return fig

    if "category" in first:
        x = [r["category"] for r in rows]
        y = [float(r[y_key]) for r in rows]
        text_labels = [_fmt_brl(v) if is_currency else f"{v:,.0f}" for v in y]
        fig = go.Figure(go.Bar(
            x=x, y=y, marker_color="#4f46e5",
            text=text_labels, textposition="outside",
            textfont=dict(size=11),
        ))
        fig.update_layout(**_bar_layout(
            f"{y_key.replace('_', ' ').capitalize()} por Categoria", "Categoria",
            y_key.replace('_', ' ').capitalize(), is_currency,
        ))
        return fig

    status_key = None
    for k in ("status", "payment", "segment"):
        if k in first:
            status_key = k
            break
    if status_key:
        labels = [r[status_key] for r in rows]
        values = [float(r.get("total", r.get("pedidos", 0))) for r in rows]
        text_labels = [_fmt_brl(v) if is_currency else f"{v:,.0f}" for v in values]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.4,
            text=text_labels, textposition="inside",
            textfont=dict(size=13),
        ))
        fig.update_layout(
            title=dict(text=f"Distribuicao por {status_key.capitalize()}", font=dict(size=16)),
            template="plotly_white", height=420,
            font=dict(family="Inter, sans-serif", size=13),
            margin=dict(l=30, r=30, t=50, b=30),
        )
        return fig

    return None


async def _send_chart(ledger_results: list[str], wants_chart: bool, user_msg: str, line_chart: bool):
    """Build and send Plotly chart if data is chartable."""
    if not ledger_results:
        return
    last_result = ledger_results[-1]
    if wants_chart or _should_auto_chart(last_result):
        fig = _build_chart_from_tool_result(last_result, user_msg=user_msg, line_chart=line_chart)
        if fig:
            await cl.Message(
                content="",
                elements=[cl.Plotly(name="chart", figure=fig, display="inline")],
            ).send()


async def _llm_create(client: OpenAI, max_retries: int = 3, **kwargs) -> object:
    """Call OpenAI chat completion with retry on transient 400/429/503 errors."""
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as exc:
            is_retryable = any(s in str(exc).lower() for s in ["400", "429", "503", "overloaded", "rate limit", "provider returned error"])
            if is_retryable and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise


@cl.on_chat_start
async def start():
    env_mode = os.environ.get("ENVIRONMENT", "local").upper()
    llm_short = LLM_MODEL.split("/")[-1]
    cl.user_session.set("history", [])
    await cl.Message(
        content=(
            f"**ShopAgent Lite** — E-Commerce Analytics\n\n"
            f"Modo: **{env_mode}** | LLM: **{llm_short}** | Build: `{_build}`\n\n"
            f"Pergunte sobre faturamento, pedidos, sentimento de clientes, etc.\n"
            f"Ex: *Qual o faturamento por estado?* ou *Grafico de vendas mensais*"
        )
    ).send()


def _exec_tool(fn_name: str, fn_args: dict) -> str:
    if fn_name == "query_ledger":
        return query_ledger(question=fn_args.get("question", ""))
    elif fn_name == "search_memory":
        return search_memory(question=fn_args.get("question", ""))
    return f"Unknown tool: {fn_name}"


def _trim_history(history: list[dict], max_exchanges: int = MAX_HISTORY) -> list[dict]:
    """Keep only the last N user+assistant exchange pairs."""
    # Count exchanges (user messages as anchors)
    user_indices = [i for i, m in enumerate(history) if m.get("role") == "user"]
    if len(user_indices) <= max_exchanges:
        return history
    start = user_indices[-max_exchanges]
    return history[start:]


@cl.on_message
async def main(message: cl.Message):
    if not OPENROUTER_API_KEY:
        await cl.Message(content="Erro: OPEN_ROUTER_API_KEY nao configurada.").send()
        return

    # Load conversation history
    history: list[dict] = cl.user_session.get("history", [])
    history = _trim_history(history)

    client = OpenAI(base_url=LLM_BASE_URL, api_key=OPENROUTER_API_KEY)
    wants_chart = _wants_chart(message.content)
    line_chart = _wants_line(message.content)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": message.content},
    ]

    tools = get_tools_definitions()
    ledger_results: list[str] = []
    tool_call_count = 0
    MAX_TOOL_CALLS = 3

    for iteration in range(MAX_TOOL_CALLS + 3):
        include_tools = tool_call_count < MAX_TOOL_CALLS
        try:
            kwargs = {
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
                "timeout": 60,
            }
            if include_tools:
                kwargs["tools"] = tools
            completion = await _llm_create(client, **kwargs)
        except Exception as exc:
            await cl.Message(content=f"Erro: {exc}").send()
            return

        msg = completion.choices[0].message
        msg_dict = msg.model_dump()
        if msg_dict.get("content") is None:
            msg_dict["content"] = ""
        messages.append(msg_dict)

        if not msg.tool_calls:
            await cl.Message(content=msg.content or "").send()
            await _send_chart(ledger_results, wants_chart, message.content, line_chart)
            history.append({"role": "user", "content": message.content})
            history.append({"role": "assistant", "content": msg.content or ""})
            cl.user_session.set("history", _trim_history(history))
            return

        if not include_tools:
            break

        # Process first tool call
        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        step = cl.Step(name=fn_name, type="tool")
        await step.__aenter__()
        step.input = json.dumps(fn_args, ensure_ascii=False)

        try:
            result = _exec_tool(fn_name, fn_args)
        except Exception as exc:
            result = f"Error: {exc}"

        step.output = result[:500]
        await step.__aexit__(None, None, None)

        if fn_name == "query_ledger":
            ledger_results.append(result)

        tool_call_count += 1

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

        # After all tools, force LLM to produce final text (no more tools)
        if tool_call_count >= MAX_TOOL_CALLS:
            messages.append({"role": "user", "content": "Agora responda em tabela markdown. NAO chame mais ferramentas."})

    # Force final answer: no tools, explicit prompt
    messages.append({
        "role": "user",
        "content": "Agora formate os resultados acima em tabela markdown para o usuario. NAO chame mais ferramentas.",
    })
    try:
        completion = await _llm_create(
            client,
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            timeout=60,
        )
        final_text = completion.choices[0].message.content or ""
        await cl.Message(content=final_text).send()
        await _send_chart(ledger_results, wants_chart, message.content, line_chart)
        history.append({"role": "user", "content": message.content})
        history.append({"role": "assistant", "content": final_text})
        cl.user_session.set("history", _trim_history(history))
    except Exception as exc:
        await cl.Message(content=f"Erro: {exc}").send()
