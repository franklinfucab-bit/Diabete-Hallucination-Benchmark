"""
Generate 修正 (corrected) horizontal comparison: NOTA replaced with 100q NOTA (FCT-derived),
FQT and FCT from 300q. Output: 300q_horizontal_comparison_ds_api_修正.json and .md
Includes: pred_vs_label per task, model performance profiles, standalone FQT/FCT reports.
"""
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_300Q = BASE_DIR / "300q results"
REPORTS_DIR = RESULTS_300Q / "reports"
RESULTS_100Q_NOTA = BASE_DIR / "results_100q_nota"

# 5 models with 100q NOTA results (no deepseek_chat)
MODELS_5 = ["deepseek-r1_7b", "gemma_7b", "llama3.1_8b", "mistral_latest", "qwen2.5_7b"]

TYPE_PREFIXES = {"NOTA": "NOTA_", "FQT": "FQT_", "FCT": "FCT_"}


def load_raw_results(models: list) -> dict:
    """Load raw results_*.json for each model."""
    raw = {}
    for model in models:
        path = RESULTS_300Q / f"results_{model}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw[model] = json.load(f)
    return raw


def compute_pred_vs_label_by_task(raw_results: dict, type_prefix: str) -> dict:
    """For wrong answers of given type, aggregate pred->label counts per model."""
    out = {}
    for model, items in raw_results.items():
        counts = defaultdict(int)
        for item in items:
            if not item.get("id", "").startswith(type_prefix) or item.get("correct", True):
                continue
            pred = item.get("pred", "?")
            label = item.get("label", "?")
            counts[f"{pred}->{label}"] += 1
        out[model] = dict(sorted(counts.items(), key=lambda x: -x[1]))
    return out


def build_model_performance_profiles(accuracy_table: list) -> dict:
    """Build per-model profile: best/worst task, spread, specialist vs balanced."""
    profiles = {}
    for row in accuracy_table:
        model = row["model"]
        accs = {
            "NOTA": float(str(row["NOTA"]).rstrip("%")),
            "FQT": float(str(row["FQT"]).rstrip("%")),
            "FCT": float(str(row["FCT"]).rstrip("%")),
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
    return profiles


def load_300q_summaries() -> dict:
    """Load 300q summaries for the 5 models."""
    summaries = {}
    for model in MODELS_5:
        f1 = RESULTS_300Q / f"summary_{model}.json"
        f2 = RESULTS_300Q / f"300q_summary_{model}.json"
        path = f1 if f1.exists() else (f2 if f2.exists() else None)
        if path:
            with open(path, "r", encoding="utf-8") as fp:
                summaries[model] = json.load(fp)
    return summaries


def load_100q_nota_summaries() -> dict:
    """Load 100q NOTA summaries."""
    summaries = {}
    for f in RESULTS_100Q_NOTA.glob("summary_*.json"):
        model = f.stem.replace("summary_", "")
        if model in MODELS_5:
            with open(f, "r", encoding="utf-8") as fp:
                summaries[model] = json.load(fp)
    return summaries


def build_type_deep_dive(summaries: dict, models: list, type_name: str, type_prefix: str) -> dict:
    """Build wrong_ids, overlap, topics for a given type."""
    wrong_ids_by_model = {}
    for m in models:
        wrong = summaries[m].get("wrong_answers", {}).get("ids", [])
        type_wrong = [x for x in wrong if x.startswith(type_prefix)]
        wrong_ids_by_model[m] = type_wrong

    wrong_count_by_model = {m: len(ids) for m, ids in wrong_ids_by_model.items()}

    id_to_models = defaultdict(set)
    for m, ids in wrong_ids_by_model.items():
        for qid in ids:
            id_to_models[qid].add(m)

    n_models = len(models)
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

    topic_to_ids = defaultdict(list)
    topic_to_models = defaultdict(set)
    for m in models:
        by_topic = summaries[m].get("wrong_answers", {}).get("by_topic", {})
        for topic, ids in by_topic.items():
            type_ids = [x for x in ids if x.startswith(type_prefix)]
            if type_ids:
                for qid in type_ids:
                    topic_to_ids[topic].append(qid)
                    topic_to_models[topic].add(m)

    topics_by_model_count = []
    for topic, model_set in topic_to_models.items():
        ids = sorted(set(topic_to_ids[topic]))
        topics_by_model_count.append({
            "topic": topic,
            "models_wrong": len(model_set),
            "ids": ids,
        })
    topics_by_model_count.sort(key=lambda x: -x["models_wrong"])

    return {
        "wrong_count_by_model": wrong_count_by_model,
        "wrong_ids_by_model": wrong_ids_by_model,
        "overlap": overlap,
        "topics_by_model_count": topics_by_model_count,
    }


def build_unexpected(wrong_ids_by_model: dict, models: list, ranking: list, type_prefix: str) -> dict:
    """Build consensus_wrong, best_model_failures, worst_model_succeeds."""
    wrong_set_by_model = {m: set(ids) for m, ids in wrong_ids_by_model.items()}
    n_models = len(models)

    consensus_wrong = []
    best_model_failures = []
    worst_model_succeeds = []

    best_model = ranking[0] if ranking else None
    worst_model = ranking[-1] if ranking else None

    all_wrong_ids = set()
    for ids in wrong_ids_by_model.values():
        all_wrong_ids.update(ids)

    for qid in all_wrong_ids:
        if not qid.startswith(type_prefix):
            continue
        models_wrong = {m for m in models if qid in wrong_set_by_model.get(m, set())}
        n_wrong = len(models_wrong)

        if n_wrong == n_models:
            consensus_wrong.append(qid)
        elif best_model and best_model in models_wrong and n_wrong < n_models:
            best_model_failures.append(qid)
        elif worst_model and worst_model not in models_wrong and n_wrong > 0:
            worst_model_succeeds.append(qid)

    return {
        "consensus_wrong": sorted(consensus_wrong),
        "best_model_failures": sorted(best_model_failures),
        "worst_model_succeeds": sorted(worst_model_succeeds),
    }


def build_comparison_修正(summaries_300q: dict, summaries_100q: dict) -> dict:
    """Build comparison with NOTA from 100q, FQT/FCT from 300q."""
    models = [m for m in MODELS_5 if m in summaries_300q and m in summaries_100q]
    if not models:
        raise ValueError("No overlapping models between 300q and 100q NOTA")

    # Accuracy table: NOTA from 100q, FQT/FCT from 300q, overall recalculated
    accuracy_table = []
    for m in models:
        s300 = summaries_300q[m]
        s100 = summaries_100q[m]
        nota_correct = s100.get("overall", {}).get("correct", 0)
        nota_total = s100.get("overall", {}).get("total", 100)
        fqt_correct = s300.get("by_type", {}).get("FQT", {}).get("correct", 0)
        fct_correct = s300.get("by_type", {}).get("FCT", {}).get("correct", 0)

        total_correct = nota_correct + fqt_correct + fct_correct
        overall_acc = (total_correct / 300 * 100) if 300 > 0 else 0
        nota_acc = (nota_correct / nota_total * 100) if nota_total > 0 else 0
        fqt_acc = s300.get("by_type", {}).get("FQT", {}).get("accuracy", "0%")
        fct_acc = s300.get("by_type", {}).get("FCT", {}).get("accuracy", "0%")

        accuracy_table.append({
            "model": m,
            "overall": f"{overall_acc:.1f}%",
            "NOTA": f"{nota_acc:.1f}%",
            "FQT": fqt_acc if isinstance(fqt_acc, str) else f"{fqt_acc:.1f}%",
            "FCT": fct_acc if isinstance(fct_acc, str) else f"{fct_acc:.1f}%",
        })

    def acc_val(row, col):
        return float(str(row[col]).rstrip("%"))

    nota_ranking = sorted(accuracy_table, key=lambda r: acc_val(r, "NOTA"), reverse=True)
    fqt_ranking = sorted(accuracy_table, key=lambda r: acc_val(r, "FQT"), reverse=True)
    fct_ranking = sorted(accuracy_table, key=lambda r: acc_val(r, "FCT"), reverse=True)

    nota_ranking = [r["model"] for r in nota_ranking]
    fqt_ranking = [r["model"] for r in fqt_ranking]
    fct_ranking = [r["model"] for r in fct_ranking]

    report = {
        "accuracy_table": accuracy_table,
        "nota_ranking": nota_ranking,
        "fqt_ranking": fqt_ranking,
        "fct_ranking": fct_ranking,
    }

    # NOTA deep dive from 100q summaries
    nota_deep_dive = build_type_deep_dive(summaries_100q, models, "NOTA", "NOTA_")
    report["nota_deep_dive"] = nota_deep_dive
    report["nota_summary"] = {
        "best_model": nota_ranking[0] if nota_ranking else None,
        "worst_model": nota_ranking[-1] if nota_ranking else None,
        "wrong_by_all_count": len(nota_deep_dive["overlap"]["wrong_by_all"]),
        "wrong_by_all_ids": nota_deep_dive["overlap"]["wrong_by_all"],
        "wrong_by_1_count": len(nota_deep_dive["overlap"].get("wrong_by_1", [])),
        "wrong_by_1_ids": nota_deep_dive["overlap"].get("wrong_by_1", []),
    }
    report["nota_unexpected"] = build_unexpected(
        nota_deep_dive["wrong_ids_by_model"], models, nota_ranking, "NOTA_"
    )

    # FQT and FCT deep dives from 300q summaries
    raw_results = load_raw_results(models)
    for type_name, type_prefix in [("FQT", "FQT_"), ("FCT", "FCT_")]:
        deep_dive = build_type_deep_dive(summaries_300q, models, type_name, type_prefix)
        deep_dive["pred_vs_label_by_model"] = compute_pred_vs_label_by_task(raw_results, type_prefix)
        ranking = report[f"{type_name.lower()}_ranking"]
        overlap = deep_dive["overlap"]
        report[f"{type_name.lower()}_deep_dive"] = deep_dive
        report[f"{type_name.lower()}_summary"] = {
            "best_model": ranking[0] if ranking else None,
            "worst_model": ranking[-1] if ranking else None,
            "wrong_by_all_count": len(overlap["wrong_by_all"]),
            "wrong_by_all_ids": overlap["wrong_by_all"],
            "wrong_by_1_count": len(overlap.get("wrong_by_1", [])),
            "wrong_by_1_ids": overlap.get("wrong_by_1", []),
        }
        report[f"{type_name.lower()}_unexpected"] = build_unexpected(
            deep_dive["wrong_ids_by_model"], models, ranking, type_prefix
        )

    report["model_performance_profiles"] = build_model_performance_profiles(accuracy_table)
    return report


def _write_type_section(lines: list, report: dict, type_name: str) -> None:
    """Append deep dive and unexpected sections for one type."""
    deep_dive = report[f"{type_name.lower()}_deep_dive"]
    summary = report[f"{type_name.lower()}_summary"]
    unexpected = report[f"{type_name.lower()}_unexpected"]

    lines.extend(["", f"## {type_name} Ranking (best first)", ""])
    for i, m in enumerate(report[f"{type_name.lower()}_ranking"], 1):
        lines.append(f"{i}. {m}")
    lines.extend(["", f"## {type_name} Deep Dive", "", "### Wrong count by model", ""])
    # Prediction confusion (when wrong, what did models choose?)
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
    other_keys = sorted(
        (k for k in deep_dive["overlap"] if k != "wrong_by_all"),
        key=lambda k: -int(k.split("_")[-1]),
    )
    for k in other_keys:
        ids = deep_dive["overlap"][k]
        lines.append(f"- **{k}** ({len(ids)}): " + (", ".join(ids[:15]) + (" ..." if len(ids) > 15 else "") if ids else "(none)"))
    lines.extend(["", f"### Hardest {type_name} topics (by number of models that got them wrong)", ""])
    for t in deep_dive["topics_by_model_count"][:15]:
        lines.append(f"- **{t['topic']}** ({t['models_wrong']} models): {', '.join(t['ids'][:5])}{' ...' if len(t['ids']) > 5 else ''}")
    lines.extend(["", f"## {type_name} Summary", ""])
    lines.append(f"- Best on {type_name}: **{summary['best_model']}**")
    lines.append(f"- Worst on {type_name}: **{summary['worst_model']}**")
    lines.append(f"- {type_name} questions wrong by all models: {summary['wrong_by_all_count']}")
    lines.append(f"- {type_name} questions wrong by only 1 model: {summary['wrong_by_1_count']}")
    lines.extend(["", f"## {type_name} Unexpected Results", ""])
    cw = unexpected["consensus_wrong"]
    bf = unexpected["best_model_failures"]
    ws = unexpected["worst_model_succeeds"]
    lines.append(f"- **Consensus wrong** (all models wrong, {len(cw)}): " + (", ".join(cw[:15]) + (" ..." if len(cw) > 15 else "") if cw else "(none)"))
    lines.append(f"- **Best model failures** (top model wrong, others correct, {len(bf)}): " + (", ".join(bf[:15]) + (" ..." if len(bf) > 15 else "") if bf else "(none)"))
    lines.append(f"- **Worst model succeeds** (worst model correct, others wrong, {len(ws)}): " + (", ".join(ws[:15]) + (" ..." if len(ws) > 15 else "") if ws else "(none)"))
    lines.append("")


def write_md_修正(report: dict, out_path: Path) -> None:
    """Write 修正 Markdown report."""
    lines = [
        "# 300q Horizontal Comparison 修正 (Overall: NOTA, FQT, FCT)",
        "",
        "**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q. 5 models.**",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT |",
        "|-------|---------|------|-----|-----|",
    ]
    for row in report["accuracy_table"]:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} |")

    # Model Performance Profiles
    if "model_performance_profiles" in report:
        lines.extend(["", "## Model Performance Profiles", ""])
        for m, p in report["model_performance_profiles"].items():
            lines.append(f"- **{m}**: Best at {p['best_task']} ({p['best_acc']:.1f}%), worst at {p['worst_task']} ({p['worst_acc']:.1f}%). Spread: {p['spread']:.1f}% ({p['profile']})")
        lines.append("")

    for type_name in ["NOTA", "FQT", "FCT"]:
        _write_type_section(lines, report, type_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_standalone_type_report(report: dict, type_name: str, out_json: Path, out_md: Path) -> None:
    """Write standalone FQT or FCT report (like _nota)."""
    tn = type_name.lower()
    sub = {
        "accuracy_table": report["accuracy_table"],
        f"{tn}_ranking": report[f"{tn}_ranking"],
        f"{tn}_deep_dive": report[f"{tn}_deep_dive"],
        f"{tn}_summary": report[f"{tn}_summary"],
        f"{tn}_unexpected": report[f"{tn}_unexpected"],
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(sub, f, indent=2, ensure_ascii=False)
    # MD: header + accuracy table + type section only
    lines = [
        f"# 300q Horizontal Comparison 修正 ({type_name} Focus)",
        "",
        "**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q. 5 models.**",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT |",
        "|-------|---------|------|-----|-----|",
    ]
    for row in report["accuracy_table"]:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} |")
    _write_type_section(lines, report, type_name)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if not RESULTS_300Q.exists():
        print(f"300q results dir not found: {RESULTS_300Q}")
        return
    if not RESULTS_100Q_NOTA.exists():
        print(f"100q NOTA results dir not found: {RESULTS_100Q_NOTA}")
        return

    summaries_300q = load_300q_summaries()
    summaries_100q = load_100q_nota_summaries()

    models_300q = set(summaries_300q.keys())
    models_100q = set(summaries_100q.keys())
    overlap = models_300q & models_100q & set(MODELS_5)
    if not overlap:
        print("No overlapping models between 300q and 100q NOTA")
        return

    print(f"300q models: {list(summaries_300q.keys())}")
    print(f"100q NOTA models: {list(summaries_100q.keys())}")
    print(f"Overlap (5): {sorted(overlap)}")

    report = build_comparison_修正(summaries_300q, summaries_100q)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "300q_horizontal_comparison_ds_api_修正.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Wrote JSON (revised)")

    md_path = REPORTS_DIR / "300q_horizontal_comparison_ds_api_修正.md"
    write_md_修正(report, md_path)
    print("Wrote MD (revised)")

    # Standalone FQT and FCT reports
    for type_name in ["FQT", "FCT"]:
        tn = type_name.lower()
        write_standalone_type_report(
            report,
            type_name,
            REPORTS_DIR / f"300q_horizontal_comparison_ds_api_修正_{tn}.json",
            REPORTS_DIR / f"300q_horizontal_comparison_ds_api_修正_{tn}.md",
        )
        print(f"Wrote standalone {type_name} report")

    print("\nNOTA ranking (100q):", report["nota_ranking"])
    print("FQT ranking:", report["fqt_ranking"])
    print("FCT ranking:", report["fct_ranking"])
    print("NOTA unexpected - consensus wrong:", len(report["nota_unexpected"]["consensus_wrong"]))


if __name__ == "__main__":
    main()
