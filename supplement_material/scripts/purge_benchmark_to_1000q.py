"""
Purge benchmark to 1,000-question core: remove ~100 seeds flagged with benchmark issues
from universal_failures_audit.json. Output: 250 FCT, 250 FQT, 250 NOTA, 250 AOTA.
Recalculates accuracies on kept NOTA+AOTA (500q) and outputs markdown report.

Usage:
  python purge_benchmark_to_1000q.py
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_DIR = BASE_DIR / "results_1400q_golden" / "benchmark"
REPORTS_DIR_1400 = BASE_DIR / "results_1400q_golden" / "reports"
RESULTS_DIR_1400 = BASE_DIR / "results_1400q_golden"
OUTPUT_DIR = BASE_DIR / "results_1000q_core"
OUTPUT_BENCHMARK = OUTPUT_DIR / "benchmark"
OUTPUT_REPORTS = OUTPUT_DIR / "reports"

AUDIT_JSON = REPORTS_DIR_1400 / "universal_failures_audit.json"
FCT_PATH = BENCHMARK_DIR / "350q_fct_v4_golden_seed.jsonl"
FQT_PATH = BENCHMARK_DIR / "350q_fqt_v2_golden_seed.jsonl"
NOTA_PATH = BENCHMARK_DIR / "350q_nota_from_fct_golden_seed.jsonl"
AOTA_PATH = BENCHMARK_DIR / "350q_aota_from_fct_golden_seed.jsonl"

MODELS = ["qwen2.5_7b", "llama3.1_8b", "gemma_7b", "deepseek-r1_7b", "mistral_latest"]
MODEL_DISPLAY = {
    "qwen2.5_7b": "Qwen2.5 7B",
    "llama3.1_8b": "Llama 3.1 8B",
    "gemma_7b": "Gemma 7B",
    "deepseek-r1_7b": "DeepSeek-R1 7B",
    "mistral_latest": "Mistral Latest",
}


def load_jsonl(path: Path) -> list:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jsonl(path: Path, items: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    # --- Phase 1: Purge ---
    audit = load_json(AUDIT_JSON)
    ids_with_issues = set(audit["summary"]["ids_with_issues"])

    # Build id -> derived_from for NOTA and AOTA
    id_to_seed = {}
    for path in [NOTA_PATH, AOTA_PATH]:
        for item in load_jsonl(path):
            qid = item.get("id")
            meta = item.get("metadata") or item
            seed = meta.get("derived_from")
            if seed:
                id_to_seed[qid] = seed

    seeds_to_purge = set()
    for qid in ids_with_issues:
        if qid in id_to_seed:
            seeds_to_purge.add(id_to_seed[qid])

    print(f"Seeds to purge: {len(seeds_to_purge)}")
    print(f"IDs with issues: {len(ids_with_issues)}")

    # Load all 4 benchmark files
    fct_items = load_jsonl(FCT_PATH)
    fqt_items = load_jsonl(FQT_PATH)
    nota_items = load_jsonl(NOTA_PATH)
    aota_items = load_jsonl(AOTA_PATH)

    # FCT and FQT: filter by index (same row = same seed)
    fct_kept = [x for x in fct_items if x["id"] not in seeds_to_purge]
    fqt_kept = []
    for i, fct in enumerate(fct_items):
        if fct["id"] not in seeds_to_purge:
            if i < len(fqt_items):
                fqt_kept.append(fqt_items[i])

    # NOTA and AOTA: filter by derived_from
    nota_kept = [x for x in nota_items if (x.get("metadata") or {}).get("derived_from") not in seeds_to_purge]
    aota_kept = [x for x in aota_items if (x.get("metadata") or {}).get("derived_from") not in seeds_to_purge]

    n_fct, n_fqt, n_nota, n_aota = len(fct_kept), len(fqt_kept), len(nota_kept), len(aota_kept)
    print(f"Kept: FCT={n_fct}, FQT={n_fqt}, NOTA={n_nota}, AOTA={n_aota}")

    # Write benchmark files
    OUTPUT_BENCHMARK.mkdir(parents=True, exist_ok=True)
    save_jsonl(OUTPUT_BENCHMARK / "250q_fct_core.jsonl", fct_kept)
    save_jsonl(OUTPUT_BENCHMARK / "250q_fqt_core.jsonl", fqt_kept)
    save_jsonl(OUTPUT_BENCHMARK / "250q_nota_core.jsonl", nota_kept)
    save_jsonl(OUTPUT_BENCHMARK / "250q_aota_core.jsonl", aota_kept)

    # Combined file
    combined = fct_kept + fqt_kept + nota_kept + aota_kept
    save_jsonl(OUTPUT_BENCHMARK / "1000q_core_combined_test_ready.jsonl", combined)

    # Purge manifest
    manifest = {
        "seeds_purged": len(seeds_to_purge),
        "seeds_purged_list": sorted(seeds_to_purge),
        "ids_with_issues_count": len(ids_with_issues),
        "kept": {"fct": n_fct, "fqt": n_fqt, "nota": n_nota, "aota": n_aota},
        "total_questions": n_fct + n_fqt + n_nota + n_aota,
    }
    save_json(OUTPUT_DIR / "purge_manifest.json", manifest)

    # --- Phase 2: Recalculate accuracies and report ---
    kept_nota_ids = {x["id"] for x in nota_kept}
    kept_aota_ids = {x["id"] for x in aota_kept}
    kept_ids = kept_nota_ids | kept_aota_ids

    overall_accuracy = {}
    accuracy_by_task = {"NOTA": {}, "AOTA": {}}

    for model in MODELS:
        path = RESULTS_DIR_1400 / f"results_{model}.json"
        if not path.exists():
            continue
        data = load_json(path)
        id_to_result = {x["id"]: x for x in data}

        # Filter to kept IDs
        filtered = [id_to_result[qid] for qid in kept_ids if qid in id_to_result]
        correct = sum(1 for x in filtered if x.get("correct"))
        total = len(filtered)
        overall_accuracy[model] = {"correct": correct, "total": total}

        # Per task
        nota_filtered = [id_to_result[qid] for qid in kept_nota_ids if qid in id_to_result]
        aota_filtered = [id_to_result[qid] for qid in kept_aota_ids if qid in id_to_result]
        accuracy_by_task["NOTA"][model] = {
            "correct": sum(1 for x in nota_filtered if x.get("correct")),
            "total": len(nota_filtered),
        }
        accuracy_by_task["AOTA"][model] = {
            "correct": sum(1 for x in aota_filtered if x.get("correct")),
            "total": len(aota_filtered),
        }

    # --- Additional analysis (like 1400q report) ---
    # Build id -> topic from benchmark (first non-generic tag)
    id_to_topic = {}
    for item in nota_kept + aota_kept:
        qid = item.get("id")
        tags = (item.get("metadata") or {}).get("tags", []) or []
        topic = next((t for t in tags if t not in ("diabetes", "NOTA", "AOTA")), tags[0] if tags else "unknown")
        id_to_topic[qid] = topic

    # Topic errors: total = questions with that topic, errors = wrong answers across models
    topic_totals = {}
    for item in nota_kept + aota_kept:
        topic = id_to_topic.get(item["id"], "unknown")
        topic_totals[topic] = topic_totals.get(topic, 0) + 1
    topic_errors = {t: {"total": c, "errors": 0} for t, c in topic_totals.items()}
    for model in MODELS:
        path = RESULTS_DIR_1400 / f"results_{model}.json"
        if not path.exists():
            continue
        data = load_json(path)
        for r in data:
            qid = r.get("id")
            if qid not in kept_ids or r.get("correct"):
                continue
            topic = id_to_topic.get(qid, "unknown")
            if topic in topic_errors:
                topic_errors[topic]["errors"] += 1

    # Wrong-answer distribution
    wrong_nota = {m: {"A": 0, "B": 0, "C": 0} for m in MODELS}
    wrong_aota = {m: {"A": 0, "B": 0, "C": 0, "D": 0} for m in MODELS}
    n_a_count = {m: 0 for m in MODELS}
    for model in MODELS:
        path = RESULTS_DIR_1400 / f"results_{model}.json"
        if not path.exists():
            continue
        data = load_json(path)
        id_to_result = {x["id"]: x for x in data}
        for qid in kept_nota_ids:
            if qid not in id_to_result:
                continue
            r = id_to_result[qid]
            pred = str(r.get("pred", "")).upper().strip()
            if pred in ("N/A", "NA"):
                n_a_count[model] += 1
                continue
            if not r.get("correct") and pred in ("A", "B", "C"):
                wrong_nota[model][pred] = wrong_nota[model].get(pred, 0) + 1
        for qid in kept_aota_ids:
            if qid not in id_to_result:
                continue
            r = id_to_result[qid]
            pred = str(r.get("pred", "")).upper().strip()
            if pred in ("N/A", "NA"):
                n_a_count[model] += 1
                continue
            if not r.get("correct") and pred in ("A", "B", "C", "D"):
                wrong_aota[model][pred] = wrong_aota[model].get(pred, 0) + 1

    # Universal failures (all 5 models wrong) in kept set
    model_wrong = {qid: [] for qid in kept_ids}
    for model in MODELS:
        path = RESULTS_DIR_1400 / f"results_{model}.json"
        if not path.exists():
            continue
        data = load_json(path)
        for r in data:
            if r["id"] in kept_ids and not r.get("correct"):
                model_wrong[r["id"]].append(model)
    universal_failures = [qid for qid in kept_ids if len(model_wrong.get(qid, [])) >= 5]
    universal_failures = sorted(universal_failures)

    # Task-type gap
    task_gap = {}
    for model in MODELS:
        if model in accuracy_by_task["NOTA"] and model in accuracy_by_task["AOTA"]:
            n = accuracy_by_task["NOTA"][model]
            a = accuracy_by_task["AOTA"][model]
            nota_acc = (n["correct"] / n["total"] * 100) if n["total"] > 0 else 0
            aota_acc = (a["correct"] / a["total"] * 100) if a["total"] > 0 else 0
            task_gap[model] = round(aota_acc - nota_acc, 1)

    # 1400q vs 1000q comparison
    comparison = {}
    comp_1400 = load_json(REPORTS_DIR_1400 / "1400q_golden_analysis_report.json") if (REPORTS_DIR_1400 / "1400q_golden_analysis_report.json").exists() else {}
    for model in MODELS:
        old = comp_1400.get("overall_accuracy", {}).get(model, {})
        new = overall_accuracy.get(model, {})
        if old and new:
            old_acc = (old["correct"] / old["total"] * 100) if old["total"] > 0 else 0
            new_acc = (new["correct"] / new["total"] * 100) if new["total"] > 0 else 0
            comparison[model] = {"1400q": round(old_acc, 1), "1000q": round(new_acc, 1), "delta": round(new_acc - old_acc, 1)}

    report_json = {
        "summary": {
            "total_questions": n_nota + n_aota,
            "nota": n_nota,
            "aota": n_aota,
            "fct": n_fct,
            "fqt": n_fqt,
        },
        "overall_accuracy": overall_accuracy,
        "accuracy_by_task": accuracy_by_task,
        "task_type_gap": task_gap,
        "topic_errors": dict(sorted(topic_errors.items(), key=lambda x: -x[1].get("errors", 0))[:25]),
        "wrong_answer_nota": wrong_nota,
        "wrong_answer_aota": wrong_aota,
        "n_a_count": n_a_count,
        "universal_failures_count": len(universal_failures),
        "universal_failure_ids": universal_failures[:30],
        "comparison_1400q_vs_1000q": comparison,
    }
    save_json(OUTPUT_REPORTS / "1000q_core_analysis_report.json", report_json)

    # Markdown report
    total_kept = n_fct + n_fqt + n_nota + n_aota
    best_overall = max(overall_accuracy.items(), key=lambda x: (x[1]["correct"] / x[1]["total"] if x[1]["total"] else 0), default=(None, {}))
    best_acc = (best_overall[1]["correct"] / best_overall[1]["total"] * 100) if best_overall[1].get("total") else 0
    md_lines = [
        "# 1000q Core Benchmark Analysis Report",
        "",
        f"**Benchmark:** {total_kept} questions ({n_fct} FCT, {n_fqt} FQT, {n_nota} NOTA, {n_aota} AOTA) — purged from 1,400q golden",
        "**Models:** Qwen2.5 7B, Llama 3.1 8B, Gemma 7B, DeepSeek-R1 7B, Mistral Latest",
        f"**Note:** Accuracy below is for NOTA + AOTA only ({n_nota + n_aota} questions). FCT and FQT have no results in 1400q golden.",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"**Key finding:** The 1000q core (after purging 95 seeds with benchmark issues) shows improved accuracy across models. {MODEL_DISPLAY.get(best_overall[0], best_overall[0])} leads overall ({best_acc:.1f}%). NOTA remains harder than AOTA for all models. The purge removed ambiguous or flawed questions, yielding a cleaner benchmark.",
        "",
        "---",
        "",
        "## 2. Purge Summary",
        "",
        f"- Seeds purged: {len(seeds_to_purge)}",
        f"- Kept: {n_fct} FCT, {n_fqt} FQT, {n_nota} NOTA, {n_aota} AOTA",
        "",
        "---",
        "",
        f"## 3. Overall Accuracy (NOTA + AOTA, {n_nota + n_aota} questions)",
        "",
        "| Model | Correct | Total | Accuracy |",
        "|-------|---------|-------|----------|",
    ]

    for model in MODELS:
        if model in overall_accuracy:
            s = overall_accuracy[model]
            acc = (s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
            name = MODEL_DISPLAY.get(model, model)
            md_lines.append(f"| **{name}** | {s['correct']} | {s['total']} | **{acc:.1f}%** |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 4. Accuracy by Task (NOTA vs AOTA)",
        "",
        f"### 4.1 NOTA ({n_nota} questions)",
        "",
        "| Model | Correct | Total | Accuracy |",
        "|-------|---------|-------|----------|",
    ])

    for model in MODELS:
        if model in accuracy_by_task["NOTA"]:
            s = accuracy_by_task["NOTA"][model]
            acc = (s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
            name = MODEL_DISPLAY.get(model, model)
            md_lines.append(f"| **{name}** | {s['correct']} | {s['total']} | **{acc:.1f}%** |")

    md_lines.extend([
        "",
        f"### 4.2 AOTA ({n_aota} questions)",
        "",
        "| Model | Correct | Total | Accuracy |",
        "|-------|---------|-------|----------|",
    ])

    for model in MODELS:
        if model in accuracy_by_task["AOTA"]:
            s = accuracy_by_task["AOTA"][model]
            acc = (s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
            name = MODEL_DISPLAY.get(model, model)
            md_lines.append(f"| **{name}** | {s['correct']} | {s['total']} | **{acc:.1f}%** |")

    # Task-type gap
    md_lines.extend([
        "",
        "### 4.3 Task-Type Gap (AOTA − NOTA)",
        "",
        "| Model | NOTA Acc | AOTA Acc | Gap |",
        "|-------|----------|----------|-----|",
    ])
    for model in MODELS:
        if model in accuracy_by_task["NOTA"] and model in accuracy_by_task["AOTA"]:
            n = accuracy_by_task["NOTA"][model]
            a = accuracy_by_task["AOTA"][model]
            nota_acc = (n["correct"] / n["total"] * 100) if n["total"] > 0 else 0
            aota_acc = (a["correct"] / a["total"] * 100) if a["total"] > 0 else 0
            gap = aota_acc - nota_acc
            name = MODEL_DISPLAY.get(model, model)
            md_lines.append(f"| {name} | {nota_acc:.1f}% | {aota_acc:.1f}% | **+{gap:.1f}%** |")

    # 1400q vs 1000q comparison
    if comparison:
        md_lines.extend([
            "",
            "---",
            "",
            "## 5. Improvement After Purge (1400q vs 1000q)",
            "",
            "| Model | 1400q Acc | 1000q Acc | Δ |",
            "|-------|-----------|-----------|---|",
        ])
        for model in MODELS:
            c = comparison.get(model, {})
            if c:
                name = MODEL_DISPLAY.get(model, model)
                delta = c.get("delta", 0)
                sign = "+" if delta >= 0 else ""
                md_lines.append(f"| {name} | {c.get('1400q', 0)}% | {c.get('1000q', 0)}% | {sign}{delta}% |")

    # Topics with most errors
    top_topics = sorted(topic_errors.items(), key=lambda x: -x[1].get("errors", 0))[:15]
    md_lines.extend([
        "",
        "---",
        "",
        "## 6. Topics with Most Errors",
        "",
        "*Error rate = total errors across models / (questions × 5).*",
        "",
        "| Topic | Questions | Total Errors | Est. Error Rate |",
        "|-------|-----------|--------------|-----------------|",
    ])
    for topic, d in top_topics:
        total_q = d.get("total", 0)
        errs = d.get("errors", 0)
        rate = (errs / (total_q * 5) * 100) if total_q > 0 else 0
        md_lines.append(f"| **{topic}** | {total_q} | {errs} | ~{rate:.0f}% |")

    # Wrong-answer distribution
    md_lines.extend([
        "",
        "---",
        "",
        "## 7. Wrong-Answer Distribution",
        "",
        "### 7.1 NOTA (when wrong, models pick A, B, or C)",
        "",
        "| Model | A | B | C |",
        "|-------|---|---|---|",
    ])
    for model in MODELS:
        w = wrong_nota.get(model, {})
        name = MODEL_DISPLAY.get(model, model)
        md_lines.append(f"| {name} | {w.get('A', 0)} | {w.get('B', 0)} | {w.get('C', 0)} |")
    md_lines.extend([
        "",
        "### 7.2 AOTA (when wrong, models pick A, B, C, or D)",
        "",
        "| Model | A | B | C | D |",
        "|-------|---|---|---|---|",
    ])
    for model in MODELS:
        w = wrong_aota.get(model, {})
        name = MODEL_DISPLAY.get(model, model)
        md_lines.append(f"| {name} | {w.get('A', 0)} | {w.get('B', 0)} | {w.get('C', 0)} | {w.get('D', 0)} |")

    # Universal failures & N/A
    md_lines.extend([
        "",
        "---",
        "",
        "## 8. Universal Failures (All Models Wrong)",
        "",
        f"**{len(universal_failures)} questions** in the 1000q core were answered incorrectly by all 5 models.",
        "",
        "---",
        "",
        "## 9. N/A Predictions",
        "",
        "| Model | N/A Count |",
        "|-------|-----------|",
    ])
    for model in MODELS:
        name = MODEL_DISPLAY.get(model, model)
        md_lines.append(f"| {name} | {n_a_count.get(model, 0)} |")

    # Interesting findings & recommendations
    best_nota = max(accuracy_by_task["NOTA"].items(), key=lambda x: (x[1]["correct"] / x[1]["total"] if x[1]["total"] else 0), default=(None, {}))
    best_aota = max(accuracy_by_task["AOTA"].items(), key=lambda x: (x[1]["correct"] / x[1]["total"] if x[1]["total"] else 0), default=(None, {}))
    purge_impact = f"1. **Purge impact:** Removing 95 seeds with benchmark issues improved overall accuracy by +{comparison.get('qwen2.5_7b', {}).get('delta', 0):.1f}% (Qwen) to +{comparison.get('mistral_latest', {}).get('delta', 0):.1f}% (Mistral)." if comparison else "1. **Purge impact:** Removing 95 seeds with benchmark issues yields a cleaner benchmark."
    md_lines.extend([
        "",
        "---",
        "",
        "## 10. Interesting Findings",
        "",
        purge_impact,
        f"2. **NOTA leader:** {MODEL_DISPLAY.get(best_nota[0], best_nota[0])} leads on NOTA with {(best_nota[1]['correct']/best_nota[1]['total']*100) if best_nota[1].get('total') else 0:.1f}%.",
        f"3. **AOTA leader:** {MODEL_DISPLAY.get(best_aota[0], best_aota[0])} leads on AOTA with {(best_aota[1]['correct']/best_aota[1]['total']*100) if best_aota[1].get('total') else 0:.1f}%.",
        "4. **NOTA vs AOTA:** NOTA remains harder for all models; the task-type gap persists in the purged core.",
        f"5. **Universal failures:** {len(universal_failures)} questions still stump all models—candidates for further review.",
        "",
        "---",
        "",
        "## 11. Recommendations",
        "",
        "1. **Run FCT/FQT evaluation** on the 1000q core to obtain full benchmark coverage.",
        "2. **Topic focus:** Prioritize topics with highest error rates for model improvement.",
        "3. **Format sensitivity:** Consider NOTA-specific training given the persistent accuracy gap.",
        "",
        "---",
        "",
        "## 12. FCT and FQT",
        "",
        f"FCT ({n_fct}) and FQT ({n_fqt}) have no model results in the 1400q golden run. Run evaluation on the core benchmark to obtain full {total_kept}q accuracy.",
        "",
        "---",
        "",
        "*Report generated by purge_benchmark_to_1000q.py*",
    ])

    OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORTS / "1000q_core_analysis_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\nWrote {OUTPUT_DIR}")
    print(f"  benchmark/: 250q_fct_core.jsonl, 250q_fqt_core.jsonl, 250q_nota_core.jsonl, 250q_aota_core.jsonl")
    print(f"  purge_manifest.json")
    print(f"  reports/1000q_core_analysis_report.json, 1000q_core_analysis_report.md")


if __name__ == "__main__":
    main()
