"""
Convert 100 FCT questions from diabetes_fct_benchmark.jsonl to AOTA (All of the Above) format.
- Uses suggested_answer (when wrong) as "most incorrect" - aligns with evaluation report dataset
- Replaces most incorrect option with "All of the above"
- Rearranges options so D is always "All of the above"
- Keeps the original correct answer
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FCT_BENCHMARK = BASE_DIR.parent / "fct" / "diabetes_fct_benchmark.jsonl"
OUTPUT_DIR = BASE_DIR / "100q AOTA Correct from FCT"
OUTPUT_FILE = OUTPUT_DIR / "100q_aota_from_fct_benchmark.jsonl"


def options_list_to_dict(options_list: list) -> dict:
    """Convert [{"option_id": "A", "text": "..."}, ...] to {"A": "...", "B": "...", ...}."""
    return {opt["option_id"]: opt["text"] for opt in options_list}


def get_most_incorrect(record: dict) -> str:
    """
    Get the "most incorrect" option using suggested_answer (method 2 / evaluation report dataset).
    When suggested_answer is wrong, use it. Otherwise use first wrong option alphabetically.
    """
    correct = record["correct_answer"]
    suggested = record.get("suggested_answer", {})
    suggested_letter = suggested.get("option_id")
    suggested_is_correct = record.get("suggested_answer_is_correct", True)

    if suggested_letter and not suggested_is_correct and suggested_letter != correct:
        return suggested_letter
    # Fallback: first wrong option
    for letter in ["A", "B", "C", "D"]:
        if letter != correct:
            return letter
    return "A"


def transform_fct_to_aota(record: dict, new_id: str) -> dict:
    """Transform a single FCT record to AOTA format."""
    correct_letter = record["correct_answer"]
    most_incorrect = get_most_incorrect(record)

    options_list = record["options"]
    options_dict = options_list_to_dict(options_list)

    # Build remaining options: 3 options (1 correct + 2 wrong), skipping most_incorrect
    remaining = [
        (letter, text)
        for letter, text in options_dict.items()
        if letter != most_incorrect
    ]
    # Rearrange so D is always "All of the above"
    new_options = {
        "A": remaining[0][1],
        "B": remaining[1][1],
        "C": remaining[2][1],
        "D": "All of the above",
    }

    # Map old correct letter to new letter
    old_to_new = {remaining[i][0]: ["A", "B", "C"][i] for i in range(3)}
    new_answer = old_to_new[correct_letter]

    tags = list(record.get("tags", []))
    if "FCT" in tags:
        tags.remove("FCT")
    if "AOTA" not in tags:
        tags.append("AOTA")

    metadata = {
        "difficulty": record.get("difficulty_score", 0.5),
        "tags": tags,
        "derived_from": record["id"],
        "most_incorrect_replaced": most_incorrect,
    }

    return {
        "id": new_id,
        "question": record["question"],
        "options": new_options,
        "answer": new_answer,
        "task": "AOTA",
        "metadata": metadata,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(FCT_BENCHMARK, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    fct_records = []
    for line in lines:
        rec = json.loads(line)
        if "id" in rec and "options" in rec:  # FCT format
            fct_records.append(rec)
            if len(fct_records) == 100:
                break
    if len(fct_records) != 100:
        raise ValueError(f"Expected 100 FCT records, got {len(fct_records)}")

    output_records = []
    for i, record in enumerate(fct_records):
        new_id = f"AOTA_{i + 1:03d}"
        transformed = transform_fct_to_aota(record, new_id)
        output_records.append(transformed)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_records)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
