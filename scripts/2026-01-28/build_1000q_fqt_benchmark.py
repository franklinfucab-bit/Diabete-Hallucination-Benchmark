"""
Build 1000-question FQT v2 benchmark by merging existing questions with newly generated ones.

1. Load existing benchmark (default: 50q sample, or --input path)
2. Generate (1000 - len(existing)) more via concurrent DeepSeek API
3. Merge, renumber IDs FQT_001 to FQT_1000
4. Save to output/Json/1000q_diabetes_fqt_benchmark_v2.jsonl
"""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_FILE = PROJECT_ROOT / "output" / "Json" / "50q_diabetes_fqt_benchmark_sample.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fqt_benchmark_v2.jsonl"

TARGET_TOTAL = 1000


def load_jsonl(filepath: Path) -> list:
    """Load questions from JSONL file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build 1000q FQT v2 benchmark from existing + generated questions")
    ap.add_argument("--input", "-i", default=None, help="Existing benchmark JSONL (default: 50q sample). Used to extend to 1000q.")
    ap.add_argument("--max-workers", type=int, default=4, help="Concurrent API workers for generation")
    ap.add_argument("--output", "-o", default=None, help="Output path (default: 1000q_diabetes_fqt_benchmark_v2.jsonl)")
    ap.add_argument("--quick-test", action="store_true", help="Generate only 20 extra to verify pipeline")
    args = ap.parse_args()

    out_path = Path(args.output) if args.output else OUTPUT_FILE
    input_path = Path(args.input) if args.input else SAMPLE_FILE

    print(f"Loading existing benchmark from {input_path}...")
    existing = load_jsonl(input_path)
    print(f"  Loaded {len(existing)} questions")

    to_generate = 20 if args.quick_test else max(0, TARGET_TOTAL - len(existing))
    if to_generate == 0:
        print(f"Already have {len(existing)} questions (>= {TARGET_TOTAL}). Renumbering and saving only.")
        merged = existing
    else:

        print(f"\nGenerating {to_generate} additional questions (concurrent, max_workers={args.max_workers})...")
        import importlib.util
        import tempfile

        spec = importlib.util.spec_from_file_location(
            "fqt_concurrent",
            SCRIPT_DIR / "Deepseek_generating_FQT_v2_concurrent.py",
        )
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)

        per_category = (to_generate + 3) // 4  # ceil divide for questions per category
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            temp_path = Path(tf.name)
        try:
            gen_mod.run(
                num_per_category=per_category,
                questions_per_call=5,
                max_workers=args.max_workers,
                output_file=temp_path,
            )
            new_questions = []
            with open(temp_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        new_questions.append(json.loads(line))
            new_questions = new_questions[:to_generate]
        finally:
            temp_path.unlink(missing_ok=True)

        print(f"  Generated {len(new_questions)} new questions")

        # Merge
        merged = existing + new_questions

    # Renumber and save
    for i, q in enumerate(merged, 1):
        q["id"] = f"FQT_{i:03d}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for q in merged:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(merged)} questions to {out_path}")


if __name__ == "__main__":
    main()
