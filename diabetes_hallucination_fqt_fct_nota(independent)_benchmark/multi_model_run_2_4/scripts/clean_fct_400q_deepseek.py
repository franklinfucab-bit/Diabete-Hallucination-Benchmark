"""
Clean 65 FCT questions in 400q benchmark to ensure "一正三误" (one correct, three clearly wrong).
Uses DeepSeek API for validation. For failed items, optionally calls API again to suggest
revised distractors.

Outputs:
  - benchmark/one_correct_cleaned_65q_fct.jsonl (PASS items)
  - benchmark/one_correct_cleaned_65q_fct_failed_for_review.jsonl (FAIL items + revision suggestions)
  - reports/one_correct_cleaned_65q_fct_audit_report.json (full audit)

Usage:
  python clean_fct_400q_deepseek.py
  python clean_fct_400q_deepseek.py --dry-run
  python clean_fct_400q_deepseek.py --no-revision   # Skip revision suggestions for failed items
  python clean_fct_400q_deepseek.py --strict --ids FCT_018,FCT_039,FCT_091   # Re-validate with NOTA-level strictness
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
    print("Error: 'requests' is required. Run: pip install requests")
    raise SystemExit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FCT_SOURCE = BASE_DIR / "benchmark" / "100q_fct_filtered.jsonl"
OUTPUT_CLEANED = BASE_DIR / "benchmark" / "one_correct_cleaned_65q_fct.jsonl"
OUTPUT_FAILED = BASE_DIR / "benchmark" / "one_correct_cleaned_65q_fct_failed_for_review.jsonl"
REPORTS_DIR = BASE_DIR / "results_400q_diabetes" / "reports"
OUTPUT_AUDIT = REPORTS_DIR / "one_correct_cleaned_65q_fct_audit_report.json"
OUTPUT_STRICT_AUDIT = REPORTS_DIR / "one_correct_cleaned_65q_fct_strict_revalidate.json"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5


def load_fct(path: Path) -> list[dict]:
    """Load FCT items from JSONL."""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def build_validation_prompt(item: dict) -> str:
    """Build prompt for DeepSeek to verify 一正三误."""
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    answer = item.get("answer", "")
    if isinstance(options, dict):
        opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items())
    else:
        opts_text = str(options)

    return f"""You are an expert in diabetes medicine and assessment design. Analyze this FCT (Factual Clinical Test) multiple-choice question.

**FCT format**: One correct answer (A/B/C/D) and three distractors. A well-designed FCT has:
- Exactly one option that is correct per current guidelines/evidence
- Three distractors that are clearly wrong (factual error, guideline violation, or context mismatch)
- No distractor that a reasonable expert could argue is partially correct

**Question ID**: {qid}

**Stem**: {question}

**Options**:
{opts_text}

**Marked correct answer**: {answer}

**Your task**: Verify "一正三误" (one correct, three clearly wrong).
1. Is the marked correct answer indeed the only correct option?
2. For each distractor: Is it clearly wrong? Could it be defensible in some contexts?
3. End with a verdict on a new line: either "VERDICT: PASS" or "VERDICT: FAIL: [brief reason, e.g. 'Option B partially correct per some guidelines']"
"""


def build_validation_prompt_strict(item: dict) -> str:
    """Build STRICT prompt aligned with NOTA validation standards.
    Use when re-validating items that passed standard check but may have logic issues
    (e.g., distractors defensible per evolving guidelines or expert disagreement).
    """
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    answer = item.get("answer", "")
    if isinstance(options, dict):
        opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items())
    else:
        opts_text = str(options)

    return f"""You are an expert in diabetes medicine and assessment design. Analyze this FCT (Factual Clinical Test) multiple-choice question using the SAME STRICTNESS as for NOTA (None of the above) validation.

**Context**: This FCT will be converted to a NOTA item. In NOTA format, the three distractors are shown as options A, B, C, and "None of the above" is correct. For NOTA to be valid, ALL distractors must be demonstrably wrong—with NO ambiguity.

**STRICT standard** (apply NOTA-level rigor):
- Each distractor must be **demonstrably wrong** (factual error, guideline violation, or context mismatch)
- **FAIL if ANY expert could argue** a distractor is correct, partially correct, or guideline-supported
- Consider **evolving guidelines** (e.g., SGLT2i in acute HF: some say hold, others say continue GDMT)—if there is genuine expert disagreement, the distractor is defensible and the question FAILS
- Consider **alternative reasonable strategies** (e.g., DPP-4 for simplification vs GLP-1 for cardiorenal benefit)—if a distractor represents a valid clinical choice, FAIL
- When in doubt, FAIL. Ambiguity invalidates both FCT and derived NOTA items.

**Question ID**: {qid}

**Stem**: {question}

**Options**:
{opts_text}

**Marked correct answer**: {answer}

**Your task**: Apply strict NOTA-level validation.
1. Could ANY knowledgeable clinician argue that a distractor is correct or reasonable per current or evolving guidelines?
2. Is there genuine expert disagreement on the "correct" action in this scenario?
3. End with a verdict: "VERDICT: PASS" (only if all distractors are unequivocally wrong) or "VERDICT: FAIL: [brief reason]"
"""


def build_revision_prompt(item: dict, analysis: str, problematic_options: list[str]) -> str:
    """Build prompt for DeepSeek to suggest revised distractors for failed items."""
    qid = item.get("id", "")
    question = item.get("question", "")
    options = item.get("options", {})
    answer = item.get("answer", "")

    if isinstance(options, dict):
        opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items())
    else:
        opts_text = str(options)

    problem_list = ", ".join(problematic_options) if problematic_options else "one or more distractors"
    return f"""You previously analyzed this FCT question and found it FAILS the "一正三误" standard.

**Question ID**: {qid}
**Stem**: {question}
**Options**:
{opts_text}
**Correct answer**: {answer}

**Your prior analysis**: {analysis}

**Problematic option(s)**: {problem_list}

**Your task**: For each problematic distractor, suggest a REVISED version that:
1. Preserves the stem and correct answer
2. Is clearly wrong (factual error, guideline violation, or context mismatch)
3. Remains plausible as a distractor (not obviously absurd)
4. No reasonable expert could argue it is partially correct

Provide your suggestions in this format:
- Option X (revised): [full revised option text]
- Option Y (revised): [full revised option text]
(only for options that need revision)
"""


def call_deepseek(prompt: str, api_key: str, system: str = "You are an expert in diabetes medicine and assessment design.") -> dict:
    """Call DeepSeek API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}


def parse_verdict(analysis: str) -> tuple[str, str]:
    """Parse PASS/FAIL from analysis. Returns (verdict, reason)."""
    if not analysis:
        return "FAIL", "No analysis returned"
    text = analysis.strip().upper()
    if "VERDICT: PASS" in text:
        return "PASS", ""
    m = re.search(r"VERDICT:\s*FAIL[:\s]*(.+?)(?:\n|$)", analysis, re.IGNORECASE | re.DOTALL)
    if m:
        reason = m.group(1).strip()[:500]
        return "FAIL", reason
    if "FAIL" in text or "logic issue" in text.lower() or "partially correct" in text.lower():
        return "FAIL", "Verdict implied from analysis"
    if "PASS" in text:
        return "PASS", ""
    return "FAIL", "Could not parse verdict"


def extract_problematic_options(analysis: str) -> list[str]:
    """Extract option letters (A/B/C/D) mentioned as problematic from analysis."""
    options = []
    for opt in ["A", "B", "C", "D"]:
        if re.search(rf"\boption\s+{opt}\b|\b{opt}\s+is\s+(?:partially|possibly|arguably)|{opt}\s*[:\-]\s*(?:partially|defensible)", analysis, re.IGNORECASE):
            options.append(opt)
    if not options and "FAIL" in analysis.upper():
        options = ["A", "B", "C", "D"]
    return options[:4]


def get_api_key():
    """Get DeepSeek API key from env or config.py."""
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Clean FCT questions for 一正三误 via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Load FCT only, no API calls")
    parser.add_argument("--no-revision", action="store_true", help="Skip revision suggestions for failed items")
    parser.add_argument("--strict", action="store_true", help="Use NOTA-level strict validation (fail if any expert could argue a distractor)")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated FCT IDs to validate (e.g. FCT_018,FCT_039,FCT_091). If empty, validate all.")
    args = parser.parse_args()

    api_key = get_api_key()
    if not args.dry_run and not api_key:
        print("Error: DEEPSEEK_API_KEY not found. Set in env or config.py (project root).")
        raise SystemExit(1)

    if not FCT_SOURCE.exists():
        print(f"Error: FCT source not found: {FCT_SOURCE}")
        raise SystemExit(1)

    items = load_fct(FCT_SOURCE)
    if args.ids:
        id_set = {x.strip() for x in args.ids.split(",") if x.strip()}
        items = [q for q in items if q.get("id", "") in id_set]
        print(f"Filtered to {len(items)} items: {sorted(id_set)}")
    else:
        print(f"Loaded {len(items)} FCT items from {FCT_SOURCE.name}")

    if args.dry_run:
        print("Dry-run: no API calls. Exiting.")
        return

    if not items:
        print("Error: No items to validate.")
        raise SystemExit(1)

    use_strict = args.strict
    if use_strict:
        print("Using STRICT (NOTA-level) validation prompt.")

    cleaned = []
    failed = []
    audit = {"summary": {}, "items": [], "strict_mode": use_strict}

    for i, item in enumerate(items):
        qid = item.get("id", "unknown")
        print(f"[{i+1}/{len(items)}] {qid}...", end=" ", flush=True)

        prompt = build_validation_prompt_strict(item) if use_strict else build_validation_prompt(item)
        out = call_deepseek(prompt, api_key)
        analysis = out.get("content") or ""
        err = out.get("error")

        if err:
            print(f"API error: {err}")
            audit["items"].append({
                "id": qid,
                "verdict": "ERROR",
                "reason": err,
                "analysis": None,
                "revision_suggestion": None,
            })
            failed.append({**item, "audit_error": err})
            time.sleep(API_DELAY)
            continue

        verdict, reason = parse_verdict(analysis)
        print(verdict)

        audit_entry = {
            "id": qid,
            "verdict": verdict,
            "reason": reason,
            "analysis": analysis,
        }

        if verdict == "PASS":
            cleaned.append(item)
            audit_entry["revision_suggestion"] = None
        else:
            problematic = extract_problematic_options(analysis)
            revision_suggestion = None

            if not args.no_revision and problematic:
                time.sleep(API_DELAY)
                rev_prompt = build_revision_prompt(item, analysis, problematic)
                rev_out = call_deepseek(rev_prompt, api_key)
                revision_suggestion = rev_out.get("content") or ""
                if rev_out.get("error"):
                    revision_suggestion = f"[API error: {rev_out['error']}]"

            audit_entry["problematic_options"] = problematic
            audit_entry["revision_suggestion"] = revision_suggestion
            failed.append({
                **item,
                "audit_verdict": verdict,
                "audit_reason": reason,
                "audit_analysis": analysis,
                "revision_suggestion": revision_suggestion,
            })

        audit["items"].append(audit_entry)
        time.sleep(API_DELAY)

    audit["summary"] = {
        "total": len(items),
        "passed": len(cleaned),
        "failed": len(failed),
        "cleaned_file": str(OUTPUT_CLEANED),
        "failed_file": str(OUTPUT_FAILED),
    }

    OUTPUT_CLEANED.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FAILED.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # When --strict + --ids (targeted revalidation), only write strict audit report
    strict_revalidate_only = use_strict and bool(args.ids)
    if strict_revalidate_only:
        with open(OUTPUT_STRICT_AUDIT, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {OUTPUT_STRICT_AUDIT} (strict revalidation report)")
    else:
        with open(OUTPUT_CLEANED, "w", encoding="utf-8") as f:
            for item in cleaned:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"\nWrote {OUTPUT_CLEANED} ({len(cleaned)} items)")

        with open(OUTPUT_FAILED, "w", encoding="utf-8") as f:
            for item in failed:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Wrote {OUTPUT_FAILED} ({len(failed)} items)")

        out_audit = OUTPUT_STRICT_AUDIT if use_strict else OUTPUT_AUDIT
        with open(out_audit, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
        print(f"Wrote {out_audit}")

    print(f"\nSummary: {len(cleaned)} passed, {len(failed)} failed")


if __name__ == "__main__":
    main()
