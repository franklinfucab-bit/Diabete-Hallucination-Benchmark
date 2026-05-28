"""
Select 350 golden FQT questions from 1000q_diabetes_fqt_benchmark_v2.jsonl,
evenly stratified by topic (metadata.topic_short: Neuropathy_FootCare, Acute_Hospital,
Retinopathy_Kidney, SpecialPops).

Output: output/Json/350q_fqt_v2_golden_seed.jsonl (350 questions, ~87-88 per topic).
"""

import json
import random
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fqt_benchmark_v2.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "350q_fqt_v2_golden_seed.jsonl"

TARGET = 350
RANDOM_SEED = 42


def get_topic(record: dict) -> str:
    """Use metadata.topic_short, fallback to metadata.topic."""
    meta = record.get("metadata") or {}
    topic = (meta.get("topic_short") or meta.get("topic") or "").strip()
    return topic or "__no_topic__"


def load_benchmark(path: Path) -> list:
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Select 350 FQT golden seed, evenly by topic.")
    ap.add_argument("--input", type=Path, default=INPUT_FILE, help="FQT v2 JSONL")
    ap.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Output JSONL")
    ap.add_argument("--target", type=int, default=TARGET, help="Target number (default 350)")
    args = ap.parse_args()

    target = max(1, args.target)
    questions = load_benchmark(args.input)

    by_topic = defaultdict(list)
    for q in questions:
        topic = get_topic(q)
        by_topic[topic].append(q)

    # Drop __no_topic__ if we have the four main topics
    topics = sorted(k for k in by_topic if k != "__no_topic__")
    if not topics:
        topics = sorted(by_topic.keys())

    print(f"Input: {args.input} ({len(questions)} questions)")
    for t in topics:
        print(f"  {t}: {len(by_topic[t])}")

    # Even allocation: base = target // n, extra = target % n
    n_topics = len(topics)
    base_per = target // n_topics
    extra = target % n_topics
    per_topic = {t: base_per + (1 if i < extra else 0) for i, t in enumerate(topics)}

    rng = random.Random(RANDOM_SEED)
    selected = []
    for t in topics:
        pool = list(by_topic[t])
        k = min(per_topic[t], len(pool))
        chosen = rng.sample(pool, k)
        selected.extend(chosen)

    selected.sort(key=lambda q: (q.get("id") or ""))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for q in selected:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Final counts
    final_by_topic = defaultdict(int)
    for q in selected:
        final_by_topic[get_topic(q)] += 1
    print(f"Output: {args.output} ({len(selected)} questions)")
    for t in topics:
        print(f"  {t}: {final_by_topic[t]}")


if __name__ == "__main__":
    main()
