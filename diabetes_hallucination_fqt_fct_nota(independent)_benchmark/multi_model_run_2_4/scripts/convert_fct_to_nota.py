"""
Convert 100 FCT questions from the combined benchmark to a NOTA (None of the Above) benchmark.
- Removes the [Suggestion] block from questions
- Replaces correct answer with "None of the above"
- Rearranges options so D is always "None of the above"
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
OUTPUT_FILE = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"

# Regex to remove [Suggestion] block (handles newlines and the full block)
SUGGESTION_PATTERN = re.compile(r"\n\n\[Suggestion\]:.*$", re.DOTALL)


def strip_suggestion(question: str) -> str:
    """Remove the [Suggestion] block from question text."""
    return SUGGESTION_PATTERN.sub("", question).strip()


def rearrange_options(options: dict, correct_letter: str) -> dict:
    """
    Build new options: 3 wrong options as A, B, C (in order, skipping correct), D = "None of the above".
    """
    letters = ["A", "B", "C", "D"]
    wrong_options = [options[letter] for letter in letters if letter != correct_letter]
    return {
        "A": wrong_options[0],
        "B": wrong_options[1],
        "C": wrong_options[2],
        "D": "None of the above",
    }


def transform_fct_to_nota(record: dict, new_id: str) -> dict:
    """Transform a single FCT record to NOTA format."""
    correct_letter = record["answer"]
    question = strip_suggestion(record["question"])
    new_options = rearrange_options(record["options"], correct_letter)

    metadata = record.get("metadata", {}).copy()
    tags = list(metadata.get("tags", []))
    if "NOTA" not in tags:
        tags.append("NOTA")
    if "FCT" in tags:
        tags.remove("FCT")
    metadata["tags"] = tags
    metadata["derived_from"] = record["id"]

    return {
        "id": new_id,
        "question": question,
        "options": new_options,
        "answer": "D",
        "task": "NOTA",
        "metadata": metadata,
    }


def main():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Lines 201-300 are 0-indexed as lines 200-299
    fct_lines = lines[200:300]
    if len(fct_lines) != 100:
        raise ValueError(f"Expected 100 FCT lines, got {len(fct_lines)}")

    output_records = []
    for i, line in enumerate(fct_lines):
        record = json.loads(line.strip())
        new_id = f"NOTA_{i + 1:03d}"
        transformed = transform_fct_to_nota(record, new_id)
        output_records.append(transformed)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_records)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
