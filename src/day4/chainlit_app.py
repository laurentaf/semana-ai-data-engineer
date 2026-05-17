"""ShopAgent Day 4 — Chainlit chat interface with CrewAI multi-agent crew.

Langfuse tracing via CrewAIInstrumentor + @observe decorator.
Each conversation is grouped by session_id in Langfuse.
"""

import os
import sys
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day4.crew import run_crew, _langfuse_client

ENV_MODE = os.environ.get("ENVIRONMENT", "local")


@cl.on_chat_start
async def start():
    lf_status = "ON" if _langfuse_client else "OFF"

    await cl.Message(
        content=(
            f"**ShopAgent Crew v4 — Multi-Agent E-Commerce Analytics**\n\n"
            f"3 agentes prontos para trabalhar:\n\n"
            f"| Agente | Funcao | Fonte |\n"
            f"|--------|--------|-------|\n"
            f"| **AnalystAgent** | Metricas SQL | The Ledger (Postgres) |\n"
            f"| **ResearchAgent** | Sentimento | The Memory (Qdrant) |\n"
            f"| **ReporterAgent** | Relatorio | Sintese dos dois |\n\n"
            f"Modo: **{ENV_MODE.upper()}** | LangFuse: **{lf_status}**\n\n"
            f"Facha uma pergunta e a crew vai trabalhar!"
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")

    session_id = cl.context.session.id
    user_id = getattr(cl.context.session, "user_id", None) or "anonymous"

    step_crew = cl.Step(name="ShopAgentCrew", type="tool")
    await step_crew.__aenter__()
    step_crew.input = message.content

    await msg.stream_token("**Crew executando...**\n\n")
    await msg.send()

    try:
        result = run_crew(
            question=message.content,
            session_id=session_id,
            user_id=user_id,
        )

        step_crew.output = result[:2000]
        await step_crew.__aexit__(None, None, None)

        await msg.stream_token(result)
        await msg.send()

    except Exception as exc:
        step_crew.output = f"ERROR: {exc}"
        await step_crew.__aexit__(None, None, None)
        await msg.stream_token(f"\n\nErro ao executar a crew: {exc}")
        await msg.send()
