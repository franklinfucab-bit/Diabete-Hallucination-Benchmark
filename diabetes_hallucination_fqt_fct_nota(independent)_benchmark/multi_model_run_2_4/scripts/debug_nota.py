import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results_102q"
# Choose the model that got 0%
DEBUG_MODEL = RESULTS_DIR / "results_phi3_latest.json" 

def debug_failures():
    with open(DEBUG_MODEL, "r") as f:
        data = json.load(f)

    print(f"--- Debugging NOTA failures for {DEBUG_MODEL} ---")
    failures = [item for item in data if item['task'] == 'NOTA' and not item['correct']]
    
    # Print the first 5 failures to see the pattern
    for item in failures[:5]:
        print(f"ID: {item['id']} | Task: {item['task']}")
        print(f"Expected: {item['label']} | Model Predicted: {item['pred']}")
        print("-" * 30)

if __name__ == "__main__":
    debug_failures()