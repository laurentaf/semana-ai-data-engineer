#!/usr/bin/env python3
"""
RAG Provocation Analysis - Day 11 Task
Analyzes reviews to complain about late deliveries
"""

import collections
import json
import re
from pathlib import Path

REVIEWS_FILE = Path(__file__).resolve().parents[2] / "gen" / "data" / "reviews" / "reviews.jsonl"

def analyze_negative_reviews():
    """Analyze negative reviews for complaints about late deliveries"""

    with open(REVIEWS_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    reviews = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            reviews.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Filter negative reviews
    negative_reviews = [r for r in reviews if r.get("sentiment") == "negative"]

    print("=== RAG Provocation - Analysis of Negative Reviews ===")
    print(f"\nTotal reviews analyzed: {len(reviews)}")
    print(f"Negative reviews found: {len(negative_reviews)} ({len(negative_reviews)/len(reviews)*100:.1f}%)")

    # 1. Complaints about late deliveries
    late_delivery_keywords = [
        "atrasou", "atraso", "demorou", "demora", "tarde",
        "dia atrasado", "dias atrasado", "semanas",
        "estava previsto", "previsão", "prazo", "entrega"
    ]

    late_delivery_complaints = []
    for review in negative_reviews:
        comment = review.get("comment", "").lower()
        if any(keyword in comment for keyword in late_delivery_keywords):
            late_delivery_complaints.append(review)

    print(f"\n COMPLAINTS ABOUT LATE DELIVERIES: {len(late_delivery_complaints)}")
    print("-" * 60)

    if late_delivery_complaints:
        print("Sample complaints:")
        for i, review in enumerate(late_delivery_complaints[:5], 1):
            print(f"{i}. Rating: {review['rating']}/5 - {review['comment'][:80]}...")
    else:
        print("No explicit late delivery complaints found in sample")

    # 2. Main themes in negative reviews
    print(f"\n MAIN THEMES IN NEGATIVE REVIEWS:")
    print("-" * 60)

    themes = {
        "late_delivery": 0,
        "product_damage": 0,
        "wrong_product": 0,
        "poor_quality": 0,
        "customer_service": 0,
        "no_delivery": 0,
        "expensive_shipping": 0
    }

    theme_keywords = {
        "late_delivery": ["atrasou", "atraso", "demorou", "demora", "tarde", "prazo"],
        "product_damage": ["danificado", "quebrado", "avariat", "amassado", "defeito"],
        "wrong_product": ["diferente", "errado", "outro produto", "nao e o que"],
        "poor_quality": ["qualidade ruim", "fraco", "barato", "desgastado", "pobre"],
        "customer_service": ["atendimento", "suporte", "não responde", "pouco"],
        "no_delivery": ["não chegou", "nunca recebi", "nao entregaram"],
        "expensive_shipping": ["frete caro", "taxa alta", "custo envio"]
    }

    for review in negative_reviews:
        comment = review.get("comment", "").lower()
        for theme, keywords in theme_keywords.items():
            if any(keyword in comment for keyword in keywords):
                themes[theme] += 1

    # Sort themes by frequency
    sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)

    for theme, count in sorted_themes:
        if count > 0:
            percentage = (count / len(negative_reviews)) * 100
            print(f"  • {theme.replace('_', ' ').title()}: {count} reviews ({percentage:.1f}%)")

    # 3. Products with most complaints
    print(f"\n PRODUCTS WITH MOST COMPLAINTS:")
    print("-" * 60)
    print("Note: Product IDs not available in review data")
    print("Would require JOIN with orders+products tables")
    print("\nHowever, we can analyze review patterns:")

    # Group negative reviews by order_id to see repeat complaints
    order_complaints = collections.Counter(r.get("order_id") for r in negative_reviews)

    print(f"  • Orders with negative reviews: {len(order_complaints)}")
    print(f"  • Most complaints from single order: {order_complaints.most_common(1)[0][1] if order_complaints else 0}")

    # 4. Actions needed
    print(f"\n IMMEDIATE ACTIONS NEEDED:")
    print("-" * 60)

    immediate_actions = []

    if themes["no_delivery"] > 0:
        immediate_actions.append("Investigate undelivered orders immediately")

    if themes["product_damage"] > len(negative_reviews) * 0.3:  # >30% of complaints
        immediate_actions.append("Review packaging and shipping procedures")

    if themes["customer_service"] > 0:
        immediate_actions.append("Improve customer service response times")

    if not immediate_actions:
        immediate_actions.append("Monitor delivery times and customer feedback")

    for i, action in enumerate(immediate_actions, 1):
        print(f"  {i}. {action}")

    # Conclusion
    print(f"\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print(f"Customers reporting late deliveries: {len(late_delivery_complaints)}")
    print(f"Top complaint themes identified: {', '.join([t[0].replace('_', ' ') for t in sorted_themes[:3] if t[1] > 0])}")
    print(f"Action items: {len(immediate_actions)} immediate actions required")
    print("=" * 60)

if __name__ == "__main__":
    analyze_negative_reviews()