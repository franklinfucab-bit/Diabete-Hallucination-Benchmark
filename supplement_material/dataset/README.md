# Dataset

Benchmark data for the diabetes hallucination benchmark: source pools (4000q full), golden set (1400q), and purged core (1000q).

## Subfolders

**4000q_full/** — Source question pools. From these we select diverse root questions to build 1400q golden.

- `895q_diabetes_fct_benchmark_v4_hardcore_lifestyle.jsonl` — FCT (895q)
- `895q_diabetes_nota_converted_from_fct_hardcore_lifestyle.jsonl` — NOTA converted from FCT (895q)
- `895q_diabetes_aota_converted_from_fct_hardcore_lifestyle.jsonl` — AOTA converted from FCT (895q)
- `1000_diabetes_fqt_benchmark.jsonl` — FQT (1000q)
- `1000q_diabetes_fct_benchmark_v4_full.jsonl` — Full FCT v4 (1000q+), optional reference

**1400q_golden/** — Golden benchmark (350 questions per type, 1400 total) before purge.

- **benchmark/** — `350q_fct_v4_golden_seed.jsonl`, `350q_fqt_v2_golden_seed.jsonl`, `350q_nota_from_fct_golden_seed.jsonl`, `350q_aota_from_fct_golden_seed.jsonl`, and `350q_golden_seed_combined_test_ready.jsonl`
- **reports/** — `1400q_golden_analysis_report.md` / `.json`, `universal_failures_audit.json`
- **results/** — Per-model result files (`results_{model}.json`; NOTA + AOTA in this run)

**1000q_core/** — Purged 1000q benchmark (250 per type) and evaluation results.

- **benchmark/** — `250q_fct_core.jsonl`, `250q_fqt_core.jsonl`, `250q_nota_core.jsonl`, `250q_aota_core.jsonl`; combined: `500q_fct_fqt_core_combined_test_ready.jsonl`, `1000q_core_combined_test_ready.jsonl`; `tab_dataset_composition.tex`
- **reports/** — `1000q_core_analysis_report.md` / `.json`
- **results/** — Per-model combined results (all 4 types in one file): `results_{model}.json`
- **purge_manifest.json** — List of purged seeds and counts

## Evaluation

To run inference on the 1000q core, use the combined benchmark:

`1000q_core/benchmark/1000q_core_combined_test_ready.jsonl`

Each line is a JSON object with `id`, `question`, `options` (array of `{option_id, text, is_correct}` or dict `{A, B, C, D}` depending on source), and `correct_answer` or `answer` (single letter A/B/C/D). Compare the model’s predicted letter to this field for accuracy.
