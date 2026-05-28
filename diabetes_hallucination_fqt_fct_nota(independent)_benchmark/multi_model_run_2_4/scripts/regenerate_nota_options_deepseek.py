"""
Regenerate NOTA options for all 65 NOTA in 400q using DeepSeek API.
Uses the user-provided prompt to generate three NEW unequivocally incorrect options (A, B, C)
per question, instead of reusing the original FCT distractors.

Input: 100q_nota_filtered.jsonl, 100q_fct_filtered.jsonl (matched by derived_from)
Output: 65q_nota_regenerated.jsonl, reports/65q_nota_regeneration_report.json

Usage:
  python regenerate_nota_options_deepseek.py
  python regenerate_nota_options_deepseek.py --dry-run
  python regenerate_nota_options_deepseek.py --ids NOTA_018,NOTA_039,NOTA_091   # Regenerate specific items only
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
NOTA_SOURCE = BASE_DIR / "benchmark" / "100q_nota_filtered.jsonl"
FCT_SOURCE = BASE_DIR / "benchmark" / "100q_fct_filtered.jsonl"
OUTPUT_JSONL = BASE_DIR / "benchmark" / "65q_nota_regenerated.jsonl"
REPORTS_DIR = BASE_DIR / "results_400q_diabetes" / "reports"
OUTPUT_REPORT = REPORTS_DIR / "65q_nota_regeneration_report.json"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT = 120
API_DELAY = 1.5

SUGGESTION_PATTERN = re.compile(r"\n\n\[Suggestion\]:.*$", re.DOTALL)


def strip_suggestion(question: str) -> str:
    """Remove the [Suggestion] block from question text."""
    return SUGGESTION_PATTERN.sub("", question).strip()


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def build_nota_generation_prompt(fct: dict) -> str:
    """Build prompt for generating new unequivocally incorrect NOTA options."""
    stem = strip_suggestion(fct.get("question", ""))
    options = fct.get("options", {})
    correct_letter = fct.get("answer", "")
    correct_text = options.get(correct_letter, "")

    wrong_letters = [k for k in ["A", "B", "C", "D"] if k != correct_letter]
    orig_a = options.get(wrong_letters[0], "") if len(wrong_letters) > 0 else ""
    orig_b = options.get(wrong_letters[1], "") if len(wrong_letters) > 1 else ""
    orig_c = options.get(wrong_letters[2], "") if len(wrong_letters) > 2 else ""

    return f"""You are an expert medical educator creating high-quality "None Of The Above" (NOTA) questions for a study on AI behavior. You will be given an existing multiple-choice question (FCT) with a stem, a correct answer, and three distractors (which are plausible but not the best). Your task is to generate a new set of three options (A, B, C) that are ALL unequivocally incorrect based on current medical guidelines. The correct answer for the NOTA version will be D: "None of the above."

Guidelines for generating incorrect options:
- Each option must contain a clear factual error, contradiction of guidelines, or an absolute falsehood.
- Avoid using the original distractors; create entirely new ones.
- Ensure the options are clinically relevant to the stem (same topic, similar complexity).
- Do not make the errors too obvious; they should appear plausible at first glance but be demonstrably wrong upon closer inspection.
- Use definitive language (avoid "may," "sometimes," "possibly").
- Refer to established guidelines (ADA, AACE, KDIGO, etc.) when constructing the error.

Here is the original question:

Stem: {stem}

Correct answer: {correct_text}

Original distractors (for context only, do not reuse):
A. {orig_a}
B. {orig_b}
C. {orig_c}

Now, generate three new incorrect options (A, B, C) for the NOTA version. Output them in the following format:

A. [New incorrect option A]
B. [New incorrect option B]
C. [New incorrect option C]

Make sure each option is a complete, standalone recommendation that could appear in a clinical vignette."""


def call_deepseek(prompt: str, api_key: str) -> dict:
    """Call DeepSeek API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert medical educator creating high-quality NOTA (None of the Above) questions. Generate options that are unequivocally incorrect per current guidelines.",
            },
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


def parse_generated_options(text: str) -> dict | None:
    """Parse A, B, C from model output. Returns {"A": ..., "B": ..., "C": ...} or None."""
    if not text or not text.strip():
        return None
    result = {}
    letters = ["A", "B", "C"]
    for i, letter in enumerate(letters):
        next_letter = letters[i + 1] if i + 1 < len(letters) else None
        if next_letter:
            pattern = rf"{letter}\s*[.:]\s*(.+?)(?=\s*{next_letter}\s*[.:])"
        else:
            pattern = rf"{letter}\s*[.:]\s*(.+)"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            opt = re.sub(r"\s+", " ", m.group(1).strip()).strip()
            if opt and len(opt) > 15:
                result[letter] = opt
    return result if len(result) == 3 else None


def get_api_key():
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import config as project_config
        return getattr(project_config, "DEEPSEEK_API_KEY", None)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Regenerate NOTA options via DeepSeek API")
    parser.add_argument("--dry-run", action="store_true", help="Load data only, no API calls")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated NOTA IDs to regenerate (e.g. NOTA_018,NOTA_039)")
    args = parser.parse_args()

    api_key = get_api_key()
    if not args.dry_run and not api_key:
        print("Error: DEEPSEEK_API_KEY not found. Set in env or config.py (project root).")
        raise SystemExit(1)

    if not NOTA_SOURCE.exists() or not FCT_SOURCE.exists():
        print(f"Error: NOTA or FCT source not found.")
        raise SystemExit(1)

    nota_list = load_jsonl(NOTA_SOURCE)
    fct_list = load_jsonl(FCT_SOURCE)
    fct_by_id = {q.get("id", ""): q for q in fct_list}

    if args.ids:
        id_set = {x.strip() for x in args.ids.split(",") if x.strip()}
        nota_list = [q for q in nota_list if q.get("id", "") in id_set]
        print(f"Filtered to {len(nota_list)} NOTA items: {sorted(id_set)}")
    else:
        print(f"Loaded {len(nota_list)} NOTA, {len(fct_list)} FCT")

    if args.dry_run:
        print("Dry-run: no API calls. Exiting.")
        return

    regenerated = []
    report_items = []

    for i, nota in enumerate(nota_list):
        nota_id = nota.get("id", "")
        derived = nota.get("metadata", {}).get("derived_from", "")
        fct = fct_by_id.get(derived) if derived else None

        if not fct:
            print(f"[{i+1}/{len(nota_list)}] {nota_id}... SKIP (no FCT match for {derived})")
            report_items.append({"id": nota_id, "status": "skip", "reason": f"No FCT for {derived}"})
            continue

        print(f"[{i+1}/{len(nota_list)}] {nota_id}...", end=" ", flush=True)

        prompt = build_nota_generation_prompt(fct)
        out = call_deepseek(prompt, api_key)
        content = out.get("content") or ""
        err = out.get("error")

        if err:
            print(f"API error: {err}")
            report_items.append({"id": nota_id, "status": "error", "reason": err})
            time.sleep(API_DELAY)
            continue

        parsed = parse_generated_options(content)
        if parsed:
            new_nota = {
                "id": nota_id,
                "question": strip_suggestion(fct.get("question", "")),
                "options": {
                    "A": parsed["A"],
                    "B": parsed["B"],
                    "C": parsed["C"],
                    "D": "None of the above",
                },
                "answer": "D",
                "task": "NOTA",
                "metadata": nota.get("metadata", {}).copy(),
            }
            regenerated.append(new_nota)
            report_items.append({"id": nota_id, "status": "ok", "options": parsed})
            print("OK")
        else:
            print("PARSE FAIL")
            report_items.append({"id": nota_id, "status": "parse_fail", "raw": content[:500]})

        time.sleep(API_DELAY)

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for item in regenerated:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"\nWrote {OUTPUT_JSONL} ({len(regenerated)} items)")

    report = {
        "summary": {"total": len(nota_list), "regenerated": len(regenerated), "failed": len(nota_list) - len(regenerated)},
        "items": report_items,
    }
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
