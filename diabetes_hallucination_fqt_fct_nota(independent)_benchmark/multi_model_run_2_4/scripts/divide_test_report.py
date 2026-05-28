import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# Configurations
INPUT_FILE = BASE_DIR / "summaries" / "multi_model_summary.json"
OUTPUT_FILE = BASE_DIR / "analysis" / "multi_model_divide_summary_report.json"
ANALYSIS_DIR = BASE_DIR / "analysis"
MODEL_NAME = "Llama-3-8B"  # You can update this if you change models

def generate_professional_report():
    print(f"?? Analyzing results for {MODEL_NAME}...")
    
    try:
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"? Error: {INPUT_FILE} not found.")
        return

    total_q = len(data)
    total_correct = sum(1 for item in data if item.get("correct"))
    overall_acc = (total_correct / total_q) * 100 if total_q > 0 else 0

    # Group by Task
    task_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    for item in data:
        t = item.get("task", "Unknown")
        task_stats[t]["total"] += 1
        if item.get("correct"):
            task_stats[t]["correct"] += 1

    # Build the Rich Metadata Object
    summary = {
        "metadata": {
            "model": MODEL_NAME,
            "date_analyzed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataset": "MedHalt-Diabetes-Combined",
            "total_questions": total_q
        },
        "overall_performance": {
            "accuracy": f"{overall_acc:.2f}%",
            "correct_count": total_correct,
            "error_count": total_q - total_correct
        },
        "task_breakdown": {}
    }

    for task, s in task_stats.items():
        acc = (s["correct"] / s["total"]) * 100
        summary["task_breakdown"][task] = {
            "accuracy": f"{acc:.2f}%",
            "correct": s["correct"],
            "total": s["total"]
        }

    # Save to JSON
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(summary, f, indent=4)

    # Print a clean table for the terminal
    print(f"\nModel: {MODEL_NAME} | Overall Accuracy: {overall_acc:.2f}%")
    print(f"{'-'*50}")
    print(f"{'Task':<20} | {'Acc':<10} | {'Count'}")
    print(f"{'-'*50}")
    for task, stats in summary["task_breakdown"].items():
        print(f"{task:<20} | {stats['accuracy']:<10} | {stats['total']}")
    
    print(f"\n? Full metadata summary saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_professional_report()