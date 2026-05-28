"""
Build Table 1: Dataset composition by clinical sub-domain.
Assigns each FCT/FQT/NOTA item to exactly one sub-domain so column totals match.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent

FCT_PATH = ROOT / "fct" / "diabetes_fct_benchmark.jsonl"
FQT_PATH = ROOT / "fqt" / "diabetes_fqt_benchmark.jsonl"
NOTA_PATH = ROOT / "nota" / "diabetes_nota_benchmark.jsonl"

# Sub-domain assignment: first match wins (order = Complications, Medications, Acute, Lifestyle).
# Tags normalized to lowercase; item matches if any of its tags contains a keyword.
COMPLICATIONS_KEYWORDS = [
    "retinopathy", "kidney", "ckd", "nephropathy", "foot", "ulcer", "charcot",
    "osteomyelitis", "wagner", "neuropathy", "neuropathic", "diabetic_foot",
    "peripheral neuropathy", "necrobiosis", "dermatology", "podiatry", "orthopedic",
    "complications", "neuroarthropathy", "gastroparesis",
]
MEDICATIONS_KEYWORDS = [
    "insulin", "sglt2", "glp-1", "glp-1", "metformin", "sulfonylurea", "pharmacotherapy",
    "pharmacology", "statin", "medication", "glimepiride", "contraindications",
    "drug", "medication management", "medication_safety", "pharmacological",
]
ACUTE_KEYWORDS = [
    "hypoglycemia", "dka", "ketoacidosis", "ketone", "emergency", "sick-day", "sick day",
    "acute", "critical care", "fluid management", "emergency_medicine", "emergency_management",
    "emergency management", "gastroenteritis", "hydration", "ketones",
]
LIFESTYLE_KEYWORDS = [
    "nutrition", "diet", "exercise", "prevention", "screening", "lifestyle",
    "patient education", "self-management", "obesity", "weight", "prediabetes",
    "gestational", "pregnancy", "obstetrics", "geriatrics", "lifestyle intervention",
    "weight management", "dietary", "primary prevention", "preventive care",
    "screening", "patient_education", "self_management", "medical nutrition",
    "diabetes education", "specialpops", "special pops",
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


def assign_subdomain_fct(record: dict) -> str:
    tags = record.get("tags") or []
    if tags_match_any(tags, COMPLICATIONS_KEYWORDS):
        return "Complications"
    if tags_match_any(tags, MEDICATIONS_KEYWORDS):
        return "Medications"
    if tags_match_any(tags, ACUTE_KEYWORDS):
        return "Acute Care"
    if tags_match_any(tags, LIFESTYLE_KEYWORDS):
        return "Lifestyle & Prevention"
    return "Lifestyle & Prevention"  # default / other


def assign_subdomain_fqt(record: dict) -> str:
    meta = record.get("metadata") or {}
    topic = (meta.get("topic_short") or meta.get("topic") or "").strip()
    if topic in ("Neuropathy_FootCare", "Retinopathy_Kidney"):
        return "Complications"
    if topic == "Acute_Hospital":
        return "Acute Care"
    if topic == "SpecialPops":
        return "Lifestyle & Prevention"
    return "Lifestyle & Prevention"


def assign_subdomain_nota(record: dict) -> str:
    tags = record.get("tags") or []
    if tags_match_any(tags, COMPLICATIONS_KEYWORDS):
        return "Complications"
    if tags_match_any(tags, MEDICATIONS_KEYWORDS):
        return "Medications"
    if tags_match_any(tags, ACUTE_KEYWORDS):
        return "Acute Care"
    if tags_match_any(tags, LIFESTYLE_KEYWORDS):
        return "Lifestyle & Prevention"
    return "Lifestyle & Prevention"


def load_jsonl(path: Path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def main():
    row_labels = [
        "Complications (e.g., Neuropathy, Retinopathy)",
        "Medications (e.g., Insulin, SGLT2i)",
        "Acute Care (e.g., Hypoglycemia)",
        "Lifestyle & Prevention",
    ]
    sub_to_idx = {
        "Complications": 0,
        "Medications": 1,
        "Acute Care": 2,
        "Lifestyle & Prevention": 3,
    }
    counts = [(0, 0, 0) for _ in row_labels]  # (fct, fqt, nota) per row

    # FCT
    fct_records = load_jsonl(FCT_PATH)
    for r in fct_records:
        sub = assign_subdomain_fct(r)
        i = sub_to_idx[sub]
        a, b, c = counts[i]
        counts[i] = (a + 1, b, c)

    # FQT
    fqt_records = load_jsonl(FQT_PATH)
    for r in fqt_records:
        sub = assign_subdomain_fqt(r)
        i = sub_to_idx[sub]
        a, b, c = counts[i]
        counts[i] = (a, b + 1, c)

    # NOTA
    nota_records = load_jsonl(NOTA_PATH)
    for r in nota_records:
        sub = assign_subdomain_nota(r)
        i = sub_to_idx[sub]
        a, b, c = counts[i]
        counts[i] = (a, b, c + 1)

    total_fct = sum(c[0] for c in counts)
    total_fqt = sum(c[1] for c in counts)
    total_nota = sum(c[2] for c in counts)

    lines = [
        "**Table 1: Dataset composition by clinical sub-domain.**",
        "",
        "| Clinical Sub-domain | FCT Items | FQT Items | NOTA Items | Total |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for label, (a, b, c) in zip(row_labels, counts):
        lines.append(f"| {label} | {a} | {b} | {c} | {a + b + c} |")
    lines.append(f"| **Total** | **{total_fct}** | **{total_fqt}** | **{total_nota}** | **{total_fct + total_fqt + total_nota}** |")

    out_path = SCRIPT_DIR / "analysis" / "dataset_composition_table.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
