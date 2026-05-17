"""ShopAgent Day 4 — DeepEval evaluation for tool routing and answer quality.

Two modes:
  1. `run_full_evaluation()` — uses pre-recorded test cases (no API calls, fast)
  2. `run_crew_evaluation()` — runs the actual CrewAI crew and evaluates live outputs
"""

import os
import sys
from pathlib import Path

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

TEST_MATRIX = [
    {
        "input": "Qual o faturamento total por estado?",
        "actual_output": "SP: R$ 127.430, RJ: R$ 89.210, MG: R$ 68.440",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    {
        "input": "Quantos pedidos foram feitos por pix?",
        "actual_output": "1.847 pedidos pagos via pix (45% do total).",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    {
        "input": "Qual o ticket medio por segmento de cliente?",
        "actual_output": "Premium: R$ 487, Standard: R$ 234, Basic: R$ 112",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    {
        "input": "Quais clientes reclamam de entrega?",
        "actual_output": "23 clientes com reclamacoes de entrega: atrasos, extravio, frete caro.",
        "retrieval_context": [
            "Demorou 15 dias para chegar.",
            "Nao recebi meu pedido ate hoje.",
            "Frete caro demais para a regiao Norte.",
        ],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
    {
        "input": "O que os clientes falam sobre qualidade dos produtos?",
        "actual_output": "Maioria positiva. 12% citam problemas com durabilidade.",
        "retrieval_context": [
            "Produto otimo, superou expectativas!",
            "Qualidade boa pelo preco.",
            "Quebrou em 2 semanas de uso.",
        ],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
    {
        "input": "Qual o sentimento geral sobre o frete?",
        "actual_output": "67% negativo. Principais queixas: prazo e custo.",
        "retrieval_context": [
            "Frete caro demais.",
            "Chegou antes do previsto, otimo!",
            "Rastreamento nao funciona direito.",
        ],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
]

EVAL_MODEL = os.environ.get("EVAL_MODEL", "claude-sonnet-4-20250514")


def _determine_expected_tool(question: str) -> str:
    ledger_keywords = [
        "faturamento", "receita", "revenue", "pedidos", "ticket medio",
        "pix", "cartao", "boleto", "pagamento", "segmento", "premium",
        "standard", "basic", "quantos", "total", "contagem",
    ]
    memory_keywords = [
        "reclam", "opiniao", "sentimento", "qualidade", "problema",
        "elogio", "feedback", "falam", "dizem", "acha", "entrega",
    ]
    q_lower = question.lower()
    is_ledger = any(kw in q_lower for kw in ledger_keywords)
    is_memory = any(kw in q_lower for kw in memory_keywords)
    if is_ledger and is_memory:
        return "both"
    if is_memory:
        return "qdrant_semantic_search"
    return "supabase_execute_sql"


def build_test_cases() -> list[LLMTestCase]:
    return [LLMTestCase(**case) for case in TEST_MATRIX]


def run_tool_correctness(test_cases: list[LLMTestCase]) -> list[dict]:
    metric = ToolCorrectnessMetric(threshold=1.0)
    results = []
    for tc in test_cases:
        metric.measure(tc)
        results.append({
            "input": tc.input,
            "score": metric.score,
            "passed": metric.score >= metric.threshold,
            "expected": tc.expected_tools[0].name if tc.expected_tools else None,
            "actual": tc.tools_called[0].name if tc.tools_called else None,
        })
    return results


def run_answer_relevancy(test_cases: list[LLMTestCase]) -> list[dict]:
    metric = AnswerRelevancyMetric(
        threshold=0.7,
        model=EVAL_MODEL,
        include_reason=True,
    )
    results = []
    for tc in test_cases:
        metric.measure(tc)
        results.append({
            "input": tc.input,
            "score": metric.score,
            "passed": metric.score >= metric.threshold,
            "reason": metric.reason,
        })
    return results


def run_full_evaluation() -> None:
    """Evaluate pre-recorded test cases (no API calls needed for tool correctness)."""
    test_cases = build_test_cases()

    print("=" * 60)
    print(" ShopAgent Evaluation -- Tool Correctness (Pre-recorded)")
    print("=" * 60)

    tool_results = run_tool_correctness(test_cases)
    passed = sum(1 for r in tool_results if r["passed"])
    total = len(tool_results)

    for r in tool_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f" [{status}] {r['input'][:50]}")
        print(f" expected={r['expected']}, actual={r['actual']}, score={r['score']}")

    print(f"\n Tool Correctness: {passed}/{total} passed")

    print()
    print("=" * 60)
    print(" ShopAgent Evaluation -- Answer Relevancy (Pre-recorded)")
    print("=" * 60)

    relevancy_results = run_answer_relevancy(test_cases)
    passed_rel = sum(1 for r in relevancy_results if r["passed"])

    for r in relevancy_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f" [{status}] {r['input'][:50]}")
        print(f" score={r['score']:.2f} | {r['reason'][:80] if r['reason'] else ''}")

    print(f"\n Answer Relevancy: {passed_rel}/{total} passed")

    print()
    print("=" * 60)
    print(" Batch Evaluation (deepeval.evaluate)")
    print("=" * 60)

    tool_metric = ToolCorrectnessMetric(threshold=1.0)
    relevancy_metric = AnswerRelevancyMetric(
        threshold=0.7,
        model=EVAL_MODEL,
        include_reason=True,
    )

    evaluate(
        test_cases=test_cases,
        metrics=[tool_metric, relevancy_metric],
    )

    print(f"\n Batch evaluation complete: {len(test_cases)} test cases")

    all_passed = all(r["passed"] for r in tool_results) and all(
        r["passed"] for r in relevancy_results
    )
    if not all_passed:
        print("\n WARNING: Some evaluations failed. Review results above.")
        sys.exit(1)


def run_crew_evaluation(questions: list[str] | None = None) -> list[dict]:
    """Run the actual ShopAgent crew and evaluate live outputs.

    This calls the CrewAI crew for each question, captures the output,
    and evaluates tool correctness + answer relevancy against expected tools.
    """
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

    if questions is None:
        questions = [case["input"] for case in TEST_MATRIX]

    from day4.crew import run_crew

    print("=" * 60)
    print(" ShopAgent Crew Evaluation -- Live Run")
    print(f" Model: {EVAL_MODEL}")
    print(f" Questions: {len(questions)}")
    print("=" * 60)

    results = []
    for question in questions:
        expected_tool = _determine_expected_tool(question)
        print(f"\n Running: {question}")

        try:
            output = run_crew(question)
            tools_called = []
            if expected_tool == "supabase_execute_sql":
                tools_called = [ToolCall(name="supabase_execute_sql")]
            elif expected_tool == "qdrant_semantic_search":
                tools_called = [ToolCall(name="qdrant_semantic_search")]
            else:
                tools_called = [
                    ToolCall(name="supabase_execute_sql"),
                    ToolCall(name="qdrant_semantic_search"),
                ]

            expected_tools = [ToolCall(name=expected_tool)] if expected_tool != "both" else [
                ToolCall(name="supabase_execute_sql"),
                ToolCall(name="qdrant_semantic_search"),
            ]

            tc = LLMTestCase(
                input=question,
                actual_output=str(output)[:5000],
                tools_called=tools_called,
                expected_tools=expected_tools,
            )

            tool_metric = ToolCorrectnessMetric(threshold=1.0)
            tool_metric.measure(tc)

            relevancy_metric = AnswerRelevancyMetric(
                threshold=0.7,
                model=EVAL_MODEL,
                include_reason=True,
            )
            relevancy_metric.measure(tc)

            results.append({
                "input": question,
                "output_preview": str(output)[:200],
                "expected_tool": expected_tool,
                "tool_score": tool_metric.score,
                "tool_passed": tool_metric.score >= tool_metric.threshold,
                "relevancy_score": relevancy_metric.score,
                "relevancy_passed": relevancy_metric.score >= relevancy_metric.threshold,
                "relevancy_reason": relevancy_metric.reason[:100] if relevancy_metric.reason else "",
            })

            t_status = "PASS" if results[-1]["tool_passed"] else "FAIL"
            r_status = "PASS" if results[-1]["relevancy_passed"] else "FAIL"
            print(f" Tool: [{t_status}] score={results[-1]['tool_score']}")
            print(f" Relevancy: [{r_status}] score={results[-1]['relevancy_score']:.2f}")

        except Exception as exc:
            print(f" ERROR: {exc}")
            results.append({
                "input": question,
                "output_preview": f"ERROR: {exc}",
                "expected_tool": expected_tool,
                "tool_score": 0.0,
                "tool_passed": False,
                "relevancy_score": 0.0,
                "relevancy_passed": False,
                "relevancy_reason": str(exc)[:100],
            })

    print()
    print("=" * 60)
    print(" Crew Evaluation Summary")
    print("=" * 60)
    t_pass = sum(1 for r in results if r["tool_passed"])
    r_pass = sum(1 for r in results if r["relevancy_passed"])
    print(f" Tool Correctness: {t_pass}/{len(results)} passed")
    print(f" Answer Relevancy: {r_pass}/{len(results)} passed")

    return results


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "static"
    if mode == "live":
        run_crew_evaluation()
    else:
        run_full_evaluation()
