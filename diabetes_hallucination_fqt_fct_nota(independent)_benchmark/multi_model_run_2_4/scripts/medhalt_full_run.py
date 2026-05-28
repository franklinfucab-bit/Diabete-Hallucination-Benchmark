import json
import urllib.request
import sys
import os
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_FILE = BASE_DIR / "diabetes_combined_ready.jsonl"
OUTPUT_FILE = BASE_DIR / "final_results_full.json"
OLLAMA_URL = "http://localhost:11435/api/generate" # Using your verified port
MODEL_NAME = "llama3:8b"

def run_query(prompt):
    payload = json.dumps({
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    }).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    # 1. Load existing results to support resume/checkpointing
    processed_ids = set()
    results = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r') as f:
            results = json.load(f)
            processed_ids = {r['id'] for r in results}
            print(f"?? Resuming: {len(processed_ids)} questions already processed.")

    # 2. Load all questions
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_data = [json.loads(line) for line in f]

    # 3. Execution loop
    for i, data in enumerate(all_data):
        if data['id'] in processed_ids:
            continue

        prompt = (
            f"Context: You are a medical expert. Answer strictly with the letter.\n\n"
            f"Question: {data['question']}\n"
            f"Options:\n" + "\n".join([f"{k}. {v}" for k, v in data['options'].items()]) +
            f"\n\nAnswer (A, B, C, or D):"
        )

        try:
            resp = run_query(prompt)
            raw_text = resp.get('response', '').strip()
            pred = next((c.upper() for c in raw_text if c.upper() in "ABCD"), "N/A")
            
            results.append({
                "id": data["id"],
                "task": data["task"],
                "pred": pred,
                "label": data["answer"],
                "correct": pred == data["answer"]
            })

            # Save progress every 10 questions to prevent data loss
            if len(results) % 10 == 0:
                with open(OUTPUT_FILE, 'w') as f:
                    json.dump(results, f, indent=4)
                sys.stdout.write(f"\rProgress: {len(results)}/{len(all_data)} saved.")
                sys.stdout.flush()

        except Exception as e:
            print(f"\n?? Error at Q{data['id']}: {e}")
            break # Stop if the API crashes so you can restart

    # Final Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\n? Finished! Total processed: {len(results)}")

if __name__ == "__main__":
    main()