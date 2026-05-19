# ShopAgent -- Semana AI Data Engineer 2026

> Build a multi-agent AI system that queries structured and semantic e-commerce data -- live, in 4 nights.

## What is ShopAgent?

ShopAgent is an autonomous agent crew built on real e-commerce data. It answers business questions
by routing to the right data store: SQL for exact numbers, vectors for customer sentiment.
Days 1-3 run 100% locally with Docker. Day 4 migrates the same architecture to the cloud.

*Central question: O que eu consigo fazer agora que nao conseguia antes?*

## Architecture

```text
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

**The Ledger (Postgres):** Exact data -- revenue, counts, averages, JOINs

**The Memory (Qdrant):** Meaning -- complaints, sentiment, review themes via RAG

### LLM Strategy

| Component | LLM | Why |
|-----------|-----|-----|
| CrewAI Agents | NVIDIA NIM (nemotron-mini-4b) | Free, fast, OpenAI-compatible |
| Query Router | NVIDIA NIM (nemotron-mini-4b) | ~0.3s routing, 100% accuracy |
| Embeddings | FastEmbed (BAAI/bge-base-en-v1.5) | Local, no API key needed |

## Quickstart

### Prerequisites

- Docker, an Anthropic API key, and a ShadowTraffic license
  (free trial at <https://shadowtraffic.io>).
- Python 3.11+ with the project `.venv`:

```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r src/requirements.txt
```

### Local Mode (Days 1-3)

```bash
cd gen
cp .env.example .env
cp license.env.example license.env
# Set ANTHROPIC_API_KEY in .env
# Set your ShadowTraffic license fields in license.env
# Get a free trial at https://shadowtraffic.io
docker compose up
```

Services started: Postgres on 5432, Qdrant on 6333, ShadowTraffic (data generator).

### Cloud Mode (Day 4)

```bash
# 1. Set ENVIRONMENT=cloud in .env
# 2. Configure cloud credentials (see .env for all variables)
# 3. Create Supabase tables + RPC function:
#    Paste the SQL from src/migrate_to_cloud.py --create-tables
#    into Supabase Dashboard > SQL Editor
# 4. Migrate data:
python src/migrate_to_cloud.py
```

## Stack by Day

| Day | Theme | Stack |
|-----|-------|-------|
| 1 Mon | INGERIR | ShadowTraffic, Pydantic, Claude Code, Docker |
| 2 Tue | CONTEXTUALIZAR | FastEmbed, Qdrant, Postgres, MCP |
| 3 Wed | AGENTE | LangChain, Chainlit, AgentSpec |
| 4 Thu | MULTI-AGENT | CrewAI, NVIDIA NIM, DeepEval, LangFuse, Cloud |

## Data Model

| Entity | Store | Fields |
|--------|-------|--------|
| customers | Postgres | customer_id, name, email, city, state, segment |
| products | Postgres | product_id, name, category, price, brand |
| orders | Postgres | order_id, customer_id (FK), product_id (FK), qty, total, status, payment, created_at |
| reviews | JSONL -> Qdrant | review_id, order_id (FK), rating, comment, sentiment |

## 3-Agent Crew (Day 4)

| Agent | Role | Store | LLM |
|-------|------|-------|-----|
| AnalystAgent | SQL data analyst | The Ledger (Postgres) | NVIDIA NIM |
| ResearchAgent | Customer experience researcher | The Memory (Qdrant) | NVIDIA NIM |
| ReporterAgent | Executive report writer | Both via context | NVIDIA NIM |

## Cloud Infrastructure (Day 4)

| Service | Local | Cloud |
|---------|-------|-------|
| Postgres | Docker (localhost:5432) | Supabase (REST API + RPC) |
| Qdrant | Docker (localhost:6333) | Qdrant Cloud (HTTPS) |
| LLM | NVIDIA NIM API | Same (works everywhere) |
| Observability | - | LangFuse Cloud |

### IPv6 Workaround

Supabase direct DB connections (`db.*.supabase.co`) are IPv6-only, which may fail on
some networks. ShopAgent handles this transparently:

1. **Primary:** Try direct `psycopg2` connection to `SUPABASE_DB_URL`
2. **Fallback:** Use Supabase REST API with `exec_shopagent_query` RPC function

The RPC function is created via the SQL Editor (see migration script) and supports
all 10 predefined SQL queries. No code changes needed -- `tools.py` auto-fallbacks.

## Project Structure

```text
gen/                        # Docker infrastructure + data generation
  docker-compose.yml        # Postgres + Qdrant + ShadowTraffic
  shadowtraffic.json        # E-commerce data generators
  init.sql                  # Postgres schema
  .env.example              # Environment template
  license.env.example       # ShadowTraffic license template
  data/reviews/             # Pre-generated review data for RAG
src/                        # Python source code
  day1/                     # Day 1: ShadowTraffic + Pydantic
  day2/                     # Day 2: FastEmbed + Qdrant indexing
  day3/                     # Day 3: LangChain agent + Chainlit
  day4/                     # Day 4: CrewAI multi-agent + Cloud
    crew.py                 # 3-agent crew (Analyst, Researcher, Reporter)
    tools.py                # ENVIRONMENT-aware tool wrappers
    chainlit_app.py         # Chat interface
    setup_supabase.py       # Cloud migration via REST API
    eval_agent.py           # DeepEval evaluation
  migrate_to_cloud.py       # Full migration script (Postgres + Qdrant)
  nim_benchmark.py          # NVIDIA NIM performance benchmarks
  requirements.txt          # All Python dependencies
.venv/                      # Project virtual environment
docs/                       # Curriculum spec and 4-day agenda
prompts/                    # Sequenced live-coding prompts per day
presentation/               # HTML slide decks
.claude/kb/                 # 18 knowledge base domains
.claude/agents/             # SubAgents (ai-ml, code-quality, communication, domain, exploration)
```

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `ENVIRONMENT` | `local` (Docker) or `cloud` | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API (Days 1-4) | Yes |
| `ANTHROPIC_BASE_URL` | Custom API endpoint | Optional |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM LLM (Day 3-4) | Yes |
| `CREWAI_LLM` | LLM for CrewAI agents (e.g. `nim/nvidia/nemotron-mini-4b-instruct`) | Yes (Day 4) |
| `SUPABASE_URL` | Supabase project URL | Cloud mode |
| `SUPABASE_KEY` | Supabase anon/publishable key | Cloud mode |
| `SUPABASE_SERVICE_KEY` | Supabase service_role key (for table creation + RPC) | Cloud mode |
| `SUPABASE_DB_URL` | Supabase direct Postgres connection | Cloud mode (optional) |
| `QDRANT_CLOUD_URL` | Qdrant Cloud cluster URL | Cloud mode |
| `QDRANT_CLOUD_API_KEY` | Qdrant Cloud API key | Cloud mode |
| `LANGFUSE_SECRET_KEY` | LangFuse observability | Cloud mode |
| `LANGFUSE_PUBLIC_KEY` | LangFuse observability | Cloud mode |
| `LANGFUSE_HOST` | LangFuse server URL | Cloud mode |

---

AIDE Brasil | Formacao AI Data Engineer 2026 | Luan Moreno | April 13-16, 2026
