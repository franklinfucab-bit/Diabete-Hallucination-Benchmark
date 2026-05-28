"""
Build merged benchmark: filtered NOTA (K) + 100 FQT + filtered FCT (K) + filtered AOTA (K).
Total = 100 + 3K lines. Reads from benchmark/ filtered JSONL and 300q for FQT.
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FILTERED_NOTA = BASE_DIR / "benchmark" / "100q_nota_filtered.jsonl"
FILTERED_FCT = BASE_DIR / "benchmark" / "100q_fct_filtered.jsonl"
FILTERED_AOTA = BASE_DIR / "benchmark" / "100q_aota_filtered.jsonl"
SOURCE_300Q = BASE_DIR / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
OUTPUT_JSONL = BASE_DIR / "benchmark" / "400q_diabetes_benchmark_combined_ready.jsonl"
MERGE_REPORT = BASE_DIR / "benchmark" / "merge_report.json"
FILTER_REPORT = BASE_DIR / "benchmark" / "filter_category_a_report.json"


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
    nota = load_jsonl(FILTERED_NOTA)
    fct = load_jsonl(FILTERED_FCT)
    aota = load_jsonl(FILTERED_AOTA)
    all_300q = load_jsonl(SOURCE_300Q)
    if len(all_300q) < 200:
        raise ValueError(f"300q has {len(all_300q)} lines, need at least 200 for FQT block")
    fqt_block = all_300q[100:200]  # lines 101-200
    if len(fqt_block) != 100 or any(r.get("task") != "FQT" for r in fqt_block):
        raise ValueError("Expected 100 FQT at lines 101-200")

    K = len(nota)
    if len(fct) != K or len(aota) != K:
        raise ValueError(f"Mismatch: NOTA={len(nota)}, FCT={len(fct)}, AOTA={len(aota)}; expected all {K}")

    merged = list(nota) + list(fqt_block) + list(fct) + list(aota)
    total = len(merged)

    benchmark_dir = BASE_DIR / "benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report = {
        "nota_count": K,
        "fqt_count": 100,
        "fct_count": K,
        "aota_count": K,
        "total": total,
        "output_file": str(OUTPUT_JSONL),
    }
    if FILTER_REPORT.exists():
        with open(FILTER_REPORT, "r", encoding="utf-8") as f:
            filter_report = json.load(f)
        report["removed_fct_ids"] = filter_report.get("removed_fct_ids", [])
        report["kept_fct_ids"] = filter_report.get("kept_fct_ids", [])
    with open(MERGE_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {OUTPUT_JSONL} ({total} lines)")
    print(f"  NOTA: {K}, FQT: 100, FCT: {K}, AOTA: {K}")
    print(f"Wrote {MERGE_REPORT}")


if __name__ == "__main__":
    main()
