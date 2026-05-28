"""
Re-check difficulty for questions where model performance disagrees with the labeled difficulty.
Uses DeepSeek API to evaluate each question and suggest a revised difficulty (0.0-1.0).
API key from config.py (project root) or DEEPSEEK_API_KEY env var.

Usage:
  python recheck_difficulty_deepseek.py
  python recheck_difficulty_deepseek.py --dry-run    # Identify questions only, no API
  python recheck_difficulty_deepseek.py --apply      # Apply suggested difficulties to benchmark
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Error: 'requests' required. Run: pip install requests")
    raise SystemExit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_JSONL = BASE_DIR / "benchmark" / "130q_nota_fct_test_ready.jsonl"
RESULTS_DIR = BASE_DIR / "results_130q_nota_fct"
REPORTS_DIR = BASE_DIR / "results_130q_nota_fct" / "reports"
OUTPUT_JSON = REPORTS_DIR / "difficulty_recheck_deepseek.json"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5

MODELS = ["llama3.1_8b", "qwen2.5_7b", "gemma_7b", "deepseek-r1_7b"]


def get_api_key():
    """Get DeepSeek API key from config or env."""
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def load_benchmark() -> list:
    """Load 130q benchmark."""
    items = []
    with open(BENCHMARK_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def load_results() -> dict:
    """Load model results: model -> {qid: {correct: bool}}."""
    out = {}
    for m in MODELS:
        path = RESULTS_DIR / f"results_{m}.json"
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        out[m] = {x["id"]: x for x in data}
    return out


def identify_disagreeing_questions(bench: list, results: dict) -> list:
    """Find questions where labeled difficulty disagrees with model performance."""
    disagree = []
    for r in bench:
        qid = r["id"]
        diff = r.get("metadata", {}).get("difficulty", 0)
        correct_count = sum(
            1 for m in MODELS
            if results.get(m, {}).get(qid, {}).get("correct")
        )
        pct = 100 * correct_count / len(MODELS) if MODELS else 0

        if diff <= 0.55 and pct < 50:
            disagree.append({
                "id": qid,
                "current_difficulty": diff,
                "models_correct_pct": pct,
                "reason": "labeled_easy_but_hard",
            })
        elif diff >= 0.7 and pct >= 75:
            disagree.append({
                "id": qid,
                "current_difficulty": diff,
                "models_correct_pct": pct,
                "reason": "labeled_hard_but_easy",
            })
    return disagree


def build_difficulty_prompt(item: dict, context: dict) -> str:
    """Build prompt for DeepSeek to suggest difficulty."""
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items()) if isinstance(options, dict) else str(options)
    task = item.get("task", "NOTA")
    current = context.get("current_difficulty", 0)
    reason = context.get("reason", "")
    pct = context.get("models_correct_pct", 0)

    return f"""You are an expert in medical education and assessment design. Evaluate the difficulty of this diabetes clinical multiple-choice question.

**Question ID**: {qid}
**Task type**: {task}
**Current difficulty label**: {current} (scale 0.0 = easiest, 1.0 = hardest)
**Context**: Model performance suggests {reason}. {pct:.0f}% of 4 LLMs answered correctly.

**Stem**: {question}

**Options**:
{opts_text}

**Your task**: Suggest a revised difficulty score (0.0 to 1.0) that better reflects how challenging this question is for an LLM or clinician. Consider:
- Factual complexity and guideline nuance
- Distractor plausibility (for NOTA: how convincing are the wrong options?)
- Subtle clinical reasoning required
- Whether the correct answer is obvious or requires careful elimination

Respond with ONLY a single line in this exact format:
DIFFICULTY: <number between 0.0 and 1.0>

Example: DIFFICULTY: 0.65
"""


def call_deepseek(prompt: str, api_key: str) -> dict:
    """Call DeepSeek API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert in medical assessment. Output only the requested format."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 200,
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}


def parse_difficulty(content: str) -> float | None:
    """Extract difficulty from DeepSeek response."""
    if not content:
        return None
    m = re.search(r"DIFFICULTY:\s*([0-9.]+)", content, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        return max(0.0, min(1.0, v))
    return None


def main():
    parser = argparse.ArgumentParser(description="Re-check difficulty via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Only identify questions, no API calls")
    parser.add_argument("--apply", action="store_true", help="Apply suggested difficulties to benchmark")
    args = parser.parse_args()

    bench = load_benchmark()
    results = load_results()
    id_to_item = {r["id"]: r for r in bench}

    disagree = identify_disagreeing_questions(bench, results)
    print(f"Found {len(disagree)} questions where performance disagrees with difficulty label.")

    if args.dry_run:
        for d in disagree:
            print(f"  {d['id']}: diff={d['current_difficulty']}, models_correct={d['models_correct_pct']:.0f}% ({d['reason']})")
        return

    # If report exists and --apply, load from it instead of re-calling API
    if args.apply and OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        reports = data.get("difficulty_recheck", [])
        print(f"Loaded {len(reports)} results from existing report.")
    else:
        api_key = get_api_key()
        if not api_key:
            print("Error: DeepSeek API key not found. Set DEEPSEEK_API_KEY or add to config.py")
            raise SystemExit(1)

        reports = []
        for i, ctx in enumerate(disagree):
            qid = ctx["id"]
            item = id_to_item.get(qid)
            if not item:
                reports.append({**ctx, "suggested_difficulty": None, "error": "Not in benchmark"})
                continue

            prompt = build_difficulty_prompt(item, ctx)
            print(f"Calling DeepSeek for {qid} ({i+1}/{len(disagree)})...")
            out = call_deepseek(prompt, api_key)

            suggested = parse_difficulty(out.get("content", "")) if out.get("content") else None
            reports.append({
                **ctx,
                "suggested_difficulty": suggested,
                "raw_response": out.get("content", ""),
                "error": out.get("error"),
            })
            time.sleep(API_DELAY)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"difficulty_recheck": reports}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_JSON}")

    if args.apply:
        # Build qid -> suggested_difficulty for valid suggestions
        updates = {}
        for r in reports:
            if r.get("suggested_difficulty") is not None:
                updates[r["id"]] = r["suggested_difficulty"]

        if not updates:
            print("No valid suggestions to apply.")
            return

        # Update benchmark
        for item in bench:
            qid = item.get("id")
            if qid in updates:
                if "metadata" not in item:
                    item["metadata"] = {}
                item["metadata"]["difficulty"] = updates[qid]
                item["metadata"]["difficulty_source"] = "deepseek_recheck"

        with open(BENCHMARK_JSONL, "w", encoding="utf-8") as f:
            for item in bench:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Applied {len(updates)} difficulty updates to {BENCHMARK_JSONL}")


if __name__ == "__main__":
    main()
