"""
Audit NOTA questions for logic issues and fix defensible options in one API call per question.
- Loads: 1000q_nota_from_fct_hardcore_lifestyle.jsonl, 1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl
- For each NOTA: one DeepSeek call (analyze + regenerate only defensible option(s))
- Outputs: 1000q_nota_benchmark_v4_hardcore_lifestyle.jsonl, 1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle_aligned.jsonl, reports

Usage:
  python scripts/audit_and_fix_nota_1000q_deepseek.py
  python scripts/audit_and_fix_nota_1000q_deepseek.py --dry-run
  python scripts/audit_and_fix_nota_1000q_deepseek.py --limit 5   # Test with 5 questions
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTA_SOURCE = PROJECT_ROOT / "output" / "Json" / "1000q_nota_from_fct_hardcore_lifestyle.jsonl"
FCT_SOURCE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl"
OUTPUT_NOTA = PROJECT_ROOT / "output" / "Json" / "1000q_nota_benchmark_v4_hardcore_lifestyle.jsonl"
OUTPUT_FCT = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle_aligned.jsonl"
REPORTS_DIR = PROJECT_ROOT / "output" / "Json" / "reports"
OUTPUT_ANALYSIS = REPORTS_DIR / "1000q_nota_logic_analysis.json"
OUTPUT_ISSUES = REPORTS_DIR / "1000q_nota_logic_issues_report.json"

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


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def get_fct_correct_text(fct: dict) -> str:
    """Extract correct answer text from FCT (1000q format: options array, correct_answer)."""
    opts = fct.get("options", [])
    correct_letter = fct.get("correct_answer", "")
    for o in opts:
        if o.get("option_id") == correct_letter:
            return o.get("text", "")
    return ""


def build_combined_prompt(nota: dict, correct_text: str) -> str:
    """Build prompt for logic analysis + regeneration of defensible option(s) only."""
    qid = nota.get("id", "")
    question = nota.get("question", "")
    options = nota.get("options", {})
    opts_text = "\n".join(f"  {k}: {v}" for k, v in options.items() if k != "D")

    return f"""You are an expert in medical education and assessment design.

**Task 1 – Logic analysis**: Analyze this NOTA question. The correct answer is D ("None of the above"). Could any of A, B, or C be defensible or partially correct? If yes, state "Logic issue: [brief description]" and which option(s) are defensible (e.g. "Option A" or "Options A and B"). If no, state "No significant logic issue."

**Task 2 – Regeneration (only if logic issue)**: If you found a logic issue, regenerate ONLY the defensible option(s). For each defensible option, output a NEW replacement that is unequivocally incorrect per current guidelines (clear factual error). Keep non-defensible options unchanged. Ensure each new option is distinct from the other 2 options (no overlap or near-duplicate).

Output format (only output replacements for defensible options):
Defensible option(s): [A and/or B and/or C]
A. [new text if A was defensible; otherwise omit]
B. [new text if B was defensible; otherwise omit]
C. [new text if C was defensible; otherwise omit]

Only include lines for options you are replacing. If no logic issue, output "N/A" for regeneration.

**Question ID**: {qid}

**Stem**: {question}

**Options**:
{opts_text}

**Correct answer (what should be correct but is not in A/B/C)**: {correct_text[:500] if correct_text else "N/A"}
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
                "content": "You are an expert in medical assessment and item design. Analyze NOTA questions for logic issues. If you find a defensible option, regenerate ONLY that option with an unequivocally incorrect replacement. Be concise and specific.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    try:
        import requests
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}


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


def extract_defensible_options(analysis: str) -> list[str]:
    """Extract which options (A, B, C) are defensible from analysis text."""
    defensible = []
    text = analysis
    # Primary: "Defensible option(s): A" or "Defensible option(s): A, B" or "Defensible option(s): [A, B]"
    m = re.search(r"defensible option[s]?:\s*\[?([A-C,\sand]+)\]?", text, re.IGNORECASE)
    if m:
        chunk = m.group(1)
        for c in re.findall(r"[A-C]", chunk):
            if c not in defensible:
                defensible.append(c)
    # Fallback: "Option A is defensible", "Options A and B"
    if not defensible:
        for letter in ["A", "B", "C"]:
            if re.search(rf"option[s]?\s+{letter}\s+(?:is|are|was|were)?\s*(?:defensible|correct|appropriate)", text, re.IGNORECASE):
                defensible.append(letter)
            elif re.search(rf"(?:defensible|correct).*{letter}\b", text, re.IGNORECASE):
                defensible.append(letter)
    return list(dict.fromkeys(defensible))  # preserve order, no dupes


def parse_replacement(text: str, letter: str) -> str | None:
    """Parse replacement text for a single option (e.g. A. ...)."""
    if not text or not text.strip():
        return None
    # Match "A. text" - capture until next "B." or "C." or end
    next_letters = [l for l in "ABC" if l != letter]
    pattern = rf"{letter}\s*[.:]\s*(.+?)(?=\s*(?:{'|'.join(next_letters)})\s*[.:]|\s*$)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        opt = re.sub(r"\s+", " ", m.group(1).strip()).strip()
        if opt and len(opt) > 15 and "keep" not in opt.lower()[:20] and "n/a" not in opt.lower()[:10]:
            return opt
    # Fallback: "A. " at start of line
    for line in text.split("\n"):
        m2 = re.match(rf"^{letter}\s*[.:]\s*(.+)$", line.strip(), re.IGNORECASE)
        if m2:
            opt = re.sub(r"\s+", " ", m2.group(1).strip()).strip()
            if opt and len(opt) > 15:
                return opt
    return None


def parse_replacements(analysis: str, defensible: list[str]) -> dict[str, str]:
    """Parse replacement text for each defensible option. Returns {letter: new_text}."""
    result = {}
    for letter in defensible:
        repl = parse_replacement(analysis, letter)
        if repl:
            result[letter] = repl
    return result


def is_distinct_from_others(new_text: str, other_texts: list[str]) -> bool:
    """Check that new_text is sufficiently different from other options (no major overlap)."""
    new_lower = new_text.lower()
    for other in other_texts:
        if not other or len(other) < 20:
            continue
        other_lower = other.lower()
        # Reject if >60% of words in new appear in other (simple heuristic)
        new_words = set(w for w in new_lower.split() if len(w) > 3)
        other_words = set(w for w in other_lower.split() if len(w) > 3)
        if new_words and other_words:
            overlap = len(new_words & other_words) / len(new_words)
            if overlap > 0.7:
                return False
    return True


def apply_fixes(nota: dict, replacements: dict[str, str]) -> dict:
    """Merge replacements into NOTA options. Only replace specified letters."""
    options = dict(nota.get("options", {}))
    for letter, text in replacements.items():
        if letter in options:
            options[letter] = text
    return {**nota, "options": options}


def build_aligned_fct(fct: dict, fixed_nota: dict) -> dict:
    """Build FCT that matches fixed NOTA: A,B,C from NOTA; D = correct from FCT. Preserve all other FCT fields."""
    opts = fixed_nota.get("options", {})
    correct_text = get_fct_correct_text(fct)
    aligned = dict(fct)
    aligned["options"] = [
        {"option_id": "A", "text": opts.get("A", ""), "is_correct": False},
        {"option_id": "B", "text": opts.get("B", ""), "is_correct": False},
        {"option_id": "C", "text": opts.get("C", ""), "is_correct": False},
        {"option_id": "D", "text": correct_text, "is_correct": True},
    ]
    aligned["correct_answer"] = "D"
    return aligned


def main():
    parser = argparse.ArgumentParser(description="Audit and fix NOTA logic issues via DeepSeek")
    parser.add_argument("--dry-run", action="store_true", help="Only load data, no API calls")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions (0 = all)")
    args = parser.parse_args()

    if not NOTA_SOURCE.exists():
        print(f"Error: NOTA source not found: {NOTA_SOURCE}")
        raise SystemExit(1)
    if not FCT_SOURCE.exists():
        print(f"Error: FCT source not found: {FCT_SOURCE}")
        raise SystemExit(1)

    nota_list = load_jsonl(NOTA_SOURCE)
    fct_list = load_jsonl(FCT_SOURCE)
    fct_by_id = {q.get("id", ""): q for q in fct_list}

    if args.limit:
        nota_list = nota_list[: args.limit]
        print(f"Limited to first {len(nota_list)} NOTA questions.")

    print(f"Loaded {len(nota_list)} NOTA, {len(fct_list)} FCT")

    api_key = get_api_key()
    if not args.dry_run and not api_key:
        print("Error: DEEPSEEK_API_KEY not found. Set DEEPSEEK_API_KEY or add to config.py")
        raise SystemExit(1)

    try:
        import requests
    except ImportError:
        print("Error: 'requests' required. Run: pip install requests")
        raise SystemExit(1)

    fixed_nota_list = []
    aligned_fct_list = []
    fct_by_id_ordered = {q.get("id", ""): q for q in fct_list}
    results = []
    ids_with_issues = []

    for i, nota in enumerate(nota_list):
        qid = nota.get("id", "")
        derived = nota.get("metadata", {}).get("derived_from", "")
        fct = fct_by_id.get(derived)

        if not fct:
            fixed_nota_list.append(nota)
            if derived in fct_by_id_ordered:
                aligned_fct_list.append(fct_by_id_ordered[derived])
            results.append({
                "id": qid,
                "has_logic_issue": False,
                "analysis": None,
                "defensible_options": [],
                "replacements": {},
                "error": "No FCT match",
            })
            continue

        correct_text = get_fct_correct_text(fct)

        if args.dry_run:
            fixed_nota_list.append(nota)
            aligned_fct_list.append(fct)
            results.append({
                "id": qid,
                "has_logic_issue": None,
                "analysis": None,
                "defensible_options": [],
                "replacements": {},
            })
            continue

        prompt = build_combined_prompt(nota, correct_text)
        print(f"[{i+1}/{len(nota_list)}] {qid}...", end=" ", flush=True)
        out = call_deepseek(prompt, api_key)
        analysis = out.get("content", "")
        err = out.get("error")

        if err:
            print(f"API error: {err}")
            fixed_nota_list.append(nota)
            aligned_fct_list.append(fct)
            results.append({
                "id": qid,
                "has_logic_issue": None,
                "analysis": analysis,
                "defensible_options": [],
                "replacements": {},
                "error": err,
            })
            time.sleep(API_DELAY)
            continue

        has_issue = has_logic_issue(analysis)
        defensible = extract_defensible_options(analysis) if has_issue else []
        replacements = parse_replacements(analysis, defensible) if defensible else {}

        # Validate: each replacement distinct from other 2 options
        options = nota.get("options", {})
        valid_replacements = {}
        for letter, new_text in replacements.items():
            others = [options[k] for k in ["A", "B", "C"] if k != letter]
            if is_distinct_from_others(new_text, others):
                valid_replacements[letter] = new_text
            else:
                print(f"(replacement for {letter} too similar to others, keeping original)")

        if has_issue and valid_replacements:
            fixed_nota = apply_fixes(nota, valid_replacements)
            aligned_fct = build_aligned_fct(fct, fixed_nota)
            ids_with_issues.append(qid)
            print(f"FIXED (defensible: {', '.join(defensible)})")
        else:
            fixed_nota = nota
            aligned_fct = fct
            if has_issue:
                print(f"ISSUE but no valid replacements")
            else:
                print("OK")

        fixed_nota_list.append(fixed_nota)
        aligned_fct_list.append(aligned_fct)
        results.append({
            "id": qid,
            "has_logic_issue": has_issue,
            "analysis": analysis,
            "defensible_options": defensible,
            "replacements": valid_replacements,
        })

        time.sleep(API_DELAY)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "total_nota": len(nota_list),
        "with_logic_issues": len(ids_with_issues),
        "ids_with_issues": ids_with_issues,
    }
    with open(OUTPUT_ANALYSIS, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "all_nota_logic_analysis": results}, f, indent=2, ensure_ascii=False)

    with_logic = [r for r in results if r.get("has_logic_issue")]
    with open(OUTPUT_ISSUES, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "items_with_issues": with_logic}, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_NOTA, "w", encoding="utf-8") as f:
        for item in fixed_nota_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(OUTPUT_FCT, "w", encoding="utf-8") as f:
        for item in aligned_fct_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nWrote {OUTPUT_NOTA} ({len(fixed_nota_list)} NOTA)")
    print(f"Wrote {OUTPUT_FCT} ({len(aligned_fct_list)} FCT)")
    print(f"Wrote {OUTPUT_ANALYSIS}")
    print(f"Wrote {OUTPUT_ISSUES}")
    print(f"Summary: {summary['with_logic_issues']}/{summary['total_nota']} NOTA had logic issues and were fixed.")
    if ids_with_issues:
        print("Fixed IDs:", ", ".join(ids_with_issues[:20]) + ("..." if len(ids_with_issues) > 20 else ""))


if __name__ == "__main__":
    main()
