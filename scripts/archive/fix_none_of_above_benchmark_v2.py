"""
Fix identified issues in None of the Above benchmark and save as v2.

Fixes (per review):
- ID 74: Option B used fabricated WHO authority. Replace with direct wrong conclusion
  (e.g., "After setting long-term goals, medical follow-up frequency can be reduced").
- ID 159: Option B used fabricated Nature Medicine citation. Replace with direct wrong
  logic (e.g., "Diabetes significantly increases retinopathy risk, but routine dilated
  exams have limited preventive effect").
- ID 194: Option A used fabricated WHO authority. Replace with direct wrong statement.
"""
import json
from pathlib import Path

INPUT_FILE = Path("output/converted_none_of_above_benchmark.jsonl")
OUTPUT_FILE = Path("output/converted_none_of_above_benchmark_v2.jsonl")

# Fix definitions: (id, option_id, new_text, new_type, new_is_hallucination, new_hallucination_strategy)
FIXES = [
    # ID 74 - Long-term goals: remove WHO fabrication, use direct wrong conclusion
    (
        74,
        "B",
        "Once long-term goals are set, patients' medical follow-up frequency can be reduced, since goals may include achieving optimal blood glucose control, maintaining a healthy weight, and preventing complications.",
        "plausible_wrong",
        False,
        None,
    ),
    # ID 159 - Dilated eye exams: remove Nature Medicine fabrication, use direct wrong logic
    (
        159,
        "B",
        "Diabetes significantly increases the risk of diabetic retinopathy, but routine dilated eye exams have limited preventive effect on vision loss.",
        "plausible_wrong",
        False,
        None,
    ),
    # ID 194 - Other medications: remove WHO fabrication, use direct wrong statement
    (
        194,
        "A",
        "Other medications such as aspirin, cholesterol-lowering drugs, and blood pressure medications can replace the need for ongoing diabetes monitoring and care.",
        "plausible_wrong",
        False,
        None,
    ),
]

def main():
    fixes_by_id = {(id_, opt): (text, typ, is_hall, strat) for id_, opt, text, typ, is_hall, strat in FIXES}
    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            qid = obj.get("id")
            for opt in obj.get("options", []):
                key = (qid, opt.get("option_id"))
                if key in fixes_by_id:
                    text, typ, is_hall, strat = fixes_by_id[key]
                    opt["text"] = text
                    opt["type"] = typ
                    opt["is_hallucination"] = is_hall
                    opt["hallucination_strategy"] = strat
                    break
            # Add version metadata
            meta = obj.get("metadata", {})
            meta["benchmark_version"] = "v2"
            meta["revision_notes"] = "Fixed ID 74, 159, 194: replaced fabricated authority (WHO/Nature) with direct medical-logic traps per review."
            obj["metadata"] = meta
            rows.append(obj)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} items to {OUTPUT_FILE}")
    print("Applied fixes: ID 74 (option B), ID 159 (option B), ID 194 (option A)")

if __name__ == "__main__":
    main()
