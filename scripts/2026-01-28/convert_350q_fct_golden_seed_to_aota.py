"""
Convert 350q FCT golden seed to AOTA (All of the Above) format.
Uses same logic as convert_fct_to_aota.py: replace one wrong option with "All of the above",
rearrange so D is always "All of the above", keep correct answer; metadata.derived_from = source FCT id.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
INPUT_FILE = WORKSPACE / "output" / "Json" / "350q_fct_v4_golden_seed.jsonl"
OUTPUT_FILE = WORKSPACE / "output" / "Json" / "350q_aota_from_fct_golden_seed.jsonl"


def options_list_to_dict(options_list: list) -> dict:
    """Convert [{"option_id": "A", "text": "..."}, ...] to {"A": "...", "B": "...", ...}."""
    return {opt["option_id"]: opt["text"] for opt in options_list}


def get_most_incorrect(record: dict) -> str:
    """
    Get the "most incorrect" option using suggested_answer when wrong; else first wrong option.
    """
    correct = record["correct_answer"]
    suggested = record.get("suggested_answer", {})
    suggested_letter = suggested.get("option_id") if isinstance(suggested, dict) else None
    suggested_is_correct = record.get("suggested_answer_is_correct", True)

    if suggested_letter and not suggested_is_correct and suggested_letter != correct:
        return suggested_letter
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

    remaining = [
        (letter, text)
        for letter, text in options_dict.items()
        if letter != most_incorrect
    ]
    if len(remaining) != 3:
        raise ValueError(f"Expected 3 remaining options after removing most_incorrect, got {len(remaining)} for id={record.get('id')}")

    new_options = {
        "A": remaining[0][1],
        "B": remaining[1][1],
        "C": remaining[2][1],
        "D": "All of the above",
    }
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
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    fct_records = []
    for line in lines:
        rec = json.loads(line)
        if "id" in rec and "options" in rec:
            fct_records.append(rec)

    output_records = []
    for i, record in enumerate(fct_records):
        new_id = f"AOTA_{i + 1:03d}"
        transformed = transform_fct_to_aota(record, new_id)
        output_records.append(transformed)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Converted {len(output_records)} FCT golden seed -> AOTA -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
