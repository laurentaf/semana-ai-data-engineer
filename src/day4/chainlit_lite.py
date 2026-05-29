"""ShopAgent Lite — Single-agent Chainlit app using NIM directly (no crewai).

Built for Render free-tier deployment (512MB RAM).
Uses NVIDIA NIM llama-3.1-70b as LLM with tool calling.
"""

import json
import os
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

Você tem acesso a 2 ferramentas:
1. query_ledger — Para dados EXATOS do banco (faturamento, pedidos, ticket medio, etc.)
2. search_memory — Para OPINIOES e SENTIMENTO dos clientes (reclamacoes, elogios, feedback)

REGRAS:
- SEMPRE use uma ferramenta antes de responder. Nunca invente numeros.
- Use query_ledger para perguntas sobre metricas, numeros, totais.
- Use search_memory para perguntas sobre opinioes, reclamacoes, sentimento.
- Para perguntas completas, use AMBAS as ferramentas.
- Responda em portugues com dados especificos.
- Inclua numeros exatos nos seus relatorios."""


@cl.on_chat_start
async def start():
    env_mode = os.environ.get("ENVIRONMENT", "local").upper()
    await cl.Message(
        content=(
            f"**ShopAgent Lite** — E-Commerce Analytics\n\n"
            f"Modo: **{env_mode}** | LLM: **NIM {NIM_MODEL.split('/')[-1]}**\n\n"
            f"Pergunte sobre faturamento, pedidos, sentimento de clientes, etc.\n"
            f"Ex: *Qual o faturamento por estado?* ou *Clientes reclamando de entrega*"
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    if not NIM_API_KEY:
        await cl.Message(content="Erro: NVIDIA_NIM_API_KEY nao configurada.").send()
        return

    client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message.content},
    ]

    tools = get_tools_definitions()

    # Agentic loop: call tools until the LLM stops requesting them
    max_iterations = 5
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

        choice = completion.choices[0]
        msg = choice.message

        # Add assistant message to conversation
        messages.append(msg.model_dump())

        # If no tool calls, we're done — stream the response
        if not msg.tool_calls:
            await cl.Message(content=msg.content or "").send()
            return

        # Execute each tool call
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            step = cl.Step(name=fn_name, type="tool")
            await step.__aenter__()
            step.input = json.dumps(fn_args, ensure_ascii=False)

            try:
                if fn_name == "query_ledger":
                    result = query_ledger(question=fn_args.get("question", ""))
                elif fn_name == "search_memory":
                    result = search_memory(question=fn_args.get("question", ""))
                else:
                    result = f"Unknown tool: {fn_name}"
            except Exception as exc:
                result = f"Error: {exc}"

            step.output = result[:500]
            await step.__aexit__(None, None, None)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # If we hit max iterations, ask NIM for a final summary
    try:
        completion = client.chat.completions.create(
            model=NIM_MODEL,
            messages=messages + [{"role": "user", "content": "Resuma os resultados encontrados em portugues."}],
            temperature=0.1,
            max_tokens=1024,
            timeout=120,
        )
        await cl.Message(content=completion.choices[0].message.content or "").send()
    except Exception as exc:
        await cl.Message(content=f"Erro: {exc}").send()
