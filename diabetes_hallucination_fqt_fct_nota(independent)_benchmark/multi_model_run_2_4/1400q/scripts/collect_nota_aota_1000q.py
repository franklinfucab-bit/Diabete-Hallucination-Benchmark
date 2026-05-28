"""
Collect NOTA and AOTA results used in the 1000q core from the 1400q golden run.
Reads 250q_nota_core.jsonl and 250q_aota_core.jsonl to get kept IDs, filters
results_1400q_golden/results_{model}.json to those IDs, and writes
results_1000q_core/results_500q_nota_aota/results_{model}.json.

Usage:
  python collect_nota_aota_1000q.py
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR_1400 = BASE_DIR / "results_1400q_golden"
OUTPUT_DIR = BASE_DIR / "results_1000q_core" / "results_500q_nota_aota"
BENCHMARK_DIR = BASE_DIR / "results_1000q_core" / "benchmark"

NOTA_CORE = BENCHMARK_DIR / "250q_nota_core.jsonl"
AOTA_CORE = BENCHMARK_DIR / "250q_aota_core.jsonl"

MODELS = ["qwen2.5_7b", "llama3.1_8b", "gemma_7b", "deepseek-r1_7b", "mistral_latest"]


def load_jsonl(path: Path) -> list:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    if not NOTA_CORE.exists() or not AOTA_CORE.exists():
        print("Run purge_benchmark_to_1000q.py first to create 250q_nota_core.jsonl and 250q_aota_core.jsonl")
        return

    nota_items = load_jsonl(NOTA_CORE)
    aota_items = load_jsonl(AOTA_CORE)
    kept_nota_ids = {x["id"] for x in nota_items}
    kept_aota_ids = {x["id"] for x in aota_items}
    kept_ids = kept_nota_ids | kept_aota_ids
    print(f"Kept NOTA: {len(kept_nota_ids)}, AOTA: {len(kept_aota_ids)}, total: {len(kept_ids)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in MODELS:
        src = RESULTS_DIR_1400 / f"results_{model}.json"
        if not src.exists():
            print(f"Skip {model}: {src} not found")
            continue
        data = load_json(src)
        id_to_result = {x["id"]: x for x in data}
        filtered = [id_to_result[qid] for qid in kept_ids if qid in id_to_result]
        out_path = OUTPUT_DIR / f"results_{model}.json"
        save_json(out_path, filtered)
        correct = sum(1 for x in filtered if x.get("correct"))
        print(f"  {model}: {correct}/{len(filtered)} -> {out_path}")
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
