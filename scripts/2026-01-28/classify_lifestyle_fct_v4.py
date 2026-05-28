"""
Classify FCT v4 Lifestyle questions as Type A (Hard Core, retain) vs Type B (Soft Core, discard).

Type A: Objective mechanisms, calculations, pharmacokinetics, quantifiable guidelines; binary Correct/Incorrect.
Type B: Behavioral psychology, wellness, communication, holistic advice; Better/Worse not True/False.

Uses same category assignment as remove_lifestyle_fct_v4.py to identify Lifestyle questions.
Classification via batched DeepSeek API calls.

Outputs:
  - Report: output/Json/fct_v4_lifestyle_classification.jsonl
  - Optional: --output-benchmark path writes filtered benchmark (non-Lifestyle + Lifestyle Type A only).
"""
import json
import os
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4.json"
REPORT_FILE = PROJECT_ROOT / "output" / "Json" / "fct_v4_lifestyle_classification.jsonl"

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_API_KEY = "sk-c48d90ddbd4d46ad91f527582066e8ea"
BATCH_SIZE = 18
MAX_RETRIES = 2

# Same as remove_lifestyle_fct_v4.py
COMPLICATIONS_KEYWORDS = [
    "retinopathy", "kidney", "ckd", "nephropathy", "foot", "ulcer", "charcot",
    "osteomyelitis", "wagner", "neuropathy", "neuropathic", "diabetic_foot",
    "peripheral neuropathy", "necrobiosis", "dermatology", "podiatry", "orthopedic",
    "complications", "neuroarthropathy", "gastroparesis",
]
MEDICATIONS_KEYWORDS = [
    "insulin", "sglt2", "glp-1", "metformin", "sulfonylurea", "pharmacotherapy",
    "pharmacology", "statin", "medication", "glimepiride", "contraindications",
    "drug", "medication management", "medication_safety", "pharmacological",
]
ACUTE_KEYWORDS = [
    "hypoglycemia", "dka", "ketoacidosis", "ketone", "emergency", "sick-day", "sick day",
    "acute", "critical care", "fluid management", "emergency_medicine", "emergency_management",
    "emergency management", "gastroenteritis", "hydration", "ketones", "glucagon", "hhs",
]
LIFESTYLE_KEYWORDS = [
    "nutrition", "diet", "exercise", "prevention", "screening", "lifestyle",
    "patient education", "self-management", "obesity", "weight", "prediabetes",
    "gestational", "pregnancy", "obstetrics", "geriatrics", "lifestyle intervention",
    "weight management", "dietary", "primary prevention", "preventive care",
    "patient_education", "self_management", "medical nutrition",
    "diabetes education", "specialpops", "special pops", "elderly",
]

CLASSIFICATION_GUIDELINES = """
## TYPE A (Hard Core – RETAIN)
Criteria: Objective biological mechanisms, exact calculations, pharmacokinetics, or quantifiable clinical guidelines. The answer must be binary (Correct/Incorrect).
Examples: Insulin-to-Carbohydrate Ratio (ICR) math, Correction Factor (ISF); how alcohol inhibits hepatic gluconeogenesis causing hypoglycemia; effect of anaerobic vs aerobic exercise on blood glucose; ADA recommendation for minimum minutes of moderate-intensity activity per week (150 min).

## TYPE B (Soft Core – DISCARD)
Criteria: Behavioral psychology, general wellness, communication strategies, or holistic advice. Answers are often "Better/Worse" rather than "True/False."
Examples: Strategies to improve patient motivation; general benefits of a high-fiber diet; how to build a therapeutic alliance; stress management techniques.
"""


def normalize(s: str) -> str:
    return (s or "").lower().strip()


def tags_match_any(tags: list, keywords: list) -> bool:
    if not tags:
        return False
    norm_tags = [normalize(t) for t in tags if isinstance(t, str)]
    for t in norm_tags:
        for kw in keywords:
            if kw in t or t in kw:
                return True
    return False


def assign_category(record: dict) -> str:
    """First match wins: Complication, Medication, Acute Care, Lifestyle."""
    tags = record.get("tags") or []
    meta = record.get("metadata") or {}
    topic = normalize(meta.get("topic") or "")
    if "neuropathy" in topic or "foot care" in topic or "retinopathy" in topic or "kidney" in topic:
        return "Complication"
    if "acute" in topic or "hospital" in topic:
        return "Acute Care"
    if "special population" in topic or "elderly" in topic or "pregnancy" in topic:
        return "Lifestyle"
    if tags_match_any(tags, COMPLICATIONS_KEYWORDS):
        return "Complication"
    if tags_match_any(tags, MEDICATIONS_KEYWORDS):
        return "Medication"
    if tags_match_any(tags, ACUTE_KEYWORDS):
        return "Acute Care"
    if tags_match_any(tags, LIFESTYLE_KEYWORDS):
        return "Lifestyle"
    return "Lifestyle"


def load_v4(path: Path) -> List[Dict]:
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def call_deepseek(prompt: str, api_key: str, model_name: str = "deepseek-chat", max_tokens: int = 4096) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a medical education expert. Classify each question as Type A or Type B. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=90)
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


def parse_classification_response(text: str, expected_ids: List[str]) -> Dict[str, str]:
    """Parse LLM response into dict question_id -> A|B. Default to A if missing or invalid."""
    out = {qid: "A" for qid in expected_ids}
    if not text:
        return out
    text = text.strip()
    # Try to extract JSON array or JSONL lines
    cleaned = text
    if "```" in text:
        if "```json" in text:
            cleaned = text.split("```json")[-1]
        else:
            cleaned = text.split("```")[-1]
        cleaned = cleaned.split("```")[0]
    cleaned = cleaned.strip()
    # Try parse as array
    try:
        # Find first [ and last ]
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            arr = json.loads(cleaned[start : end + 1])
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict):
                        qid = item.get("id") or item.get("question_id")
                        sub = (item.get("lifestyle_subtype") or item.get("subtype") or "").upper()
                        if qid and sub in ("A", "B"):
                            out[str(qid)] = sub
                return out
    except json.JSONDecodeError:
        pass
    # Try line-by-line JSON
    for line in cleaned.split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            qid = obj.get("id") or obj.get("question_id")
            sub = (obj.get("lifestyle_subtype") or obj.get("subtype") or "").upper()
            if qid and sub in ("A", "B"):
                out[str(qid)] = sub
        except json.JSONDecodeError:
            continue
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Classify FCT v4 Lifestyle questions as Type A (retain) vs Type B (discard).")
    ap.add_argument("--input", type=Path, default=INPUT_FILE, help="FCT v4 JSONL path")
    ap.add_argument("--report", type=Path, default=REPORT_FILE, help="Output classification report JSONL")
    ap.add_argument("--output-benchmark", type=Path, default=None, help="If set, write filtered benchmark (non-Lifestyle + Lifestyle Type A only)")
    ap.add_argument("--api-key", default=None, help="DeepSeek API key (or set DEEPSEEK_API_KEY)")
    ap.add_argument("--dry-run", action="store_true", help="Only identify Lifestyle questions, do not call API")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Questions per API batch")
    args = ap.parse_args()

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY") or DEFAULT_API_KEY
    if not api_key and not args.dry_run:
        raise SystemExit("Set DEEPSEEK_API_KEY or pass --api-key. Use --dry-run to skip API.")

    questions = load_v4(args.input)
    lifestyle_questions = [(i, q) for i, q in enumerate(questions) if assign_category(q) == "Lifestyle"]
    lifestyle_ids = [q["id"] for _, q in lifestyle_questions]
    print(f"Loaded {len(questions)} questions from {args.input}")
    print(f"Lifestyle questions: {len(lifestyle_questions)}")

    if not lifestyle_questions:
        print("No Lifestyle questions to classify.")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            pass
        return

    if args.dry_run:
        print("Dry run: would classify these Lifestyle IDs:", lifestyle_ids[:20], "..." if len(lifestyle_ids) > 20 else "")
        return

    # Batched LLM classification
    id_to_subtype: Dict[str, str] = {}
    batch_size = max(1, min(args.batch_size, 25))
    for start in range(0, len(lifestyle_questions), batch_size):
        batch = lifestyle_questions[start : start + batch_size]
        batch_ids = [q["id"] for _, q in batch]
        lines = []
        for _, q in batch:
            qtext = (q.get("question") or "")[:400]
            lines.append(f"  - id: {q['id']}, question: {qtext}")
        block = "\n".join(lines)
        prompt = f"""{CLASSIFICATION_GUIDELINES}

For each of the following FCT Lifestyle questions, output exactly one classification: A (Hard Core, retain) or B (Soft Core, discard).
Output a JSON array of objects, each with "id" (question id string) and "lifestyle_subtype" ("A" or "B"). No other text.

Questions:
{block}

Output (JSON array only):"""
        for attempt in range(MAX_RETRIES + 1):
            try:
                raw = call_deepseek(prompt, api_key)
                parsed = parse_classification_response(raw, batch_ids)
                for qid in batch_ids:
                    id_to_subtype[qid] = parsed.get(qid, "A")
                print(f"  Batch {start // batch_size + 1}: classified {len(batch_ids)} questions")
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                    continue
                print(f"  Batch failed for {batch_ids[0]}..{batch_ids[-1]}: {e}, defaulting to A")
                for qid in batch_ids:
                    id_to_subtype[qid] = "A"
        time.sleep(0.5)

    # Ensure all lifestyle IDs have a subtype
    for qid in lifestyle_ids:
        if qid not in id_to_subtype:
            id_to_subtype[qid] = "A"

    # Write report
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        for _, q in lifestyle_questions:
            qid = q["id"]
            sub = id_to_subtype.get(qid, "A")
            snippet = (q.get("question") or "")[:200]
            f.write(json.dumps({"question_id": qid, "lifestyle_subtype": sub, "question_snippet": snippet}, ensure_ascii=False) + "\n")

    type_a_ids = [qid for qid in lifestyle_ids if id_to_subtype.get(qid) == "A"]
    type_b_ids = [qid for qid in lifestyle_ids if id_to_subtype.get(qid) == "B"]
    print()
    print("Classification summary:")
    print(f"  Type A (Hard Core, retain): {len(type_a_ids)}")
    print(f"  Type B (Soft Core, discard): {len(type_b_ids)}")
    if type_b_ids:
        print(f"  Type B IDs (first 20): {type_b_ids[:20]}" + (" ..." if len(type_b_ids) > 20 else ""))
    print(f"Report: {args.report}")

    if args.output_benchmark:
        type_b_set = set(type_b_ids)
        kept = [q for q in questions if assign_category(q) != "Lifestyle" or q["id"] not in type_b_set]
        args.output_benchmark.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_benchmark, "w", encoding="utf-8") as f:
            for q in kept:
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
        print(f"Filtered benchmark ({len(kept)} questions, Type B Lifestyle removed): {args.output_benchmark}")


if __name__ == "__main__":
    main()
