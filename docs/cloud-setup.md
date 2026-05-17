# ShopAgent Day 4 — Cloud Setup Guide

## Overview

Day 4 migrates from local Docker to cloud — same code, different endpoints.
The `ENVIRONMENT=cloud` toggle in `.env` switches everything automatically.

| Component | Local (Day 1-3) | Cloud (Day 4) |
|-----------|-----------------|---------------|
| Postgres | Docker :5432 | Supabase Cloud |
| Qdrant | Docker :6333 | Qdrant Cloud |
| LLM | Claude via API | Claude via API (same) |
| Observability | None | LangFuse Cloud |
| Query Routing | NIM nemotron-mini-4b | NIM (same, from cloud) |

## Step-by-step

### 1. Supabase (Postgres Cloud)

1. Go to https://supabase.com and create a free project
2. Get your connection string:
   - Dashboard > Settings > Database > Connection string (URI)
   - Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
3. Set in `.env`:
   ```
   ENVIRONMENT=cloud
   SUPABASE_DB_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
   ```

### 2. Qdrant Cloud

1. Go to https://cloud.qdrant.io and create a free cluster
2. Get your URL and API key from the dashboard
3. Set in `.env`:
   ```
   QDRANT_CLOUD_URL=https://xxx.cloud.qdrant.io:6333
   QDRANT_CLOUD_API_KEY=your-api-key
   ```

### 3. LangFuse (Observability)

1. Go to https://cloud.langfuse.com and sign up
2. Create a project and copy the keys
3. Set in `.env`:
   ```
   LANGFUSE_SECRET_KEY=sk-lf-xxx
   LANGFUSE_PUBLIC_KEY=pk-lf-xxx
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

### 4. Run Migration

```bash
# Preview what will migrate (no changes)
python src/migrate_to_cloud.py --dry-run

# Full migration (copies data from Docker -> Supabase + Qdrant Cloud)
python src/migrate_to_cloud.py
```

### 5. Switch to Cloud Mode

In `.env`:
```
ENVIRONMENT=cloud
```

### 6. Launch Day 4

```powershell
.\start-shopagent.ps1 -Day 4 -SkipDocker
```

Or directly:
```bash
chainlit run src/day4/chainlit_app.py --port 8001
```

### 7. Verify

Open the app and ask:
- "Qual o faturamento total por estado?" — should hit Supabase
- "Clientes reclamando de entrega?" — should hit Qdrant Cloud
- "Analise completa por regiao" — both agents + reporter

Check LangFuse dashboard for traces, token usage, and cost.

## Architecture: Local vs Cloud

```
LOCAL (Day 1-3)                    CLOUD (Day 4)
┌──────────────┐                   ┌──────────────┐
│ Docker       │                   │ Supabase     │
│ Postgres     │  ──migration──>   │ Postgres     │
│ :5432        │                   │ (cloud URL)  │
└──────────────┘                   └──────────────┘
┌──────────────┐                   ┌──────────────┐
│ Docker       │                   │ Qdrant Cloud  │
│ Qdrant       │  ──re-ingest──>   │ (cloud URL)  │
│ :6333        │                   │ + API key    │
└──────────────┘                   └──────────────┘
                                     ┌──────────────┐
                                     │ LangFuse     │
                                     │ (traces)     │
                                     └──────────────┘
```

## Cost Estimates (Free Tiers)

| Service | Free Tier | Limits |
|---------|-----------|--------|
| Supabase | 500MB DB, 2 projects | Enough for ShopAgent |
| Qdrant Cloud | 1 cluster, 1GB | Enough for reviews |
| LangFuse | 50K observations/mo | Good for dev |
| NVIDIA NIM | 1000 credits | Routing calls only |
