"""
Combine all 4 x 350q golden seed files into one test-ready JSONL.

Inputs (in order):
  - 350q_fct_v4_golden_seed.jsonl
  - 350q_nota_from_fct_golden_seed.jsonl
  - 350q_aota_from_fct_golden_seed.jsonl
  - 350q_fqt_v2_golden_seed.jsonl

Output: 350q_golden_seed_combined_test_ready.jsonl (1400 lines).
Each record kept as-is; FCT/FQT have correct_answer, NOTA/AOTA have answer.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "Json"

FILES = [
    OUTPUT_DIR / "350q_fct_v4_golden_seed.jsonl",
    OUTPUT_DIR / "350q_nota_from_fct_golden_seed.jsonl",
    OUTPUT_DIR / "350q_aota_from_fct_golden_seed.jsonl",
    OUTPUT_DIR / "350q_fqt_v2_golden_seed.jsonl",
]
OUTPUT_FILE = OUTPUT_DIR / "350q_golden_seed_combined_test_ready.jsonl"


def load_jsonl(path: Path) -> list:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def main():
    combined = []
    for path in FILES:
        if not path.exists():
            raise FileNotFoundError(path)
        rows = load_jsonl(path)
        combined.extend(rows)
        print(f"  {path.name}: {len(rows)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in combined:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(combined)} rows -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
