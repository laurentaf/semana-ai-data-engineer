"""ShopAgent Day 3 -- Chainlit chat interface with LangChain agent streaming."""

import sys
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from day3.agent import create_shopagent


@cl.on_chat_start
async def start():
    agent = create_shopagent()
    cl.user_session.set("agent", agent)
    await cl.Message(
        content=(
            "**ShopAgent conectado!**\n\n"
            "Sou seu analista de dados de e-commerce. Posso consultar:\n\n"
            "- **The Ledger** (Postgres) -- faturamento, pedidos, metricas\n"
            "- **The Memory** (Qdrant) -- opinoes, reclamacoes, sentimentos\n\n"
            "Como posso ajudar?"
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    msg = cl.Message(content="")
    current_step = None

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message.content}]},
        version="v2",
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
            tool_name = event["name"]
            current_step = cl.Step(
                name=tool_name,
                type="tool",
            )
            await current_step.__aenter__()
            current_step.input = str(event["data"].get("input", ""))

        elif kind == "on_tool_end":
            if current_step:
                output = str(event["data"].get("output", ""))
                current_step.output = output[:2000] if len(output) > 2000 else output
                await current_step.__aexit__(None, None, None)
                current_step = None

    await msg.send()
