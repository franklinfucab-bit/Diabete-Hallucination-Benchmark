import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results_102q"
ANALYSIS_DIR = BASE_DIR / "analysis"


def analyze():
    files = list(RESULTS_DIR.glob("results_*.json"))
    final_data = {}

    for file in files:
        model_name = file.stem.replace("results_", "")
        with open(file, "r") as f:
            data = json.load(f)
            
        stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for item in data:
            task = item['task']
            stats[task]["total"] += 1
            if item['correct']:
                stats[task]["correct"] += 1
        
        model_results = {}
        for task in ['FCT', 'FQT', 'NOTA']:
            s = stats[task]
            acc = (s['correct'] / s['total'] * 100) if s['total'] > 0 else 0
            model_results[task] = {"accuracy": f"{acc:.1f}%", "correct": s['correct'], "total": s['total']}
        
        final_data[model_name] = model_results

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_DIR / "detailed_task_analysis.json", "w") as f:
        json.dump(final_data, f, indent=4)
    print("Analysis saved to analysis/detailed_task_analysis.json")

if __name__ == "__main__":
    analyze()