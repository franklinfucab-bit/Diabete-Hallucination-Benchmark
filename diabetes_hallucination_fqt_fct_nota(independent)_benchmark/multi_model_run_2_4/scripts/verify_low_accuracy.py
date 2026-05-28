"""
Verify accuracy for low-accuracy model+task combinations from detailed_task_analysis.json.

This script:
1. Loads detailed_task_analysis.json and identifies model+task pairs with accuracy below threshold
2. Recomputes accuracy from raw results and verifies it matches the reported value
3. Cross-checks labels against ground truth (diabetes_combined_ready.jsonl)
4. Outputs a detailed report for manual review of each item

Usage:
  python verify_low_accuracy.py              # Default threshold 80%
  python verify_low_accuracy.py --threshold 70
  python verify_low_accuracy.py --verbose    # Print each incorrect item for review
"""

import argparse
import json
import os
from pathlib import Path

# --- CONFIG ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_ROOT = BASE_DIR.parent
RESULTS_DIR = BASE_DIR / "results_102q"
ANALYSIS_DIR = BASE_DIR / "analysis"
DEFAULT_ACCURACY_THRESHOLD = 80.0  # Flag model+task pairs with accuracy below this %
GROUND_TRUTH_FILE = BASE_DIR / "diabetes_combined_ready.jsonl"
DETAILED_ANALYSIS = ANALYSIS_DIR / "detailed_task_analysis.json"
OUTPUT_REPORT = ANALYSIS_DIR / "low_accuracy_verification_report.json"


def load_ground_truth():
    """Load id -> correct_answer from diabetes_combined_ready.jsonl"""
    gt = {}
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            gt[data["id"]] = data["answer"]
    return gt


def parse_accuracy_pct(s: str) -> float:
    """Parse '85.3%' -> 85.3"""
    return float(s.rstrip("%"))


def main():
    parser = argparse.ArgumentParser(description="Verify accuracy for low-accuracy model+task pairs")
    parser.add_argument("--threshold", type=float, default=DEFAULT_ACCURACY_THRESHOLD,
                        help=f"Accuracy threshold (default: {DEFAULT_ACCURACY_THRESHOLD}). Pairs below this are verified.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print each incorrect item (pred vs label) for manual review")
    args = parser.parse_args()
    ACCURACY_THRESHOLD = args.threshold

    # Load ground truth
    if not GROUND_TRUTH_FILE.exists():
        print(f"Warning: Ground truth file not found: {GROUND_TRUTH_FILE}")
        ground_truth = {}
    else:
        ground_truth = load_ground_truth()
        print(f"Loaded ground truth for {len(ground_truth)} items")

    # Load detailed analysis
    with open(DETAILED_ANALYSIS, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    # Find low-accuracy model+task pairs
    low_acc_pairs = []
    for model, tasks in analysis.items():
        for task, stats in tasks.items():
            acc = parse_accuracy_pct(stats["accuracy"])
            if acc < ACCURACY_THRESHOLD:
                low_acc_pairs.append((model, task, stats))

    if not low_acc_pairs:
        print(f"No model+task pairs with accuracy < {ACCURACY_THRESHOLD}%")
        return

    print(f"\nFound {len(low_acc_pairs)} low-accuracy model+task pairs:")
    for model, task, stats in low_acc_pairs:
        print(f"  - {model} / {task}: {stats['accuracy']} ({stats['correct']}/{stats['total']})")

    # Map model name to results file (e.g., phi3_latest -> results_phi3_latest.json)
    results_files = {f.stem.replace("results_", ""): f for f in RESULTS_DIR.glob("results_*.json")}

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "threshold": ACCURACY_THRESHOLD,
        "low_accuracy_pairs": [],
        "discrepancies": [],
        "summary": {},
    }

    for model, task, expected_stats in low_acc_pairs:
        # Find results file (model name may use : or _)
        file_key = model.replace(":", "_")
        results_path = results_files.get(file_key)
        if not results_path:
            results_path = RESULTS_DIR / f"results_{file_key}.json"
        if not results_path.exists():
            report["discrepancies"].append({
                "model": model,
                "task": task,
                "error": f"Results file not found: {results_path.name}",
            })
            continue

        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)

        # Filter to this task only
        task_items = [r for r in results if r["task"] == task]

        # Recompute accuracy
        total = len(task_items)
        correct_count = sum(1 for r in task_items if r.get("correct", False))
        recomputed_acc = (correct_count / total * 100) if total > 0 else 0.0

        # Verify against reported
        reported_correct = expected_stats["correct"]
        reported_total = expected_stats["total"]
        reported_acc = parse_accuracy_pct(expected_stats["accuracy"])

        verification_ok = (
            correct_count == reported_correct and total == reported_total
        )

        # Cross-check labels vs ground truth
        label_mismatches = []
        for r in task_items:
            qid = r.get("id")
            if qid and ground_truth:
                gt_answer = ground_truth.get(qid)
                if gt_answer is not None and r.get("label") != gt_answer:
                    label_mismatches.append({
                        "id": qid,
                        "result_label": r.get("label"),
                        "ground_truth": gt_answer,
                    })

        # Build item-level detail for manual review
        items_detail = []
        for r in task_items:
            pred = r.get("pred", "N/A")
            label = r.get("label", "N/A")
            correct = r.get("correct", False)
            gt = ground_truth.get(r.get("id"), "?")
            items_detail.append({
                "id": r.get("id"),
                "pred": pred,
                "label": label,
                "correct": correct,
                "ground_truth_match": label == gt if ground_truth else None,
            })

        pair_report = {
            "model": model,
            "task": task,
            "reported": {
                "accuracy": expected_stats["accuracy"],
                "correct": reported_correct,
                "total": reported_total,
            },
            "recomputed": {
                "accuracy": f"{recomputed_acc:.1f}%",
                "correct": correct_count,
                "total": total,
            },
            "verification_passed": verification_ok,
            "label_mismatches_count": len(label_mismatches),
            "label_mismatches": label_mismatches if label_mismatches else None,
            "items": items_detail,
        }

        report["low_accuracy_pairs"].append(pair_report)

        if not verification_ok:
            report["discrepancies"].append({
                "model": model,
                "task": task,
                "issue": "Accuracy mismatch",
                "reported": f"{reported_correct}/{reported_total}",
                "recomputed": f"{correct_count}/{total}",
            })
        if label_mismatches:
            report["discrepancies"].append({
                "model": model,
                "task": task,
                "issue": "Label vs ground truth mismatch",
                "count": len(label_mismatches),
                "examples": label_mismatches[:3],
            })

    # Summary
    report["summary"] = {
        "total_low_acc_pairs": len(low_acc_pairs),
        "verification_passed": all(p["verification_passed"] for p in report["low_accuracy_pairs"]),
        "label_mismatches_total": sum(p["label_mismatches_count"] for p in report["low_accuracy_pairs"]),
        "discrepancy_count": len(report["discrepancies"]),
    }

    # Save report
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n--- Verification Summary ---")
    print(f"Verification passed: {report['summary']['verification_passed']}")
    print(f"Label mismatches: {report['summary']['label_mismatches_total']}")
    print(f"Discrepancies: {report['summary']['discrepancy_count']}")
    print(f"\nFull report saved to: {OUTPUT_REPORT}")

    # Print per-pair summary
    for p in report["low_accuracy_pairs"]:
        status = "OK" if p["verification_passed"] else "MISMATCH"
        print(f"\n  {p['model']} / {p['task']}: {status}")
        print(f"    Reported: {p['reported']['correct']}/{p['reported']['total']} = {p['reported']['accuracy']}")
        print(f"    Recomputed: {p['recomputed']['correct']}/{p['recomputed']['total']} = {p['recomputed']['accuracy']}")
        if p["label_mismatches_count"]:
            print(f"    Label mismatches: {p['label_mismatches_count']}")
        if args.verbose and p.get("items"):
            incorrect = [i for i in p["items"] if not i["correct"]]
            if incorrect:
                print(f"    Incorrect items ({len(incorrect)}):")
                for i in incorrect[:15]:  # Limit to 15 for readability
                    print(f"      {i['id']}: pred={i['pred']} (correct={i['label']})")
                if len(incorrect) > 15:
                    print(f"      ... and {len(incorrect) - 15} more")


if __name__ == "__main__":
    main()
