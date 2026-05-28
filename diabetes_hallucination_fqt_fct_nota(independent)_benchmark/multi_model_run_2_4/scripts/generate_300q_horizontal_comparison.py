"""
Generate horizontal comparison report across model summaries,
covering NOTA, FQT, and FCT with deep dives and unexpected results.
"""
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "300q results"
REPORTS_DIR = RESULTS_DIR / "reports"

TYPE_PREFIXES = {"NOTA": "NOTA_", "FQT": "FQT_", "FCT": "FCT_"}


def load_summaries() -> dict:
    """Load all summary_<model>.json and 300q_summary_*.json files."""
    summaries = {}
    for f in sorted(RESULTS_DIR.glob("summary_*.json")):
        model = f.stem.replace("summary_", "")
        with open(f, "r", encoding="utf-8") as fp:
            summaries[model] = json.load(fp)
    for f in sorted(RESULTS_DIR.glob("300q_summary_*.json")):
        model = f.stem.replace("300q_summary_", "")
        with open(f, "r", encoding="utf-8") as fp:
            summaries[model] = json.load(fp)
    return summaries


def build_type_deep_dive(summaries: dict, models: list, type_name: str, type_prefix: str) -> dict:
    """Build wrong_ids, overlap, topics, summary for a given type (NOTA, FQT, FCT)."""
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


def build_comparison(summaries: dict) -> dict:
    """Build horizontal comparison structure for NOTA, FQT, FCT."""
    models = list(summaries.keys())

    accuracy_table = []
    for m in models:
        s = summaries[m]
        by_type = s.get("by_type", {})
        overall = s.get("overall", {})
        accuracy_table.append({
            "model": m,
            "overall": overall.get("accuracy", "0%"),
            "NOTA": by_type.get("NOTA", {}).get("accuracy", "0%"),
            "FQT": by_type.get("FQT", {}).get("accuracy", "0%"),
            "FCT": by_type.get("FCT", {}).get("accuracy", "0%"),
        })

    def acc_val(row, col):
        return float(row[col].rstrip("%"))

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

    for type_name, type_prefix in TYPE_PREFIXES.items():
        deep_dive = build_type_deep_dive(summaries, models, type_name, type_prefix)
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

    return report


def _write_type_section(lines: list, report: dict, type_name: str) -> None:
    """Append deep dive and unexpected sections for one type."""
    deep_dive = report[f"{type_name.lower()}_deep_dive"]
    summary = report[f"{type_name.lower()}_summary"]
    unexpected = report[f"{type_name.lower()}_unexpected"]

    lines.extend([
        "",
        f"## {type_name} Ranking (best first)",
        "",
    ])
    for i, m in enumerate(report[f"{type_name.lower()}_ranking"], 1):
        lines.append(f"{i}. {m}")
    lines.extend([
        "",
        f"## {type_name} Deep Dive",
        "",
        "### Wrong count by model",
        "",
    ])
    for m, c in deep_dive["wrong_count_by_model"].items():
        lines.append(f"- **{m}**: {c} {type_name} wrong")
    lines.extend([
        "",
        f"### Overlap: {type_name} questions wrong by N models",
        "",
        f"- **All models** ({len(deep_dive['overlap']['wrong_by_all'])}): ",
    ])
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
    lines.extend([
        "",
        f"### Hardest {type_name} topics (by number of models that got them wrong)",
        "",
    ])
    for t in deep_dive["topics_by_model_count"][:15]:
        lines.append(f"- **{t['topic']}** ({t['models_wrong']} models): {', '.join(t['ids'][:5])}{' ...' if len(t['ids']) > 5 else ''}")
    lines.extend([
        "",
        f"## {type_name} Summary",
        "",
        f"- Best on {type_name}: **{summary['best_model']}**",
        f"- Worst on {type_name}: **{summary['worst_model']}**",
        f"- {type_name} questions wrong by all models: {summary['wrong_by_all_count']}",
        f"- {type_name} questions wrong by only 1 model: {summary['wrong_by_1_count']}",
        "",
        f"## {type_name} Unexpected Results",
        "",
    ])
    cw = unexpected["consensus_wrong"]
    bf = unexpected["best_model_failures"]
    ws = unexpected["worst_model_succeeds"]
    lines.append(f"- **Consensus wrong** (all models wrong, {len(cw)}): " + (", ".join(cw[:15]) + (" ..." if len(cw) > 15 else "") if cw else "(none)"))
    lines.append(f"- **Best model failures** (top model wrong, others correct, {len(bf)}): " + (", ".join(bf[:15]) + (" ..." if len(bf) > 15 else "") if bf else "(none)"))
    lines.append(f"- **Worst model succeeds** (worst model correct, others wrong, {len(ws)}): " + (", ".join(ws[:15]) + (" ..." if len(ws) > 15 else "") if ws else "(none)"))
    lines.append("")


def write_md_full(report: dict, out_path: Path) -> None:
    """Write full Markdown report (NOTA, FQT, FCT)."""
    lines = [
        "# 300q Horizontal Comparison (Overall: NOTA, FQT, FCT)",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT |",
        "|-------|---------|------|-----|-----|",
    ]
    for row in report["accuracy_table"]:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} |")

    for type_name in ["NOTA", "FQT", "FCT"]:
        _write_type_section(lines, report, type_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_md_nota(report: dict, out_path: Path) -> None:
    """Write NOTA-focused Markdown report."""
    lines = [
        "# 300q Horizontal Comparison (NOTA Focus)",
        "",
        "## Accuracy Table",
        "",
        "| Model | Overall | NOTA | FQT | FCT |",
        "|-------|---------|------|-----|-----|",
    ]
    for row in report["accuracy_table"]:
        lines.append(f"| {row['model']} | {row['overall']} | {row['NOTA']} | {row['FQT']} | {row['FCT']} |")

    _write_type_section(lines, report, "NOTA")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if not RESULTS_DIR.exists():
        print(f"Results dir not found: {RESULTS_DIR}")
        return

    summaries = load_summaries()
    if not summaries:
        print("No summary_*.json or 300q_summary_*.json files found")
        return

    print(f"Loaded {len(summaries)} summaries: {list(summaries.keys())}")

    report = build_comparison(summaries)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Overall report (NOTA + FQT + FCT)
    json_path = REPORTS_DIR / "300q_horizontal_comparison_ds_api.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_path.name} (overall)")

    md_path = REPORTS_DIR / "300q_horizontal_comparison_ds_api.md"
    write_md_full(report, md_path)
    print(f"Wrote {md_path.name} (overall)")

    # NOTA focus report (subset)
    nota_report = {
        "accuracy_table": report["accuracy_table"],
        "nota_ranking": report["nota_ranking"],
        "nota_deep_dive": report["nota_deep_dive"],
        "nota_summary": report["nota_summary"],
        "nota_unexpected": report["nota_unexpected"],
    }
    json_path_nota = REPORTS_DIR / "300q_horizontal_comparison_ds_api_nota.json"
    with open(json_path_nota, "w", encoding="utf-8") as f:
        json.dump(nota_report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_path_nota.name} (NOTA focus)")

    md_path_nota = REPORTS_DIR / "300q_horizontal_comparison_ds_api_nota.md"
    write_md_nota(report, md_path_nota)
    print(f"Wrote {md_path_nota.name} (NOTA focus)")

    print("\nNOTA ranking:", report["nota_ranking"])
    print("FQT ranking:", report["fqt_ranking"])
    print("FCT ranking:", report["fct_ranking"])
    print("NOTA unexpected - consensus wrong:", len(report["nota_unexpected"]["consensus_wrong"]))


if __name__ == "__main__":
    main()
