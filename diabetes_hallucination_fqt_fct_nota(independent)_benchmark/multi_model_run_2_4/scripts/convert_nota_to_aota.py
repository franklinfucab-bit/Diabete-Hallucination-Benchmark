"""
Convert 100 NOTA (None of the Above) questions to AOTA (All of the Above) format.
- Replaces option D "None of the above" with "All of the above"
- Changes task from NOTA to AOTA
- Renames ids from NOTA_001 to AOTA_001 etc.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
SOURCE_FILE = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"
OUTPUT_DIR = BASE_DIR / "100q AOTA no correct anwser"
OUTPUT_FILE = OUTPUT_DIR / "100q_aota_benchmark.jsonl"


def transform_nota_to_aota(record: dict, new_id: str) -> dict:
    """Transform a single NOTA record to AOTA format."""
    record = record.copy()
    record["id"] = new_id
    record["task"] = "AOTA"
    record["options"] = record["options"].copy()
    record["options"]["D"] = "All of the above"

    metadata = record.get("metadata", {}).copy()
    tags = list(metadata.get("tags", []))
    if "NOTA" in tags:
        tags[tags.index("NOTA")] = "AOTA"
    elif "AOTA" not in tags:
        tags.append("AOTA")
    metadata["tags"] = tags
    record["metadata"] = metadata

    return record


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    if len(records) != 100:
        raise ValueError(f"Expected 100 NOTA records, got {len(records)}")

    output_records = []
    for i, record in enumerate(records):
        new_id = f"AOTA_{i + 1:03d}"
        transformed = transform_nota_to_aota(record, new_id)
        output_records.append(transformed)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_records)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
