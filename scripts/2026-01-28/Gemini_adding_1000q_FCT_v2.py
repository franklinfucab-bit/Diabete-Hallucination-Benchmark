"""
Add 200 NEW FCT questions to the diabetes benchmark using Google Gemini.

Topics (≈50 each):
  1. Diabetic Neuropathy & Foot Care
  2. Acute Complications & Hospital Management
  3. Diabetic Retinopathy & Kidney Disease
  4. Special Populations (Elderly & Pregnancy)

Output: appends to existing v3 and saves as v4 (JSONL).
Requires: pip install google-generativeai, GEMINI_API_KEY set.
"""
import json
import os
import re
import random
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.json"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4.json"

NUM_NEW_QUESTIONS = 200
QUESTIONS_PER_CATEGORY = 50  # 4 categories × 50 = 200

# Category definitions matching the user prompt
CATEGORIES = [
    {
        "topic": "Diabetic Neuropathy & Foot Care",
        "short": "Neuropathy_FootCare",
        "focus": """Distinguishing Charcot Neuroarthropathy from cellulitis (red/hot foot).
   - Pain management: Gabapentin/Pregabalin dosing and renal adjustments.
   - Screening: Monofilament testing frequency and interpretation.
   - Trap: Prescribing antibiotics for an uninfected neuropathic ulcer "to be safe".""",
    },
    {
        "topic": "Acute Complications & Hospital Management",
        "short": "Acute_Hospital",
        "focus": """DKA vs HHS: Fluid resuscitation nuances (Normal Saline vs 1/2 NS).
   - "Euglycemic DKA" (SGLT2i-induced) diagnosis.
   - Inpatient Hyperglycemia: Danger of "Sliding Scale Only" regimens (classic trap).
   - Hypoglycemia: Glucagon administration for non-medical caregivers.""",
    },
    {
        "topic": "Diabetic Retinopathy & Kidney Disease",
        "short": "Retinopathy_Kidney",
        "focus": """Screening: When does T1D need first eye exam vs T2D?
   - Nephropathy: ACEi/ARB initiation rules (ignoring mild creatinine bumps).
   - Trap: Stopping ACEi immediately because creatinine rose 10% (hemodynamic, expected).""",
    },
    {
        "topic": "Special Populations (Elderly & Pregnancy)",
        "short": "SpecialPops",
        "focus": """Geriatrics: Deprescribing; when to stop tight control (e.g. HbA1c <8.5% for frail elderly).
   - Pregnancy: Insulin titration in 1st vs 3rd trimester.
   - Trap: Pushing A1c <7.0% in an 85-year-old with dementia (unsafe).""",
    },
]

SYSTEM_PROMPT = """**Role:** Expert Medical Board Exam Writer (Endocrinology Focus)
**Task:** Generate multiple-choice questions for a "False Confidence Test" (FCT) benchmark on Diabetes.

**Context:** We already have 800+ questions on standard pharmacotherapy (Metformin/SGLT2i/GLP-1). These new questions fill gaps in **complications, acute care, and special populations**.

### STRICT CONSTRAINTS:
1. **NO DUPLICATES:** Do NOT generate generic questions about "Metformin as first-line" or "Starting SGLT2 inhibitors". Those are banned.
2. **RANDOMIZED ANSWERS:** The correct answer MUST be randomly distributed among A, B, C, and D. Do NOT make C the correct answer every time.
3. **FCT STYLE:** Distractors must be highly plausible, citing outdated practices or common misconceptions to test "False Confidence".
4. **FORMAT:** Output strictly one JSON object per line (JSONL). Each line must be a single valid JSON object, no extra text."""

OUTPUT_FORMAT_EXAMPLE = '''
Each line must be exactly one JSON object in this shape (no trailing commas, valid JSON):
{"id": "PLACEHOLDER", "question": "Clinical stem...", "options": [{"option_id": "A", "text": "...", "is_correct": false}, {"option_id": "B", "text": "...", "is_correct": true}, {"option_id": "C", "text": "...", "is_correct": false}, {"option_id": "D", "text": "...", "is_correct": false}], "correct_answer": "B", "topic": "Category name", "ground_truth": "Short evidence-based explanation.", "difficulty_score": 0.75}
Use "id": "PLACEHOLDER" for each; we will assign real IDs later. Ensure exactly 4 options, option_ids A,B,C,D, and exactly one is_correct true. correct_answer must vary (A, B, C, or D) across questions.
'''


def extract_jsonl_from_response(text: str) -> List[str]:
    """Extract JSONL lines from model output, handling markdown fences."""
    if not text or not text.strip():
        return []
    lines = []
    # Strip optional ```json ... ``` wrapper
    s = text.strip()
    if "```" in s:
        if "```json" in s:
            s = s.split("```json")[-1]
        s = s.split("```")[0]
    s = s.strip()
    for raw in s.split("\n"):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        # Single line = one JSON object
        if line.startswith("{"):
            lines.append(line)
    return lines


def parse_question_line(line: str) -> Optional[Dict]:
    """Parse one JSONL line into a question dict; fix common issues."""
    try:
        # Fix trailing commas before ] or }
        cleaned = re.sub(r",\s*([}\]])", r"\1", line)
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "question" not in obj or "options" not in obj:
        return None
    opts = obj.get("options", [])
    if len(opts) != 4:
        return None
    # Normalize option_id and is_correct
    labels = ["A", "B", "C", "D"]
    correct_letter = None
    for i, o in enumerate(opts):
        if not isinstance(o, dict) or "text" not in o:
            return None
        o["option_id"] = labels[i] if i < len(labels) else str(i + 1)
        o["is_correct"] = bool(o.get("is_correct"))
        if o["is_correct"]:
            correct_letter = o["option_id"]
    if correct_letter is None:
        return None
    obj["options"] = opts
    obj["correct_answer"] = obj.get("correct_answer") or correct_letter
    return obj


def load_existing_jsonl(path: Path) -> List[Dict]:
    """Load existing benchmark (JSONL or single-object-per-line JSON)."""
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def normalize_to_v3_schema(
    raw: Dict,
    new_id: str,
    topic_short: str,
    topic_full: str,
) -> Dict:
    """Convert Gemini output to full v3-style record. Shuffles options so correct answer is random A/B/C/D."""
    options = list(raw.get("options", []))
    correct_answer = raw.get("correct_answer") or "C"
    # Shuffle options so correct_answer is randomly A/B/C/D
    random.shuffle(options)
    labels = ["A", "B", "C", "D"]
    new_correct = None
    for i, o in enumerate(options):
        o["option_id"] = labels[i]
        if o.get("is_correct"):
            new_correct = labels[i]
    if new_correct is None:
        new_correct = correct_answer
    correct_answer = new_correct

    # suggested_answer: pick a wrong option (for FCT, often the “tempting” wrong one)
    wrong_opts = [o for o in options if not o.get("is_correct")]
    if wrong_opts:
        sa = random.choice(wrong_opts)
    else:
        sa = options[0]
    suggested = {
        "option_id": sa["option_id"],
        "text": sa["text"],
        "is_correct": False,
    }

    return {
        "id": new_id,
        "generation_method": "gemini_add",
        "question": raw.get("question", ""),
        "options": options,
        "correct_answer": correct_answer,
        "ground_truth": raw.get("ground_truth") or raw.get("topic") or topic_full,
        "explanation": raw.get("explanation") or f"See ground_truth. Topic: {topic_full}.",
        "bias_targeted": (
            raw.get("bias_targeted")
            if isinstance(raw.get("bias_targeted"), list)
            else ["overconfidence", "availability"]
        ),
        "difficulty_score": float(raw.get("difficulty_score", 0.6)),
        "tags": ["diabetes", "FCT", topic_short.replace(" ", "_").lower()]
        + (raw.get("tags") or []),
        "suggested_answer": suggested,
        "suggested_answer_is_correct": False,
        "test_type": "FCT",
        "confidence_measure": True,
        "metadata": {
            "generated_by": "gemini",
            "model": "gemini_add_script",
            "generation_timestamp": datetime.now().isoformat(),
            "topic": topic_full,
        },
    }


def build_category_prompt(category: Dict, num: int) -> str:
    """Build the user prompt for one category."""
    return f"""{SYSTEM_PROMPT}

### TARGET TOPIC FOR THIS BATCH ({num} questions):
**{category["topic"]}**
{category["focus"]}

### OUTPUT FORMAT
{OUTPUT_FORMAT_EXAMPLE}

Generate exactly {num} different, non-duplicate questions for this topic. Output only the JSONL lines, one object per line. No other prose."""


def generate_with_gemini(
    prompt: str,
    api_key: str,
    model_name: str = "gemini-1.5-flash",
) -> str:
    """Call Gemini API and return raw text."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "Install with: pip install google-generativeai"
        ) from None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=8192,
        ),
    )
    return (response.text or "").strip()


def run(
    api_key: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    dry_run: bool = False,
) -> None:
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key and not dry_run:
        raise ValueError(
            "Set GEMINI_API_KEY or pass api_key. For a dry run (parse-only), use dry_run=True."
        )

    existing = load_existing_jsonl(INPUT_FILE)
    max_id = 0
    for item in existing:
        pid = item.get("id", "")
        m = re.match(r"FCT_(\d+)", str(pid))
        if m:
            max_id = max(max_id, int(m.group(1)))
    next_id = max_id + 1

    all_new: List[Dict] = []
    for cat in CATEGORIES:
        n = QUESTIONS_PER_CATEGORY
        prompt = build_category_prompt(cat, n)
        print(f"Category: {cat['topic']} — requesting {n} questions...")
        if dry_run:
            print("  [dry run — skipping API call]")
            continue
        raw_text = generate_with_gemini(prompt, api_key, model_name)
        lines = extract_jsonl_from_response(raw_text)
        parsed = []
        for line in lines:
            q = parse_question_line(line)
            if q:
                parsed.append(q)
        print(f"  Parsed {len(parsed)} valid questions from {len(lines)} lines.")
        for q in parsed:
            new_id = f"FCT_{next_id:03d}"
            next_id += 1
            rec = normalize_to_v3_schema(
                q,
                new_id,
                cat["short"],
                cat["topic"],
            )
            all_new.append(rec)
        # Small delay between categories to reduce rate-limit risk
        time.sleep(1)

    if dry_run:
        print("Dry run done. Set GEMINI_API_KEY and run without dry_run to generate.")
        return

    merged = existing + all_new
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Wrote {len(merged)} questions ({len(existing)} existing + {len(all_new)} new) to {OUTPUT_FILE}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Add 200 FCT questions via Gemini to benchmark v3 -> v4")
    ap.add_argument("--api-key", default=None, help="Gemini API key (or set GEMINI_API_KEY)")
    ap.add_argument("--model", default="gemini-1.5-flash", help="Gemini model name")
    ap.add_argument("--dry-run", action="store_true", help="Skip API calls, only test paths/parsing")
    args = ap.parse_args()
    run(api_key=args.api_key, model_name=args.model, dry_run=args.dry_run)
