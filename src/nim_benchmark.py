"""Benchmark NVIDIA NIM models for The Ledger (SQL query routing speed).

Tests: latency, quality of query name mapping, and result formatting
for the ShopAgent AnalystAgent use case.
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")

SYSTEM_PROMPT = """Voce e o ShopAgent AnalystAgent. Dada uma pergunta, responda qual query SQL usar.

Queries disponiveis: revenue_by_state, orders_by_status, top_products,
payment_distribution, segment_analysis, revenue_by_category,
customer_count_by_state, orders_by_month, satisfaction_by_region

Responda APENAS com o nome da query, nada mais."""

TEST_QUESTIONS = [
    "Qual o faturamento total por estado?",
    "Quantos pedidos foram feitos por pix?",
    "Quais os top 10 produtos mais vendidos?",
    "Analise por segmento de cliente",
    "Faturamento por categoria de produto",
]

CANDIDATES = [
    # Fast tier (small models)
    "meta/llama-3.2-1b-instruct",
    "meta/llama-3.2-3b-instruct",
    "nvidia/nvidia-nemotron-nano-9b-v2",
    "nvidia/llama-3.1-nemotron-nano-8b-v1",
    # Mid tier
    "meta/llama-3.1-8b-instruct",
    "mistralai/ministral-14b-instruct-2512",
    "nvidia/nemotron-mini-4b-instruct",
    # Strong tier
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1",
    "qwen/qwen3-next-80b-a3b-instruct",
]

EXPECTED = {
    "Qual o faturamento total por estado?": "revenue_by_state",
    "Quantos pedidos foram feitos por pix?": "payment_distribution",
    "Quais os top 10 produtos mais vendidos?": "top_products",
    "Analise por segmento de cliente": "segment_analysis",
    "Faturamento por categoria de produto": "revenue_by_category",
}

VALID_QUERIES = {
    "revenue_by_state", "orders_by_status", "top_products",
    "payment_distribution", "segment_analysis", "revenue_by_category",
    "customer_count_by_state", "orders_by_month", "satisfaction_by_region",
}


def create_client() -> OpenAI:
    return OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)


def test_model(client: OpenAI, model: str) -> dict:
    results = {"model": model, "questions": [], "latencies": [], "correct": 0, "valid": 0, "errors": 0}

    for question in TEST_QUESTIONS:
        expected = EXPECTED[question]
        start = time.perf_counter()

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=50,
            )
            latency = time.perf_counter() - start
            response = completion.choices[0].message.content.strip().lower()

            # Normalize response
            response_clean = response.replace(" ", "_").replace("-", "_").strip(".")

            is_correct = response_clean == expected
            is_valid = response_clean in VALID_QUERIES

            if is_correct:
                results["correct"] += 1
            if is_valid:
                results["valid"] += 1

            results["questions"].append({
                "question": question[:50],
                "expected": expected,
                "got": response_clean,
                "correct": is_correct,
                "valid": is_valid,
                "latency": latency,
            })
            results["latencies"].append(latency)

        except Exception as exc:
            latency = time.perf_counter() - start
            results["errors"] += 1
            results["questions"].append({
                "question": question[:50],
                "expected": expected,
                "got": f"ERROR: {exc}",
                "correct": False,
                "valid": False,
                "latency": latency,
            })
            results["latencies"].append(latency)

    if results["latencies"]:
        results["avg_latency"] = sum(results["latencies"]) / len(results["latencies"])
        results["min_latency"] = min(results["latencies"])
        results["max_latency"] = max(results["latencies"])
    else:
        results["avg_latency"] = results["min_latency"] = results["max_latency"] = 0

    results["accuracy"] = results["correct"] / len(TEST_QUESTIONS) if TEST_QUESTIONS else 0
    results["valid_rate"] = results["valid"] / len(TEST_QUESTIONS) if TEST_QUESTIONS else 0

    return results


def print_results(all_results: list[dict]) -> None:
    print()
    print("=" * 90)
    print("  NVIDIA NIM Benchmark — The Ledger (SQL Query Routing)")
    print("=" * 90)
    print()

    # Sort by accuracy desc, then avg_latency asc
    all_results.sort(key=lambda r: (-r["accuracy"], r["avg_latency"]))

    print(f"  {'Model':<48} {'Avg(s)':>7} {'Min(s)':>7} {'Acc':>6} {'Valid':>6} {'Err':>4}")
    print(f"  {'-'*48} {'-'*7} {'-'*7} {'-'*6} {'-'*6} {'-'*4}")

    for r in all_results:
        short_name = r["model"].split("/")[-1] if "/" in r["model"] else r["model"]
        model_label = r["model"][:48]
        print(f"  {model_label:<48} {r['avg_latency']:>7.2f} {r['min_latency']:>7.2f} {r['accuracy']:>5.0%} {r['valid_rate']:>5.0%} {r['errors']:>4}")

    print()

    # Best pick
    best = all_results[0]
    print(f"  BEST PICK: {best['model']}")
    print(f"    Accuracy: {best['accuracy']:.0%}  |  Avg latency: {best['avg_latency']:.2f}s")
    print()

    # Detail per question for top 3
    print("  Top 3 detail:")
    for r in all_results[:3]:
        print(f"\n  {r['model']}")
        for q in r["questions"]:
            mark = "v" if q["correct"] else ("~" if q["valid"] else "x")
            print(f"    [{mark}] {q['question']:<50} -> {q['got']:<30} (expected: {q['expected']}, {q['latency']:.2f}s)")


def main():
    models_to_test = CANDIDATES
    if len(sys.argv) > 1:
        models_to_test = sys.argv[1:]

    print(f"  Testing {len(models_to_test)} models x {len(TEST_QUESTIONS)} questions = {len(models_to_test) * len(TEST_QUESTIONS)} API calls")
    print()

    client = create_client()
    all_results = []

    for model in models_to_test:
        short_name = model.split("/")[-1]
        print(f"  Benchmarking: {model}...", end="", flush=True)
        result = test_model(client, model)
        all_results.append(result)
        print(f" avg={result['avg_latency']:.2f}s acc={result['accuracy']:.0%} err={result['errors']}")

    print_results(all_results)


if __name__ == "__main__":
    main()
