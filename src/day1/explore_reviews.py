#!/usr/bin/env python3
"""
Explore reviews.jsonl for ShopAgent Day 1
Shows structure, samples, and distributions
"""

import json
from collections import Counter
from pathlib import Path

def analyze_reviews():
    reviews_file = Path("../../gen/data/reviews/reviews.jsonl")

    print("=== ShopAgent Reviews Analysis ===\n")

    # Read all reviews
    reviews = []
    errors = 0
    with open(reviews_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            try:
                review = json.loads(line)
                reviews.append(review)
            except json.JSONDecodeError:
                errors += 1

    total_reviews = len(reviews)
    if errors > 0:
        print(f"Aviis: Ignoradas {errors} linhas malformadas")
    print(f"Total de reviews: {total_reviews:,}\n")

    # 1. Show structure from first review
    print("ESTRUTURA de cada review:")
    if reviews:
        first_review = reviews[0]
        for key, value in first_review.items():
            print(f"  - {key}: {type(value).__name__} = {repr(value)[:60]}")
    print()

    # 2. Sample 10 reviews
    print("AMOSTRA de 10 primeiras reviews:")
    print("-" * 80)
    for i, review in enumerate(reviews[:10], 1):
        print(f"{i}. Rating: {review['rating']}/5 | Sentiment: {review['sentiment']}")
        print(f"   Pedido: {review['order_id']}")
        print(f"   Comentário: {review['comment'][:90]}...")
        print()

    # 3. Distribution of sentiments
    print("DISTRIBUIÇÃO por sentimento:")
    sentiment_counts = Counter(r['sentiment'] for r in reviews)
    for sentiment, count in sentiment_counts.most_common():
        percentage = (count / total_reviews) * 100
        print(f"  {sentiment:12s}: {count:4,} ({percentage:5.1f}%)")
    print()

    # 4. Distribution of ratings
    print("DISTRIBUIÇÃO por rating (estrelas):")
    rating_counts = Counter(r['rating'] for r in reviews)
    for rating in sorted(rating_counts.keys()):
        count = rating_counts[rating]
        percentage = (count / total_reviews) * 100
        bar = "*" * int(percentage)
        print(f"  {rating}*: {count:4,} ({percentage:5.1f}%) {bar}")
    print()

    # 5. Rating vs Sentiment matrix
    print("MATRIZ Rating vs Sentimento:")
    matrix = Counter((r['rating'], r['sentiment']) for r in reviews)
    sentiments = ['negative', 'neutral', 'positive']
    ratings = [1, 2, 3, 4, 5]

    print("Rating | Negative | Neutral | Positive | Total")  # Fixed encoding issue
    print("-" * 45)
    for rating in ratings:
        row_counts = [matrix.get((rating, s), 0) for s in sentiments]
        row_total = sum(row_counts)
        print(f"{rating}★     | {row_counts[0]:8,} | {row_counts[1]:7,} | {row_counts[2]:8,} | {row_total:,}")
    print("-" * 50)

if __name__ == "__main__":
    analyze_reviews()