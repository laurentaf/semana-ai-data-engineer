"""ShopAgent Lite — Single-agent Chainlit app using NIM directly (no crewai).

Built for Render free-tier deployment (512MB RAM).
Uses NVIDIA NIM llama-3.1-70b as LLM with tool calling + Plotly charts.
"""

import json
import os
import re
import sys
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day4.cloud_tools import query_ledger, search_memory, get_tools_definitions

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_MODEL = os.environ.get("NIM_LEDGER_MODEL", "meta/llama-3.1-70b-instruct")

SYSTEM_PROMPT = """Voce e o ShopAgent, um assistente de analise de e-commerce.

Voce tem acesso a 2 ferramentas:
1. query_ledger — Para dados EXATOS do banco (faturamento, pedidos, ticket medio, etc.)
2. search_memory — Para OPINIOES e SENTIMENTO dos clientes (reclamacoes, elogios, feedback)

REGRAS:
- SEMPRE use uma ferramenta antes de responder. Nunca invente numeros.
- Use query_ledger para perguntas sobre metricas, numeros, totais.
- Use search_memory para perguntas sobre opinioes, reclamacoes, sentimento.
- Chame NO MAXIMO UMA ferramenta por vez. Nunca chame duas ferramentas na mesma mensagem.
- Responda em portugues com dados especificos.
- Inclua numeros exatos nos seus relatorios.
- Quando os dados tiverem multiplas linhas/periodos/estados, liste TODOS os resultados em tabela markdown.
- NAO resuma dados mensais em um unico total. Liste cada periodo separadamente."""


def _wants_chart(text: str) -> bool:
    words = _normalize(text)
    return any(kw in words for kw in ["grafico", "chart", "plot", "curva", "linha do tempo"])


def _normalize(text: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _build_chart_from_tool_result(tool_result: str) -> dict | None:
    """Parse query_ledger result and build a Plotly chart if data is chartable."""
    # Extract the JSON rows from the tool result
    # Format: "Query: xxx\n\n[{...}, {...}]"
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

    # Detect chart type based on data shape
    import plotly.graph_objects as go

    # Monthly timeline (has "mes" column)
    if "mes" in first:
        x = [r["mes"] for r in rows]
        y_key = "faturamento" if "faturamento" in first else "pedidos"
        y = [float(r[y_key]) for r in rows]
        fig = go.Figure(go.Bar(x=x, y=y, marker_color="#4f46e5"))
        fig.update_layout(
            title=f"{y_key.capitalize()} por Mes",
            xaxis_title="Mes",
            yaxis_title=y_key.capitalize(),
            template="plotly_white",
            height=400,
        )
        return fig.to_dict()

    # By state (has "state" column)
    if "state" in first:
        x = [r["state"] for r in rows]
        y_key = "faturamento" if "faturamento" in first else "pedidos"
        y = [float(r[y_key]) for r in rows]
        fig = go.Figure(go.Bar(x=x, y=y, marker_color="#4f46e5"))
        fig.update_layout(
            title=f"{y_key.capitalize()} por Estado",
            xaxis_title="Estado",
            yaxis_title=y_key.capitalize(),
            template="plotly_white",
            height=400,
        )
        return fig.to_dict()

    # By category
    if "category" in first:
        x = [r["category"] for r in rows]
        y_key = "faturamento" if "faturamento" in first else "pedidos"
        y = [float(r[y_key]) for r in rows]
        fig = go.Figure(go.Bar(x=x, y=y, marker_color="#4f46e5"))
        fig.update_layout(
            title=f"{y_key.capitalize()} por Categoria",
            xaxis_title="Categoria",
            yaxis_title=y_key.capitalize(),
            template="plotly_white",
            height=400,
        )
        return fig.to_dict()

    # By status / payment (pie chart)
    status_key = None
    for k in ("status", "payment", "segment"):
        if k in first:
            status_key = k
            break
    if status_key:
        labels = [r[status_key] for r in rows]
        values = [float(r.get("total", r.get("pedidos", 0))) for r in rows]
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4))
        fig.update_layout(
            title=f"Distribuicao por {status_key.capitalize()}",
            template="plotly_white",
            height=400,
        )
        return fig.to_dict()

    return None


@cl.on_chat_start
async def start():
    env_mode = os.environ.get("ENVIRONMENT", "local").upper()
    await cl.Message(
        content=(
            f"**ShopAgent Lite** — E-Commerce Analytics\n\n"
            f"Modo: **{env_mode}** | LLM: **NIM {NIM_MODEL.split('/')[-1]}**\n\n"
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


@cl.on_message
async def main(message: cl.Message):
    if not NIM_API_KEY:
        await cl.Message(content="Erro: NVIDIA_NIM_API_KEY nao configurada.").send()
        return

    client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)
    wants_chart = _wants_chart(message.content)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message.content},
    ]

    tools = get_tools_definitions()

    # Collect query_ledger results for chart building
    ledger_results: list[str] = []

    # Agentic loop: NIM only supports single tool-call per turn,
    # so we process one tool per iteration.
    max_iterations = 4
    for _ in range(max_iterations):
        try:
            completion = client.chat.completions.create(
                model=NIM_MODEL,
                messages=messages,
                tools=tools,
                temperature=0.1,
                max_tokens=1024,
                timeout=120,
            )
        except Exception as exc:
            await cl.Message(content=f"Erro ao chamar NIM: {exc}").send()
            return

        msg = completion.choices[0].message
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            # No tool calls — final answer
            await cl.Message(content=msg.content or "").send()
            # Append chart if requested and we have ledger data
            if wants_chart and ledger_results:
                chart = _build_chart_from_tool_result(ledger_results[-1])
                if chart:
                    await cl.Message(content="", elements=[cl.Plotly(name="chart", figure=chart)]).send()
            return

        # Process only the FIRST tool call (NIM single-tool limitation)
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

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

        # If model requested multiple tool calls, inject a hint to call the next one
        if len(msg.tool_calls) > 1:
            remaining = [tc.function.name for tc in msg.tool_calls[1:]]
            messages.append({
                "role": "user",
                "content": f"Voce tambem precisava chamar: {', '.join(remaining)}. Chame agora se ainda for necessario.",
            })

    # If we hit max iterations, force a final answer
    messages.append({"role": "user", "content": "Resuma os resultados encontrados em portugues em tabela markdown."})
    try:
        completion = client.chat.completions.create(
            model=NIM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            timeout=120,
        )
        await cl.Message(content=completion.choices[0].message.content or "").send()
        if wants_chart and ledger_results:
            chart = _build_chart_from_tool_result(ledger_results[-1])
            if chart:
                await cl.Message(content="", elements=[cl.Plotly(name="chart", figure=chart)]).send()
    except Exception as exc:
        await cl.Message(content=f"Erro: {exc}").send()
