"""
Remove N Lifestyle questions from FCT benchmark (e.g. after adding Acute Care).

Uses same category assignment as build_dataset_composition_table: first match wins
(Complication, Medication, Acute Care, Lifestyle). Randomly selects N Lifestyle
questions to remove (seed 42 for reproducibility).

Usage:
  python remove_lifestyle_fct_v4.py --input output/Json/1000q_diabetes_fct_benchmark_v4_temp.json --output output/Json/1000q_diabetes_fct_benchmark_v4.json --n 50
"""
import json
import random
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

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


def main():
    ap = argparse.ArgumentParser(description="Remove N random Lifestyle questions from FCT benchmark.")
    ap.add_argument("--input", type=Path, required=True, help="Input JSONL (e.g. v4_temp with 1104 questions)")
    ap.add_argument("--output", type=Path, required=True, help="Output JSONL (e.g. final v4)")
    ap.add_argument("--n", type=int, default=50, help="Number of Lifestyle questions to remove (default 50)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = ap.parse_args()

    questions = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))

    lifestyle_indices = [i for i, q in enumerate(questions) if assign_category(q) == "Lifestyle"]
    n_remove = min(args.n, len(lifestyle_indices))
    random.seed(args.seed)
    to_remove_indices = set(random.sample(lifestyle_indices, n_remove))

    kept = [q for i, q in enumerate(questions) if i not in to_remove_indices]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for q in kept:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"Input: {args.input} ({len(questions)} questions)")
    print(f"Lifestyle count: {len(lifestyle_indices)}")
    print(f"Removed: {n_remove} Lifestyle questions (seed={args.seed})")
    print(f"Output: {args.output} ({len(kept)} questions)")


if __name__ == "__main__":
    main()
