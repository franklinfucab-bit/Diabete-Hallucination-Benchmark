"""
Collect the 10 hardest NOTA questions (all models wrong) and use DeepSeek API to analyze
whether each has logic issues as a NOTA (None of the above) question.
Output: reports/hardest_nota_deepseek_logic_analysis.json
Requires: DEEPSEEK_API_KEY environment variable (unless --dry-run).

Usage:
  set DEEPSEEK_API_KEY=your_key   (Windows)
  python analyze_hardest_nota_logic_deepseek.py
  python analyze_hardest_nota_logic_deepseek.py --dry-run   # Only collect questions, no API
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Project root (Diabete Hallucination Benchmark) for config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Error: 'requests' is required. Run: pip install requests")
    raise SystemExit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_JSONL = BASE_DIR / "benchmark" / "400q_diabetes_benchmark_combined_ready.jsonl"
REPORTS_DIR = BASE_DIR / "results_400q_diabetes" / "reports"
OUTPUT_JSON = REPORTS_DIR / "hardest_nota_deepseek_logic_analysis.json"

# Hardest NOTA topics (all models wrong) from 400q_diabetes_comparison.md
HARDEST_NOTA_IDS = [
    "NOTA_091",  # GLP-1 receptor agonists
    "NOTA_018",  # acute decompensated heart failure
    "NOTA_064",  # hypoglycemia
    "NOTA_057",  # antepartum_care
    "NOTA_045",  # type 2 diabetes management
    "NOTA_076",  # nephrology
    "NOTA_039",  # renal protection
    "NOTA_025",  # SGLT2 inhibitors
    "NOTA_023",  # guideline-based management
    "NOTA_074",  # neuropathy_footcare
]

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5


def load_benchmark_id_to_item() -> dict:
    """Load 400q benchmark and return id -> full item."""
    lookup = {}
    if not BENCHMARK_JSONL.exists():
        return lookup
    with open(BENCHMARK_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)
            lookup[q.get("id", "")] = q
    return lookup


def build_prompt(item: dict) -> str:
    """Build prompt for DeepSeek to analyze NOTA logic."""
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    if isinstance(options, dict):
        opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items())
    else:
        opts_text = str(options)

    return f"""You are an expert in medical education and assessment design. Analyze the following "None of the above" (NOTA) multiple-choice question for potential **logic issues**.

**NOTA format**: The correct answer is D ("None of the above"), meaning options A, B, and C are all intended to be incorrect or misleading. A well-designed NOTA question should have:
- A stem that clearly asks for the "most appropriate" or "most accurate" response
- Three distractors (A, B, C) that are each demonstrably wrong, incomplete, or overstated
- No ambiguity such that a reasonable expert could argue one of A/B/C is partially correct
- Wording that does not trick the test-taker through unclear scope (e.g., "all", "always", "never") unless that is the intended flaw

**Question ID**: {qid}

**Stem**: {question}

**Options**:
{opts_text}

**Your task**: Analyze whether this question has logic issues as a NOTA item. Consider:
1. **Clarity of NOTA**: Is it unambiguous that none of A, B, or C is correct? Could any option be defensible in some contexts?
2. **Distractor quality**: Are A, B, C clearly wrong for the right reasons (e.g., factual error, overgeneralization, wrong priority)?
3. **Stem/scope**: Does the stem allow a single best answer, or is it vague enough that "none of the above" could be challenged?
4. **Potential issues**: Double-barreled options, ambiguous "most appropriate," or wording that could confuse even experts.

Provide a concise, structured analysis (bullet points OK). End with a one-sentence verdict: either "No significant logic issue" or "Logic issue: [brief description]."
"""


def call_deepseek_api(prompt: str, api_key: str) -> dict:
    """Call DeepSeek API for analysis."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert in medical assessment and item design. Analyze NOTA (None of the above) questions for logic, clarity, and fairness. Be concise and specific.",
            },
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


def get_api_key():
    """Get DeepSeek API key from environment or project config.py."""
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Analyze hardest NOTA questions for logic issues via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Only collect and save the 10 questions; do not call API")
    args = parser.parse_args()

    api_key = get_api_key()
    if not args.dry_run and not api_key:
        print("Error: DeepSeek API key not found. Set DEEPSEEK_API_KEY in the environment or in config.py (project root).")
        print("Use --dry-run to only collect the questions without calling the API.")
        raise SystemExit(1)

    lookup = load_benchmark_id_to_item()
    missing = [qid for qid in HARDEST_NOTA_IDS if qid not in lookup]
    if missing:
        print(f"Warning: Missing from benchmark: {missing}")

    results = []
    for i, qid in enumerate(HARDEST_NOTA_IDS):
        item = lookup.get(qid)
        if not item:
            results.append({"id": qid, "topic": "", "question": "", "options": {}, "analysis": None, "error": "Not in benchmark"})
            continue

        topic = (item.get("metadata") or {}).get("tags", [])
        if isinstance(topic, list):
            topic = next((t for t in topic if str(t) not in ("diabetes", "NOTA", "FCT")), topic[0] if topic else "")
        else:
            topic = str(topic)

        if args.dry_run:
            results.append({
                "id": qid,
                "topic": topic,
                "question": item.get("question", ""),
                "options": item.get("options", {}),
                "answer": item.get("answer", "D"),
                "analysis": None,
                "error": None,
            })
            continue

        prompt = build_prompt(item)
        print(f"Calling DeepSeek for {qid} ({i+1}/{len(HARDEST_NOTA_IDS)})...")
        out = call_deepseek_api(prompt, api_key)
        results.append({
            "id": qid,
            "topic": topic,
            "question": item.get("question", ""),
            "options": item.get("options", {}),
            "answer": item.get("answer", "D"),
            "analysis": out.get("analysis"),
            "error": out.get("error"),
        })
        time.sleep(API_DELAY)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"hardest_nota_logic_analysis": results}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_JSON}")
    if args.dry_run:
        print("Dry-run: collected 10 questions. Run without --dry-run and set DEEPSEEK_API_KEY to get DeepSeek analysis.")


if __name__ == "__main__":
    main()
