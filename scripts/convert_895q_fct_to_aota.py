"""
Convert 895q FCT v4 hardcore to AOTA (All of the Above) format.
Input: supplement_material/dataset/4000q_full/895q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl
Output: supplement_material/dataset/4000q_full/895q_diabetes_aota_converted_from_fct_hardcore_lifestyle.jsonl
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "supplement_material" / "dataset" / "4000q_full" / "895q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "supplement_material" / "dataset" / "4000q_full" / "895q_diabetes_aota_converted_from_fct_hardcore_lifestyle.jsonl"


def get_most_incorrect(record: dict) -> str:
    correct = record.get("correct_answer", "")
    suggested = record.get("suggested_answer", {})
    suggested_letter = suggested.get("option_id") if suggested else None
    suggested_is_correct = record.get("suggested_answer_is_correct", True)
    if suggested_letter and not suggested_is_correct and suggested_letter != correct:
        return suggested_letter
    for letter in ["A", "B", "C", "D"]:
        if letter != correct:
            return letter
    return "A"


def transform_fct_to_aota(record: dict, new_id: str) -> dict:
    correct_letter = record.get("correct_answer", "")
    most_incorrect = get_most_incorrect(record)
    options_list = record.get("options", [])
    ordered_options = [(opt["option_id"], opt["text"]) for opt in options_list]
    remaining = [(letter, text) for letter, text in ordered_options if letter != most_incorrect]
    if len(remaining) != 3:
        raise ValueError(f"Expected 3 remaining for {record.get('id')}, got {len(remaining)}")
    new_options = {
        "A": remaining[0][1],
        "B": remaining[1][1],
        "C": remaining[2][1],
        "D": "All of the above",
    }
    old_to_new = {remaining[i][0]: ["A", "B", "C"][i] for i in range(3)}
    new_answer = old_to_new.get(correct_letter, "A")
    tags = list(record.get("tags", []))
    if "FCT" in tags:
        tags.remove("FCT")
    if "AOTA" not in tags:
        tags.append("AOTA")
    metadata = {
        "difficulty": record.get("difficulty_score", 0.5),
        "tags": tags,
        "derived_from": record.get("id", ""),
        "most_incorrect_replaced": most_incorrect,
    }
    return {
        "id": new_id,
        "question": record.get("question", ""),
        "options": new_options,
        "answer": new_answer,
        "task": "AOTA",
        "metadata": metadata,
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    output_records = []
    for i, record in enumerate(records):
        new_id = f"AOTA_{i + 1:04d}" if len(records) >= 1000 else f"AOTA_{i + 1:03d}"
        output_records.append(transform_fct_to_aota(record, new_id))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {OUTPUT_FILE} ({len(output_records)} records)")


if __name__ == "__main__":
    main()
