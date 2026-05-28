"""
Select 300-400 "golden seed" questions from FCT v4 hardcore lifestyle benchmark.

Retains only: Medication (用药计算、禁忌症), Acute Care (DKA、低血糖急救), Complication (并发症诊断).
Strictly selects the highest-quality, most hardcore questions by:
  - Filtering to these three categories only
  - Ranking by difficulty_score (higher = more hardcore, preferred)
  - Stratified sampling to keep category balance (Medication ~40%, Acute Care ~31%, Complication ~29%)

Output: 300-400 questions (default 350) written to output/Json/350q_fct_v4_golden_seed.jsonl
"""
import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle_aligned.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "350q_fct_v4_golden_seed.jsonl"

SEED_MIN = 300
SEED_MAX = 400
SEED_TARGET = 350

# Same category logic as remove_lifestyle_fct_v4.py
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


def load_benchmark(path: Path):
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Select 300-400 golden seed FCT questions (Medication, Acute Care, Complication only).")
    ap.add_argument("--input", type=Path, default=INPUT_FILE, help="FCT v4 hardcore lifestyle JSONL")
    ap.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Output seed set JSONL")
    ap.add_argument("--target", type=int, default=SEED_TARGET, help=f"Target number of questions ({SEED_MIN}-{SEED_MAX}, default {SEED_TARGET})")
    args = ap.parse_args()

    target = max(SEED_MIN, min(SEED_MAX, args.target))
    questions = load_benchmark(args.input)

    # Keep only Medication, Acute Care, Complication
    by_cat = defaultdict(list)
    for q in questions:
        cat = assign_category(q)
        if cat in ("Medication", "Acute Care", "Complication"):
            diff = float(q.get("difficulty_score") or 0.5)
            by_cat[cat].append((diff, q))

    # Sort each category by difficulty descending (higher = more hardcore)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: -x[0])

    n_med = len(by_cat["Medication"])
    n_acute = len(by_cat["Acute Care"])
    n_comp = len(by_cat["Complication"])
    total_candidates = n_med + n_acute + n_comp

    print(f"Input: {args.input} ({len(questions)} questions)")
    print(f"Medication: {n_med}, Acute Care: {n_acute}, Complication: {n_comp} (total candidates: {total_candidates})")

    if total_candidates == 0:
        print("No candidates in Medication/Acute Care/Complication.")
        return

    # Stratified selection: allocate target proportionally by category size, then take top by difficulty within each
    # Proportions from current counts (med 293/731, acute 229/731, comp 209/731)
    med_ratio = n_med / total_candidates if total_candidates else 1 / 3
    acute_ratio = n_acute / total_candidates if total_candidates else 1 / 3
    comp_ratio = n_comp / total_candidates if total_candidates else 1 / 3

    n_med_take = min(n_med, max(1, int(round(target * med_ratio))))
    n_acute_take = min(n_acute, max(1, int(round(target * acute_ratio))))
    n_comp_take = min(n_comp, max(1, int(round(target * comp_ratio))))

    # If sum < target, add from largest category; if sum > target, trim from largest
    seed = []
    seed.extend([q for _, q in by_cat["Medication"][:n_med_take]])
    seed.extend([q for _, q in by_cat["Acute Care"][:n_acute_take]])
    seed.extend([q for _, q in by_cat["Complication"][:n_comp_take]])

    current = len(seed)
    if current < target and current < total_candidates:
        # Add more from category with most remaining (by difficulty)
        pool = []
        for cat in ("Medication", "Acute Care", "Complication"):
            taken = n_med_take if cat == "Medication" else (n_acute_take if cat == "Acute Care" else n_comp_take)
            pool.extend(by_cat[cat][taken:])
        pool.sort(key=lambda x: -x[0])
        for _, q in pool[: target - current]:
            seed.append(q)
    elif current > target:
        seed = seed[:target]

    # Preserve original order of IDs for reproducibility (sort by id)
    seed.sort(key=lambda q: (q.get("id") or ""))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for q in seed:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Count by category in final seed
    final_med = sum(1 for q in seed if assign_category(q) == "Medication")
    final_acute = sum(1 for q in seed if assign_category(q) == "Acute Care")
    final_comp = sum(1 for q in seed if assign_category(q) == "Complication")

    print(f"Seed set: {len(seed)} questions (target {target})")
    print(f"  Medication: {final_med}, Acute Care: {final_acute}, Complication: {final_comp}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
