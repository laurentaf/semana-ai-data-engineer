# SEMANA AI DATA ENGINEER 2026

## De Zero a Agente Autonomo | ShopAgent

**13 a 17 de Abril de 2026 | 20h - 23h (Brasilia)**
AIDE Brasil | Formacao AI Data Engineer | Luan Moreno

---

## Visao Geral

Em 4 fases praticas + 1 podcast, os participantes constroem do zero o **ShopAgent**: um sistema multi-agent de IA para e-commerce que consulta dados estruturados (SQL) e semanticos (vetores), com interface conversacional e frontend profissional.

**Pergunta Central:** *O que eu consigo fazer agora que nao conseguia antes?*

**Filosofia Docker-First:** Dias 1-3 rodam 100% local. Dia 4 migra para cloud -- mesma arquitetura, so muda o endpoint.

---

## Stack Completa

```
+------------------+     +------------------+     +------------------+
|  DATA GENERATION |     |   AI / LLM       |     |   INTERFACE      |
|  ShadowTraffic   |     |   Claude         |     |   Chainlit       |
+--------+---------+     |   LlamaIndex     |     |   Impeccable     |
         |               |   LangChain      |     |   UI/UX Pro Max  |
         v               |   CrewAI         |     +--------+---------+
+------------------+     +--------+---------+              |
|  STORAGE         |              |                        v
|  Postgres        |              v               +------------------+
|  (The Ledger)    |     +------------------+     |   QUALITY        |
|  Qdrant          |<--->|   MCP Protocol   |     |   DeepEval       |
|  (The Memory)    |     |   AgentSpec      |     |   LangFuse       |
+------------------+     +------------------+     +------------------+
```

---

## Arco Narrativo

| Dia | Tema | Emocao | O Participante Sai Com... |
|-----|------|--------|--------------------------|
| 1 Seg | **INGERIR** | Curiosidade | Dados fluindo + Claude Code + Agentic Commerce |
| 2 Ter | **CONTEXTUALIZAR** | Confianca | IA pesquisando nos SEUS dados (RAG + Ledger) |
| 3 Qua | **AGENTE** | Empolgacao | Agente autonomo + AgentSpec modo Deus |
| 4 Qui | **MULTI-AGENT** | Orgulho | Time de agentes + Frontend lindo + Cloud |
| 5 Sex | **REFLETIR** | Inspiracao | Clareza sobre carreira e proximo passo |

### Progressao de Autonomia

```
Dia 1: EU FACO, IA AJUDA         (Claude Code assiste)
Dia 2: IA BUSCA, EU PERGUNTO     (RAG + Ledger via MCP)
Dia 3: IA PROJETA, EU VALIDO     (AgentSpec + Agent autonomo)
Dia 4: IA CONSTROI, IA EXECUTA   (AgentSpec + CrewAI + Frontend)
```

---

## Agentic Commerce -- O Conceito Disruptivo

> *O shopper do futuro nao e humano. E um agente de IA que decide e executa.*

O ShopAgent nao e so um exercicio tecnico -- e um exemplo real do que o mercado esta adotando:

- **McKinsey (Jan 2026):** AI agents podem intermediar **$3-5 trilhoes** em comercio global ate 2030
- **Google Cloud (Jan 2026):** Lancou "Gemini Enterprise for CX" -- agentes autonomos discovery-to-purchase
- **60%+ das buscas** de produto ja comecam em interfaces de IA, nao em search engines
- **O funil colapsa:** awareness -> pesquisa -> comparacao -> checkout acontece numa unica conversa com IA

| Antes | Agora (Agentic Commerce) |
|-------|--------------------------|
| Humano navega, compara, decide | Agente pesquisa, compara, executa |
| SEO para olhos humanos | AEO (Agent Engine Optimization) para maquinas |
| Funil de 7 etapas | Conversa unica |
| Dados para dashboards | Dados para agentes |

**O ShopAgent e exatamente isso:** um sistema que consulta dados de e-commerce (precos, estoque, reviews) e toma decisoes autonomas. Cada noite da semana constroi um pedaco desse futuro.

Agentic Commerce aparece como fio condutor em cada dia:

| Dia | Conexao com Agentic Commerce |
|-----|------------------------------|
| 1 | "O mercado esta mudando: $3-5 tri intermediados por agentes. Vamos construir um." |
| 2 | "Pra um agente funcionar, precisa de dados exatos E compreensao. Isso e Ledger + RAG." |
| 3 | "Um agente de verdade decide sozinho. AgentSpec projeta, o agente executa." |
| 4 | "Na pratica, um time de agentes com frontend profissional. Isso e o produto." |

---

# DIA 1 -- Segunda-feira (13/Abr)

## INGERIR: Dados + Fundamentos + Agentic Commerce

> *De "o que e isso?" para "tenho dados fluindo e entendo pra onde o mercado vai"*

### Topicos do Dia

1. **AI Data Engineering** -- numeros, cenario e realidade do mercado
2. **AI Coding Agents** -- o que sao, tipos, quando usar cada
3. **Claude Code** -- deep dive: Claude & Claude Code
4. **Configuration** -- MCPs, SubAgents, KBs (conceitual)
5. **Agentic Commerce & ShopAgent** -- o caso de uso disruptivo
6. **ShadowTraffic** -- geracao de todos os dados do ShopAgent
7. **Pydantic & Structured Outputs** -- validacao + provocacao RAG

### Agenda Detalhada

#### Bloco 1: AI Data Engineering + AI Coding Agents (20h00 - 20h25)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h00 | AI Data Engineering | O que e, numeros do mercado, como IA muda o DE |
| 20h10 | AI Coding Agents | O que sao e os 4 tipos |
| 20h18 | Panorama | Cursor (IDE), Claude Code (Terminal), Codex (Cloud), OpenClaw (Chat) |

#### Bloco 2: Claude Code Deep Dive (20h25 - 21h00)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h25 | O que e Claude & Claude Code | Anthropic, modelos, como funciona |
| 20h35 | Demo ao vivo | Claude Code explorando dados, gerando codigo |
| 20h45 | Configuration | Conceito de MCPs, SubAgents, Knowledge Bases |
| 20h55 | Preview | "Esses conceitos vao voltar nos Dias 2, 3 e 4 com forca total" |

#### Bloco 3: Agentic Commerce & ShopAgent (21h00 - 21h25)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h00 | Agentic Commerce | O conceito: agentes de IA como shoppers autonomos |
| 21h08 | Os numeros | McKinsey $3-5T, Google CX, 60% buscas em IA |
| 21h15 | ShopAgent | "Nosso caso de uso: vamos construir um agente de e-commerce" |
| 21h20 | A semana | O que vamos construir em cada noite |

> **Momento disruptivo:** "Ate 2030, agentes de IA vao intermediar mais comercio
> do que todos os marketplaces juntos. Nesta semana, voces vao construir um desses agentes."

#### Bloco 4: ShadowTraffic (21h25 - 22h10)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h25 | docker-compose up | Subir ShadowTraffic + Postgres + Qdrant |
| 21h35 | Config ShadowTraffic | Generators: customers, products, orders -> Postgres |
| 21h50 | Reviews | Generator com textos realistas -> JSONL |
| 22h00 | Validacao ao vivo | Claude Code explorando os dados gerados |

**ShadowTraffic gera DOIS tipos de dados:**
```
ShadowTraffic
    |
    +---> DADOS EXATOS -> Postgres
    |     customers (customer_id, name, email, state, segment)
    |     products  (product_id, name, category, price, brand)
    |     orders    (order_id, customer_id, product_id, qty, total, status, payment)
    |
    +---> DADOS TEXTO -> JSONL
          reviews   (review_id, order_id, rating, comment, sentiment)
          "Entrega demorou 15 dias, pessimo"
          "Produto excelente, superou expectativas"
          "Ainda nao recebi meu pedido"
```

```json
{
  "generators": [
    {
      "table": "customers",
      "row": {
        "customer_id": { "_gen": "uuid" },
        "name": { "_gen": "string", "expr": "#{Name.fullName}" },
        "email": { "_gen": "string", "expr": "#{Internet.emailAddress}" },
        "state": { "_gen": "oneOf", "choices": ["SP", "RJ", "MG", "RS", "PR", "SC"] },
        "segment": { "_gen": "oneOf", "choices": ["premium", "standard", "basic"] }
      }
    },
    {
      "table": "orders",
      "row": {
        "order_id": { "_gen": "uuid" },
        "customer_id": { "_gen": "lookup", "topic": "customers", "path": ["row", "customer_id"] },
        "total": { "_gen": "uniformDistribution", "min": 29.90, "max": 899.90 },
        "status": { "_gen": "oneOf", "choices": ["delivered", "shipped", "cancelled"] },
        "payment": { "_gen": "oneOf", "choices": ["pix", "credit_card", "boleto"] }
      }
    }
  ],
  "connections": {
    "pg": {
      "kind": "postgres",
      "connectionConfigs": { "host": "postgres", "port": 5432, "db": "shopagent" }
    },
    "fs": { "kind": "fileSystem" }
  }
}
```

#### Bloco 5: Pydantic & Structured Outputs (22h10 - 22h45)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 22h10 | Pydantic | Claude Code gera modelos a partir dos dados |
| 22h20 | Validacao | JSON bruto -> modelo tipado -> erro se invalido |
| 22h30 | Structured Outputs | Claude retornando JSON tipado, nao texto livre |
| 22h40 | Provocacao RAG | "E se fossem 50.000 reviews? E buscar por significado?" |

```python
from pydantic import BaseModel, Field
from typing import Literal

class Order(BaseModel):
    order_id: str
    customer_id: str
    total: float = Field(ge=0)
    status: Literal['delivered', 'shipped', 'cancelled']
    payment: Literal['pix', 'credit_card', 'boleto']

order = Order(**raw_json)  # Validado!
```

> **Provocacao final:** "Legal, o Claude analisou 10 reviews. Mas e se fossem 50.000?
> E se eu perguntasse 'quem reclama de entrega?' -- o Claude nao tem acesso aos dados.
> Amanha vamos resolver isso."

#### Bloco 6: Encerramento (22h45 - 23h00)

- Recap: "Voces tem dados reais fluindo e entendem pra onde o mercado vai"
- Desafio: gerar 10.000 orders e explorar com Claude Code
- Preview Dia 2: "Amanha a IA vai pesquisar nos SEUS dados"

**Entrega do Dia:**
- [x] Docker rodando (ShadowTraffic + Postgres + Qdrant)
- [x] Dados exatos no Postgres + reviews em JSONL
- [x] Pydantic validando + Structured Outputs
- [x] Entendimento de Agentic Commerce e o projeto ShopAgent

---

# DIA 2 -- Terca-feira (14/Abr)

## CONTEXTUALIZAR: Prompt Eng -> Context Eng -> RAG + Ledger

> *De "a IA inventa" para "a IA pesquisa nos MEUS dados e responde certo"*

### Topicos do Dia

1. **Prompt Engineering** -- o basico, e por que nao basta
2. **Context Engineering** -- a evolucao (Karpathy, 2026)
3. **RAG vs Ledger** -- dois tipos de dado, dois stores
4. **Ledger (Postgres)** -- dados exatos via SQL
5. **RAG (Qdrant)** -- busca semantica em reviews
6. **LlamaIndex** -- framework de ingestao e query
7. **MCP** -- conectar ambos os stores
8. **Claude Code pesquisa** -- demo fim a fim

### A Progressao do Dia

```
PROMPT ENGINEERING          "Pergunto direto pro Claude"
        |                    -> inventa quando nao sabe
        v
CONTEXT ENGINEERING         "Dou contexto: schema, exemplos, restricoes"
        |                    -> melhor, mas nao tem dados frescos
        v
RAG vs LEDGER               "Dois tipos de dado, dois stores"
        |                    Texto -> Qdrant | Numeros -> Postgres
        v
MCP CONECTA TUDO            "Claude Code pesquisa nos dois"
                             -> demo fim a fim
```

### Agenda Detalhada

#### Bloco 1: Prompt Engineering -> Context Engineering (20h00 - 20h40)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h00 | Prompt Engineering | Pergunta direto pro Claude -- funciona? |
| 20h08 | Demo: falha | "Qual meu faturamento de marco?" -> Claude inventa |
| 20h12 | Context Engineering | A evolucao: contexto > prompt (Karpathy, 2026) |
| 20h20 | Os 4 pilares | System Prompt + Schema + Few-Shot + Restricoes |
| 20h30 | Demo: melhora | Com contexto, Claude gera SQL correto (mas nao executa) |
| 20h38 | O problema | "Melhor, mas os dados mudam todo dia. Preciso de dados FRESCOS." |

```python
# SEM contexto -- Claude inventa
"Qual faturamento do meu e-commerce em marco?"
# -> "Desculpe, nao tenho acesso aos seus dados..."

# COM contexto -- Claude entende o schema
system = """Schema: customers (state, segment), orders (total, status, payment)
Exemplo: "Pedidos por pix?" -> SELECT COUNT(*) FROM orders WHERE payment='pix'"""
# -> "SELECT c.state, SUM(o.total) FROM orders o JOIN customers c..."
# Mas GERA a query, nao EXECUTA.
```

#### Bloco 2: RAG vs Ledger -- Conceito (20h40 - 21h00)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h40 | O problema dos 2 tipos | Dados exatos vs dados texto |
| 20h48 | The Ledger | Postgres: "Faturamento de SP?" -> SELECT SUM(total) -> R$ 127.430 |
| 20h54 | The Memory | Qdrant: "Quem reclama de entrega?" -> busca semantica |

> **Conceito Core:** Um agente inteligente precisa de **duas pernas**:
> uma para fatos exatos (SQL) e outra para significado (vetores).

| Pergunta | Store | Por que? |
|----------|-------|----------|
| "Faturamento de SP?" | Ledger (SQL) | Numero exato: `SELECT SUM(total)` |
| "Quem reclama de entrega?" | Memory (RAG) | "demorou" = "nao chegou" = "15 dias" |
| "Ticket medio dos insatisfeitos?" | Ambos | Qdrant acha -> Postgres calcula |

#### Bloco 3: Ledger -- Postgres + MCP Supabase (21h00 - 21h30)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h00 | Os dados ja estao la | ShadowTraffic do Dia 1 populou o Postgres |
| 21h05 | MCP Supabase | Conectar MCP oficial ao Postgres local |
| 21h15 | Demo | Claude Code: "Faturamento por estado?" -> SQL via MCP -> resultado |
| 21h25 | Exercicio | Perguntas que so SQL resolve (agregacoes, JOINs) |

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "http://localhost:54321/mcp"
    }
  }
}
```

```
Claude Code > "Qual faturamento total por estado?"
  [MCP Supabase] -> execute_sql ->
  
  state | pedidos | faturamento
  SP    |   1.230 |   127.430,50
  RJ    |     890 |    89.210,30
  MG    |     720 |    68.440,10
```

#### Bloco 4: RAG -- LlamaIndex + Qdrant + MCP (21h30 - 22h15)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h30 | O que e RAG? | Buscar nos dados antes de responder |
| 21h38 | LlamaIndex | SimpleDirectoryReader carrega reviews JSONL do Dia 1 |
| 21h48 | Embeddings -> Qdrant | Chunks -> embeddings -> Qdrant (Docker local) |
| 22h00 | MCP Qdrant | Conectar MCP oficial ao Qdrant |
| 22h08 | Demo semantica | "Clientes reclamando de entrega?" -> 23 reviews |

```python
import qdrant_client
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
client = qdrant_client.QdrantClient(url="http://localhost:6333")
vector_store = QdrantVectorStore(client=client, collection_name="reviews")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Reviews JSONL do Dia 1 -> embeddings -> Qdrant
documents = SimpleDirectoryReader("./data/reviews/").load_data()
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

query_engine = index.as_query_engine()
response = query_engine.query("Clientes reclamando de entrega")
# -> "Encontrei 23 reviews: 'demorou 15 dias', 'nao recebi', 'frete caro'..."
```

#### Bloco 5: Claude Code Pesquisa nos Dois (22h15 - 22h45)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 22h15 | As duas pernas juntas | Claude Code com MCP Supabase + MCP Qdrant |
| 22h25 | Demo fim a fim | Perguntas hibridas ao vivo |
| 22h35 | Exploracao | Participantes sugerem perguntas, Claude Code responde |

```
Claude Code > "Quais clientes do Sudeste reclamam de entrega?"
  [MCP Qdrant] -> busca semantica -> 23 reviews

Claude Code > "Qual o ticket medio desses clientes?"
  [MCP Supabase] -> SELECT AVG(total) -> R$ 347,82

Claude Code > "Resumo executivo"
  -> "23 clientes do Sudeste com problemas de entrega.
      Ticket medio: R$ 347,82 (75% acima da media).
      Temas: atraso (15), extravio (5), custo frete (3)."
```

> **A limitacao:** "Viram que EU decidi quando usar Qdrant e quando usar Supabase?
> E se o agente decidisse sozinho? Amanha."

#### Bloco 6: Encerramento (22h45 - 23h00)

- Recap: "A IA agora pesquisa nos SEUS dados -- numeros exatos E significado"
- Desafio: criar 5 perguntas hibridas e testar
- Preview Dia 3: "Amanha o agente decide sozinho. E vamos entrar no modo Deus."

**Entrega do Dia:**
- [x] Prompt Eng -> Context Eng (evolucao entendida)
- [x] Postgres populado + MCP Supabase conectado (Ledger)
- [x] Qdrant indexado + MCP Qdrant conectado (Memory/RAG)
- [x] Claude Code pesquisando nos dois stores
- [x] LlamaIndex pipeline completo

---

# DIA 3 -- Quarta-feira (15/Abr)

## AGENTE: Spec-Driven Development + AgentSpec

> *De "eu decido" para "o agente decide" -- e o AgentSpec projeta tudo*

### Topicos do Dia

1. **Conceito de Agentes e Workflows** -- o que e um agente, como funciona
2. **Design Patterns** -- ReAct, Tool Use, routing, chain-of-thought
3. **Spec-Driven Development & AgentSpec** -- modo Deus ativado
4. **LangChain + Chainlit** -- agente autonomo com interface conversacional

### O Salto do Dia 3

```
Dias 1-2: Usamos Claude Code no modo "normal"
          Plan Mode, perguntas diretas, codigo passo a passo
          
Dia 3:    MODO DEUS
          AgentSpec ativa 58 agentes especializados
          /brainstorm -> /define -> /design -> /build
          "A IA projeta, eu valido"
```

### Agenda Detalhada

#### Bloco 1: Conceito de Agentes e Workflows (20h00 - 20h30)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h00 | O que e um Agent? | Diferenca: tool vs agent vs workflow |
| 20h10 | Autonomia | "No Dia 2 VOCES decidiram. Hoje o AGENTE decide." |
| 20h18 | Componentes | Perception -> Reasoning -> Action -> Memory |
| 20h25 | Tipos de workflow | Sequential, parallel, hierarchical, consensus |

```
TOOL:      Eu chamo, ele executa         (chave de fenda)
AGENT:     Eu pergunto, ele decide como   (robo com ferramentas)
WORKFLOW:  Eu defino o fluxo, agentes executam (fabrica de robos)
```

#### Bloco 2: Design Patterns de Agentes (20h30 - 21h00)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h30 | ReAct Pattern | Reason + Act -- o padrao fundamental |
| 20h38 | Tool Use | Agent escolhe qual ferramenta usar (Ledger vs Memory) |
| 20h45 | Routing | Como o agente decide: "isso e SQL" vs "isso e semantica" |
| 20h52 | Chain-of-Thought | Pensamento passo a passo visivel |

```
Pergunta: "Clientes premium do Sudeste que reclamam de entrega: ticket medio?"

Agent (ReAct):
  Thought: "Preciso encontrar quem reclama (semantico) e calcular ticket (SQL)"
  Action:  Qdrant -> busca "reclamacao entrega" -> 23 reviews
  Thought: "Agora preciso filtrar por Sudeste e calcular media"
  Action:  Supabase -> SELECT AVG(total) WHERE state IN ('SP','RJ','MG','ES')
  Answer:  "R$ 347,82 baseado em 23 reviews negativos"
```

#### Bloco 3: Spec-Driven Development & AgentSpec (21h00 - 22h00)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h00 | O problema | "Ate agora: Plan Mode, codigo manual, passo a passo" |
| 21h05 | Spec-Driven Dev | O conceito: especificacao primeiro, codigo depois |
| 21h12 | AgentSpec | O plugin: 58 agentes, 22 dominios, 29 comandos |
| 21h20 | /brainstorm | Ao vivo: AgentSpec explora o ShopAgent |
| 21h30 | /define | Captura requisitos estruturados (clarity score) |
| 21h40 | /design | Gera arquitetura, file manifest, pipeline design |
| 21h50 | /build | AgentSpec delega para agentes especialistas |

**O momento "modo Deus":**
```bash
# Ate agora (Dias 1-2): Plan Mode, manual
Claude Code > "Cria um agente que consulta Supabase e Qdrant"
# -> Claude gera codigo passo a passo, voce vai ajustando

# Agora (Dia 3): AgentSpec
/agentspec:brainstorm "ShopAgent: agente e-commerce com Qdrant + Supabase via MCP"

  [58 agentes especializados ativados]
  [3+ perguntas geradas, 2+ abordagens propostas]
  [Confidence score em cada decisao]

/agentspec:define SHOPAGENT

  [Requisitos estruturados capturados]
  [Clarity score: 14/15]
  [Quality gate: aprovado para design]

/agentspec:design SHOPAGENT

  [File manifest completo gerado]
  [Pipeline architecture definida]
  [Delegation map: quais agentes vao construir o que]

/agentspec:build SHOPAGENT

  [Agentes especialistas delegados automaticamente]
  [Codigo gerado com testes]
  [Build report com resultados]
```

> **AgentSpec:** 58 agentes especializados | 22 dominios de conhecimento | 29 comandos
> Workflow: Brainstorm -> Define -> Design -> Build -> Ship
> Cada fase tem quality gates -- so avanca se passar.
> github.com/luanmorenommaciel/agentspec

#### Bloco 4: LangChain + Chainlit (22h00 - 22h40)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 22h00 | LangChain Agent | Agente com Tool Use (Supabase + Qdrant) |
| 22h12 | Demo | Agent decide sozinho: "isso e SQL" vs "isso e semantica" |
| 22h20 | Chainlit | Interface conversacional para o agente |
| 22h30 | Demo | Chat bonito com o agente pensando ao vivo |

```python
# LangChain Agent com 2 tools
from langchain.agents import create_react_agent
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514")
agent = create_react_agent(llm, tools=[supabase_tool, qdrant_tool])

# O agente DECIDE sozinho qual tool usar
agent.invoke({"input": "Quem reclama de entrega?"})
# -> Thought: "busca semantica" -> Action: qdrant_tool -> Resposta

agent.invoke({"input": "Faturamento de SP?"})
# -> Thought: "numero exato" -> Action: supabase_tool -> Resposta
```

```python
# Chainlit conecta o agente ao chat
import chainlit as cl

@cl.on_message
async def on_message(message: cl.Message):
    response = agent.invoke({"input": message.content})
    await cl.Message(content=response["output"]).send()
```

#### Bloco 5: Encerramento (22h40 - 23h00)

- Recap: "Voces viram o agente decidir sozinho E o AgentSpec projetar tudo"
- Preview Dia 4: "Amanha: um TIME de agentes, frontend profissional, cloud, e o grand finale"

**Entrega do Dia:**
- [x] Conceito de agentes e design patterns dominado
- [x] AgentSpec: brainstorm -> define -> design -> build
- [x] LangChain agent decidindo autonomamente qual store usar
- [x] Chainlit com interface conversacional funcionando

---

# DIA 4 -- Quinta-feira (16/Abr)

## MULTI-AGENT: CrewAI + Frontend + Cloud + Grand Finale

> *De "um agente" para "um time de agentes com frontend profissional em cloud"*

### Topicos do Dia

1. **Conceito de Multi-Agent e Agentic** -- por que especializar
2. **Design Patterns Multi-Agent** -- sequential, hierarchical, delegation
3. **AgentSpec construindo tudo** -- /build + /ship do sistema completo
4. **CrewAI + Chainlit** -- 3 agentes + interface conversacional
5. **DeepEval** -- avaliar qualidade das respostas
6. **LangFuse** -- observabilidade completa
7. **Frontend E-Commerce** -- a pagina que vai matar todo mundo

### Os 3 Agentes do ShopAgent

```
                    +------------------+
                    |  ReporterAgent   |  Combina resultados
                    |  Goal: Relatorio |  e gera resposta
                    |  executivo       |  final acionavel
                    +--------+---------+
                             |
                    recebe contexto de ambos
                             |
              +--------------+--------------+
              |                             |
    +---------+--------+          +---------+--------+
    |  AnalystAgent    |          |  ResearchAgent   |
    |  Role: SQL       |          |  Role: Semantica |
    |  Tool: Supabase  |          |  Tool: Qdrant    |
    |  (The Ledger)    |          |  (The Memory)    |
    +------------------+          +------------------+
```

### Agenda Detalhada

#### Bloco 1: Multi-Agent Conceito + Design Patterns (20h00 - 20h25)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h00 | Por que multi-agent? | 1 agente quebra em tarefas complexas |
| 20h08 | Especializacao | Analista + Pesquisador + Reporter |
| 20h15 | Design Patterns | Sequential, hierarchical, delegation, consensus |
| 20h22 | Agentic Commerce | "Na pratica, um time de agentes de e-commerce" |

```
1 AGENTE:        "Faz um relatorio completo de satisfacao"
                  -> tenta tudo, resposta confusa e incompleta

3 AGENTES:       Mesma pergunta:
  AnalystAgent   -> metricas por regiao (LIMPO, EXATO)
  ResearchAgent  -> temas de reclamacao (PROFUNDO, SEMANTICO)
  ReporterAgent  -> relatorio executivo (ACIONAVEL)
```

#### Bloco 2: AgentSpec Constroi Tudo (20h25 - 21h10)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 20h25 | /agentspec:build SHOPAGENT | AgentSpec gera o codigo CrewAI completo |
| 20h40 | O que foi gerado | agents.yaml, tasks.yaml, crew.py, tools |
| 20h50 | /agentspec:ship SHOPAGENT | Archiva com lessons learned |
| 21h05 | Resultado | Sistema multi-agent completo, gerado por IA |

```bash
/agentspec:build SHOPAGENT

  [pipeline-architect] -> Gerando crew.py com 3 agentes
  [data-engineer]      -> Configurando tools MCP (Supabase + Qdrant)
  [python-specialist]  -> Gerando agents.yaml + tasks.yaml
  [test-engineer]      -> Testes automatizados
  
  Build Report:
  - 6 arquivos gerados
  - 3 agentes configurados
  - 2 tools MCP conectados
  - Testes: 12/12 passed
  - Confidence: 0.94

/agentspec:ship SHOPAGENT

  [Archivando projeto completo]
  [Lessons learned documentadas]
  [Ready for production]
```

#### Bloco 3: CrewAI + Chainlit (21h10 - 21h50)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h10 | CrewAI rodando | 3 agentes executando com o codigo do AgentSpec |
| 21h25 | Demo | Pergunta complexa -> AnalystAgent + ResearchAgent + ReporterAgent |
| 21h35 | Chainlit | Interface conversacional mostrando cada agente trabalhando |
| 21h45 | Cloud Migration | Docker -> Supabase Cloud + Qdrant Cloud (so muda URL) |

```python
# Gerado pelo AgentSpec
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class ShopAgentCrew:
    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'], tools=[supabase_tool])

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], tools=[qdrant_tool])

    @agent
    def reporter(self) -> Agent:
        return Agent(config=self.agents_config['reporter'])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential)
```

```python
# Cloud: so muda a URL
# Docker local (Dias 1-3)
SUPABASE_URL = "http://localhost:54321"
QDRANT_URL = "http://localhost:6333"

# Cloud (Dia 4) -- mesma arquitetura!
SUPABASE_URL = "https://xxxxx.supabase.co"
QDRANT_URL = "https://xxxxx.cloud.qdrant.io:6333"
```

#### Bloco 4: DeepEval + LangFuse (21h50 - 22h15)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 21h50 | DeepEval | O agente esta chamando a ferramenta certa? |
| 22h00 | Metricas | ToolCorrectness + AnswerRelevancy |
| 22h08 | LangFuse | Traces de cada agente, custo, latencia |

```python
# DeepEval: o agente decidiu certo?
test = LLMTestCase(
    input="Qual faturamento de SP?",
    expected_tools=["supabase_execute_sql"],
    actual_tools=["supabase_execute_sql"]
)
# PASSED

# LangFuse: trace completo
# AnalystAgent: 2.3s, 1 tool call, 340 tokens
# ResearchAgent: 1.8s, 1 tool call, 280 tokens
# ReporterAgent: 3.1s, 0 tool calls, 520 tokens
# Total: 7.2s, 1140 tokens, $0.003
```

#### Bloco 5: Frontend E-Commerce -- O Golpe Final (22h15 - 22h35)

| Horario | Atividade | Detalhes |
|---------|-----------|---------|
| 22h15 | O setup | Impeccable + UI/UX Pro Max Skill no Claude Code |
| 22h20 | Geracao ao vivo | Claude Code gera pagina e-commerce do ShopAgent |
| 22h28 | O resultado | Pagina profissional com design system completo |

> **Esse e o momento que mata todo mundo.**
>
> Ate agora: backend, dados, agentes, terminal.
> Agora: Claude Code gera um **frontend lindo de e-commerce** em minutos.

**As ferramentas:**

- **Impeccable** (18.5k stars) -- Design skill para Claude Code com 7 dominios
  (tipografia, cores OKLCH, spatial design, motion, interacao, responsivo, UX writing)
  e 18 comandos (/audit, /polish, /animate, /colorize...)

- **UI/UX Pro Max Skill** -- 67 estilos UI, 161 paletas de cores, 57 font pairings,
  161 regras por industria. Inclui design system completo para e-commerce.

```bash
# Instalar as skills
# Impeccable
cp -r impeccable/.claude your-project/

# UI/UX Pro Max
uipro init --ai claude

# Gerar a pagina do ShopAgent
Claude Code > "Cria uma pagina de e-commerce para o ShopAgent.
               Dashboard com metricas de vendas, reviews de clientes,
               e chat com o agente integrado. Stack: HTML + Tailwind."

  [UI/UX Pro Max] -> Design system gerado:
    PATTERN: Dashboard + Conversational
    STYLE: Modern Minimal
    COLORS: E-commerce optimized palette
    TYPOGRAPHY: Inter / JetBrains Mono

  [Impeccable] -> Refinamento:
    /colorize -> Paleta sofisticada com tinted neutrals
    /typeset  -> Hierarquia tipografica correta
    /animate  -> Micro-interacoes no chat e graficos
    /polish   -> Toques finais profissionais

# Resultado: pagina de e-commerce profissional
# com dashboard + chat do ShopAgent integrado
```

> **O impacto:** O participante ve o sistema inteiro -- dados, agentes, backend, frontend --
> tudo gerado com IA. De zero a produto em 4 fases. "Isso e real?"

#### Bloco 6: Grand Finale + Pitch (22h35 - 23h00)

**22h35 - 22h45: Demo Final Completa**

O ShopAgent rodando end-to-end:
1. Frontend lindo de e-commerce
2. Chat integrado com Chainlit
3. Multi-agent CrewAI processando
4. Dados reais do Supabase Cloud + Qdrant Cloud
5. Traces no LangFuse
6. Tudo gerado com AgentSpec + Impeccable + UI/UX Pro Max

**22h45 - 22h50: Recapitulacao da Semana**

| Dia | O que construimos |
|-----|-------------------|
| 1 | Dados reais + Agentic Commerce + Claude Code |
| 2 | IA pesquisando nos dados (RAG + Ledger + MCP) |
| 3 | Agente autonomo + AgentSpec modo Deus |
| 4 | Multi-agent + Frontend profissional + Cloud |

> *"Em 4 fases voces construiram um sistema de Agentic Commerce completo.
> Com dados reais, agentes inteligentes, interface profissional, e tudo em cloud.
> Voces provaram que conseguem. A Formacao e onde voces dominam."*

**22h50 - 23h00: Pitch -- Formacao AI Data Engineer**

- "Voces viram o que e possivel em 4 fases. Imaginem 70 horas."
- 4 Camadas: MindSet, Foundation, Workshops, Bootcamps
- 16 modulos + 6 workshops + 4 bootcamps hands-on
- AgentSpec completo: 58 agentes, 22 dominios, 29 comandos
- **Membros Fundadores: R$ 2.997** (vs R$ 3.997 -- desconto de R$ 1.000)
- Bonus exclusivo para inscritos durante a Semana

**23h00: Q&A + Fechamento**

**Entrega do Dia:**
- [x] Multi-agent CrewAI com 3 agentes especializados
- [x] AgentSpec /build + /ship completo
- [x] DeepEval avaliando qualidade
- [x] LangFuse com traces de observabilidade
- [x] Cloud: Supabase + Qdrant Cloud
- [x] Frontend profissional de e-commerce (Impeccable + UI/UX Pro Max)
- [x] Sistema completo end-to-end: de dados a produto

---

# DIA 5 -- Sexta-feira (17/Abr)

## REFLETIR: Podcast -- O Futuro do AI Data Engineer

> *Conversa aberta sobre carreira, mercado e o que vem pela frente*

**Formato:** Podcast ao vivo (1-2h) com convidados. Tom descontraido e inspirador.

### Temas

1. Agentic Commerce -- o que muda no e-commerce com agentes?
2. O que muda na carreira de Data Engineer com IA?
3. Context Engineering vs Prompt Engineering -- a evolucao real
4. Spec-Driven Development -- o futuro do desenvolvimento com IA
5. MCP como padrao: The Ledger + The Memory -- para onde vai?
6. Multi-Agent Systems: hype ou realidade?
7. AI Coding Agents: proximos 12 meses
8. Retrospectiva: o que os participantes construiram na Semana
9. Ultimo lembrete sobre a Formacao (natural, sem pressao)

**Entrega:** Inspiracao + clareza sobre o caminho + comunidade

---

## Modelo de Dados E-Commerce

### Entidades do ShopAgent (todas geradas por ShadowTraffic)

```
+-------------+       +-------------+
|  customers  |       |  products   |
|-------------|       |-------------|
| customer_id |<--+   | product_id  |<--+
| name        |   |   | name        |   |
| email       |   |   | category    |   |
| city        |   |   | price       |   |
| state       |   |   | brand       |   |
| segment     |   |   +-------------+   |
+-------------+   |     ShadowTraffic   |
  ShadowTraffic   |       -> Postgres   |
    -> Postgres   |                     |
                  |                     |
            +-----+-----+        +-----+-----+
            |   orders   |        |  reviews   |
            |------------|        |------------|
            | order_id   |        | review_id  |
            | customer_id|        | order_id   |
            | product_id |        | rating     |
            | qty        |        | comment    |
            | total      |        | sentiment  |
            | status     |        +------------+
            | payment    |     ShadowTraffic
            +------------+       -> JSONL
          ShadowTraffic          -> Qdrant (Dia 2)
            -> Postgres
```

---

## Progressao de Stack por Dia

| Dia | Stack Nova | Stack Acumulada |
|-----|-----------|-----------------|
| 1 | ShadowTraffic, Pydantic, Claude Code, Docker | ShadowTraffic, Pydantic, Claude Code, Docker |
| 2 | LlamaIndex, Qdrant, Postgres, MCP, Context Eng | + LlamaIndex, Qdrant, MCP |
| 3 | AgentSpec, LangChain, Chainlit, Design Patterns | + AgentSpec, LangChain, Chainlit |
| 4 | CrewAI, DeepEval, LangFuse, Impeccable, UI/UX Pro Max, Cloud | Tudo: sistema completo |

---

## Conexao Semana <-> Formacao

| Dia | Semana (Intro -- 20%) | Formacao (Dominio -- 100%) |
|-----|----------------------|---------------------------|
| 1 | ShadowTraffic + Pydantic + Claude Code | Foundation: 16 modulos + 4 AI Coding Agents |
| 2 | Context Eng + RAG + Ledger + MCP | Workshops: RAG production-ready + MCP avancado |
| 3 | AgentSpec basico + LangChain + Chainlit | Workshops: AgentSpec completo (58 agentes, 22 dominios) |
| 4 | CrewAI + DeepEval + LangFuse + Frontend | Bootcamps: Multi-Agent + LLMOps + Deploy prod |

> *"Em 4 fases voces construiram o ShopAgent. Em 70 horas voces dominam."*

---

## Metricas de Sucesso

| Metrica | Meta | Como Medir |
|---------|------|------------|
| Audiencia Dia 1 | 1.000+ ao vivo | Plataforma de live |
| Retencao Dia 1->4 | > 40% | Audiencia Dia 4 / Dia 1 |
| Engajamento Chat | > 300 msgs/noite | Chat da live |
| ShopAgent Completo | > 30% constroem | Formulario pos-evento |
| Conversao Formacao | > 5% audiencia | Vendas durante/apos |

---

## Timeline de Preparacao

| Quando | Acao |
|--------|------|
| 4 sem antes (16/Mar) | docker-compose.yml + configs ShadowTraffic + repo ShopAgent + AgentSpec testado |
| 3 sem antes (23/Mar) | Dry run Dia 1-2 + LlamaIndex pipeline + MCP Supabase/Qdrant |
| 2 sem antes (30/Mar) | Dry run Dia 3-4 + AgentSpec flow + CrewAI + Impeccable + pitch pronto |
| 1 sem antes (06/Abr) | Divulgacao + teste end-to-end + convidados podcast + Cloud setup |
| Semana evento (13/Abr) | Executar! + metricas + ajustar pitch baseado no engajamento |

---

## Docker Compose (Dias 1-3)

```yaml
services:
  shadowtraffic:
    image: shadowtraffic/shadowtraffic:latest
    env_file: license.env
    volumes:
      - ./config:/home/config
      - ./data:/tmp/data

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: shopagent
      POSTGRES_USER: shopagent
      POSTGRES_PASSWORD: shopagent
    ports:
      - "5432:5432"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

---

*AIDE Brasil | Formacao AI Data Engineer 2026 | Luan Moreno*
