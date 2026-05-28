"""
Analyze low-accuracy model+task pairs: answer distribution and DeepSeek API reason analysis.

This script:
1. Loads low-accuracy pairs from detailed_task_analysis.json
2. Computes prediction spread/distribution (A, B, C, D counts)
3. Builds confusion patterns (pred vs correct)
4. Calls DeepSeek API to analyze reasons for the low accuracy
5. Outputs JSONL: one line per question with full question, options, and pair-level analysis

Output (low_accuracy_deepseek_analysis.jsonl) structure:
  1. Summary line: {"type": "summary", ...} - all low tests overview
  2. For each test: separator line, test_summary line, then question lines
     - separator: {"type": "separator", "test": "model / task"}
     - test_summary: {"type": "test_summary", "model", "task", "accuracy", ...}
     - question: {"type": "question", "id", "question", "options", "model_answer", "correct", ...}

Usage:
  python analyze_low_accuracy_deepseek.py
  python analyze_low_accuracy_deepseek.py --threshold 70
  python analyze_low_accuracy_deepseek.py --dry-run   # Skip API calls, only compute stats
  python analyze_low_accuracy_deepseek.py --limit 2 # Limit to 2 pairs for testing

Requires: DEEPSEEK_API_KEY environment variable
"""

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' is required. Run: pip install requests")
    sys.exit(1)

# --- CONFIG ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_ROOT = BASE_DIR.parent
RESULTS_DIR = BASE_DIR / "results_102q"
ANALYSIS_DIR = BASE_DIR / "analysis"
DEFAULT_ACCURACY_THRESHOLD = 80.0
GROUND_TRUTH_FILE = BASE_DIR / "diabetes_combined_ready.jsonl"
DETAILED_ANALYSIS = ANALYSIS_DIR / "detailed_task_analysis.json"
OUTPUT_REPORT = ANALYSIS_DIR / "low_accuracy_deepseek_analysis.jsonl"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 90
API_DELAY = 1.5  # Rate limit between calls


def load_ground_truth():
    """Load id -> {answer, question, options} from diabetes_combined_ready.jsonl"""
    gt = {}
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            gt[data["id"]] = {
                "answer": data["answer"],
                "question": data.get("question", ""),
                "options": data.get("options", {}),
            }
    return gt


def parse_accuracy_pct(s: str) -> float:
    return float(s.rstrip("%"))


def compute_distribution(data: list) -> dict:
    """Compute prediction distribution and confusion matrix."""
    pred_counts = Counter(r.get("pred", "N/A") for r in data)
    label_counts = Counter(r.get("label", "N/A") for r in data)
    total = len(data)

    # Confusion: pred -> label
    confusion = defaultdict(lambda: defaultdict(int))
    for r in data:
        p = r.get("pred", "N/A")
        l = r.get("label", "N/A")
        confusion[p][l] += 1

    return {
        "prediction_distribution": dict(pred_counts),
        "correct_answer_distribution": dict(label_counts),
        "total": total,
        "correct": sum(1 for r in data if r.get("correct", False)),
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
    }


def get_sample_incorrect(items: list, ground_truth: dict, max_samples: int = 5) -> list:
    """Get sample incorrect items with question/option context for analysis."""
    incorrect = [i for i in items if not i.get("correct", False)]

    samples = []
    for r in incorrect[:max_samples]:
        qid = r.get("id")
        gt = ground_truth.get(qid, {})
        opts = gt.get("options", {})
        if isinstance(opts, dict):
            opts_text = "\n".join(f"  {k}: {v[:120]}..." if len(str(v)) > 120 else f"  {k}: {v}" for k, v in opts.items())
        else:
            opts_text = str(opts)

        samples.append({
            "id": qid,
            "pred": r.get("pred"),
            "correct": r.get("label"),
            "question_preview": (gt.get("question", "") or "")[:300] + "..." if len(gt.get("question", "") or "") > 300 else (gt.get("question", "") or ""),
            "options": opts_text,
        })
    return samples


def build_analysis_prompt(model: str, task: str, stats: dict, samples: list) -> str:
    """Build prompt for DeepSeek to analyze low accuracy reasons."""
    dist = stats.get("distribution", {})
    pred_dist = dist.get("prediction_distribution", {})
    pred_total = dist.get("total", 0)
    correct_count = dist.get("correct", 0)
    correct_pct = (correct_count / pred_total * 100) if pred_total else 0

    task_desc = {
        "FCT": "Factual Confidence Test - questions with one correct answer based on evidence",
        "FQT": "False Question Test - questions with fabricated premises; correct answer is D (challenges the premise)",
        "NOTA": "None of the Above - questions where none of A/B/C are correct; correct answer is D",
    }.get(task, task)

    prompt = f"""You are a medical education and AI evaluation expert. Analyze why a small language model (evaluated on a diabetes benchmark) has low accuracy on this task type.

**Model:** {model}
**Task type:** {task} ({task_desc})
**Accuracy:** {correct_count}/{pred_total} = {correct_pct:.1f}%

**Prediction distribution (what the model chose):**
{json.dumps(pred_dist, indent=2)}

**Confusion matrix (predicted -> correct):**
{json.dumps(dist.get("confusion_matrix", {}), indent=2)}

**Sample incorrect answers (model predicted wrong):**
"""
    for i, s in enumerate(samples, 1):
        prompt += f"""
--- Sample {i} ---
ID: {s.get("id")}
Model predicted: {s.get("pred")} | Correct: {s.get("correct")}
Question: {s.get("question_preview", "")}
Options:
{s.get("options", "")}
"""

    prompt += """

Based on the distribution and sample errors, provide:
1. **Main bias/pattern**: What option does the model tend to favor when wrong? (e.g., position bias, first plausible option)
2. **Task-specific reason**: Why does this task type (FCT/FQT/NOTA) challenge this model?
3. **Possible causes**: Training data limitations, instruction following, medical knowledge gaps, hallucination tendency
4. **Recommendations**: How could the model or prompt be improved for this task?

Respond in English, structured and concise."""
    return prompt


def call_deepseek_api(prompt: str, api_key: str) -> dict:
    """Call DeepSeek API for analysis."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert in medical AI evaluation and diabetes education. Analyze model failure patterns concisely."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"analysis": content, "error": None}
    except Exception as e:
        return {"analysis": None, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Analyze low-accuracy pairs with DeepSeek")
    parser.add_argument("--threshold", type=float, default=DEFAULT_ACCURACY_THRESHOLD,
                        help=f"Accuracy threshold (default: {DEFAULT_ACCURACY_THRESHOLD})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only compute distribution stats, skip DeepSeek API calls")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of pairs to analyze (for testing)")
    parser.add_argument("--samples", type=int, default=5,
                        help="Number of sample incorrect items per pair (default: 5)")
    args = parser.parse_args()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not args.dry_run and not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable is required.")
        print("Set it with: set DEEPSEEK_API_KEY=your_key  (Windows) or export DEEPSEEK_API_KEY=your_key (Linux/Mac)")
        sys.exit(1)

    # Load data
    ground_truth = load_ground_truth()
    with open(DETAILED_ANALYSIS, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    # Find low-accuracy pairs
    low_acc_pairs = []
    for model, tasks in analysis.items():
        for task, stats in tasks.items():
            acc = parse_accuracy_pct(stats["accuracy"])
            if acc < args.threshold:
                low_acc_pairs.append((model, task, stats))

    if not low_acc_pairs:
        print(f"No model+task pairs with accuracy < {args.threshold}%")
        return

    if args.limit:
        low_acc_pairs = low_acc_pairs[: args.limit]
        print(f"Limited to {args.limit} pairs")

    results_files = {f.stem.replace("results_", ""): f for f in RESULTS_DIR.glob("results_*.json")}
    pair_summaries = []
    all_pair_summaries = []

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as out_f:
        # 1. Summary line - all low tests
        for model, task, expected_stats in low_acc_pairs:
            all_pair_summaries.append({
                "model": model,
                "task": task,
                "accuracy": expected_stats["accuracy"],
                "correct": expected_stats["correct"],
                "total": expected_stats["total"],
            })

        summary_line = {
            "type": "summary",
            "threshold": args.threshold,
            "total_pairs": len(low_acc_pairs),
            "total_questions": sum(s["total"] for s in all_pair_summaries),
            "pairs": all_pair_summaries,
        }
        out_f.write(json.dumps(summary_line, ensure_ascii=False) + "\n")

        # 2. For each test: separator, test_summary, question lines
        for model, task, expected_stats in low_acc_pairs:
            file_key = model.replace(":", "_")
            results_path = results_files.get(file_key) or (RESULTS_DIR / f"results_{file_key}.json")
            if not results_path.exists():
                pair_summaries.append({"model": model, "task": task, "error": "Results file not found"})
                continue

            with open(results_path, "r", encoding="utf-8") as f:
                results = json.load(f)

            task_items = [r for r in results if r["task"] == task]
            distribution = compute_distribution(task_items)
            samples = get_sample_incorrect(task_items, ground_truth, max_samples=args.samples)

            deepseek_analysis = None
            deepseek_error = None
            if not args.dry_run and api_key:
                prompt = build_analysis_prompt(model, task, {"distribution": distribution}, samples)
                print(f"\nCalling DeepSeek for {model} / {task}...")
                api_result = call_deepseek_api(prompt, api_key)
                deepseek_analysis = api_result.get("analysis")
                deepseek_error = api_result.get("error")
                if api_result.get("error"):
                    print(f"  API error: {api_result['error']}")
                else:
                    print(f"  Done. Analysis length: {len(api_result.get('analysis') or '')} chars")
                time.sleep(API_DELAY)

            # Separator line
            test_label = f"{model} / {task}"
            out_f.write(json.dumps({"type": "separator", "test": test_label}, ensure_ascii=False) + "\n")

            # Test summary line
            test_summary = {
                "type": "test_summary",
                "model": model,
                "task": task,
                "accuracy": expected_stats["accuracy"],
                "correct": expected_stats["correct"],
                "total": expected_stats["total"],
                "prediction_distribution": distribution.get("prediction_distribution", {}),
                "confusion_matrix": distribution.get("confusion_matrix", {}),
                "deepseek_analysis": deepseek_analysis,
                "deepseek_error": deepseek_error,
            }
            out_f.write(json.dumps(test_summary, ensure_ascii=False) + "\n")

            # Question lines with model's answer
            for r in task_items:
                qid = r.get("id")
                gt = ground_truth.get(qid, {})
                question_text = gt.get("question", "")
                options = gt.get("options", {})

                question_line = {
                    "type": "question",
                    "id": qid,
                    "question": question_text,
                    "options": options,
                    "model_answer": r.get("pred"),
                    "correct": r.get("label"),
                    "is_correct": r.get("correct", False),
                }
                out_f.write(json.dumps(question_line, ensure_ascii=False) + "\n")

            pair_summaries.append({
                "model": model,
                "task": task,
                "accuracy": expected_stats["accuracy"],
                "prediction_distribution": distribution.get("prediction_distribution", {}),
                "questions_written": len(task_items),
            })

    total_lines = 1 + sum(2 + p.get("questions_written", 0) for p in pair_summaries if "error" not in p)
    print(f"\nReport saved to: {OUTPUT_REPORT} ({total_lines} lines)")

    # Print summary
    print("\n--- Distribution Summary ---")
    for p in pair_summaries:
        if "error" in p:
            print(f"  {p['model']} / {p['task']}: {p['error']}")
        else:
            print(f"  {p['model']} / {p['task']}: pred={p.get('prediction_distribution', {})} ({p.get('questions_written', 0)} questions)")


if __name__ == "__main__":
    main()
