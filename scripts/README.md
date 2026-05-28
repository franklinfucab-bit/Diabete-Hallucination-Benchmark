# Scripts

Generation and evaluation scripts for the Diabetes Hallucination Benchmark.

## Structure

- **2026-01-27/** — Initial FQT, FCT, NOTA generation scripts
- **2026-01-28/** — 1000q generation, DeepSeek/Gemini pipelines, merge scripts
- **Evaluation/** — Benchmark quality evaluation (Concur, single-thread)
- **archive/** — Deprecated scripts

## Key Scripts

| Script | Purpose |
|--------|---------|
| `2026-01-28/Deepseek_generating_FQT_v2*.py` | Generate 1000q FQT benchmark |
| `2026-01-28/merge_nota_v3.py` | Merge NOTA v3 from chunks |
| `build_nota_v3_2_sglt2_neuro.py` | Build NOTA v3.2 with SGLT2/neuro topics |
| `Evaluation/Concur_evaluate_benchmark_quality.py` | Evaluate benchmark quality (parallel) |

## Output Paths

- FQT/FCT: `output/Json/`
- NOTA: `output/nota/`
- Release: `../diabetes_hallucination_fqt_fct_nota_benchmark/`
