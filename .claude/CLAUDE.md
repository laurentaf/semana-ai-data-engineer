# ShopAgent — Semana AI Data Engineer 2026

## Project Overview

Multi-agent e-commerce AI system built across 4 live phases (April 13-16, 2026) + 1 podcast.
Participants go from zero to a working ShopAgent: autonomous agents that query structured data (SQL)
and semantic data (vectors), with a conversational interface and professional frontend.

**Central Question:** *O que eu consigo fazer agora que nao conseguia antes?*

**Docker-First:** Days 1-3 run 100% local. Day 4 migrates to cloud — same architecture, different endpoint.

## Architecture: The Ledger + The Memory

```
+------------------+ +------------------+ +------------------+
| DATA GENERATION  | | AI / LLM         | | INTERFACE        |
| ShadowTraffic    | | NVIDIA NIM       | | Chainlit         |
+--------+---------+ | FastEmbed        +--------+---------+
         |           | CrewAI           |
         v           | LangChain        v
+------------------+ +--------+---------+ +------------------+
| STORAGE          | |        | QUALITY  |
| Postgres         | v        | DeepEval |
| (The Ledger)     +------------------+  | LangFuse |
| Qdrant           |<--->| MCP Protocol  | +------------------+
| (The Memory)     |     +------------------+
+------------------+
```

**The Ledger (Supabase/Postgres):** Exact data — revenue, counts, averages, JOINs
**The Memory (Qdrant):** Meaning — complaints, sentiment, review themes via RAG

### LLM Strategy

| Component | LLM | Why |
|-----------|-----|-----|
| CrewAI Agents | NVIDIA NIM (nemotron-mini-4b) | Free, fast, OpenAI-compatible |
| Query Router | NVIDIA NIM (nemotron-mini-4b) | ~0.3s routing, 100% accuracy |
| Embeddings | FastEmbed (BAAI/bge-base-en-v1.5) | Local, no API key, no LlamaIndex dependency |

## 3-Agent Crew (Day 4)

| Agent | Role | Tool | Store |
|-------|------|------|-------|
| AnalystAgent | SQL data analyst | supabase_execute_sql | The Ledger |
| ResearchAgent | Customer experience researcher | qdrant_semantic_search | The Memory |
| ReporterAgent | Executive report writer | (synthesis only) | Both via context |

## Stack by Day

| Day | Theme | New Stack |
|-----|-------|-----------|
| 1 Mon | INGERIR | ShadowTraffic, Pydantic, Claude Code, Docker |
| 2 Tue | CONTEXTUALIZAR | FastEmbed, Qdrant, Postgres, MCP |
| 3 Wed | AGENTE | LangChain, Chainlit, AgentSpec |
| 4 Thu | MULTI-AGENT | CrewAI, NVIDIA NIM, DeepEval, LangFuse, Cloud |

## Cloud Infrastructure (Day 4)

| Service | Local | Cloud |
|---------|-------|-------|
| Postgres | Docker (localhost:5432) | Supabase (REST API + RPC fallback) |
| Qdrant | Docker (localhost:6333) | Qdrant Cloud (HTTPS) |
| LLM | NVIDIA NIM API | Same (works everywhere) |
| Observability | - | LangFuse Cloud |

### IPv6 Workaround

Supabase direct DB connections (`db.*.supabase.co`) are IPv6-only. ShopAgent handles this:
1. **Primary:** Direct `psycopg2` connection to `SUPABASE_DB_URL`
2. **Fallback:** Supabase REST API with `exec_shopagent_query` RPC function

The RPC function is created via the SQL Editor (see `src/migrate_to_cloud.py --create-tables`).

## Directory Structure

```
.env.example              # Root env template (canonical — all keys here)
.venv/                    # Project virtual environment
gen/                      # Data generation (ShadowTraffic + Docker)
  docker-compose.yml      # Postgres + Qdrant + ShadowTraffic (reads ../.env)
  shadowtraffic.json      # E-commerce data generators
  init.sql                # Postgres schema (customers, products, orders)
  data/reviews/reviews.jsonl  # Pre-generated Portuguese reviews for RAG
  license.env.example     # ShadowTraffic license template
docs/                     # Event documentation
  agenda.md               # 900-line detailed agenda with code examples
  semana-ai-data-engineer-shop-agent.md  # Full curriculum spec
prompts/                  # Sequenced live-coding prompts per day
  d1-ingest/              # Day 1: ShadowTraffic + Pydantic (11 prompts)
  d2-context/             # Day 2: RAG + Ledger + MCP (11 prompts)
  d3-agent/               # Day 3: LangChain + Chainlit
  d4-multi-agent/         # Day 4: CrewAI + DeepEval + Frontend
src/                      # Python source + requirements per day
  requirements.txt        # Master requirements (all days)
  day1/                   # models.py, test_models.py, structured_outputs.py
  day2/                   # ledger_queries.py, ingest_reviews.py, query_reviews.py
  day3/                   # LangChain agent, tools (FastEmbed + Qdrant client)
  day4/                   # CrewAI crew, tools, Chainlit app, Supabase migration
  migrate_to_cloud.py     # Full cloud migration (REST API based)
  nim_benchmark.py        # NVIDIA NIM performance benchmarks
presentation/             # HTML slide decks (Days 1-4)
.claude/
  kb/                     # 18 Knowledge Base domains
  agents/                 # SubAgents (ai-ml/, code-quality/, communication/, domain/, exploration/)
  commands/               # Custom Claude Code commands
```

## Knowledge Base Domains (18)

| Domain | Path | Purpose | Day |
|--------|------|---------|-----|
| shadowtraffic | kb/shadowtraffic/ | Synthetic data generation | 1 |
| pydantic | kb/pydantic/ | Data validation + structured outputs | 1 |
| python | kb/python/ | Clean code patterns | 1-4 |
| qdrant | kb/qdrant/ | Vector DB (The Memory) | 2-4 |
| supabase | kb/supabase/ | Postgres (The Ledger) | 2-4 |
| prompt-engineering | kb/prompt-engineering/ | Prompting techniques | 2 |
| langchain | kb/langchain/ | Agent framework + tool routing | 3 |
| chainlit | kb/chainlit/ | Chat interface + streaming | 3-4 |
| genai | kb/genai/ | GenAI architecture patterns | 3-4 |
| crewai | kb/crewai/ | Multi-agent orchestration | 4 |
| deepeval | kb/deeval/ | LLM evaluation + testing | 4 |
| langfuse | kb/langfuse/ | LLMOps observability | 4 |
| testing | kb/testing/ | pytest patterns | 3-4 |
| architecture | kb/architecture/ | System design | 1-4 |
| exploration | kb/exploration/ | Codebase analysis | 1-4 |
| communication | kb/communication/ | Stakeholder communication | 1-4 |
| aide-slides | kb/aide-slides/ | Slide deck design system | 1-4 |
| fastembed | kb/fastembed/ | Local embedding models | 2-4 |

## SubAgents

| Agent | Category | Domain |
|-------|----------|--------|
| genai-architect | ai-ml/ | Multi-agent architecture design |
| ai-data-engineer | ai-ml/ | Pipeline + cloud optimization |
| ai-prompt-specialist | ai-ml/ | Prompt engineering |
| llm-specialist | ai-ml/ | LLM selection + optimization |
| code-reviewer | code-quality/ | Code review specialist |
| code-cleaner | code-quality/ | Python code cleaning |
| code-documenter | code-quality/ | Documentation specialist |
| python-developer | code-quality/ | Python code architect |
| shell-script-specialist | code-quality/ | Shell scripting |
| the-planner | communication/ | Project planning |
| meeting-analyst | communication/ | Meeting notes extraction |
| shopagent-builder | domain/ | ShopAgent components by day |
| aide-slide-builder | domain/ | Slide deck builder |
| aide-slide-reviewer | domain/ | Slide deck reviewer |
| aide-slide-fixer | domain/ | Slide deck fixer |
| aide-slide-planner | domain/ | Slide content planner |
| codebase-explorer | exploration/ | Code analysis + discovery |
| kb-architect | exploration/ | Knowledge base design |

## Data Model (4 Entities)

| Entity | Store | Fields |
|--------|-------|--------|
| customers | Postgres | customer_id, name, email, city, state, segment |
| products | Postgres | product_id, name, category, price, brand |
| orders | Postgres | order_id, customer_id (FK), product_id (FK), qty, total, status, payment, created_at |
| reviews | JSONL->Qdrant | review_id, order_id (FK), rating, comment, sentiment |

## Local Dev Quickstart

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r src/requirements.txt

cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY, NVIDIA_NIM_API_KEY
cd gen && cp license.env.example license.env
# Set your ShadowTraffic license fields in license.env
docker compose up
```

## Conventions

- Python 3.11+ with type hints
- KB files: concepts < 150 lines, patterns < 200 lines
- File naming: kebab-case
- MCP validation required before KB updates
- All code production-ready (real imports, error handling)
- Environment-based URLs (localhost for local, cloud URLs via env vars)
- FastEmbed for all embeddings (no LlamaIndex LLM dependency)
- NVIDIA NIM for all CrewAI agent LLMs (free, OpenAI-compatible)
