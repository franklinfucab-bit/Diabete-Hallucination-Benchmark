"""
Add 200 NEW FCT questions to the diabetes benchmark using DeepSeek API.

Topics (≈50 each):
  1. Diabetic Neuropathy & Foot Care
  2. Acute Complications & Hospital Management
  3. Diabetic Retinopathy & Kidney Disease
  4. Special Populations (Elderly & Pregnancy)

Output: appends to existing v3 and saves as v4 (JSONL).
Requires: requests, DEEPSEEK_API_KEY set (or use --api-key).
"""
import json
import os
import re
import random
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.json"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.5.json"

# DeepSeek API config
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_API_KEY = "sk-c48d90ddbd4d46ad91f527582066e8ea"

TARGET_TOTAL = 1000  # Aim for 1000 questions in the final benchmark
MAX_QUESTIONS_PER_CALL = 50  # Max to request per API call (model often returns ~25–30 per call)
MAX_RETRIES_PER_CATEGORY = 2  # Extra calls per category if we get fewer than target

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
    """Convert DeepSeek output to full v3-style record. Shuffles options so correct answer is random A/B/C/D."""
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

    # suggested_answer: pick a wrong option (for FCT, often the "tempting" wrong one)
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
        "generation_method": "deepseek_add",
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
            "generated_by": "deepseek",
            "model": "deepseek-chat",
            "generation_timestamp": datetime.now().isoformat(),
            "topic": topic_full,
        },
    }


def build_category_prompt(category: Dict, num: int, additional: bool = False) -> str:
    """Build the user prompt for one category. If additional=True, ask for N *more* distinct questions."""
    intro = (
        f"Generate exactly {num} ADDITIONAL, distinct questions for the same topic (do not repeat concepts from earlier batches)."
        if additional
        else f"Generate exactly {num} different, non-duplicate questions for this topic."
    )
    return f"""{SYSTEM_PROMPT}

### TARGET TOPIC FOR THIS BATCH ({num} questions):
**{category["topic"]}**
{category["focus"]}

### OUTPUT FORMAT
{OUTPUT_FORMAT_EXAMPLE}

{intro} Output only the JSONL lines, one object per line. No other prose."""


def generate_with_deepseek(
    prompt: str,
    api_key: str,
    model_name: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 8000,
) -> str:
    """Call DeepSeek API and return raw text. deepseek-chat supports max 8000 output tokens."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "You are a medical education expert specializing in diabetes care, creating high-quality multiple-choice questions for False Confidence Tests (FCT).",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=120)
    if not response.ok:
        try:
            err = response.json()
            msg = err.get("error", {}).get("message", err) if isinstance(err.get("error"), dict) else response.text
        except Exception:
            msg = response.text or response.reason
        raise RuntimeError(f"DeepSeek API {response.status_code}: {msg}")
    result = response.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content.strip()


def run(
    api_key: Optional[str] = None,
    model_name: str = "deepseek-chat",
    dry_run: bool = False,
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
) -> None:
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or DEFAULT_API_KEY
    if not api_key and not dry_run:
        raise ValueError(
            "Set DEEPSEEK_API_KEY or pass api_key. For a dry run (parse-only), use dry_run=True."
        )
    in_path = input_file or INPUT_FILE
    out_path = output_file or OUTPUT_FILE

    existing = load_existing_jsonl(in_path)
    max_id = 0
    for item in existing:
        pid = item.get("id", "")
        m = re.match(r"FCT_(\d+)", str(pid))
        if m:
            max_id = max(max_id, int(m.group(1)))
    next_id = max_id + 1

    need = max(0, TARGET_TOTAL - len(existing))
    print(f"Loaded {len(existing)} existing questions from {in_path}")
    print(f"Target total: {TARGET_TOTAL} → need {need} new questions.")
    print(f"Starting ID: FCT_{next_id:03d}")
    print()

    all_new: List[Dict] = []
    if need > 0:
        per_cat = (need + 3) // 4  # ceil(need/4) per category
        for cat in CATEGORIES:
            target = per_cat
            cat_new: List[Dict] = []
            for attempt in range(MAX_RETRIES_PER_CATEGORY + 1):
                to_request = min(target - len(cat_new), MAX_QUESTIONS_PER_CALL)
                if to_request <= 0:
                    break
                prompt = build_category_prompt(
                    cat, to_request, additional=(attempt > 0)
                )
                label = f" (extra batch)" if attempt > 0 else ""
                print(f"Category: {cat['topic']}{label} — requesting {to_request} questions...")
                if dry_run:
                    print("  [dry run — skipping API call]")
                    break
                try:
                    raw_text = generate_with_deepseek(prompt, api_key, model_name)
                except Exception as e:
                    print(f"  ERROR: {e}")
                    break
                lines = extract_jsonl_from_response(raw_text)
                parsed = []
                for line in lines:
                    q = parse_question_line(line)
                    if q:
                        parsed.append(q)
                cat_new.extend(parsed)
                print(f"  Parsed {len(parsed)} valid from {len(lines)} lines → {len(cat_new)} total for this category.")
                if len(cat_new) >= target:
                    break
                time.sleep(1)
            for q in cat_new:
                new_id = f"FCT_{next_id}"
                next_id += 1
                rec = normalize_to_v3_schema(
                    q,
                    new_id,
                    cat["short"],
                    cat["topic"],
                )
                all_new.append(rec)
            time.sleep(1)

    if dry_run and need > 0:
        print("Dry run done. Set DEEPSEEK_API_KEY and run without dry_run to generate.")
        return

    # Cap new questions so total does not exceed TARGET_TOTAL
    all_new_trimmed = all_new[:need] if need > 0 else []
    merged = existing + all_new_trimmed
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print()
    print(f"Wrote {len(merged)} questions ({len(existing)} existing + {len(all_new_trimmed)} new) to {out_path}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Add FCT questions via DeepSeek until benchmark reaches TARGET_TOTAL (default 1000)."
    )
    ap.add_argument("--api-key", default=None, help="DeepSeek API key (or set DEEPSEEK_API_KEY)")
    ap.add_argument("--model", default="deepseek-chat", help="DeepSeek model name")
    ap.add_argument("--dry-run", action="store_true", help="Skip API calls, only test paths/parsing")
    ap.add_argument("--input", type=Path, default=None, help=f"Input JSONL (default: {INPUT_FILE.name})")
    ap.add_argument("--output", type=Path, default=None, help=f"Output JSONL (default: {OUTPUT_FILE.name})")
    args = ap.parse_args()
    run(
        api_key=args.api_key,
        model_name=args.model,
        dry_run=args.dry_run,
        input_file=args.input,
        output_file=args.output,
    )
