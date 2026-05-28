"""
Verify FCT subdomain (topic) balance: read FCT questions, extract topic per record,
report per-topic counts. Use on filtered FCT JSONL or 300q FCT block.
"""
import json
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
GENERIC_TAGS = {"diabetes", "fct", "nota", "fqt", "fqt_v2"}

# Default: check filtered FCT in benchmark/
FILTERED_FCT = BASE_DIR / "benchmark" / "100q_fct_filtered.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def extract_topic(q: dict) -> str:
    """First non-generic tag from metadata.tags or metadata.topic_hint."""
    meta = q.get("metadata") or {}
    for t in meta.get("tags") or []:
        t_str = str(t).strip()
        if t_str and t_str.lower() not in GENERIC_TAGS:
            return t_str
    hint = meta.get("topic_hint")
    if hint and str(hint).strip() and str(hint).strip().lower() not in GENERIC_TAGS:
        return str(hint).strip()
    return "Other"


def main():
    path = FILTERED_FCT
    if not path.exists():
        print(f"File not found: {path}")
        return
    items = load_jsonl(path)
    topics = [extract_topic(q) for q in items]
    counts = Counter(topics)
    n_topics = len(counts)
    max_count = max(counts.values()) if counts else 0
    total = len(items)

    print(f"FCT file: {path}")
    print(f"Total questions: {total}")
    print(f"Distinct topics: {n_topics}")
    print(f"Max count per topic: {max_count}")
    if total > 0:
        print(f"Balance: {'OK (no single topic dominates)' if max_count <= 2 else 'WARNING (some topics have >2 questions)'}")
    print("\nPer-topic counts:")
    for topic, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {topic}: {c}")


if __name__ == "__main__":
    main()
