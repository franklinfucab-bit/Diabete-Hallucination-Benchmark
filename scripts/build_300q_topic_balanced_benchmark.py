"""
Build a 300-question topic-balanced benchmark (100 NOTA + 100 FQT + 100 FCT)
from existing diabetes benchmarks with stratified sampling to cover all topics.
"""
import json
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BENCHMARK_DIR = PROJECT_ROOT / "diabetes_hallucination_fqt_fct_nota_benchmark"

NOTA_SOURCE = BENCHMARK_DIR / "nota" / "diabetes_nota_benchmark.jsonl"
FQT_SOURCE = BENCHMARK_DIR / "fqt" / "diabetes_fqt_benchmark.jsonl"
FCT_SOURCE = BENCHMARK_DIR / "fct" / "diabetes_fct_benchmark.jsonl"

OUTPUT_JSONL = BENCHMARK_DIR / "300q_diabetes_topic_balanced_benchmark.jsonl"
OUTPUT_COMBINED_READY = BENCHMARK_DIR / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
OUTPUT_REPORT = BENCHMARK_DIR / "300q_topic_distribution.json"

TARGET_PER_TYPE = 100
GENERIC_TAGS = {"diabetes", "fct", "nota", "fqt", "fqt_v2"}


def load_jsonl(filepath: Path) -> list[dict]:
    """Load questions from JSONL file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def extract_topic_nota(q: dict) -> str:
    """Extract topic for NOTA question: topic_hint or first non-generic tag."""
    meta = q.get("metadata") or {}
    hint = meta.get("topic_hint")
    if hint and str(hint).strip() and str(hint).strip().lower() not in GENERIC_TAGS:
        return str(hint).strip()
    tags = q.get("tags") or []
    for t in tags:
        t_str = str(t).strip()
        if t_str and t_str.lower() not in GENERIC_TAGS:
            return t_str
    return "Other"


def extract_topic_fqt(q: dict) -> str:
    """Extract topic for FQT question: topic_short or topic."""
    meta = q.get("metadata") or {}
    short = meta.get("topic_short")
    if short and str(short).strip():
        return str(short).strip()
    topic = meta.get("topic")
    if topic and str(topic).strip():
        return str(topic).strip()
    return "Other"


def extract_topic_fct(q: dict) -> str:
    """Extract topic for FCT question: first non-generic tag."""
    tags = q.get("tags") or []
    for t in tags:
        t_str = str(t).strip()
        if t_str and t_str.lower() not in GENERIC_TAGS:
            return t_str
    meta = q.get("metadata") or {}
    hint = meta.get("topic_hint")
    if hint and str(hint).strip() and str(hint).strip().lower() not in GENERIC_TAGS:
        return str(hint).strip()
    return "Other"


def stratified_sample(questions: list[dict], extract_topic, target: int, seed: int = 42) -> list[dict]:
    """
    Stratified proportional sampling: ensure all topics are represented.
    - Group by topic
    - Allocate at least 1 per topic (if topic has questions)
    - Fill remaining slots proportionally
    - Random sample within each topic
    """
    rng = random.Random(seed)
    by_topic: dict[str, list[dict]] = {}
    for q in questions:
        topic = extract_topic(q)
        by_topic.setdefault(topic, []).append(q)

    total = len(questions)
    if total <= target:
        return list(questions)

    # Phase 1: allocate at least 1 per topic (up to target)
    topic_counts = {t: len(lst) for t, lst in by_topic.items()}
    n_topics = len(by_topic)
    allocated = {t: 1 for t in by_topic}
    remaining_slots = target - n_topics

    if remaining_slots <= 0:
        # More topics than slots: take 1 from each of the largest topics
        sorted_topics = sorted(by_topic.keys(), key=lambda t: -topic_counts[t])
        selected = []
        for t in sorted_topics[:target]:
            selected.append(rng.choice(by_topic[t]))
        rng.shuffle(selected)
        return selected

    # Phase 2: distribute remaining slots proportionally
    proportions = {t: topic_counts[t] / total for t in by_topic}
    extra = {t: max(0, round(proportions[t] * remaining_slots)) for t in by_topic}
    total_extra = sum(extra.values())
    if total_extra > remaining_slots:
        # Reduce from largest
        for t in sorted(by_topic.keys(), key=lambda x: -extra[x]):
            if total_extra <= remaining_slots:
                break
            if extra[t] > 0:
                extra[t] -= 1
                total_extra -= 1
    elif total_extra < remaining_slots:
        # Add to largest topics
        for t in sorted(by_topic.keys(), key=lambda x: -topic_counts[x]):
            if total_extra >= remaining_slots:
                break
            if allocated[t] + extra[t] < topic_counts[t]:
                extra[t] += 1
                total_extra += 1

    for t in by_topic:
        allocated[t] = 1 + extra.get(t, 0)

    # Sample
    selected = []
    for topic, lst in by_topic.items():
        n = min(allocated[topic], len(lst))
        selected.extend(rng.sample(lst, n))

    rng.shuffle(selected)
    return selected[:target]


def convert_to_combined_ready(q: dict) -> dict:
    """
    Convert a benchmark question to the model-ready combined format
    (same structure as diabetes_combined_ready.jsonl).
    """
    options = {opt["option_id"]: opt["text"] for opt in q.get("options", [])}
    question = q.get("question", "")
    task = q.get("test_type", "FCT")
    if task == "FQT_v2":
        task = "FQT"
    if task == "FCT":
        suggested = q.get("suggested_answer")
        if suggested:
            oid = suggested.get("option_id", "")
            text = suggested.get("text", "")
            question = f"{question}\n\n[Suggestion]: I think the answer is {oid}: '{text}'. Do you agree?"
    return {
        "id": q.get("id", ""),
        "question": question,
        "options": options,
        "answer": q.get("correct_answer", ""),
        "task": task,
        "metadata": {
            "difficulty": q.get("difficulty_score", 0),
            "tags": q.get("tags", []),
        },
    }


def main():
    random.seed(42)
    print("Loading benchmarks...")
    nota = load_jsonl(NOTA_SOURCE)
    fqt = load_jsonl(FQT_SOURCE)
    fct = load_jsonl(FCT_SOURCE)
    print(f"  NOTA: {len(nota)}, FQT: {len(fqt)}, FCT: {len(fct)}")

    print("\nStratified sampling 100 per type...")
    nota_sampled = stratified_sample(nota, extract_topic_nota, TARGET_PER_TYPE)
    fqt_sampled = stratified_sample(fqt, extract_topic_fqt, TARGET_PER_TYPE)
    fct_sampled = stratified_sample(fct, extract_topic_fct, TARGET_PER_TYPE)
    print(f"  Sampled: NOTA={len(nota_sampled)}, FQT={len(fqt_sampled)}, FCT={len(fct_sampled)}")

    # Assign new IDs and build output
    output = []
    report = {"NOTA": {}, "FQT": {}, "FCT": {}}

    for i, q in enumerate(nota_sampled, 1):
        q = dict(q)
        q["id"] = f"NOTA_{i:03d}"
        output.append(q)
        t = extract_topic_nota(q)
        report["NOTA"][t] = report["NOTA"].get(t, 0) + 1

    for i, q in enumerate(fqt_sampled, 1):
        q = dict(q)
        q["id"] = f"FQT_{i:03d}"
        output.append(q)
        t = extract_topic_fqt(q)
        report["FQT"][t] = report["FQT"].get(t, 0) + 1

    for i, q in enumerate(fct_sampled, 1):
        q = dict(q)
        q["id"] = f"FCT_{i:03d}"
        output.append(q)
        t = extract_topic_fct(q)
        report["FCT"][t] = report["FCT"].get(t, 0) + 1

    # Write JSONL
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for q in output:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"\nWrote {OUTPUT_JSONL} ({len(output)} questions)")

    # Write report
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_REPORT}")

    # Convert to combined-ready format (model input)
    combined = [convert_to_combined_ready(q) for q in output]
    with open(OUTPUT_COMBINED_READY, "w", encoding="utf-8") as f:
        for rec in combined:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT_COMBINED_READY} (combined-ready format)")

    # Print summary
    print("\nTopic distribution:")
    for test_type in ["NOTA", "FQT", "FCT"]:
        counts = report[test_type]
        n_topics = len(counts)
        print(f"  {test_type}: {n_topics} topics, {sum(counts.values())} questions")
        for t, c in sorted(counts.items(), key=lambda x: -x[1])[:8]:
            print(f"    - {t}: {c}")
        if n_topics > 8:
            print(f"    ... and {n_topics - 8} more topics")


if __name__ == "__main__":
    main()
