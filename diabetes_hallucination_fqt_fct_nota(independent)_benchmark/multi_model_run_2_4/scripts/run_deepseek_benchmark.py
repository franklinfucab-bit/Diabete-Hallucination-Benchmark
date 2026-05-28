"""
Run the 102-question diabetes benchmark against DeepSeek API.

Uses the same benchmark settings, question format, and prompt as run_multi_models.py.
Outputs: v1_102q_combined_benchmark_test_format.jsonl, results_*.json, deepseek_benchmark_summary.json

Requires: requests, config.DEEPSEEK_API_KEY (or DEEPSEEK_API_KEY env var)
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add project root for config import
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_ROOT = BASE_DIR.parent
PROJECT_ROOT = BENCHMARK_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Error: 'requests' is required. Run: pip install requests")
    sys.exit(1)

try:
    import config
except ImportError:
    config = None

# --- CONFIGURATION ---
INPUT_FILE = BASE_DIR / "diabetes_combined_ready.jsonl"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
LIMIT_PER_TYPE = 34  # Total ~102 questions
BENCHMARK_DIR = BASE_DIR / "benchmark"
BENCHMARK_JSONL = BENCHMARK_DIR / "v1_102q_combined_benchmark_test_format.jsonl"
RESULTS_DIR = BASE_DIR / "results_102q"
SUMMARIES_DIR = BASE_DIR / "summaries"
API_TIMEOUT = 90


def get_api_key() -> str:
    """Load API key from config or environment."""
    if config and getattr(config, "DEEPSEEK_API_KEY", None):
        return config.DEEPSEEK_API_KEY
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        print("Error: DEEPSEEK_API_KEY not found in config.py or environment.")
        print("Set it in config.py or: set DEEPSEEK_API_KEY=your_key  (Windows)")
        sys.exit(1)
    return key


def get_balanced_test_set(limit_per_type: int = LIMIT_PER_TYPE):
    """Load 34 FCT + 34 FQT + 34 NOTA = 102 questions (same as run_multi_models)."""
    categories = defaultdict(list)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            categories[data["task"]].append(data)

    test_set = []
    for task in ["FCT", "FQT", "NOTA"]:
        test_set.extend(categories[task][:limit_per_type])
    return test_set


def build_prompt(data: dict) -> str:
    """Same prompt format as run_multi_models.py."""
    return (
        f"Context: You are a medical expert. Answer strictly with the letter.\n\n"
        f"Question: {data['question']}\nOptions:\n"
        + "\n".join([f"{k}. {v}" for k, v in data["options"].items()])
        + "\n\nAnswer (A, B, C, or D):"
    )


def extract_answer(text: str) -> str:
    """Extract first A/B/C/D from response; otherwise N/A (same as run_multi_models)."""
    return next(
        (c.upper() for c in (text or "").strip() if c.upper() in "ABCD"),
        "N/A",
    )


def call_deepseek(prompt: str, api_key: str, model: str = "deepseek-chat") -> str:
    """Call DeepSeek API and return response content."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 256,
    }
    resp = requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        json=payload,
        timeout=API_TIMEOUT,
    )
    resp.raise_for_status()
    result = resp.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content


def main():
    parser = argparse.ArgumentParser(
        description="Run 102-question diabetes benchmark against DeepSeek API"
    )
    parser.add_argument(
        "--model",
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek model (default: deepseek-chat)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit questions per task for quick tests (default: 34 = 102 total)",
    )
    args = parser.parse_args()

    limit_per_type = args.limit if args.limit is not None else LIMIT_PER_TYPE
    api_key = get_api_key()
    model = args.model

    test_set = get_balanced_test_set(limit_per_type)
    print(f"Loaded {len(test_set)} questions (limit_per_type={limit_per_type})")

    # Save benchmark jsonl (102-question test set for reproducibility)
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_JSONL, "w", encoding="utf-8") as f:
        for item in test_set:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved benchmark to {BENCHMARK_JSONL}")

    results = []
    correct_count = 0

    print(f"\n--- Starting DeepSeek: {model} ---")
    for i, data in enumerate(test_set):
        prompt = build_prompt(data)
        try:
            content = call_deepseek(prompt, api_key, model)
            pred = extract_answer(content)
            is_correct = pred == data["answer"]
            if is_correct:
                correct_count += 1
            results.append(
                {
                    "id": data["id"],
                    "task": data["task"],
                    "pred": pred,
                    "label": data["answer"],
                    "correct": is_correct,
                }
            )
        except Exception as e:
            print(f"Error on Q{i} ({data['id']}): {e}")
            results.append(
                {
                    "id": data["id"],
                    "task": data["task"],
                    "pred": "N/A",
                    "label": data["answer"],
                    "correct": False,
                }
            )

    acc = (correct_count / len(test_set)) * 100
    print(f"Finished. Accuracy: {acc:.2f}% ({correct_count}/{len(test_set)})")

    # Save results (same schema as results_*.json)
    model_safe = model.replace("-", "_").replace(":", "_")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / f"results_{model_safe}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Saved results to {results_file}")

    # Save summary
    summary = [
        {
            "model": model,
            "accuracy": f"{acc:.2f}%",
            "total": len(test_set),
            "correct": correct_count,
        }
    ]
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    summary_file = SUMMARIES_DIR / "deepseek_benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    print(f"Saved summary to {summary_file}")


if __name__ == "__main__":
    main()
