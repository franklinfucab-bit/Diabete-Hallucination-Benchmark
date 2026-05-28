# 1400q Golden Benchmark Analysis Report

**Benchmark:** 700 questions (350 NOTA + 350 AOTA) from golden seed  
**Models:** Qwen2.5 7B, Llama 3.1 8B, Gemma 7B, DeepSeek-R1 7B, Mistral Latest  
**Date:** 2026-02-24

---

## 1. Executive Summary

**Key finding:** The benchmark reveals a clear divide between **NOTA** (None of the above) and **AOTA** (All of the above) task types. Models perform much better on AOTA than NOTA across the board. Qwen2.5 leads on NOTA (60.3%); Mistral leads on AOTA (85.1%). Gemma shows a strong bias toward answering "D" (All of the above) for AOTA when wrong—171 of 184 wrong answers were D.

---

## 2. Overall Accuracy by Model

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Mistral Latest** | 377 | 700 | **53.9%** |
| **Qwen2.5 7B** | 498 | 700 | **71.1%** |
| **Llama 3.1 8B** | 316 | 699 | **45.2%** |
| **DeepSeek-R1 7B** | 322 | 695 | **46.3%** |
| **Gemma 7B** | 238 | 700 | **34.0%** |

*Note: DeepSeek missing 5 questions; Llama missing 1.*

---

## 3. Accuracy by Question Type: FCT, FQT, NOTA, AOTA

*Comparison table: models in rows, question types in columns. Source: 400q benchmark (65 FCT, 100 FQT, 65 NOTA, 65 AOTA) for all four types. The 1400q golden benchmark contains only NOTA and AOTA (350 each).*

| Model | FCT | FQT | NOTA | AOTA |
|-------|-----|-----|------|------|
| **Qwen2.5 7B** | 84.6% | 93.0% | 41.5% | 93.8% |
| **Llama 3.1 8B** | 72.3% | 96.0% | 17.2% | 72.3% |
| **Gemma 7B** | 75.4% | 8.0% | 21.5% | 32.3% |
| **DeepSeek-R1 7B** | 67.7% | 22.0% | 21.5% | 81.5% |
| **Mistral Latest** | 53.8% | 49.0% | 16.9% | 89.2% |

**1400q Golden (NOTA + AOTA only, 350 each):**

| Model | NOTA | AOTA |
|-------|------|------|
| **Qwen2.5 7B** | 60.3% | 82.0% |
| **Llama 3.1 8B** | 17.1% | 73.1% |
| **Gemma 7B** | 20.6% | 47.4% |
| **DeepSeek-R1 7B** | 26.1% | 66.8% |
| **Mistral Latest** | 22.6% | 85.1% |

---

## 3.1 FCT vs NOTA vs AOTA: Same Clinical Scenarios (Paired Comparison)

*NOTA and AOTA are both converted from FCT questions—they share the same clinical scenario but differ in format:*
- **FCT:** Original format—pick the one correct answer (A, B, C, or D).
- **NOTA:** Converted—all distractors (A, B, C) are wrong; correct answer is D ("None of the above").
- **AOTA:** Converted—D is "All of the above" (distractor); correct answer is one of A, B, or C.

*Below: accuracy on the **same 65 paired scenarios** (400q benchmark).*

| Model | FCT (original) | NOTA (from FCT) | AOTA (from FCT) | NOTA vs FCT Δ | AOTA vs FCT Δ |
|-------|-----------------|-----------------|-----------------|---------------|---------------|
| **Qwen2.5 7B** | 84.6% | 41.5% | 93.8% | −43.1% | +9.2% |
| **Llama 3.1 8B** | 72.3% | 17.2% | 72.3% | −55.1% | 0.0% |
| **Gemma 7B** | 75.4% | 21.5% | 32.3% | −53.9% | −43.1% |
| **DeepSeek-R1 7B** | 67.7% | 21.5% | 81.5% | −46.2% | +13.8% |
| **Mistral Latest** | 53.8% | 16.9% | 89.2% | −36.9% | +35.4% |

**Findings:**
- **NOTA is consistently harder than FCT** for all models (−37% to −55%). Converting to NOTA format substantially reduces accuracy.
- **AOTA vs FCT is mixed:** Qwen, DeepSeek, and Mistral do as well or better on AOTA; Gemma does much worse (−43%).
- **Format sensitivity:** The same clinical knowledge performs very differently depending on whether the task is FCT (pick correct), NOTA (reject all), or AOTA (pick one, avoid "All of the above").

---

## 4. Accuracy by Question Type (NOTA vs AOTA) — Detail

### 4.1 NOTA (None of the Above) — 350 questions

Correct answer is always **D**. All models must reject distractors A, B, C.

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 211 | 350 | **60.3%** |
| **DeepSeek-R1 7B** | 91 | 349 | **26.1%** |
| **Mistral Latest** | 79 | 350 | **22.6%** |
| **Gemma 7B** | 72 | 350 | **20.6%** |
| **Llama 3.1 8B** | 60 | 350 | **17.1%** |

### 4.2 AOTA (All of the Above) — 350 questions

Correct answer is **A**, **B**, or **C** (one specific option). D = "All of the above" is a distractor.

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Mistral Latest** | 298 | 350 | **85.1%** |
| **Qwen2.5 7B** | 287 | 350 | **82.0%** |
| **Llama 3.1 8B** | 256 | 350 | **73.1%** |
| **DeepSeek-R1 7B** | 231 | 346 | **66.8%** |
| **Gemma 7B** | 166 | 350 | **47.4%** |

### 4.3 Task-Type Gap

| Model | NOTA Acc | AOTA Acc | Gap (AOTA − NOTA) |
|-------|----------|----------|-------------------|
| Qwen2.5 7B | 60.3% | 82.0% | **+21.7%** |
| Llama 3.1 8B | 17.1% | 73.1% | **+56.0%** |
| Gemma 7B | 20.6% | 47.4% | **+26.8%** |
| DeepSeek-R1 7B | 26.1% | 66.8% | **+40.7%** |
| Mistral Latest | 22.6% | 85.1% | **+62.5%** |

**NOTA is consistently harder for all models.** Llama and Mistral show the largest gaps.

---

## 5. Topics with Most Errors

*Primary topic = first non-generic tag per question. Error rate = total errors across models / (questions × 5 models).*

| Topic | Questions | Total Errors | Est. Error Rate |
|-------|-----------|--------------|-----------------|
| **acute_hospital** | 202 | 576 | ~57% |
| **hypoglycemia** | 62 | 155 | ~50% |
| **guideline-based management** | 62 | 144 | ~46% |
| **pharmacotherapy** | 44 | 104 | ~47% |
| **retinopathy_kidney** | 32 | 100 | ~62% |
| **neuropathy_footcare** | 42 | 88 | ~42% |
| **insulin pump** | 20 | 61 | ~61% |
| **medication safety** | 18 | 42 | ~47% |
| **basal rate adjustment** | 4 | 14 | ~70% |
| **GLP-1 agonist** | 4 | 14 | ~70% |

**Topics with highest error rates:** basal rate adjustment, GLP-1 agonist, retinopathy_kidney, insulin pump.

---

## 6. Wrong-Answer Distribution

### 6.1 NOTA (when wrong, models pick A, B, or C)

| Model | A | B | C |
|-------|---|---|---|
| Qwen2.5 7B | 49 | 50 | 40 |
| Llama 3.1 8B | 117 | 117 | 56 |
| Gemma 7B | 70 | 114 | 94 |
| DeepSeek-R1 7B | 98 | 92 | 68 |
| Mistral Latest | 110 | 79 | 82 |

Llama and Gemma show a slight bias toward **B** when wrong on NOTA.

### 6.2 AOTA (when wrong, models pick A, B, C, or D)

| Model | A | B | C | D |
|-------|---|---|---|---|
| Qwen2.5 7B | 6 | 14 | 6 | **37** |
| Llama 3.1 8B | 38 | 37 | 16 | 2 |
| **Gemma 7B** | 12 | 12 | 1 | **171** |
| DeepSeek-R1 7B | 33 | 32 | 23 | 25 |
| Mistral Latest | 21 | 20 | 10 | 1 |

**Gemma:** When wrong on AOTA, it picks **D** (All of the above) 171 of 184 times — a strong default bias.

**Qwen2.5:** Also favors D when wrong (37 of 63), but less extreme.

---

## 7. Universal Failures (All Models Wrong)

**108 questions** were answered incorrectly by all 5 models.

- Sample NOTA IDs: NOTA_005, NOTA_008, NOTA_011, NOTA_023, NOTA_027, NOTA_032, NOTA_042, NOTA_048, NOTA_062, NOTA_072
- These are strong candidates for benchmark review, curriculum design, or targeted training.

---

## 8. N/A Predictions

| Model | N/A Count |
|-------|-----------|
| Qwen2.5 7B | 0 |
| Llama 3.1 8B | 1 |
| Gemma 7B | 0 |
| DeepSeek-R1 7B | 2 |
| Mistral Latest | 0 |

---

## 9. Interesting Findings

1. **NOTA vs AOTA asymmetry:** NOTA requires rejecting all distractors; AOTA requires selecting one correct option. The large accuracy gap (e.g., Mistral 22.6% vs 85.1%) suggests NOTA is a harder cognitive task.

2. **Gemma’s AOTA bias:** Gemma defaults to "All of the above" when uncertain on AOTA; 93% of its wrong AOTA answers are D. This is a clear behavioral pattern.

3. **Qwen2.5 as NOTA leader:** Qwen2.5 is the only model above 50% on NOTA (60.3%). It may be better at rejecting plausible distractors.

4. **Acute hospital dominates:** 202 of 700 questions (29%) are tagged acute_hospital, and this topic has the highest total error count. Hospital/acute care scenarios may be harder across models.

5. **Specialized topics:** Basal rate adjustment, GLP-1 agonist, retinopathy_kidney, and insulin pump show the highest error rates per question, suggesting these are harder for current models.

6. **108 universal failures:** Over 15% of questions stump all models. These could be used for focused training or benchmark refinement.

---

## 10. Recommendations

1. **Benchmark design:** Consider balancing NOTA and AOTA difficulty or adding more NOTA practice items.
2. **Model calibration:** Gemma’s AOTA bias could be addressed by prompt design or post-processing.
3. **Topic coverage:** Prioritize acute hospital, hypoglycemia, and guideline-based management for model improvement.
4. **Audit universal failures:** Review the 108 questions all models miss for logic issues, ambiguity, or outdated content. *(See Section 11 and `universal_failures_audit.json`.)*

---

## 11. Universal Failures Audit (DeepSeek)

The 108 questions that all 5 models answered incorrectly were audited via DeepSeek API for logic issues, ambiguity, and outdated content.

**Script:** `1400q/scripts/audit_universal_failures_deepseek.py`  
**Output:** `results_1400q_golden/reports/universal_failures_audit.json`

**Run:**
```bash
cd diabetes_hallucination_fqt_fct_nota_benchmark/multi_model_run_2_4/1400q/scripts
python audit_universal_failures_deepseek.py
```

**Sample findings (from pilot audit):** All 3 pilot questions (AOTA_040, AOTA_044, AOTA_047) were flagged with benchmark issues:
- **AOTA_040:** Ambiguous clinical scenario—multiple defensible fluid management options in DKA.
- **AOTA_044:** Flawed key—"primary rationale" for low-dose insulin is debatable; correct answer not aligned with current guidelines.
- **AOTA_047:** Invalid structure—"All of the above" with mutually exclusive numerical options.

*Run the full audit to get the complete list of questions with potential benchmark issues.*

---

*Report generated from `results_1400q_golden` and `350q_*_golden_seed.jsonl` benchmark.*
