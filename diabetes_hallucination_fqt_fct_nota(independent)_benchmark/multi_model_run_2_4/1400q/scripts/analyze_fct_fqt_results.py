"""Analyze FCT/FQT results from results_500q_core and add to report."""
import json
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results_500q_core"
REPORT_JSON = Path(__file__).resolve().parent.parent / "results_1000q_core" / "reports" / "1000q_core_analysis_report.json"
REPORT_MD = Path(__file__).resolve().parent.parent / "results_1000q_core" / "reports" / "1000q_core_analysis_report.md"

MODELS = ["qwen2.5_7b", "llama3.1_8b", "gemma_7b", "deepseek-r1_7b", "mistral_latest"]
DISPLAY_NAMES = {
    "qwen2.5_7b": "Qwen2.5 7B",
    "llama3.1_8b": "Llama 3.1 8B",
    "gemma_7b": "Gemma 7B",
    "deepseek-r1_7b": "DeepSeek-R1 7B",
    "mistral_latest": "Mistral Latest",
}


def main():
    fct_acc = {}
    fqt_acc = {}
    combined_acc = {}
    fct_correct_by_id = defaultdict(set)
    fqt_correct_by_id = defaultdict(set)
    all_fct_ids = set()
    all_fqt_ids = set()

    for m in MODELS:
        f = RESULTS_DIR / f"results_{m}.json"
        if not f.exists():
            print(f"Missing: {f}")
            continue
        data = json.load(open(f, encoding="utf-8"))
        fct_c, fct_t = 0, 0
        fqt_c, fqt_t = 0, 0
        for r in data:
            if r["id"].startswith("FCT_"):
                fct_t += 1
                all_fct_ids.add(r["id"])
                if r.get("correct"):
                    fct_c += 1
                    fct_correct_by_id[r["id"]].add(m)
            else:
                fqt_t += 1
                all_fqt_ids.add(r["id"])
                if r.get("correct"):
                    fqt_c += 1
                    fqt_correct_by_id[r["id"]].add(m)
        fct_acc[m] = {"correct": fct_c, "total": fct_t}
        fqt_acc[m] = {"correct": fqt_c, "total": fqt_t}
        combined_acc[m] = {"correct": fct_c + fqt_c, "total": fct_t + fqt_t}

    fct_universal = sorted([i for i in all_fct_ids if len(fct_correct_by_id[i]) == 0])
    fqt_universal = sorted([i for i in all_fqt_ids if len(fqt_correct_by_id[i]) == 0])

    # FCT vs FQT gap (FCT - FQT, positive = FCT harder)
    fct_fqt_gap = {}
    for m in MODELS:
        fct_pct = 100 * fct_acc[m]["correct"] / fct_acc[m]["total"] if fct_acc[m]["total"] else 0
        fqt_pct = 100 * fqt_acc[m]["correct"] / fqt_acc[m]["total"] if fqt_acc[m]["total"] else 0
        fct_fqt_gap[m] = round(fct_pct - fqt_pct, 1)

    # Build FCT/FQT report section
    fct_fqt_report = {
        "fct_accuracy": {m: {"correct": fct_acc[m]["correct"], "total": fct_acc[m]["total"]} for m in MODELS},
        "fqt_accuracy": {m: {"correct": fqt_acc[m]["correct"], "total": fqt_acc[m]["total"]} for m in MODELS},
        "combined_fct_fqt_accuracy": {m: {"correct": combined_acc[m]["correct"], "total": combined_acc[m]["total"]} for m in MODELS},
        "fct_fqt_gap": fct_fqt_gap,
        "fct_universal_failures_count": len(fct_universal),
        "fct_universal_failure_ids": fct_universal,
        "fqt_universal_failures_count": len(fqt_universal),
        "fqt_universal_failure_ids": fqt_universal,
    }

    # Load existing report and merge
    report = json.load(open(REPORT_JSON, encoding="utf-8"))
    report["fct_fqt"] = fct_fqt_report
    json.dump(report, open(REPORT_JSON, "w", encoding="utf-8"), indent=2)

    # Update MD report
    md = REPORT_MD.read_text(encoding="utf-8")

    # Replace the FCT and FQT section
    new_section = """## 12. FCT and FQT (500q Core)

*Results from results_500q_core: 255 FCT + 255 FQT = 510 questions.*

### 12.1 Overall FCT+FQT Accuracy (510 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
"""
    for m in MODELS:
        a = combined_acc[m]
        pct = 100 * a["correct"] / a["total"] if a["total"] else 0
        new_section += f"| **{DISPLAY_NAMES.get(m, m)}** | {a['correct']} | {a['total']} | **{pct:.1f}%** |\n"

    new_section += """
### 12.2 FCT Accuracy (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
"""
    for m in MODELS:
        a = fct_acc[m]
        pct = 100 * a["correct"] / a["total"] if a["total"] else 0
        new_section += f"| **{DISPLAY_NAMES.get(m, m)}** | {a['correct']} | {a['total']} | **{pct:.1f}%** |\n"

    new_section += """
### 12.3 FQT Accuracy (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
"""
    for m in MODELS:
        a = fqt_acc[m]
        pct = 100 * a["correct"] / a["total"] if a["total"] else 0
        new_section += f"| **{DISPLAY_NAMES.get(m, m)}** | {a['correct']} | {a['total']} | **{pct:.1f}%** |\n"

    new_section += """
### 12.4 FCT vs FQT Gap (FCT − FQT)

*Positive = FCT harder; Negative = FQT harder.*

| Model | FCT Acc | FQT Acc | Gap |
|-------|---------|---------|-----|
"""
    for m in MODELS:
        fc = 100 * fct_acc[m]["correct"] / fct_acc[m]["total"] if fct_acc[m]["total"] else 0
        fq = 100 * fqt_acc[m]["correct"] / fqt_acc[m]["total"] if fqt_acc[m]["total"] else 0
        gap = fct_fqt_gap[m]
        new_section += f"| {DISPLAY_NAMES.get(m, m)} | {fc:.1f}% | {fq:.1f}% | **{gap:+.1f}%** |\n"

    new_section += f"""
### 12.5 Universal Failures (All Models Wrong)

- **FCT:** {len(fct_universal)} questions
- **FQT:** {len(fqt_universal)} questions
"""

    # Find and replace the old FCT/FQT section
    old_start = "## 12. FCT and FQT"
    old_end = "*Report generated by purge_benchmark_to_1000q.py*"
    if old_start in md and old_end in md:
        before = md[: md.index(old_start)]
        after = md[md.index(old_end) :]
        md = before + new_section.rstrip() + "\n\n---\n\n" + after
    else:
        # Append if pattern not found
        md = md.rstrip() + "\n\n" + new_section

    REPORT_MD.write_text(md, encoding="utf-8")

    print("FCT accuracy:")
    for m in MODELS:
        a = fct_acc[m]
        pct = 100 * a["correct"] / a["total"] if a["total"] else 0
        print(f"  {m}: {a['correct']}/{a['total']} = {pct:.1f}%")
    print("FQT accuracy:")
    for m in MODELS:
        a = fqt_acc[m]
        pct = 100 * a["correct"] / a["total"] if a["total"] else 0
        print(f"  {m}: {a['correct']}/{a['total']} = {pct:.1f}%")
    print(f"FCT universal failures: {len(fct_universal)}")
    print(f"FQT universal failures: {len(fqt_universal)}")
    print(f"\nUpdated {REPORT_JSON} and {REPORT_MD}")


if __name__ == "__main__":
    main()
