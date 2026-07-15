"""ShopAgent — Chainlit chat with LangChain ReAct agent (fast, concise, tool-aware)."""

import json
import os
import re
import sys
from pathlib import Path

import chainlit as cl
import plotly.io as pio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day3.tools import CHART_DIR, execute_sql, qdrant_semantic_search, render_plotly_chart

ENV_MODE = os.environ.get("ENVIRONMENT", "local")
OPENCODE_GO_KEY = os.environ.get("OPENCODE_GO_API_KEY", os.environ.get("OPENCODE_API_KEY", ""))
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-v4-flash")

# LangFuse observability
_lf_enabled = bool(
    os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    and not os.environ.get("LANGFUSE_SECRET_KEY", "").startswith("sk-lf-your")
)
_lf_handler = None
if _lf_enabled:
    try:
        from langfuse.langchain import CallbackHandler as _LfHandler
        _lf_handler = _LfHandler()
        import langfuse as _lf
        _client = _lf.get_client()
    except Exception:
        _lf_enabled = False

SYSTEM_PROMPT = """Voce e o ShopAgent, analista de e-commerce autonomo.

Fontes de dados:
1. **The Ledger (Postgres)** — Dados exatos via SQL. Tabelas: customers, products, orders.
   Use TO_CHAR(created_at, 'YYYY-MM') para meses. Filtre com WHERE.

2. **The Memory (Qdrant)** — Reviews dos clientes com:
   - comment, rating (1-5), sentiment (positive/neutral/negative), created_at (data ISO)
   - created_at esta indexado. A ferramenta ja filtra por periodo se voce mencionar na pergunta.
   - Para analise temporal: pergunte uma vez com "evolucao" ou "comparacao" + periodos.

3. **render_plotly_chart** — Gera graficos Plotly interativos.

REGRAS:
- CHAME CADA FERRAMENTA UMA UNICA VEZ. Nao repita chamadas.
- SQL para numeros exatos. Qdrant para opinioes/sentimento.
- NUNCA invente dados. Se nao tem, diga.
- Responda em portugues, adapte o nivel de detalhe ao que foi perguntado.
- Para relatorio COMPLETO: chame SQL + Qdrant (cada um uma vez) e synthesize.
- Para analise temporal de sentimento: a ferramenta Qdrant ja retorna dados agregados por mes. Apenas apresente em tabela.
- GRAFICO: use apenas para dados simples (faturamento por estado, vendas por mes). Nao gere graficos multi-serie."""


def _get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENCODE_GO_KEY,
        base_url="https://opencode.ai/zen/go/v1",
        temperature=0,
        streaming=True,
        max_tokens=4096,
    )


def _get_lf_config(session_id: str, user_id: str = "anonymous") -> dict:
    if not _lf_handler:
        return {}
    return {
        "callbacks": [_lf_handler],
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_user_id": user_id,
            "langfuse_tags": ["shopagent-day4", ENV_MODE],
        },
    }


@cl.on_chat_start
async def start():
    llm = _get_llm()
    agent = create_react_agent(
        model=llm,
        tools=[execute_sql, qdrant_semantic_search, render_plotly_chart],
        prompt=SYSTEM_PROMPT,
    )
    cl.user_session.set("agent", agent)
    lf_status = "ON" if _lf_enabled else "OFF"
    await cl.Message(
        content=(
            f"**ShopAgent** — E-Commerce Analytics | Modo: **{ENV_MODE.upper()}** | LangFuse: **{lf_status}**\n\n"
            "Pergunte sobre faturamento, pedidos, clientes, opinioes ou graficos.\n"
            "Ex: *Qual o faturamento por estado?*, *Clientes reclamando de atraso*, *Grafico de vendas mensais*"
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    msg = cl.Message(content="")
    current_step = None

    session_id = cl.context.session.id
    user_id = getattr(cl.context.session, "user_id", None) or "anonymous"
    lf_config = _get_lf_config(session_id=session_id, user_id=user_id)

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message.content}]},
        version="v2",
        config=lf_config or None,
    ):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                token = chunk.content
                if isinstance(token, str):
                    await msg.stream_token(token)
                elif isinstance(token, list):
                    for block in token:
                        if isinstance(block, dict) and block.get("type") == "text":
                            await msg.stream_token(block["text"])

        elif kind == "on_tool_start":
            current_step = cl.Step(name=event["name"], type="tool")
            await current_step.__aenter__()
            current_step.input = str(event["data"].get("input", ""))

        elif kind == "on_tool_end":
            if current_step:
                current_step.output = str(event["data"].get("output", ""))[:2000]
                await current_step.__aexit__(None, None, None)
                if current_step.name == "render_plotly_chart":
                    match = re.search(r'ID: (\w+)', current_step.output)
                    if match:
                        chart_id = match.group(1)
                        chart_file = CHART_DIR / f"{chart_id}.json"
                        if chart_file.exists():
                            try:
                                fig_json = json.loads(chart_file.read_text(encoding="utf-8"))
                                fig = pio.from_json(json.dumps(fig_json))
                                await cl.Message(
                                    content="",
                                    elements=[cl.Plotly(name="chart", figure=fig, display="inline")],
                                ).send()
                            except Exception:
                                pass
                current_step = None

    await msg.send()

    if _lf_enabled:
        try:
            import langfuse as _lf
            _lf.get_client().flush()
        except Exception:
            pass
