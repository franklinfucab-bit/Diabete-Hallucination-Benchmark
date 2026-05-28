"""
Combine each model's FCT+FQT (results_500q_core) and NOTA+AOTA (results_500q_nota_aota)
into one file per model: results_1000q_core/combined/results_{model}.json.

Usage:
  python combine_1000q_results.py
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FCT_FQT_DIR = BASE_DIR / "results_500q_core"
NOTA_AOTA_DIR = BASE_DIR / "results_1000q_core" / "results_500q_nota_aota"
OUTPUT_DIR = BASE_DIR / "results_1000q_core" / "combined"

MODELS = ["qwen2.5_7b", "llama3.1_8b", "gemma_7b", "deepseek-r1_7b", "mistral_latest"]


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def category_from_id(qid: str) -> str:
    if qid.startswith("FCT_"):
        return "FCT"
    if qid.startswith("FQT_"):
        return "FQT"
    if qid.startswith("NOTA_"):
        return "NOTA"
    if qid.startswith("AOTA_"):
        return "AOTA"
    return "unknown"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in MODELS:
        fct_fqt_path = FCT_FQT_DIR / f"results_{model}.json"
        nota_aota_path = NOTA_AOTA_DIR / f"results_{model}.json"
        if not fct_fqt_path.exists():
            print(f"Skip {model}: missing {fct_fqt_path}")
            continue
        if not nota_aota_path.exists():
            print(f"Skip {model}: missing {nota_aota_path}")
            continue
        fct_fqt = load_json(fct_fqt_path)
        nota_aota = load_json(nota_aota_path)
        # Ensure each record has category for consistency
        for r in nota_aota:
            if "category" not in r:
                r["category"] = category_from_id(r.get("id", ""))
        combined = fct_fqt + nota_aota
        out_path = OUTPUT_DIR / f"results_{model}.json"
        save_json(out_path, combined)
        correct = sum(1 for x in combined if x.get("correct"))
        print(f"  {model}: {correct}/{len(combined)} -> {out_path}")
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
