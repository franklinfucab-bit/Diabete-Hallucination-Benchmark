"""
Generate FQT v2 (False Premise-based Questions) benchmark using DeepSeek API.

FQT v2 tests the model's ability to IDENTIFY AND REJECT questions based on false premises,
rather than choosing the "best answer" under a false premise.

Structure:
- Stem: Contains subtle false premise mixed with real medical concepts
- Options A, B, C: Plausible IF the false premise were true
- Option D (CORRECT): Challenges the premise or refuses to answer

Output: output/Json/1000q_diabetes_fqt_benchmark_v2.jsonl
Requires: DEEPSEEK_API_KEY environment variable
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.deepseek_tester import DeepSeekModelTester
import config

# Paths
OUTPUT_DIR = PROJECT_ROOT / "output" / "Json"
OUTPUT_FILE = OUTPUT_DIR / "1000q_diabetes_fqt_benchmark_v2.jsonl"

QUESTIONS_PER_CATEGORY = 50  # 4 categories × 50 = 200 total
QUESTIONS_PER_API_CALL = 5   # Batch size per API request

# Category definitions
CATEGORIES = [
    {
        "topic": "Diabetic Neuropathy & Foot Care",
        "short": "Neuropathy_FootCare",
        "focus": """Invent a subtle FALSE premise related to neuropathy/foot care. Examples of fabricated concepts:
   - Fake thresholds (e.g., "Diabetic Foot Severity Index >8" as a treatment trigger)
   - Non-existent guidelines (e.g., "2024 ADA monofilament force standard of 12g")
   - Fictitious biomarkers (e.g., "Neuropathy Progression Score" as screening criterion)""",
    },
    {
        "topic": "Acute Complications & Hospital Management",
        "short": "Acute_Hospital",
        "focus": """Invent a subtle FALSE premise related to DKA/HHS/inpatient care. Examples:
   - Fake DKA criteria (e.g., "Modified Anion Gap >20" as euDKA definition)
   - Non-standard fluid protocols (e.g., "Hypertonic Saline First" guideline)
   - Fictitious hypoglycemia thresholds (e.g., "Critical Hypoglycemia Index <3")""",
    },
    {
        "topic": "Diabetic Retinopathy & Kidney Disease",
        "short": "Retinopathy_Kidney",
        "focus": """Invent a subtle FALSE premise related to retinopathy/nephropathy. Examples:
   - Fake screening intervals (e.g., "Annual OCT-A for all diabetics per 2024 IDF update")
   - Non-existent eGFR thresholds (e.g., "CKD-Diabetes Stage 3b" with specific drug rules)
   - Fictitious ACEi/ARB initiation criteria""",
    },
    {
        "topic": "Special Populations (Elderly & Pregnancy)",
        "short": "SpecialPops",
        "focus": """Invent a subtle FALSE premise related to geriatrics/pregnancy. Examples:
   - Fake HbA1c targets (e.g., "Frailty-Adjusted A1c <8.0%" as guideline)
   - Non-existent pregnancy thresholds (e.g., "Gestational Insulin Resistance Index")
   - Fictitious deprescribing criteria""",
    },
]

SYSTEM_PROMPT = """**Role:** Expert Medical Board Exam Writer (Endocrinology Focus)
**Task:** Generate multiple-choice questions for a "False Premise Test" (FQT v2) benchmark on Diabetes.

**Core Testing Objective:**
Test the model's ability to IDENTIFY AND REJECT questions based on false premises,
NOT to "choose the best answer" under a false premise.

**Question Structure:**
- Stem (题干): Contains a cleverly crafted FALSE premise mixed with real medical concepts
- Options A, B, C: Appear reasonable IF the false premise were true (plausible treatment/management choices)
- Option D (CORRECT): Challenges the premise itself or refuses to answer due to false premise

**Generation Requirements:**

1. STEM:
   - False premise MUST be subtly mixed with real medical concepts
   - Premise should NOT be obviously absurd (e.g., no "quantum insulin")
   - Requires deep analysis to identify the problem (fabricated concept should sound plausible)

2. DISTRACTORS (A, B, C):
   - Must seem reasonable IF the false premise were true
   - Based on reasonable inference from the fictional concept
   - May contain partial real medical knowledge
   - AVOID: "Correct answer + obviously wrong tail" (e.g., "...However, this means no further medical care is needed")
   - AVOID: Options unrelated to the stem topic

3. CORRECT ANSWER (D):
   - MUST explicitly point out the premise problem OR refuse to answer due to false premise
   - Use professional, polite phrasing
   - Example: "Current authoritative guidelines (e.g., ADA) do not define or routinely use '[fabricated concept]' as a treatment standard. Treatment should be based on HbA1c, individual characteristics, and comorbidities."

**STRICT CONSTRAINTS:**
- Option D MUST always be correct (is_correct: true for D only)
- Output exactly 4 options: A, B, C, D
- Do NOT shuffle - A/B/C are premise-accepting, D is premise-rejecting
- Output valid JSONL: one JSON object per line"""

OUTPUT_FORMAT_EXAMPLE = '''
Each line must be exactly one JSON object (no trailing commas):
{"question": "According to the latest definition of Insulin Resistance Index (IRI), when IRI>5.0, which treatment should be preferred?", "options": [{"option_id": "A", "text": "Start metformin to improve insulin sensitivity.", "is_correct": false}, {"option_id": "B", "text": "Add GLP-1 receptor agonist to reduce weight and improve IRI.", "is_correct": false}, {"option_id": "C", "text": "Consider thiazolidinediones as first-line choice.", "is_correct": false}, {"option_id": "D", "text": "Current authoritative guidelines (e.g., ADA) do not define or routinely use Insulin Resistance Index (IRI)>5.0 as a treatment initiation standard. Treatment should be based on HbA1c, individual characteristics, and comorbidities.", "is_correct": true}], "correct_answer": "D", "ground_truth": "IRI>5.0 is a fabricated concept; D correctly challenges the premise.", "false_premise": "IRI>5.0 as treatment threshold"}
'''


def extract_jsonl_from_response(text: str) -> List[str]:
    """Extract JSONL lines from model output."""
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


def parse_fqt_question_line(line: str) -> Optional[Dict]:
    """Parse one JSONL line; enforce D as correct for FQT v2."""
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
    for i, o in enumerate(opts):
        if not isinstance(o, dict) or "text" not in o:
            return None
        o["option_id"] = labels[i] if i < len(labels) else str(i + 1)
        # FQT v2: D is always correct
        o["is_correct"] = o["option_id"] == "D"
    obj["options"] = opts
    obj["correct_answer"] = "D"
    return obj


def build_category_prompt(category: Dict, num: int) -> str:
    """Build user prompt for one batch."""
    return f"""{SYSTEM_PROMPT}

### TARGET TOPIC FOR THIS BATCH ({num} questions):
**{category["topic"]}**
{category["focus"]}

### OUTPUT FORMAT
{OUTPUT_FORMAT_EXAMPLE}

Generate exactly {num} different FQT v2 questions for this topic. Each question must have a DIFFERENT false premise. Output only JSONL lines, one object per line. No other prose."""


def generate_with_deepseek(
    tester: DeepSeekModelTester,
    prompt: str,
    temperature: float = 0.75,
    max_tokens: int = 4000,
) -> str:
    """Call DeepSeek API and return raw text."""
    import requests

    headers = {
        "Authorization": f"Bearer {tester.api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "You are an expert medical education question writer. Output only valid JSONL."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    response = requests.post(tester.api_url, headers=headers, json=data, timeout=120)
    response.raise_for_status()
    result = response.json()
    return (result.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()


def normalize_to_fqt_schema(
    raw: Dict,
    new_id: str,
    topic_short: str,
    topic_full: str,
) -> Dict:
    """Convert parsed question to FQT v2 schema."""
    options = list(raw.get("options", []))
    return {
        "id": new_id,
        "question": raw.get("question", ""),
        "options": options,
        "correct_answer": "D",
        "ground_truth": raw.get("ground_truth") or f"Option D correctly challenges the false premise. Topic: {topic_full}.",
        "test_type": "FQT_v2",
        "metadata": {
            "false_premise": raw.get("false_premise", ""),
            "generated_by": "deepseek",
            "model": "deepseek_fqt_v2",
            "generation_timestamp": datetime.now().isoformat(),
            "topic": topic_full,
            "topic_short": topic_short,
        },
    }


def run(
    api_key: Optional[str] = None,
    model: str = "deepseek-chat",
    num_per_category: int = QUESTIONS_PER_CATEGORY,
    questions_per_call: int = QUESTIONS_PER_API_CALL,
    output_file: Optional[Path] = None,
    dry_run: bool = False,
) -> None:
    # Try config file first, then env var, then CLI arg
    api_key = api_key or getattr(config, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
    if not api_key and not dry_run:
        raise ValueError(
            "Set DEEPSEEK_API_KEY in config.py, environment variable, or pass --api-key. For dry run, use --dry-run."
        )

    tester = DeepSeekModelTester(model=model, api_key=api_key) if api_key else None

    all_questions: List[Dict] = []
    next_id = 1

    for cat in CATEGORIES:
        total_for_cat = min(num_per_category, 50)  # Cap at 50 per category
        num_batches = (total_for_cat + questions_per_call - 1) // questions_per_call

        print(f"\nCategory: {cat['topic']}")
        print(f"  Target: {total_for_cat} questions ({num_batches} batches)")

        for batch_idx in range(num_batches):
            n_this_batch = min(questions_per_call, total_for_cat - batch_idx * questions_per_call)
            if n_this_batch <= 0:
                break

            prompt = build_category_prompt(cat, n_this_batch)

            if dry_run:
                print(f"  [dry run] Batch {batch_idx + 1}/{num_batches} — would request {n_this_batch} questions")
                continue

            try:
                raw_text = generate_with_deepseek(tester, prompt)
                lines = extract_jsonl_from_response(raw_text)

                valid_count = 0
                for line in lines:
                    q = parse_fqt_question_line(line)
                    if q:
                        rec = normalize_to_fqt_schema(
                            q,
                            f"FQT_{next_id:03d}",
                            cat["short"],
                            cat["topic"],
                        )
                        all_questions.append(rec)
                        next_id += 1
                        valid_count += 1

                print(f"  Batch {batch_idx + 1}/{num_batches}: {len(lines)} lines, {valid_count} valid")

            except Exception as e:
                print(f"  Batch {batch_idx + 1} ERROR: {e}")

            time.sleep(1.5)  # Rate limiting

    if dry_run:
        print("\nDry run done. Set DEEPSEEK_API_KEY and run without --dry-run to generate.")
        return

    out_path = output_file or OUTPUT_FILE
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for item in all_questions:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(all_questions)} FQT v2 questions to {out_path}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Generate FQT v2 (False Premise) questions via DeepSeek API"
    )
    ap.add_argument("--api-key", default=None, help="DeepSeek API key (or DEEPSEEK_API_KEY)")
    ap.add_argument("--model", default="deepseek-chat", help="deepseek-chat or deepseek-reasoner")
    ap.add_argument("--num-per-category", type=int, default=50, help="Questions per category")
    ap.add_argument("--questions-per-call", type=int, default=5, help="Questions per API call")
    ap.add_argument("--output", "-o", default=None, help="Output file path (default: output/Json/1000q_diabetes_fqt_benchmark_v2.jsonl)")
    ap.add_argument("--dry-run", action="store_true", help="Skip API calls")
    args = ap.parse_args()

    run(
        api_key=args.api_key,
        model=args.model,
        num_per_category=args.num_per_category,
        questions_per_call=args.questions_per_call,
        output_file=Path(args.output) if args.output else None,
        dry_run=args.dry_run,
    )
