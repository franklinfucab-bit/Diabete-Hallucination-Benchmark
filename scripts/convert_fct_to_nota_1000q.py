"""
Convert 1000q FCT benchmark to NOTA (None of the Above) format.
- Reads: output/Json/1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl
- Outputs: output/Json/1000q_nota_from_fct_hardcore_lifestyle.jsonl
- Handles FCT format: options as array [{option_id, text, is_correct}], correct_answer
- Removes [Suggestion] block from questions
- Rearranges options so D is always "None of the above"

Usage:
  python scripts/convert_fct_to_nota_1000q.py
  python scripts/convert_fct_to_nota_1000q.py --input path/to/fct.jsonl --output path/to/nota.jsonl
"""
import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "Json" / "1000q_nota_from_fct_hardcore_lifestyle.jsonl"

SUGGESTION_PATTERN = re.compile(r"\n\n\[Suggestion\]:.*$", re.DOTALL)


def strip_suggestion(question: str) -> str:
    """Remove the [Suggestion] block from question text."""
    return SUGGESTION_PATTERN.sub("", question).strip()


def transform_fct_to_nota(record: dict, new_id: str) -> dict:
    """Transform a single FCT record (1000q format) to NOTA format."""
    opts = record.get("options", [])
    correct_letter = record.get("correct_answer", "")

    if len(opts) < 4:
        raise ValueError(f"FCT {record.get('id')} has fewer than 4 options")

    options_dict = {o["option_id"]: o["text"] for o in opts}
    wrong_options = [options_dict[k] for k in ["A", "B", "C", "D"] if k != correct_letter]  # preserve order

    if len(wrong_options) != 3:
        raise ValueError(f"FCT {record.get('id')} has wrong number of distractors")

    question = strip_suggestion(record.get("question", ""))
    new_options = {
        "A": wrong_options[0],
        "B": wrong_options[1],
        "C": wrong_options[2],
        "D": "None of the above",
    }

    tags = list(record.get("tags", []))
    if "NOTA" not in tags:
        tags.append("NOTA")
    if "FCT" in tags:
        tags.remove("FCT")

    metadata = record.get("metadata", {}).copy() if isinstance(record.get("metadata"), dict) else {}
    metadata["tags"] = tags
    metadata["derived_from"] = record.get("id", "")

    return {
        "id": new_id,
        "question": question,
        "options": new_options,
        "answer": "D",
        "task": "NOTA",
        "metadata": metadata,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert 1000q FCT to NOTA format")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input FCT JSONL path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output NOTA JSONL path")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        raise SystemExit(1)

    output_records = []
    skipped = 0
    with open(args.input, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                new_id = f"NOTA_{i + 1:03d}"
                transformed = transform_fct_to_nota(record, new_id)
                output_records.append(transformed)
            except (ValueError, KeyError) as e:
                print(f"Skipping line {i + 1}: {e}")
                skipped += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_records)} records to {args.output}")
    if skipped:
        print(f"Skipped {skipped} records due to errors.")


if __name__ == "__main__":
    main()
