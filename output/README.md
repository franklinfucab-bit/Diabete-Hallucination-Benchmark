# Output Folder

Generated benchmarks, evaluation reports, and artifacts.

## Release Benchmark (Recommended)

**`../diabetes_hallucination_fqt_fct_nota_benchmark/`** — Curated release with FQT, FCT, and NOTA benchmarks and evaluation reports. Use this for model evaluation.

## Directory Structure

```
output/
├── Json/                    # Current FQT & FCT benchmarks (1000q)
│   ├── 1000q_diabetes_fqt_benchmark_v2.jsonl
│   ├── 1000q_diabetes_fct_benchmark_v3.5.json
│   ├── 1000q_diabetes_fct_benchmark_v3.7.json
│   ├── 1000q_diabetes_fct_benchmark_v3.8.json
│   └── *_evaluation_report.jsonl
│
├── nota/                    # Current NOTA benchmarks (1000q)
│   ├── 1000q_diabetes_nota_benchmark_v3.jsonl
│   ├── 1000q_diabetes_nota_benchmark_v3.1.jsonl
│   ├── 1000q_diabetes_nota_benchmark_v3.2.jsonl
│   └── *_evaluation_report.jsonl
│
├── archive/                  # Old versions and temporary files
│   ├── json/                 # Archived benchmark versions, samples, checkpoints
│   ├── tmp/                  # NOTA v3 generation temp files
│   ├── NOTA_V3_TMP_FILES_README.md
│   └── ...
│
├── logs/                     # Merge and evaluation logs
├── reports/                  # Generation comparison reports
│
├── 2026-01-27/               # Historical outputs by date
│   ├── fake_questions_test/
│   ├── false_confidence_test/
│   └── none_of_above/
│
├── binary/benchmark/          # Legacy binary benchmark
├── fake_questions_test/       # Legacy FQT
├── multiple_choice/          # Legacy multiple choice
└── none_of_above/            # Legacy NOTA benchmarks
```

## File Types

- **Benchmark**: `*_benchmark.jsonl` or `*_benchmark.json`
- **Evaluation report**: `*_evaluation_report.jsonl`
- **Checkpoint**: `*.eval_checkpoint.json` (for resuming evaluation)
