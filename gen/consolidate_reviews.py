"""Consolidate ShadowTraffic review fragment files into a single JSONL."""

import json
from pathlib import Path

REVIEWS_DIR = Path(__file__).parent / "data" / "reviews"
OUTPUT_FILE = REVIEWS_DIR / "reviews.jsonl"

def consolidate_reviews():
    fragments = sorted(REVIEWS_DIR.glob("reviews*.jsonl"))
    # Only process numbered fragments (reviews0.jsonl, reviews1.jsonl, ...), not the consolidated file
    fragments = [f for f in fragments if f.name != "reviews.jsonl" and f.name != "reviews_clean.jsonl"]

    reviews = []
    for frag in fragments:
        for line in frag.read_text(encoding="utf-8").strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                reviews.append(obj)
            except json.JSONDecodeError:
                continue

    # Write consolidated file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for review in reviews:
            f.write(json.dumps(review, ensure_ascii=False) + "\n")

    print(f"Consolidated {len(reviews)} reviews from {len(fragments)} files into {OUTPUT_FILE}")
    return len(reviews)

if __name__ == "__main__":
    consolidate_reviews()
