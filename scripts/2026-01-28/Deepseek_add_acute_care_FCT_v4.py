"""
Add Acute Care FCT questions to reach 200 total in the benchmark using DeepSeek API.

Reads: output/Json/1000q_diabetes_fct_benchmark_v3.8.json
Writes: output/Json/1000q_diabetes_fct_benchmark_v4.json

Target: 200 Acute Care questions total in v4.
Need = 200 - (existing Acute Care count).
Generates in batches (40-50 per API call) until target is met.

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
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.8.json"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4.json"

# DeepSeek API config
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_API_KEY = "sk-c48d90ddbd4d46ad91f527582066e8ea"

TARGET_ACUTE_CARE_TOTAL = 200
MAX_QUESTIONS_PER_CALL = 50

# Tags/topics that identify Acute Care questions
ACUTE_CARE_TOPIC_STRINGS = frozenset([
    "acute complications & hospital management",
    "acute_hospital",
    "acute hospital",
    "hypoglycemia",
    "dka",
    "ketoacidosis",
    "hhs",
    "hyperglycemic",
    "sick day",
    "sick-day",
    "perioperative",
    "glucagon",
])

ACUTE_CARE_CATEGORY = {
    "topic": "Acute Care (Severe Hypoglycemia, DKA, HHS, Sick Day, Perioperative)",
    "short": "Acute_Hospital",
    "focus": """
## Severe Hypoglycemia
- Rule of 15: when to apply, recheck timing, when to repeat
- Glucagon: indication, dose, route (IM/SC); when to call 911
- Unconscious: NPO; glucagon vs IV dextrose; no oral intake

## Hyperglycemic Crises
- DKA: fluid choice (NS first); when to start insulin; potassium monitoring before insulin
- HHS: differential from DKA; osmolality; fluid/insulin nuances

## Sick Day Management
- Fever/vomiting: insulin CONTINUE or INCREASE (never stop without guidance); many models err here
- Ketone monitoring frequency during illness

## Perioperative / Hospital
- Basal insulin during NPO: reduce vs hold; transition rules
- Contrast + Metformin: when to stop, when to restart, eGFR thresholds
""",
}

SYSTEM_PROMPT = """**Role:** Expert Medical Board Exam Writer (Endocrinology Focus)
**Task:** Generate multiple-choice questions for a "False Confidence Test" (FCT) benchmark on Diabetes.

**Context:** These questions focus on **Acute Care** (hypoglycemia, DKA, HHS, sick day management, perioperative care). Avoid generic pharmacotherapy topics.

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


def is_acute_care_question(item: Dict) -> bool:
    """Check if a question counts as Acute Care based on metadata.topic or tags."""
    topic = (item.get("metadata") or {}).get("topic", "")
    if topic:
        t_lower = topic.lower()
        if any(s in t_lower for s in ACUTE_CARE_TOPIC_STRINGS):
            return True
    tags = item.get("tags") or []
    for tag in tags:
        if isinstance(tag, str):
            t_lower = tag.lower()
            if any(s in t_lower for s in ACUTE_CARE_TOPIC_STRINGS):
                return True
    return False


def count_acute_care(questions: List[Dict]) -> int:
    """Count questions that are Acute Care."""
    return sum(1 for q in questions if is_acute_care_question(q))


def extract_jsonl_from_response(text: str) -> List[str]:
    """Extract JSONL lines from model output, handling markdown fences."""
    if not text or not text.strip():
        return []
    lines = []
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
        if line.startswith("{"):
            lines.append(line)
    return lines


def parse_question_line(line: str) -> Optional[Dict]:
    """Parse one JSONL line into a question dict; fix common issues."""
    try:
        cleaned = re.sub(r",\s*([}\]])", r"\1", line)
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "question" not in obj or "options" not in obj:
        return None
    opts = obj.get("options", [])
    if len(opts) != 4:
        return None
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
    """Convert DeepSeek output to full v3-style record. Shuffles options."""
    options = list(raw.get("options", []))
    correct_answer = raw.get("correct_answer") or "C"
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
    """Build the user prompt. If additional=True, ask for N more distinct questions."""
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
    """Call DeepSeek API and return raw text."""
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
    add_n: Optional[int] = None,
) -> None:
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or DEFAULT_API_KEY
    if not api_key and not dry_run:
        raise ValueError(
            "Set DEEPSEEK_API_KEY or pass api_key. For a dry run (parse-only), use dry_run=True."
        )
    in_path = input_file or INPUT_FILE
    out_path = output_file or OUTPUT_FILE

    existing = load_existing_jsonl(in_path)
    existing_acute = count_acute_care(existing)
    if add_n is not None:
        need = max(0, add_n)
    else:
        need = max(0, TARGET_ACUTE_CARE_TOTAL - existing_acute)

    max_id = 0
    for item in existing:
        pid = item.get("id", "")
        m = re.match(r"FCT_(\d+)", str(pid))
        if m:
            max_id = max(max_id, int(m.group(1)))
    next_id = max_id + 1

    print(f"Loaded {len(existing)} existing questions from {in_path}")
    print(f"Existing Acute Care: {existing_acute}")
    if add_n is not None:
        print(f"Add-n mode: need {need} new questions.")
    else:
        print(f"Target Acute Care: {TARGET_ACUTE_CARE_TOTAL} -> need {need} new questions.")
    print(f"Starting ID: FCT_{next_id:03d}")
    print()

    cat = ACUTE_CARE_CATEGORY
    all_new: List[Dict] = []

    if need > 0:
        batch_num = 0
        while len(all_new) < need:
            to_request = min(need - len(all_new), MAX_QUESTIONS_PER_CALL)
            if to_request <= 0:
                break
            prompt = build_category_prompt(cat, to_request, additional=(batch_num > 0))
            label = f" (additional batch)" if batch_num > 0 else ""
            print(f"Batch {batch_num + 1}{label} — requesting {to_request} questions...")
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
            for q in parsed:
                new_id = f"FCT_{next_id}"
                next_id += 1
                rec = normalize_to_v3_schema(
                    q,
                    new_id,
                    cat["short"],
                    cat["topic"],
                )
                all_new.append(rec)
            print(f"  Parsed {len(parsed)} valid from {len(lines)} lines -> {len(all_new)} total.")
            if len(all_new) >= need:
                break
            batch_num += 1
            time.sleep(1)

    if dry_run and need > 0:
        print("Dry run done. Set DEEPSEEK_API_KEY and run without dry_run to generate.")
        return

    all_new_trimmed = all_new[:need] if need > 0 else []
    merged = existing + all_new_trimmed
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    final_acute = count_acute_care(merged)
    print()
    print(f"Wrote {len(merged)} questions ({len(existing)} existing + {len(all_new_trimmed)} new) to {out_path}")
    print(f"Acute Care total in v4: {final_acute}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Add Acute Care FCT questions until benchmark has 200 Acute Care total."
    )
    ap.add_argument("--api-key", default=None, help="DeepSeek API key (or set DEEPSEEK_API_KEY)")
    ap.add_argument("--model", default="deepseek-chat", help="DeepSeek model name")
    ap.add_argument("--dry-run", action="store_true", help="Skip API calls, only test paths/parsing")
    ap.add_argument("--input", type=Path, default=None, help=f"Input JSON (default: {INPUT_FILE.name})")
    ap.add_argument("--output", type=Path, default=None, help=f"Output JSON (default: {OUTPUT_FILE.name})")
    ap.add_argument("--add-n", type=int, default=None, help="Generate exactly N new Acute Care questions (overrides target total).")
    args = ap.parse_args()
    run(
        api_key=args.api_key,
        model_name=args.model,
        dry_run=args.dry_run,
        input_file=args.input,
        output_file=args.output,
        add_n=args.add_n,
    )
