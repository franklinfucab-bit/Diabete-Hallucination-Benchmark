"""
Generate 400q horizontal comparison: 300q (NOTA, FQT, FCT) + 100q AOTA Correct from FCT.
Output: 400q_horizontal_comparison_ds_api_修正.json and .md
"""
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_300Q = BASE_DIR / "300q results"
REPORTS_DIR = RESULTS_300Q / "reports"
AOTA_RESULTS = BASE_DIR / "100q AOTA Correct from FCT" / "results_100q_aota_correct"

MODELS_5 = ["deepseek-r1_7b", "gemma_7b", "llama3.1_8b", "mistral_latest", "qwen2.5_7b"]


def load_300q_report() -> dict:
    """Load 300q 修正 report (5 models, no deepseek_chat). Prefer filename containing revised/修正."""
    best = None
    for p in sorted(REPORTS_DIR.glob("300q*.json")):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "nota_unexpected" not in data or "fct_unexpected" not in data:
            continue
        models = [r["model"] for r in data.get("accuracy_table", [])]
        if set(MODELS_5).issubset(set(models)) and "deepseek_chat" not in models:
            return data
        if best is None:
            best = data
    if best:
        return best
    raise FileNotFoundError("300q 修正 report not found")


def load_aota_stats() -> dict:
    path = AOTA_RESULTS / "100q_aota_stats.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_aota_raw_results() -> dict:
    raw = {}
    for model in MODELS_5:
        path = AOTA_RESULTS / f"results_{model}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw[model] = json.load(f)
    return raw


def build_aota_deep_dive(aota_stats: dict, raw_results: dict) -> dict:
    wrong_ids_by_model = {}
    for model, items in raw_results.items():
        wrong = [r["id"] for r in items if not r.get("correct", True)]
        wrong_ids_by_model[model] = wrong
    wrong_count_by_model = {m: len(ids) for m, ids in wrong_ids_by_model.items()}
    id_to_models = defaultdict(set)
    for m, ids in wrong_ids_by_model.items():
        for qid in ids:
            id_to_models[qid].add(m)
    n_models = len(MODELS_5)
    overlap = {"wrong_by_all": []}
    for c in range(1, n_models):
        overlap[f"wrong_by_{c}"] = []
    for qid, model_set in id_to_models.items():
        c = len(model_set)
        if c == n_models:
            overlap["wrong_by_all"].append(qid)
        else:
            overlap[f"wrong_by_{c}"].append(qid)
    for k in overlap:
        overlap[k].sort()
    pred_vs_label_by_model = {}
    for model, items in raw_results.items():
        counts = defaultdict(int)
        for item in items:
            if item.get("correct", True):
                continue
            pred, label = item.get("pred", "?"), item.get("label", "?")
            counts[f"{pred}->{label}"] += 1
        pred_vs_label_by_model[model] = dict(sorted(counts.items(), key=lambda x: -x[1]))
    return {
        "wrong_count_by_model": wrong_count_by_model,
        "wrong_ids_by_model": wrong_ids_by_model,
        "overlap": overlap,
        "topics_by_model_count": [],
        "pred_vs_label_by_model": pred_vs_label_by_model,
    }


def build_aota_unexpected(wrong_ids_by_model: dict, aota_ranking: list) -> dict:
    wrong_set_by_model = {m: set(ids) for m, ids in wrong_ids_by_model.items()}
    n_models = len(MODELS_5)
    consensus_wrong, best_model_failures, worst_model_succeeds = [], [], []
    best_model = aota_ranking[0] if aota_ranking else None
    worst_model = aota_ranking[-1] if aota_ranking else None
    all_wrong_ids = set()
    for ids in wrong_ids_by_model.values():
        all_wrong_ids.update(ids)
    for qid in all_wrong_ids:
        if not qid.startswith("AOTA_"):
            continue
        models_wrong = {m for m in MODELS_5 if m in wrong_set_by_model and qid in wrong_set_by_model[m]}
        n_wrong = len(models_wrong)
        if n_wrong == n_models:
            consensus_wrong.append(qid)
        elif best_model and best_model in models_wrong and n_wrong < n_models:
            best_model_failures.append(qid)
        elif worst_model and worst_model not in models_wrong and n_wrong > 0:
            worst_model_succeeds.append(qid)
    return {"consensus_wrong": sorted(consensus_wrong), "best_model_failures": sorted(best_model_failures), "worst_model_succeeds": sorted(worst_model_succeeds)}


def build_400q_report(report_300q: dict, aota_stats: dict, aota_raw: dict) -> dict:
    report = report_300q.copy()
    accuracy_table = []
    for row in report["accuracy_table"]:
        model = row["model"]
        nota_val = float(str(row["NOTA"]).rstrip("%"))
        fqt_val = float(str(row["FQT"]).rstrip("%"))
        fct_val = float(str(row["FCT"]).rstrip("%"))
        aota_model = aota_stats["models"].get(model, {})
        aota_correct = aota_model.get("correct", 0)
        aota_total = aota_model.get("total", 100)
        aota_acc = (aota_correct / aota_total * 100) if aota_total > 0 else 0
        nota_correct = int(nota_val)
        fqt_correct = int(fqt_val)
        fct_correct = int(fct_val)
        total_correct = nota_correct + fqt_correct + fct_correct + aota_correct
        overall_acc = (total_correct / 400 * 100) if 400 > 0 else 0
        accuracy_table.append({
            "model": model,
            "overall": f"{overall_acc:.1f}%",
            "NOTA": row["NOTA"],
            "FQT": row["FQT"],
            "FCT": row["FCT"],
            "AOTA": f"{aota_acc:.1f}%",
        })
    report["accuracy_table"] = accuracy_table

    def acc_val(row, col):
        return float(str(row[col]).rstrip("%"))

    aota_ranking = [r["model"] for r in sorted(accuracy_table, key=lambda r: acc_val(r, "AOTA"), reverse=True)]
    report["aota_ranking"] = aota_ranking
    aota_deep_dive = build_aota_deep_dive(aota_stats, aota_raw)
    report["aota_deep_dive"] = aota_deep_dive
    report["aota_summary"] = {
        "best_model": aota_ranking[0] if aota_ranking else None,
        "worst_model": aota_ranking[-1] if aota_ranking else None,
        "wrong_by_all_count": len(aota_deep_dive["overlap"]["wrong_by_all"]),
        "wrong_by_all_ids": aota_deep_dive["overlap"]["wrong_by_all"],
        "wrong_by_1_count": len(aota_deep_dive["overlap"].get("wrong_by_1", [])),
        "wrong_by_1_ids": aota_deep_dive["overlap"].get("wrong_by_1", []),
    }
    report["aota_unexpected"] = build_aota_unexpected(aota_deep_dive["wrong_ids_by_model"], aota_ranking)
    profiles = {}
    for row in accuracy_table:
        model = row["model"]
        accs = {"NOTA": acc_val(row, "NOTA"), "FQT": acc_val(row, "FQT"), "FCT": acc_val(row, "FCT"), "AOTA": acc_val(row, "AOTA")}
        best_task = max(accs, key=accs.get)
        worst_task = min(accs, key=accs.get)
        spread = accs[best_task] - accs[worst_task]
        profiles[model] = {"best_task": best_task, "best_acc": accs[best_task], "worst_task": worst_task, "worst_acc": accs[worst_task], "spread": round(spread, 1), "profile": "specialist" if spread > 50 else "balanced"}
    report["model_performance_profiles"] = profiles
    return report


def write_md_400q(report: dict, out_path: Path) -> None:
    lines = [
        "# 400q Horizontal Comparison 修正 (Overall: NOTA, FQT, FCT, AOTA)",
        "",
        "**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q; AOTA = 100q AOTA Correct from FCT. 5 models.**",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT | AOTA |",
        "|-------|---------|------|-----|-----|------|",
    ]
    for row in report["accuracy_table"]:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} | {row['AOTA']} |")
    if "model_performance_profiles" in report:
        lines.extend(["", "## Model Performance Profiles", ""])
        for m, p in report["model_performance_profiles"].items():
            lines.append(f"- **{m}**: Best at {p['best_task']} ({p['best_acc']:.1f}%), worst at {p['worst_task']} ({p['worst_acc']:.1f}%). Spread: {p['spread']:.1f}% ({p['profile']})")
        lines.append("")

    def _write_type_section(type_name: str):
        deep_dive = report[f"{type_name.lower()}_deep_dive"]
        summary = report[f"{type_name.lower()}_summary"]
        unexpected = report[f"{type_name.lower()}_unexpected"]
        lines.extend(["", f"## {type_name} Ranking (best first)", ""])
        for i, m in enumerate(report[f"{type_name.lower()}_ranking"], 1):
            lines.append(f"{i}. {m}")
        lines.extend(["", f"## {type_name} Deep Dive", "", "### Wrong count by model", ""])
        if "pred_vs_label_by_model" in deep_dive:
            lines.extend(["", "### When wrong, what did models choose? (pred->label)", ""])
            for m, pvl in deep_dive["pred_vs_label_by_model"].items():
                parts = [f"{k}: {v}" for k, v in list(pvl.items())[:8]]
                lines.append(f"- **{m}**: " + ", ".join(parts) + (" ..." if len(pvl) > 8 else ""))
            lines.append("")
        for m, c in deep_dive["wrong_count_by_model"].items():
            lines.append(f"- **{m}**: {c} {type_name} wrong")
        lines.extend(["", f"### Overlap: {type_name} questions wrong by N models", ""])
        lines.append(f"- **All models** ({len(deep_dive['overlap']['wrong_by_all'])}): ")
        ids = deep_dive["overlap"]["wrong_by_all"]
        if ids:
            lines.append("  " + ", ".join(ids[:20]) + (" ..." if len(ids) > 20 else ""))
        other_keys = sorted((k for k in deep_dive["overlap"] if k != "wrong_by_all"), key=lambda k: -int(k.split("_")[-1]))
        for k in other_keys:
            ids = deep_dive["overlap"][k]
            lines.append(f"- **{k}** ({len(ids)}): " + (", ".join(ids[:15]) + (" ..." if len(ids) > 15 else "") if ids else "(none)"))
        if deep_dive.get("topics_by_model_count"):
            lines.extend(["", f"### Hardest {type_name} topics", ""])
            for t in deep_dive["topics_by_model_count"][:15]:
                lines.append(f"- **{t['topic']}** ({t['models_wrong']} models): {', '.join(t['ids'][:5])}{' ...' if len(t['ids']) > 5 else ''}")
        lines.extend(["", f"## {type_name} Summary", ""])
        lines.append(f"- Best on {type_name}: **{summary['best_model']}**")
        lines.append(f"- Worst on {type_name}: **{summary['worst_model']}**")
        lines.append(f"- {type_name} questions wrong by all models: {summary['wrong_by_all_count']}")
        lines.append(f"- {type_name} questions wrong by only 1 model: {summary['wrong_by_1_count']}")
        lines.extend(["", f"## {type_name} Unexpected Results", ""])
        cw, bf, ws = unexpected["consensus_wrong"], unexpected["best_model_failures"], unexpected["worst_model_succeeds"]
        lines.append(f"- **Consensus wrong** ({len(cw)}): " + (", ".join(cw[:15]) + (" ..." if len(cw) > 15 else "") if cw else "(none)"))
        lines.append(f"- **Best model failures** ({len(bf)}): " + (", ".join(bf[:15]) + (" ..." if len(bf) > 15 else "") if bf else "(none)"))
        lines.append(f"- **Worst model succeeds** ({len(ws)}): " + (", ".join(ws[:15]) + (" ..." if len(ws) > 15 else "") if ws else "(none)"))
        lines.append("")

    for type_name in ["NOTA", "FQT", "FCT", "AOTA"]:
        _write_type_section(type_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if not REPORTS_DIR.exists():
        print("Reports dir not found")
        return
    if not (AOTA_RESULTS / "100q_aota_stats.json").exists():
        print("AOTA stats not found. Run analyze_100q_aota_results.py --correct-from-fct first.")
        return
    report_300q = load_300q_report()
    aota_stats = load_aota_stats()
    aota_raw = load_aota_raw_results()
    report = build_400q_report(report_300q, aota_stats, aota_raw)
    json_path = REPORTS_DIR / "400q_horizontal_comparison_ds_api_revised.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Wrote 400q_horizontal_comparison_ds_api_revised.json")
    md_path = REPORTS_DIR / "400q_horizontal_comparison_ds_api_revised.md"
    write_md_400q(report, md_path)
    print("Wrote 400q_horizontal_comparison_ds_api_revised.md")
    print("\n400q Overall ranking:")
    for row in sorted(report["accuracy_table"], key=lambda r: float(str(r["overall"]).rstrip("%")), reverse=True):
        print(f"  {row['model']}: {row['overall']}")
    print("\nAOTA ranking:", report["aota_ranking"])


if __name__ == "__main__":
    main()
