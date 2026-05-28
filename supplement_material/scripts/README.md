# Scripts — Reproducibility Proof

This folder contains the scripts used to run the benchmark and to produce the 1000q core from the 1400q golden set. All paths are relative (no hardcoded `C:/Users/...`). `BASE_DIR` is the parent of this folder (i.e. `supplement_material/` when run from here).

## Contents

### Inference and answer extraction

- **run_inference.py** — Run the benchmark on local LLMs via the Ollama API (port 11434). Reads `BASE_DIR/data/1000q_core_combined_test_ready.jsonl`, sends zero-shot prompts, extracts A/B/C/D with regex, and writes per-model JSONs to `BASE_DIR/results/`. Used on SSH for evaluation.
- **run_infererence.py** — Same purpose (alternate spelling); use one of the two.
- **extract_answer.py** — Standalone regex script to extract the chosen option (A, B, C, or D) from model output. Strips `<think>...</think>`, then finds the last A–D. Same logic as inside `run_inference.py`. Run with `--text "..."` or stdin.

### Benchmark filtering and analysis

- **purge_benchmark_to_1000q.py** — Build the 1000q core from the 1400q golden benchmark: drop seeds listed in `universal_failures_audit.json`, output 250 questions per type (FCT, FQT, NOTA, AOTA), and write accuracy reports. Expects `BASE_DIR/results_1400q_golden/` (benchmark + reports + per-model results) and writes `BASE_DIR/results_1000q_core/` (benchmark, purge_manifest, reports).
- **collect_nota_aota_1000q.py** — Collect NOTA and AOTA results for the 1000q subset from the 1400q golden result files; writes filtered per-model JSONs.
- **combine_1000q_results.py** — Merge each model’s FCT+FQT and NOTA+AOTA result files into one combined result file per model.
- **analyze_fct_fqt_results.py** — Analyze FCT/FQT results (e.g. from 500q core) and append sections to the 1000q core analysis report.
- **audit_universal_failures_deepseek.py** — Audit questions that all models get wrong; outputs `universal_failures_audit.json` used by the purge script.

## Running

- From the repo: `python supplement_material/scripts/run_inference.py` (or `cd supplement_material/scripts` then `python run_inference.py`). Ensure `BASE_DIR` has `data/` and `results/` (or adjust paths in the script).
- For **purge_benchmark_to_1000q.py**, run from a directory where the parent contains `results_1400q_golden/` and where `results_1000q_core/` should be created; or set `BASE_DIR` inside the script to your 1400q tree.

## Before zipping for submission

- Do not include scripts that contain `C:/Users/...` or other machine-specific paths. These scripts use only `Path(__file__).resolve().parent` and `BASE_DIR`.
