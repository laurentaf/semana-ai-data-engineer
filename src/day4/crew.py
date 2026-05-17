"""ShopAgent Day 4 — CrewAI crew with 3 specialized agents.

Architecture:
    AnalystAgent  (The Ledger)  -> SQL metrics from Supabase/Postgres
    ResearchAgent (The Memory)  -> Semantic insights from Qdrant
    ReporterAgent (Synthesis)   -> Executive report combining both
"""

import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe

from tools import supabase_execute_sql, qdrant_semantic_search

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

LLM_MODEL = os.environ.get("CREWAI_LLM", "anthropic/claude-sonnet-4-20250514")

_lf: Langfuse | None = None


def _get_langfuse() -> Langfuse | None:
    global _lf
    if _lf is not None:
        return _lf
    secret = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    public = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()
    if secret and public and not secret.startswith("sk-lf-"):
        _lf = Langfuse(
            public_key=public,
            secret_key=secret,
            host=host,
        )
        return _lf
    return None


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
                "customer_count_by_state, orders_by_month, revenue_by_month, satisfaction_by_region. For monthly revenue trends or evolucao temporal, use revenue_by_month."
            ),
            tools=[supabase_execute_sql],
            llm=LLM_MODEL,
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
            llm=LLM_MODEL,
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
            llm=LLM_MODEL,
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
        """Assemble the ShopAgent crew with optional LangFuse tracing."""
        lf = _get_langfuse()
        callbacks = []
        if lf:
            handlers = lf.get_callback_handlers(
                metadata={"crew": "shopagent-v4", "environment": os.environ.get("ENVIRONMENT", "local")}
            )
            callbacks = handlers if isinstance(handlers, list) else [handlers]

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
            callback=callbacks if callbacks else None,
        )


@observe()
def run_crew(question: str) -> str:
    """Run the ShopAgent crew with Langfuse tracing."""
    shop_crew = ShopAgentCrew()
    result = shop_crew.crew().kickoff(inputs={"question": question})
    return result.raw


if __name__ == "__main__":
    question = "Analise completa de satisfacao dos clientes por regiao"

    print("=" * 60)
    print("  ShopAgent Crew -- Day 4 Multi-Agent")
    print(f"  Question: {question}")
    print("=" * 60)

    output = run_crew(question)

    print()
    print("=" * 60)
    print("  FINAL REPORT")
    print("=" * 60)
    print(output)
