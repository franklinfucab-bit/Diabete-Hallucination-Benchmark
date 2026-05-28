"""
Build a test-ready benchmark from the new 65q NOTA and 65q FCT (regenerated/aligned).
Output: 130q_nota_fct_test_ready.jsonl (65 NOTA + 65 FCT)
Same format as 400q: question, options, answer, task, metadata.
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
NOTA_SOURCE = BASE_DIR / "benchmark" / "65q_nota_regenerated.jsonl"
FCT_SOURCE = BASE_DIR / "benchmark" / "65q_fct_from_nota.jsonl"
OUTPUT_JSONL = BASE_DIR / "benchmark" / "130q_nota_fct_test_ready.jsonl"


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
    nota = load_jsonl(NOTA_SOURCE)
    fct = load_jsonl(FCT_SOURCE)

    if len(nota) != len(fct):
        raise ValueError(f"Mismatch: NOTA={len(nota)}, FCT={len(fct)}")

    merged = list(nota) + list(fct)
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {OUTPUT_JSONL} ({len(merged)} lines)")
    print(f"  NOTA: {len(nota)}, FCT: {len(fct)}")


if __name__ == "__main__":
    main()
