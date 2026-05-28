"""
Analyze 100q AOTA results: accuracy rate and option stats (A, B, C, D, N/A) per model.
Outputs 100q_aota_stats.json and 100q_aota_stats.md

Usage:
  python analyze_100q_aota_results.py                    # default: wrong answer variant
  python analyze_100q_aota_results.py --correct-from-fct # Correct from FCT variant
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

VALID_OPTIONS = {"A", "B", "C", "D"}


def analyze_results(results: list) -> dict:
    """Compute accuracy and option stats for a single model."""
    total = len(results)
    correct = sum(1 for r in results if r.get("correct", False))

    option_counts = defaultdict(int)
    for r in results:
        pred = r.get("pred", "N/A")
        if pred in VALID_OPTIONS:
            option_counts[pred] += 1
        else:
            option_counts["N/A"] += 1

    option_stats = {}
    for opt in ["A", "B", "C", "D", "N/A"]:
        count = option_counts.get(opt, 0)
        pct = (count / total * 100) if total > 0 else 0
        option_stats[opt] = {"count": count, "pct": round(pct, 1)}

    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        "accuracy": round(accuracy, 1),
        "correct": correct,
        "total": total,
        "option_stats": option_stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze 100q AOTA results")
    parser.add_argument(
        "--correct-from-fct",
        action="store_true",
        help="Analyze '100q AOTA Correct from FCT' results (has real correct answer)",
    )
    args = parser.parse_args()

    if args.correct_from_fct:
        results_dir = BASE_DIR / "100q AOTA Correct from FCT" / "results_100q_aota_correct"
        title = "100q AOTA Correct from FCT"
    else:
        results_dir = BASE_DIR / "100q AOTA wrong anwser" / "results_100q_aota"
        title = "100q AOTA (No Correct Answer)"

    if not results_dir.exists():
        print(f"Results dir not found: {results_dir}")
        return

    files = list(results_dir.glob("results_*.json"))
    if not files:
        print(f"No results_*.json found in {results_dir}")
        return

    models = {}
    for f in sorted(files):
        model_name = f.stem.replace("results_", "")
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        models[model_name] = analyze_results(data)

    ranking = sorted(models.keys(), key=lambda m: models[m]["accuracy"], reverse=True)

    stats = {"models": models, "ranking": ranking}

    json_path = results_dir / "100q_aota_stats.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_path}")

    md_path = results_dir / "100q_aota_stats.md"
    lines = [
        f"# {title} Model Statistics",
        "",
        "## Accuracy by Model",
        "",
        "| Model | Accuracy | Correct | Total |",
        "|-------|----------|---------|-------|",
    ]
    for m in ranking:
        s = models[m]
        lines.append(f"| {m} | {s['accuracy']}% | {s['correct']} | {s['total']} |")

    lines.extend([
        "",
        "## Option Selection Stats",
        "",
    ])
    for m in ranking:
        s = models[m]
        lines.append(f"### {m}")
        lines.append("")
        lines.append("| Option | Count | % |")
        lines.append("|--------|-------|---|")
        for opt in ["A", "B", "C", "D", "N/A"]:
            o = s["option_stats"][opt]
            lines.append(f"| {opt} | {o['count']} | {o['pct']}% |")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {md_path.name}")

    print("\nAccuracy ranking:")
    for i, m in enumerate(ranking, 1):
        print(f"  {i}. {m}: {models[m]['accuracy']}%")


if __name__ == "__main__":
    main()
