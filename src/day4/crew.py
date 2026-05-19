"""ShopAgent Day 4 — CrewAI crew with 3 specialized agents.

Architecture:
  AnalystAgent (The Ledger) -> SQL metrics from Supabase/Postgres
  ResearchAgent (The Memory) -> Semantic insights from Qdrant
  ReporterAgent (Synthesis) -> Executive report combining both

Langfuse tracing via:
  - openinference CrewAIInstrumentor (auto-instruments crew execution)
  - @observe decorator (adds session_id, user_id, tags)
"""

import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# env vars MUST be loaded before langfuse import (per best practice)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# langfuse init after dotenv
_langfuse_enabled = bool(
    os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    and not os.environ.get("LANGFUSE_SECRET_KEY", "").startswith("sk-lf-your")
)

if _langfuse_enabled:
    from langfuse import get_client, observe
    _langfuse_client = get_client()

    from openinference.instrumentation.crewai import CrewAIInstrumentor
    CrewAIInstrumentor().instrument(skip_dep_check=True)
else:
    _langfuse_client = None
    observe = lambda **kwargs: (lambda f: f)  # no-op decorator

from day4.tools import supabase_execute_sql, qdrant_semantic_search

LLM_MODEL = os.environ.get("CREWAI_LLM", "anthropic/claude-sonnet-4-20250514")


def _get_llm():
    """Build CrewAI LLM instance.

    Precedence (configured via CREWAI_LLM env var):
    - 'nim/...' -> NVIDIA NIM (OpenAI-compatible, free tier available)
    - 'anthropic/...' -> Anthropic API (requires ANTHROPIC_API_KEY)
    - anything else -> passed through to CrewAI default
    """
    model = os.environ.get("CREWAI_LLM", LLM_MODEL)
    nim_key = os.environ.get("NVIDIA_NIM_API_KEY", "")

    # NVIDIA NIM: free, fast, OpenAI-compatible
    if model.startswith("nim/") and nim_key:
        actual_model = model.replace("nim/", "", 1)
        from crewai import LLM
        return LLM(
            model=f"openai/{actual_model}",
            api_key=nim_key,
            base_url="https://integrate.api.nvidia.com/v1",
            timeout=120,
            max_tokens=1024,
            temperature=0.1,
        )

    # Default: return model string (CrewAI resolves it)
    return model


@CrewBase
class ShopAgentCrew:
    """ShopAgent multi-agent crew for e-commerce analysis."""

    @agent
    def analyst(self) -> Agent:
        """AnalystAgent -- SQL queries against The Ledger (Supabase/Postgres)."""
        return Agent(
            role="E-Commerce Data Analyst",
            goal="Extract precise metrics from the ShopAgent database using SQL queries",
            backstory=(
                "You are an expert SQL analyst specialized in e-commerce data. "
                "You query Supabase Postgres for exact numbers: revenue, order counts, "
                "payment distributions, and customer segment metrics. You never guess "
                "numbers -- every figure comes from a SQL query result. "
                "Available queries: revenue_by_state, orders_by_status, top_products, "
                "payment_distribution, segment_analysis, revenue_by_category, "
                "customer_count_by_state, orders_by_month, revenue_by_month, "
                "satisfaction_by_region. "
                "For monthly revenue trends or evolucao temporal, use revenue_by_month."
            ),
            tools=[supabase_execute_sql],
            llm=_get_llm(),
            verbose=True,
            max_iter=5,
            allow_delegation=False,
        )

    @agent
    def researcher(self) -> Agent:
        """ResearchAgent -- Semantic search in The Memory (Qdrant)."""
        return Agent(
            role="Customer Experience Researcher",
            goal="Analyze customer reviews and sentiment using semantic search",
            backstory=(
                "You are a customer experience researcher who understands what customers "
                "feel, not just what they buy. You search Qdrant for review themes, "
                "complaints, and sentiment patterns. You find the human story behind "
                "the data. Ask questions in Portuguese for best semantic match."
            ),
            tools=[qdrant_semantic_search],
            llm=_get_llm(),
            verbose=True,
            max_iter=5,
            allow_delegation=False,
        )

    @agent
    def reporter(self) -> Agent:
        """ReporterAgent -- Synthesizes findings into executive report."""
        return Agent(
            role="Executive Report Writer",
            goal="Combine analyst metrics and researcher insights into actionable reports",
            backstory=(
                "You are a senior business analyst who synthesizes quantitative data "
                "and qualitative insights into clear, actionable executive reports. "
                "Your reports always include specific numbers, key findings, and "
                "concrete recommendations. Write in Portuguese."
            ),
            llm=_get_llm(),
            verbose=True,
            max_iter=3,
            allow_delegation=False,
        )

    @task
    def analysis_task(self) -> Task:
        """Extract quantitative metrics from The Ledger."""
        return Task(
            description=(
                "Analyze the ShopAgent e-commerce database to answer: {question}\n\n"
                "Run the most relevant predefined SQL queries to extract metrics. "
                "Focus on revenue, order counts, customer segments, and payment data. "
                "Present results as structured data with exact numbers."
            ),
            expected_output=(
                "Structured data summary with exact numbers from SQL queries: "
                "revenue totals, order counts, averages, and distributions. "
                "Include the specific query names used."
            ),
            agent=self.analyst(),
        )

    @task
    def research_task(self) -> Task:
        """Find customer sentiment patterns from The Memory."""
        return Task(
            description=(
                "Search customer reviews to understand sentiment related to: {question}\n\n"
                "Use semantic search to find relevant review themes, complaints, "
                "and positive feedback. Identify patterns and recurring issues. "
                "Search in Portuguese for best results."
            ),
            expected_output=(
                "Qualitative analysis of customer sentiment: main themes found, "
                "complaint patterns, positive feedback highlights, and "
                "representative review excerpts."
            ),
            agent=self.researcher(),
        )

    @task
    def report_task(self) -> Task:
        """Synthesize analyst and researcher findings into executive report."""
        return Task(
            description=(
                "Create an executive report that answers: {question}\n\n"
                "Combine the quantitative data from the analyst with the "
                "qualitative insights from the researcher. Include:\n"
                "1. Key metrics (exact numbers)\n"
                "2. Customer sentiment analysis\n"
                "3. Main findings\n"
                "4. Actionable recommendations\n\n"
                "Write the report in Portuguese. Be specific and data-driven."
            ),
            expected_output=(
                "Executive report in Portuguese with sections: "
                "Metricas-Chave, Analise de Sentimento, Principais Descobertas, "
                "and Recomendacoes. Must include specific numbers and review excerpts."
            ),
            agent=self.reporter(),
            context=[self.analysis_task(), self.research_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the ShopAgent crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            verbose=True,
        )


@observe(name="shopagent-crew-run")
def run_crew(question: str, session_id: str | None = None, user_id: str | None = None) -> str:
    """Run the ShopAgent crew with Langfuse tracing.

    The @observe decorator creates a root span. CrewAIInstrumentor
    auto-instruments the crew execution with nested spans per agent.
    Session/user context set via env vars (Langfuse v4 pattern).
    """
    os.environ["LANGFUSE_SESSION_ID"] = session_id or ""
    os.environ["LANGFUSE_USER_ID"] = user_id or ""
    os.environ["LANGFUSE_TAGS"] = "shopagent-day4," + os.environ.get("ENVIRONMENT", "local")

    shop_crew = ShopAgentCrew()
    result = shop_crew.crew().kickoff(inputs={"question": question})

    if _langfuse_client:
        _langfuse_client.flush()

    return result.raw


if __name__ == "__main__":
    question = "Analise completa de satisfacao dos clientes por regiao"

    print("=" * 60)
    print(" ShopAgent Crew -- Day 4 Multi-Agent")
    print(f" Question: {question}")
    print("=" * 60)

    output = run_crew(question, session_id="cli-session", user_id="cli-user")

    print()
    print("=" * 60)
    print(" FINAL REPORT")
    print("=" * 60)
    print(output)
