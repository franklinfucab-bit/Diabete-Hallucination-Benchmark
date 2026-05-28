"""
Analyze 100q NOTA results: overall accuracy, wrong-answer topics/IDs,
and analysis (confusion patterns, difficulty distribution, hardest topics).
Outputs summary_{model}.json per model and 100q_results_summary_all.json.
"""
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_JSONL = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"
RESULTS_DIR = BASE_DIR / "results_100q_nota"

GENERIC_TAGS = {"diabetes", "fct", "nota", "fqt", "fqt_v2"}


def load_benchmark_lookup() -> dict:
    """Build id -> {tags, topic, difficulty} from 100q benchmark JSONL."""
    lookup = {}
    if not BENCHMARK_JSONL.exists():
        return lookup
    with open(BENCHMARK_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)
            qid = q.get("id", "")
            meta = q.get("metadata") or {}
            tags = meta.get("tags") or []
            difficulty = meta.get("difficulty", 0)
            topic = "Other"
            for t in tags:
                t_str = str(t).strip()
                if t_str and t_str.lower() not in GENERIC_TAGS:
                    topic = t_str
                    break
            lookup[qid] = {"tags": tags, "topic": topic, "difficulty": difficulty}
    return lookup


def analyze_results(results: list, benchmark: dict) -> dict:
    """Analyze a single model's results."""
    wrong_ids = []
    wrong_by_topic = defaultdict(list)
    pred_vs_label = defaultdict(int)
    wrong_by_difficulty = defaultdict(int)

    for item in results:
        qid = item.get("id", "")
        correct = item.get("correct", False)
        if correct:
            continue
        wrong_ids.append(qid)
        info = benchmark.get(qid, {})
        topic = info.get("topic", "Other")
        wrong_by_topic[topic].append(qid)
        pred = item.get("pred", "?")
        label = item.get("label", "?")
        pred_vs_label[f"{pred}->{label}"] += 1
        diff = info.get("difficulty", 0)
        diff_str = str(round(diff, 2)) if isinstance(diff, (int, float)) else str(diff)
        wrong_by_difficulty[diff_str] += 1

    total = len(results)
    correct_count = sum(1 for r in results if r.get("correct"))
    overall_acc = (correct_count / total * 100) if total > 0 else 0

    hardest = [
        {"topic": t, "wrong_count": len(ids), "ids": ids}
        for t, ids in sorted(wrong_by_topic.items(), key=lambda x: -len(x[1]))
    ]

    return {
        "overall": {
            "accuracy": f"{overall_acc:.1f}%",
            "correct": correct_count,
            "total": total,
            "wrong": total - correct_count,
        },
        "by_type": {
            "NOTA": {
                "accuracy": f"{overall_acc:.1f}%",
                "correct": correct_count,
                "total": total,
            }
        },
        "wrong_answers": {
            "ids": wrong_ids,
            "by_topic": dict(wrong_by_topic),
        },
        "analysis": {
            "pred_vs_label": dict(pred_vs_label),
            "wrong_by_difficulty": dict(wrong_by_difficulty),
            "hardest_topics": hardest[:20],
        },
    }


def main():
    benchmark = load_benchmark_lookup()
    print(f"Loaded benchmark lookup: {len(benchmark)} questions")

    if not RESULTS_DIR.exists():
        print(f"Results dir not found: {RESULTS_DIR}")
        return

    files = list(RESULTS_DIR.glob("results_*.json"))
    if not files:
        print(f"No results_*.json found in {RESULTS_DIR}")
        print("Run run_100q_nota_multi_models.py first to generate results.")
        return

    all_summaries = {}
    for f in sorted(files):
        model_name = f.stem.replace("results_", "")
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        summary = analyze_results(data, benchmark)
        summary["model"] = model_name
        out_path = RESULTS_DIR / f"summary_{model_name}.json"
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(summary, fp, indent=2, ensure_ascii=False)
        print(f"  Wrote {out_path.name}")
        all_summaries[model_name] = {
            "overall": summary["overall"],
            "by_type": summary["by_type"],
        }

    combined_path = RESULTS_DIR / "100q_results_summary_all.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)
    print(f"Wrote {combined_path.name} (cross-model comparison)")

    print("\nOverall accuracy by model:")
    for m, s in all_summaries.items():
        print(f"  {m}: {s['overall']['accuracy']} ({s['overall']['correct']}/{s['overall']['total']})")


if __name__ == "__main__":
    main()
