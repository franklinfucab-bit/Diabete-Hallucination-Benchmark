"""
Verify that 100q NOTA questions match the FCT questions in 300q benchmark.
NOTA_001 should have same question text as FCT_001 (with [Suggestion] stripped), etc.
"""
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FCT_SOURCE = BASE_DIR / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
NOTA_SOURCE = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"

SUGGESTION_PATTERN = re.compile(r"\n\n\[Suggestion\]:.*$", re.DOTALL)


def strip_suggestion(text: str) -> str:
    return SUGGESTION_PATTERN.sub("", text).strip()


def main():
    # Load FCT (lines 201-300)
    with open(FCT_SOURCE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    fct_items = [json.loads(line) for line in lines[200:300] if line.strip()]

    # Load NOTA
    with open(NOTA_SOURCE, "r", encoding="utf-8") as f:
        nota_items = [json.loads(line) for line in f if line.strip()]

    if len(fct_items) != 100 or len(nota_items) != 100:
        print(f"MISMATCH: FCT has {len(fct_items)}, NOTA has {len(nota_items)}")
        return

    mismatches = []
    for i, (fct, nota) in enumerate(zip(fct_items, nota_items)):
        fct_q = strip_suggestion(fct["question"])
        nota_q = nota["question"].strip()
        derived = nota.get("metadata", {}).get("derived_from", "")
        expected_fct_id = f"FCT_{i+1:03d}"

        if fct_q != nota_q:
            mismatches.append({
                "index": i + 1,
                "fct_id": fct["id"],
                "nota_id": nota["id"],
                "reason": "question text differs",
            })
        if derived != expected_fct_id:
            mismatches.append({
                "index": i + 1,
                "fct_id": fct["id"],
                "nota_id": nota["id"],
                "reason": f"derived_from={derived} expected {expected_fct_id}",
            })

    if not mismatches:
        print("CONFIRMED: All 100 NOTA questions match FCT questions (201-300) in 300q benchmark.")
        print("- NOTA_001..NOTA_100 correspond to FCT_001..FCT_100")
        print("- Question text matches (FCT [Suggestion] block stripped)")
        print("- Each NOTA has metadata.derived_from = FCT_XXX")
    else:
        print(f"FOUND {len(mismatches)} mismatches:")
        for m in mismatches[:10]:
            print(f"  {m}")
        if len(mismatches) > 10:
            print(f"  ... and {len(mismatches) - 10} more")


if __name__ == "__main__":
    main()
