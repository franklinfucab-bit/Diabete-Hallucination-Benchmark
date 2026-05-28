"""
Analyze ALL NOTA questions in the 130q benchmark for logic issues via DeepSeek API.
Output: results_130q_nota_fct/reports/all_nota_logic_analysis.json
API key from config.py or DEEPSEEK_API_KEY env var.

Usage:
  python analyze_all_nota_logic_deepseek.py
  python analyze_all_nota_logic_deepseek.py --dry-run   # Collect questions only, no API
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
REPORTS_DIR = BASE_DIR / "results_130q_nota_fct" / "reports"
OUTPUT_JSON = REPORTS_DIR / "all_nota_logic_analysis.json"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5


def get_api_key():
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def load_all_nota() -> list:
    """Load all NOTA questions from 130q benchmark."""
    items = []
    with open(BENCHMARK_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)
            if q.get("task") == "NOTA":
                items.append(q)
    return items


def build_prompt(item: dict) -> str:
    """Build prompt for DeepSeek to analyze NOTA logic."""
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items()) if isinstance(options, dict) else str(options)

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


def call_deepseek(prompt: str, api_key: str) -> dict:
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
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"analysis": content, "error": None}
    except Exception as e:
        return {"analysis": None, "error": str(e)}


def has_logic_issue(analysis: str) -> bool:
    """Heuristic: does the analysis indicate a logic issue?"""
    if not analysis:
        return False
    text = analysis.lower()
    if "no significant logic issue" in text or "no logic issue" in text:
        return False
    if "logic issue:" in text or "logic issues:" in text:
        return True
    if "potential issue" in text or "concern:" in text:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Analyze all NOTA questions for logic issues via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Only collect questions, no API calls")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions (0 = all)")
    args = parser.parse_args()

    items = load_all_nota()
    if args.limit:
        items = items[: args.limit]
        print(f"Limited to first {len(items)} NOTA questions.")
    print(f"Found {len(items)} NOTA questions in 130q benchmark.")

    if not items:
        print("No NOTA questions found.")
        return

    api_key = get_api_key()
    if not args.dry_run and not api_key:
        print("Error: DeepSeek API key not found. Set DEEPSEEK_API_KEY or add to config.py")
        print("Use --dry-run to collect questions without calling API.")
        raise SystemExit(1)

    results = []
    for i, item in enumerate(items):
        qid = item.get("id", "")
        topic = (item.get("metadata") or {}).get("tags", [])
        if isinstance(topic, list):
            topic = next((t for t in topic if str(t) not in ("diabetes", "NOTA", "FCT")), topic[0] if topic else "")

        if args.dry_run:
            results.append({
                "id": qid,
                "topic": topic,
                "question": item.get("question", ""),
                "options": item.get("options", {}),
                "answer": item.get("answer", "D"),
                "difficulty": (item.get("metadata") or {}).get("difficulty"),
                "analysis": None,
                "has_logic_issue": None,
                "error": None,
            })
            continue

        prompt = build_prompt(item)
        print(f"Calling DeepSeek for {qid} ({i+1}/{len(items)})...")
        out = call_deepseek(prompt, api_key)
        analysis = out.get("analysis")
        has_issue = has_logic_issue(analysis) if analysis else None
        results.append({
            "id": qid,
            "topic": topic,
            "question": item.get("question", ""),
            "options": item.get("options", {}),
            "answer": item.get("answer", "D"),
            "difficulty": (item.get("metadata") or {}).get("difficulty"),
            "analysis": analysis,
            "has_logic_issue": has_issue,
            "error": out.get("error"),
        })
        time.sleep(API_DELAY)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with_logic_issues = [r for r in results if r.get("has_logic_issue")]
    summary = {
        "total_nota": len(results),
        "with_logic_issues": len(with_logic_issues),
        "ids_with_issues": [r["id"] for r in with_logic_issues],
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "all_nota_logic_analysis": results}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Summary: {summary['with_logic_issues']}/{summary['total_nota']} NOTA questions flagged with potential logic issues.")
    if with_logic_issues:
        print("IDs with issues:", ", ".join(summary["ids_with_issues"]))


if __name__ == "__main__":
    main()
