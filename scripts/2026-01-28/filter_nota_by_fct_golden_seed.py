"""
Filter NOTA benchmark to only rows whose metadata.derived_from is in the FCT golden seed IDs.
Reads: 350q_fct_v4_golden_seed.jsonl (for IDs), 1000q_nota_benchmark_v4_hardcore_lifestyle.jsonl.
Writes: 350q_nota_from_fct_golden_seed.jsonl (same order as FCT seed by derived_from).
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
FCT_SEED_FILE = PROJECT_ROOT / "output" / "Json" / "350q_fct_v4_golden_seed.jsonl"
NOTA_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_nota_benchmark_v4_hardcore_lifestyle.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "350q_nota_from_fct_golden_seed.jsonl"


def main():
    # FCT seed IDs in order
    fct_ids_ordered = []
    with open(FCT_SEED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            fct_ids_ordered.append(rec.get("id"))
    fct_set = set(fct_ids_ordered)

    # NOTA by derived_from
    nota_by_fct = {}
    with open(NOTA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            derived = (rec.get("metadata") or {}).get("derived_from")
            if derived in fct_set:
                nota_by_fct[derived] = rec

    # Output in same order as FCT seed
    out = []
    for fid in fct_ids_ordered:
        if fid in nota_by_fct:
            out.append(nota_by_fct[fid])
        else:
            raise ValueError(f"NOTA missing for FCT id {fid}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(out)} NOTA rows -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
