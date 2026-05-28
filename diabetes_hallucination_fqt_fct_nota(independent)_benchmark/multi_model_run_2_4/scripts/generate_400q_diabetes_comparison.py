"""
Generate 400q diabetes comparison report: accuracy table, rankings, wrong-answer overlap.
Reads 400q_results_summary_all.json and raw results_*.json; optionally benchmark for hardest topics.
Outputs reports/400q_diabetes_comparison.json and .md.
"""
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results_400q_diabetes"
SUMMARY_ALL = RESULTS_DIR / "400q_results_summary_all.json"
BENCHMARK_JSONL = BASE_DIR / "benchmark" / "400q_diabetes_benchmark_combined_ready.jsonl"
REPORTS_DIR = RESULTS_DIR / "reports"
OUTPUT_JSON = REPORTS_DIR / "400q_diabetes_comparison.json"
OUTPUT_MD = REPORTS_DIR / "400q_diabetes_comparison.md"

MODELS_5 = ["deepseek-r1_7b", "gemma_7b", "llama3.1_8b", "mistral_latest", "qwen2.5_7b"]
GENERIC_TAGS = {"diabetes", "fct", "nota", "fqt", "fqt_v2", "aota"}
TASK_TYPES = ["NOTA", "FQT", "FCT", "AOTA"]


def task_from_id(qid: str) -> str:
    if qid.startswith("NOTA_"):
        return "NOTA"
    if qid.startswith("FQT_"):
        return "FQT"
    if qid.startswith("FCT_"):
        return "FCT"
    if qid.startswith("AOTA_"):
        return "AOTA"
    return "Other"


def load_benchmark_topics() -> dict:
    """id -> topic (first non-generic tag from metadata.tags)."""
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
            topic = "Other"
            for t in meta.get("tags") or []:
                t_str = str(t).strip()
                if t_str and t_str.lower() not in GENERIC_TAGS:
                    topic = t_str
                    break
            lookup[qid] = topic
    return lookup


def load_raw_results() -> dict:
    """model -> list of {id, pred, label, correct}."""
    raw = {}
    for model in MODELS_5:
        path = RESULTS_DIR / f"results_{model}.json"
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw[model] = json.load(f)
    return raw


def build_wrong_by_task(raw_results: dict) -> dict:
    """task -> model -> set of wrong ids."""
    by_task = defaultdict(dict)
    for model, items in raw_results.items():
        for t in TASK_TYPES:
            by_task[t][model] = set()
        for item in items:
            if item.get("correct", True):
                continue
            qid = item.get("id", "")
            task = task_from_id(qid)
            if task in by_task:
                by_task[task][model].add(qid)
    return dict(by_task)


def build_overlap(wrong_by_task: dict) -> dict:
    """task -> {wrong_by_all: [...], wrong_by_4: [...], ...}."""
    n_models = len(MODELS_5)
    overlap_by_task = {}
    for task, model_to_ids in wrong_by_task.items():
        id_to_count = defaultdict(int)
        for model, ids in model_to_ids.items():
            for qid in ids:
                id_to_count[qid] += 1
        overlap = {}
        for c in range(1, n_models + 1):
            key = "wrong_by_all" if c == n_models else f"wrong_by_{c}"
            overlap[key] = sorted([qid for qid, cnt in id_to_count.items() if cnt == c])
        overlap_by_task[task] = overlap
    return overlap_by_task


def main():
    if not SUMMARY_ALL.exists():
        print(f"Summary not found: {SUMMARY_ALL}. Run analyze_400q_results.py first.")
        return

    with open(SUMMARY_ALL, "r", encoding="utf-8") as f:
        all_summaries = json.load(f)

    models = [m for m in MODELS_5 if m in all_summaries]
    if not models:
        print("No model summaries found.")
        return

    raw_results = load_raw_results()
    wrong_by_task = build_wrong_by_task(raw_results)
    overlap_by_task = build_overlap(wrong_by_task)
    id_to_topic = load_benchmark_topics()

    # Accuracy table from summary
    accuracy_table = []
    for model in models:
        s = all_summaries[model]
        row = {
            "model": model,
            "overall": s["overall"]["accuracy"],
            "NOTA": s["by_type"].get("NOTA", {}).get("accuracy", "0%"),
            "FQT": s["by_type"].get("FQT", {}).get("accuracy", "0%"),
            "FCT": s["by_type"].get("FCT", {}).get("accuracy", "0%"),
            "AOTA": s["by_type"].get("AOTA", {}).get("accuracy", "0%"),
        }
        accuracy_table.append(row)

    def acc_val(acc_str):
        return float(str(acc_str).rstrip("%"))

    # Rankings per task (best first)
    rankings = {}
    for task in TASK_TYPES:
        rankings[task] = sorted(
            models,
            key=lambda m: acc_val(all_summaries.get(m, {}).get("by_type", {}).get(task, {}).get("accuracy", "0%")),
            reverse=True,
        )

    # Model performance profiles
    profiles = {}
    for row in accuracy_table:
        model = row["model"]
        accs = {
            "NOTA": acc_val(row["NOTA"]),
            "FQT": acc_val(row["FQT"]),
            "FCT": acc_val(row["FCT"]),
            "AOTA": acc_val(row["AOTA"]),
        }
        best_task = max(accs, key=accs.get)
        worst_task = min(accs, key=accs.get)
        spread = accs[best_task] - accs[worst_task]
        profiles[model] = {
            "best_task": best_task,
            "best_acc": accs[best_task],
            "worst_task": worst_task,
            "worst_acc": accs[worst_task],
            "spread": round(spread, 1),
            "profile": "specialist" if spread > 50 else "balanced",
        }

    # Wrong count by model per task
    wrong_count = {task: {m: len(wrong_by_task.get(task, {}).get(m, set())) for m in models} for task in TASK_TYPES}

    # Hardest topics per task (topics where all models wrong)
    hardest_topics = {}
    for task in TASK_TYPES:
        wrong_all = set(overlap_by_task.get(task, {}).get("wrong_by_all", []))
        topic_to_ids = defaultdict(list)
        for qid in wrong_all:
            topic_to_ids[id_to_topic.get(qid, "Other")].append(qid)
        hardest_topics[task] = [
            {"topic": t, "wrong_count": len(ids), "ids": sorted(ids)}
            for t, ids in sorted(topic_to_ids.items(), key=lambda x: -len(x[1]))
        ][:15]

    report = {
        "accuracy_table": accuracy_table,
        "model_performance_profiles": profiles,
        "rankings": rankings,
        "wrong_count_by_task": wrong_count,
        "overlap_by_task": overlap_by_task,
        "hardest_topics_by_task": hardest_topics,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_JSON}")

    # Markdown
    lines = [
        "# 400q Diabetes Benchmark – Model Comparison",
        "",
        "**295 questions: 65 NOTA + 100 FQT + 65 FCT + 65 AOTA. 5 models.**",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT | AOTA |",
        "|-------|---------|------|-----|-----|------|",
    ]
    for row in accuracy_table:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} | {row['AOTA']} |")

    lines.extend(["", "## Model Performance Profiles", ""])
    for m, p in profiles.items():
        lines.append(f"- **{m}**: Best at {p['best_task']} ({p['best_acc']:.1f}%), worst at {p['worst_task']} ({p['worst_acc']:.1f}%). Spread: {p['spread']:.1f}% ({p['profile']})")
    lines.append("")

    for task in TASK_TYPES:
        lines.extend(["", f"## {task} Ranking (best first)", ""])
        for i, m in enumerate(rankings[task], 1):
            lines.append(f"{i}. {m}")
        lines.extend(["", f"## {task} Deep Dive", "", "### Wrong count by model", ""])
        for m in models:
            cnt = wrong_count[task].get(m, 0)
            lines.append(f"- **{m}**: {cnt} {task} wrong")
        lines.extend(["", "### Overlap: questions wrong by N models", ""])
        overlap = overlap_by_task.get(task, {})
        n_models = len(models)
        for c in range(n_models, 0, -1):
            key = "wrong_by_all" if c == n_models else f"wrong_by_{c}"
            ids = overlap.get(key, [])
            label = "All models" if c == n_models else f"{c} models"
            lines.append(f"- **{label}** ({len(ids)}): " + (", ".join(ids[:15]) + ("..." if len(ids) > 15 else "")))
        lines.extend(["", "### Hardest topics (all models wrong)", ""])
        for ht in hardest_topics.get(task, [])[:10]:
            lines.append(f"- **{ht['topic']}** ({len(ht['ids'])}): " + ", ".join(ht["ids"][:5]) + ("..." if len(ht["ids"]) > 5 else ""))
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
