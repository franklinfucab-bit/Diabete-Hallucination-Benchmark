# Supplement Materials

Supplement data and code for the diabetes hallucination benchmark.

## Pipeline

- **4000q full** (`dataset/4000q_full/`): 895q FCT, 895q NOTA, 895q AOTA (hardcore-lifestyle), 1000q FQT. We select **diverse root questions** from these to build **1400q golden** (350 per type).
- **1400q golden** (`dataset/1400q_golden/`): 350 FCT, 350 FQT, 350 NOTA, 350 AOTA. **purge_benchmark_to_1000q.py** (in `scripts/`) purges seeds listed in `universal_failures_audit.json` and outputs **1000q core** (250 per type).
- **1000q core** (`dataset/1000q_core/`): Purged benchmark, reports, and per-model combined results.

Key scripts: **purge_benchmark_to_1000q.py**, **audit_universal_failures_deepseek.py**, **collect_nota_aota_1000q.py**, **combine_1000q_results.py**. See `scripts/README.md`.

## Layout

| Folder | Contents |
|--------|----------|
| **scripts/** | Inference (run_inference.py), purge, audit, collect, combine, extract_answer. All paths relative. |
| **dataset/1400q_golden/** | Benchmark (350q per type), reports, per-model results. |
| **dataset/1000q_core/** | Benchmark (250q per type), reports, combined results, purge_manifest.json. |
| **dataset/4000q_full/** | Source pools: 895q FCT/NOTA/AOTA, 1000q FQT. |

Reports and benchmark details (analysis reports, audit files, composition tables) are in the **dataset** subfolders: `dataset/1400q_golden/reports/`, `dataset/1000q_core/reports/`, and the respective `benchmark/` folders. See `dataset/README.md`.

For regenerating from the main project, use `diabetes_hallucination_fqt_fct_nota_benchmark/multi_model_run_2_4/1400q/`. Before zipping for submission, ensure no scripts contain `C:/Users/...` or other machine-specific paths.
