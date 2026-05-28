"""
Audit the 108 universal failure questions (all 5 models wrong) for logic issues,
ambiguity, or outdated content using DeepSeek API.
Output: results_1400q_golden/reports/universal_failures_audit.json
API key from config.py or DEEPSEEK_API_KEY env var.

Usage:
  python audit_universal_failures_deepseek.py
  python audit_universal_failures_deepseek.py --dry-run
  python audit_universal_failures_deepseek.py --limit 5   # Test with 5 questions
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Error: 'requests' required. Run: pip install requests")
    raise SystemExit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# Benchmark: prefer results_1400q_golden/benchmark, fallback to output/Json
BENCHMARK_DIR = BASE_DIR / "results_1400q_golden" / "benchmark"
BENCHMARK_NOTA = BENCHMARK_DIR / "350q_nota_from_fct_golden_seed.jsonl"
BENCHMARK_AOTA = BENCHMARK_DIR / "350q_aota_from_fct_golden_seed.jsonl"
if not BENCHMARK_NOTA.exists():
    BENCHMARK_NOTA = PROJECT_ROOT / "output" / "Json" / "350q_nota_from_fct_golden_seed.jsonl"
if not BENCHMARK_AOTA.exists():
    BENCHMARK_AOTA = PROJECT_ROOT / "output" / "Json" / "350q_aota_from_fct_golden_seed.jsonl"
RESULTS_DIR = BASE_DIR / "results_1400q_golden"
REPORTS_DIR = RESULTS_DIR / "reports"
OUTPUT_JSON = REPORTS_DIR / "universal_failures_audit.json"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5

MODELS = ["qwen2.5_7b", "llama3.1_8b", "gemma_7b", "deepseek-r1_7b", "mistral_latest"]


def get_api_key():
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def load_benchmark() -> dict:
    """Load benchmark: id -> item."""
    id_to_item = {}
    for path in [BENCHMARK_NOTA, BENCHMARK_AOTA]:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    q = json.loads(line)
                    id_to_item[q["id"]] = q
    return id_to_item


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


def get_universal_failures(id_to_item: dict, results: dict) -> list:
    """Questions all models got wrong."""
    failures = []
    for qid in id_to_item:
        if all(not results.get(m, {}).get(qid, {}).get("correct") for m in MODELS if qid in results.get(m, {})):
            failures.append(qid)
    return sorted(failures)


def build_prompt(item: dict) -> str:
    """Build prompt for DeepSeek to audit question."""
    qid = item.get("id", "")
    task = item.get("task", "NOTA")
    question = item.get("question", "")
    options = item.get("options", {})
    opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items()) if isinstance(options, dict) else str(options)
    answer = item.get("answer", "D")

    return f"""You are an expert in medical education and assessment design. This diabetes clinical question was answered incorrectly by ALL 5 LLMs (Qwen, Llama, Gemma, DeepSeek, Mistral). Audit it for potential issues.

**Question ID**: {qid}
**Task type**: {task}
**Correct answer**: {answer}

**Stem**: {question}

**Options**:
{opts_text}

**Your task**: Analyze why all models might fail. Consider:
1. **Logic issues**: Is the correct answer unambiguous? Could any distractor be defensible? Double-barreled or confusing wording?
2. **Ambiguity**: Is the stem vague? Does "most appropriate" or "most accurate" allow multiple interpretations? Could guideline updates change the answer?
3. **Outdated content**: Does the question rely on superseded guidelines, old drug names, or outdated thresholds?
4. **Distractor quality**: Are wrong options too plausible? Or is the correct answer non-obvious even to experts?

Provide a concise analysis (bullet points OK). End with a verdict:
- "Benchmark issue: [brief description]" if the question has flaws that warrant review/removal
- "No benchmark issue" if the question is sound and models simply lack the knowledge
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
                "content": "You are an expert in medical assessment. Audit questions for logic, ambiguity, and outdated content. Be concise and specific.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}


def has_benchmark_issue(analysis: str) -> bool:
    """Heuristic: does the analysis indicate a benchmark issue?"""
    if not analysis:
        return False
    text = analysis.lower()
    if "no benchmark issue" in text:
        return False
    if "benchmark issue:" in text or "benchmark issues:" in text:
        return True
    if "logic issue" in text or "ambiguous" in text or "outdated" in text:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Audit universal failure questions via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Identify questions only, no API")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions (0 = all)")
    args = parser.parse_args()

    id_to_item = load_benchmark()
    results = load_results()
    failures = get_universal_failures(id_to_item, results)
    print(f"Found {len(failures)} universal failure questions (all 5 models wrong).")

    if args.limit:
        failures = failures[: args.limit]
        print(f"Limited to first {len(failures)} questions.")

    if args.dry_run:
        print("Universal failure IDs:", failures[:20], "..." if len(failures) > 20 else "")
        return

    api_key = get_api_key()
    if not api_key:
        print("Error: DeepSeek API key not found. Set DEEPSEEK_API_KEY or add to config.py")
        raise SystemExit(1)

    reports = []
    for i, qid in enumerate(failures):
        item = id_to_item.get(qid)
        if not item:
            reports.append({"id": qid, "task": "", "analysis": None, "has_benchmark_issue": None, "error": "Not in benchmark"})
            continue

        prompt = build_prompt(item)
        print(f"Calling DeepSeek for {qid} ({i+1}/{len(failures)})...")
        out = call_deepseek(prompt, api_key)
        analysis = out.get("content")
        has_issue = has_benchmark_issue(analysis) if analysis else None
        reports.append({
            "id": qid,
            "task": item.get("task", ""),
            "question": item.get("question", "")[:200] + "..." if len(item.get("question", "")) > 200 else item.get("question", ""),
            "analysis": analysis,
            "has_benchmark_issue": has_issue,
            "error": out.get("error"),
        })
        time.sleep(API_DELAY)

    with_issues = [r for r in reports if r.get("has_benchmark_issue")]
    summary = {
        "total_audited": len(reports),
        "with_benchmark_issues": len(with_issues),
        "ids_with_issues": [r["id"] for r in with_issues],
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "audit_results": reports}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Summary: {summary['with_benchmark_issues']}/{summary['total_audited']} questions flagged with potential benchmark issues.")
    if with_issues:
        print("IDs with issues:", ", ".join(summary["ids_with_issues"][:20]), "..." if len(with_issues) > 20 else "")


if __name__ == "__main__":
    main()
