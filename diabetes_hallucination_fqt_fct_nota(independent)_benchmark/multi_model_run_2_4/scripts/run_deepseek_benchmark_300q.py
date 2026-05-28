"""
Run the 300-question diabetes benchmark against DeepSeek API.

Uses the same benchmark settings, question format, and prompt as run_multi_models.py (300q).
Outputs (all with 300q prefix):
  - benchmark/300q_v1_combined_benchmark_test_format.jsonl
  - 300q results/300q_results_{model}.json
  - 300q results/300q_summary_{model}.json (same format as other 300q summaries)

Requires: requests, config.DEEPSEEK_API_KEY (or DEEPSEEK_API_KEY env var)
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

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
INPUT_FILE = BENCHMARK_ROOT / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
BENCHMARK_DIR = BASE_DIR / "benchmark"
BENCHMARK_JSONL = BENCHMARK_DIR / "300q_v1_combined_benchmark_test_format.jsonl"
RESULTS_DIR = BASE_DIR / "300q results"
API_TIMEOUT = 90
GENERIC_TAGS = {"diabetes", "fct", "nota", "fqt", "fqt_v2"}


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


def load_test_set(limit: Optional[int] = None) -> List[dict]:
    """Load 300 questions from combined_ready (or limit for quick tests)."""
    test_set = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            test_set.append(data)
            if limit is not None and len(test_set) >= limit:
                break
    return test_set


def build_benchmark_lookup(test_set: List[dict]) -> dict:
    """Build id -> {tags, topic, difficulty} from test set (combined_ready format)."""
    lookup = {}
    for q in test_set:
        qid = q.get("id", "")
        meta = q.get("metadata") or {}
        tags = meta.get("tags") or []
        difficulty = meta.get("difficulty", 0)
        topic = "Other"
        for t in tags:
            t_str = str(t).strip()
            if t_str and t_str.lower() not in GENERIC_TAGS:
                topic = t_str
                break
        lookup[qid] = {"tags": tags, "topic": topic, "difficulty": difficulty}
    return lookup


def task_from_id(qid: str) -> str:
    """Derive task from id prefix (NOTA_, FQT_, FCT_)."""
    if qid.startswith("NOTA_"):
        return "NOTA"
    if qid.startswith("FQT_"):
        return "FQT"
    if qid.startswith("FCT_"):
        return "FCT"
    return "Other"


def analyze_results(results: List[dict], benchmark: dict) -> dict:
    """Same logic as analyze_300q_results.analyze_results."""
    by_type = defaultdict(lambda: {"correct": 0, "total": 0})
    wrong_ids = []
    wrong_by_topic = defaultdict(list)
    pred_vs_label = defaultdict(int)
    wrong_by_difficulty = defaultdict(int)

    for item in results:
        qid = item.get("id", "")
        correct = item.get("correct", False)
        task = task_from_id(qid)
        by_type[task]["total"] += 1
        if correct:
            by_type[task]["correct"] += 1
        else:
            wrong_ids.append(qid)
            info = benchmark.get(qid, {})
            topic = info.get("topic", "Other")
            wrong_by_topic[topic].append(qid)
            pred = item.get("pred", "?")
            label = item.get("label", "?")
            pred_vs_label[f"{pred}->{label}"] += 1
            diff = info.get("difficulty", 0)
            diff_str = str(round(diff, 2)) if isinstance(diff, (int, float)) else str(diff)
            wrong_by_difficulty[diff_str] += 1

    total = len(results)
    correct_count = sum(1 for r in results if r.get("correct"))
    overall_acc = (correct_count / total * 100) if total > 0 else 0

    by_type_out = {}
    for t in ["NOTA", "FQT", "FCT"]:
        s = by_type.get(t, {"correct": 0, "total": 0})
        acc = (s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
        by_type_out[t] = {
            "accuracy": f"{acc:.1f}%",
            "correct": s["correct"],
            "total": s["total"],
        }

    hardest = [
        {"topic": t, "wrong_count": len(ids), "ids": ids}
        for t, ids in sorted(wrong_by_topic.items(), key=lambda x: -len(x[1]))
    ]

    return {
        "overall": {
            "accuracy": f"{overall_acc:.1f}%",
            "correct": correct_count,
            "total": total,
            "wrong": total - correct_count,
        },
        "by_type": by_type_out,
        "wrong_answers": {
            "ids": wrong_ids,
            "by_topic": dict(wrong_by_topic),
        },
        "analysis": {
            "pred_vs_label": dict(pred_vs_label),
            "wrong_by_difficulty": dict(wrong_by_difficulty),
            "hardest_topics": hardest[:20],
        },
    }


def build_prompt(data: dict) -> str:
    """Same prompt format as run_multi_models.py."""
    return (
        f"Context: You are a medical expert. Answer strictly with the letter.\n\n"
        f"Question: {data['question']}\nOptions:\n"
        + "\n".join([f"{k}. {v}" for k, v in data["options"].items()])
        + "\n\nAnswer (A, B, C, or D):"
    )


def extract_answer(text: str) -> str:
    """Extract first A/B/C/D from response; otherwise N/A."""
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
        description="Run 300-question diabetes benchmark against DeepSeek API"
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
        help="Limit total questions for quick tests (default: all 300)",
    )
    args = parser.parse_args()

    api_key = get_api_key()
    model = args.model

    test_set = load_test_set(limit=args.limit)
    print(f"Loaded {len(test_set)} questions")

    benchmark_lookup = build_benchmark_lookup(test_set)

    # Save benchmark jsonl (300q prefix)
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_JSONL, "w", encoding="utf-8") as f:
        for item in test_set:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved benchmark to {BENCHMARK_JSONL}")

    results = []
    correct_count = 0

    print(f"\n--- Starting DeepSeek 300q: {model} ---")
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
                    "pred": "N/A",
                    "label": data["answer"],
                    "correct": False,
                }
            )

    acc = (correct_count / len(test_set)) * 100
    print(f"Finished. Accuracy: {acc:.2f}% ({correct_count}/{len(test_set)})")

    model_safe = model.replace("-", "_").replace(":", "_")

    # Save results (300q prefix)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / f"300q_results_{model_safe}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Saved results to {results_file}")

    # Generate and save summary (300q prefix, same format as other 300q)
    summary = analyze_results(results, benchmark_lookup)
    summary["model"] = model_safe
    summary_file = RESULTS_DIR / f"300q_summary_{model_safe}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {summary_file}")


if __name__ == "__main__":
    main()
