"""ShopAgent Day 4 — Chainlit chat interface with CrewAI multi-agent crew."""

import os
import sys
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day4.crew import ShopAgentCrew, _get_langfuse

ENV_MODE = os.environ.get("ENVIRONMENT", "local")


@cl.on_chat_start
async def start():
    lf = _get_langfuse()
    lf_status = "ON" if lf else "OFF"

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

    cl.user_session.set("crew", None)


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")

    step_analyst = cl.Step(name="AnalystAgent", type="tool")
    step_researcher = cl.Step(name="ResearchAgent", type="tool")
    step_reporter = cl.Step(name="ReporterAgent", type="tool")

    with step_analyst:
        step_analyst.input = message.content
        await step_analyst.__aenter__()

    await msg.stream_token("**AnalystAgent** consultando The Ledger...\n\n")
    await msg.send()

    try:
        from day4.crew import run_crew

        result = run_crew(message.content)

        step_analyst.output = "SQL queries executed against The Ledger"
        await step_analyst.__aexit__(None, None, None)

        with step_researcher:
            step_researcher.input = message.content
            step_researcher.output = "Semantic search executed against The Memory"
            await step_researcher.__aenter__()
            await step_researcher.__aexit__(None, None, None)

        with step_reporter:
            step_reporter.input = "Analyst + Researcher findings"
            step_reporter.output = result[:2000]
            await step_reporter.__aenter__()
            await step_reporter.__aexit__(None, None, None)

        await msg.stream_token(result)
        await msg.send()

    except Exception as exc:
        await step_analyst.__aexit__(None, None, None)
        await msg.stream_token(f"\n\nErro ao executar a crew: {exc}")
        await msg.send()
