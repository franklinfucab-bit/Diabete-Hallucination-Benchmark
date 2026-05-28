"""
Build a new 65q FCT question set from regenerated NOTA.
- Same wrong options (A, B, C) as the regenerated NOTA
- Keep the correct option from the original FCT as D
- Output: 65q_fct_from_nota.jsonl

This ensures FCT and NOTA are perfectly aligned: FCT has one correct (D) and three
unequivocally wrong distractors (A, B, C) that match the NOTA options.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTA_REGENERATED = BASE_DIR / "benchmark" / "65q_nota_regenerated.jsonl"
FCT_SOURCE = BASE_DIR / "benchmark" / "100q_fct_filtered.jsonl"
OUTPUT_FCT = BASE_DIR / "benchmark" / "65q_fct_from_nota.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main():
    nota_list = load_jsonl(NOTA_REGENERATED)
    fct_list = load_jsonl(FCT_SOURCE)
    fct_by_id = {q.get("id", ""): q for q in fct_list}

    output = []
    for nota in nota_list:
        nota_id = nota.get("id", "")
        derived = nota.get("metadata", {}).get("derived_from", "")
        fct = fct_by_id.get(derived)

        if not fct:
            print(f"Skipping {nota_id}: no FCT for {derived}")
            continue

        # Get correct option text from original FCT
        correct_letter = fct.get("answer", "")
        correct_text = fct.get("options", {}).get(correct_letter, "")

        if not correct_text:
            print(f"Skipping {nota_id}: no correct option in FCT")
            continue

        # New FCT: A, B, C = wrong options from regenerated NOTA; D = correct from FCT
        nota_opts = nota.get("options", {})
        new_fct = {
            "id": derived,  # Use FCT id (e.g., FCT_001)
            "question": nota.get("question", ""),
            "options": {
                "A": nota_opts.get("A", ""),
                "B": nota_opts.get("B", ""),
                "C": nota_opts.get("C", ""),
                "D": correct_text,
            },
            "answer": "D",
            "task": "FCT",
            "metadata": fct.get("metadata", {}).copy(),
        }
        # Ensure FCT tag in metadata
        tags = list(new_fct["metadata"].get("tags", []))
        if "FCT" not in tags:
            tags.append("FCT")
        new_fct["metadata"]["tags"] = tags

        output.append(new_fct)

    OUTPUT_FCT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FCT, "w", encoding="utf-8") as f:
        for item in output:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {OUTPUT_FCT} ({len(output)} items)")


if __name__ == "__main__":
    main()
