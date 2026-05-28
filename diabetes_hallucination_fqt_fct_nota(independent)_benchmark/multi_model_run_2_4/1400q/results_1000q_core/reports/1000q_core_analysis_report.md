# 1000q Core Benchmark Analysis Report

**Benchmark:** 1020 questions (255 FCT, 255 FQT, 255 NOTA, 255 AOTA) — purged from 1,400q golden
**Models:** Qwen2.5 7B, Llama 3.1 8B, Gemma 7B, DeepSeek-R1 7B, Mistral Latest
**Note:** NOTA + AOTA accuracy from 1000q core (510 questions). FCT + FQT from results_500q_core (510 questions).

### Accuracy by Question Type

| Model | FCT | FQT | NOTA | AOTA |
|-------|-----|-----|------|------|
| **Qwen2.5 7B** | 94.5% | 93.7% | 82.0% | 87.1% |
| **Llama 3.1 8B** | 88.2% | 95.3% | 23.5% | 78.0% |
| **Gemma 7B** | 69.4% | 2.7% | 28.2% | 51.8% |
| **DeepSeek-R1 7B** | 72.2% | 22.4% | 34.3% | 70.6% |
| **Mistral Latest** | 81.6% | 27.8% | 31.0% | 90.6% |

---

## 1. Executive Summary

**Key finding:** The 1000q core (after purging 95 seeds with benchmark issues) shows improved accuracy across models. Qwen2.5 7B leads on NOTA+AOTA (84.5%) and FCT+FQT (94.1%). NOTA remains harder than AOTA for all models. FQT (false-premise questions) is much harder than FCT for Gemma, DeepSeek, and Mistral—Gemma scores only 2.7% on FQT vs 69.4% on FCT.

---

## 2. Purge Summary

- Seeds purged: 95
- Kept: 255 FCT, 255 FQT, 255 NOTA, 255 AOTA

---

## 3. Overall Accuracy (NOTA + AOTA, 510 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 431 | 510 | **84.5%** |
| **Llama 3.1 8B** | 259 | 510 | **50.8%** |
| **Gemma 7B** | 204 | 510 | **40.0%** |
| **DeepSeek-R1 7B** | 265 | 506 | **52.4%** |
| **Mistral Latest** | 310 | 510 | **60.8%** |

---

## 4. Accuracy by Task (NOTA vs AOTA)

### 4.1 NOTA (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 209 | 255 | **82.0%** |
| **Llama 3.1 8B** | 60 | 255 | **23.5%** |
| **Gemma 7B** | 72 | 255 | **28.2%** |
| **DeepSeek-R1 7B** | 87 | 254 | **34.3%** |
| **Mistral Latest** | 79 | 255 | **31.0%** |

### 4.2 AOTA (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 222 | 255 | **87.1%** |
| **Llama 3.1 8B** | 199 | 255 | **78.0%** |
| **Gemma 7B** | 132 | 255 | **51.8%** |
| **DeepSeek-R1 7B** | 178 | 252 | **70.6%** |
| **Mistral Latest** | 231 | 255 | **90.6%** |

### 4.3 Task-Type Gap (AOTA − NOTA)

| Model | NOTA Acc | AOTA Acc | Gap |
|-------|----------|----------|-----|
| Qwen2.5 7B | 82.0% | 87.1% | **+5.1%** |
| Llama 3.1 8B | 23.5% | 78.0% | **+54.5%** |
| Gemma 7B | 28.2% | 51.8% | **+23.5%** |
| DeepSeek-R1 7B | 34.3% | 70.6% | **+36.4%** |
| Mistral Latest | 31.0% | 90.6% | **+59.6%** |

---

## 5. Improvement After Purge (1400q vs 1000q)

| Model | 1400q Acc | 1000q Acc | Δ |
|-------|-----------|-----------|---|
| Qwen2.5 7B | 71.1% | 84.5% | +13.4% |
| Llama 3.1 8B | 45.1% | 50.8% | +5.6% |
| Gemma 7B | 34.0% | 40.0% | +6.0% |
| DeepSeek-R1 7B | 46.3% | 52.4% | +6.0% |
| Mistral Latest | 53.9% | 60.8% | +6.9% |

---

## 6. Topics with Most Errors

*Error rate = total errors across models / (questions × 5).*

| Topic | Questions | Total Errors | Est. Error Rate |
|-------|-----------|--------------|-----------------|
| **acute_hospital** | 146 | 354 | ~48% |
| **guideline-based management** | 50 | 108 | ~43% |
| **hypoglycemia** | 40 | 76 | ~38% |
| **pharmacotherapy** | 34 | 69 | ~41% |
| **neuropathy_footcare** | 36 | 67 | ~37% |
| **medication safety** | 18 | 42 | ~47% |
| **retinopathy_kidney** | 16 | 36 | ~45% |
| **insulin pump** | 10 | 28 | ~56% |
| **cardiovascular prevention** | 12 | 21 | ~35% |
| **gestational diabetes** | 6 | 15 | ~50% |
| **GLP-1 agonist** | 4 | 14 | ~70% |
| **type 1 diabetes** | 8 | 12 | ~30% |
| **SMBG** | 8 | 11 | ~28% |
| **lipid guidelines** | 4 | 9 | ~45% |
| **sulfonylureas** | 6 | 9 | ~30% |

---

## 7. Wrong-Answer Distribution

### 7.1 NOTA (when wrong, models pick A, B, or C)

| Model | A | B | C |
|-------|---|---|---|
| Qwen2.5 7B | 20 | 13 | 13 |
| Llama 3.1 8B | 76 | 81 | 38 |
| Gemma 7B | 43 | 77 | 63 |
| DeepSeek-R1 7B | 53 | 70 | 44 |
| Mistral Latest | 70 | 55 | 51 |

### 7.2 AOTA (when wrong, models pick A, B, C, or D)

| Model | A | B | C | D |
|-------|---|---|---|---|
| Qwen2.5 7B | 1 | 4 | 4 | 24 |
| Llama 3.1 8B | 24 | 20 | 9 | 2 |
| Gemma 7B | 0 | 6 | 1 | 116 |
| DeepSeek-R1 7B | 15 | 23 | 17 | 18 |
| Mistral Latest | 10 | 10 | 3 | 1 |

---

## 8. Universal Failures (All Models Wrong)

**8 questions** in the 1000q core were answered incorrectly by all 5 models.

---

## 9. N/A Predictions

| Model | N/A Count |
|-------|-----------|
| Qwen2.5 7B | 0 |
| Llama 3.1 8B | 1 |
| Gemma 7B | 0 |
| DeepSeek-R1 7B | 1 |
| Mistral Latest | 0 |

---

## 10. Interesting Findings

1. **Purge impact:** Removing 95 seeds with benchmark issues improved overall accuracy by +13.4% (Qwen) to +6.9% (Mistral).
2. **NOTA leader:** Qwen2.5 7B leads on NOTA with 82.0%.
3. **AOTA leader:** Mistral Latest leads on AOTA with 90.6%.
4. **NOTA vs AOTA:** NOTA remains harder for all models; the task-type gap persists in the purged core.
5. **Universal failures:** 8 questions still stump all models—candidates for further review.
6. **FCT/FQT:** Qwen2.5 and Llama 3.1 excel on both FCT (factual) and FQT (false-premise). Gemma, DeepSeek, and Mistral struggle on FQT—accepting fabricated concepts instead of answering D (challenge the premise).

---

## 11. Recommendations

1. **FQT robustness:** Models that accept false premises (Gemma, DeepSeek, Mistral) may benefit from training on hallucination-detection and premise-challenging.
2. **Topic focus:** Prioritize topics with highest error rates for model improvement.
3. **Format sensitivity:** Consider NOTA-specific training given the persistent accuracy gap.

---

## 12. FCT and FQT (500q Core)

*Results from results_500q_core: 255 FCT + 255 FQT = 510 questions.*

### 12.1 Overall FCT+FQT Accuracy (510 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 480 | 510 | **94.1%** |
| **Llama 3.1 8B** | 468 | 510 | **91.8%** |
| **Gemma 7B** | 184 | 510 | **36.1%** |
| **DeepSeek-R1 7B** | 241 | 509 | **47.3%** |
| **Mistral Latest** | 279 | 510 | **54.7%** |

### 12.2 FCT Accuracy (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 241 | 255 | **94.5%** |
| **Llama 3.1 8B** | 225 | 255 | **88.2%** |
| **Gemma 7B** | 177 | 255 | **69.4%** |
| **DeepSeek-R1 7B** | 184 | 255 | **72.2%** |
| **Mistral Latest** | 208 | 255 | **81.6%** |

### 12.3 FQT Accuracy (255 questions)

| Model | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| **Qwen2.5 7B** | 239 | 255 | **93.7%** |
| **Llama 3.1 8B** | 243 | 255 | **95.3%** |
| **Gemma 7B** | 7 | 255 | **2.7%** |
| **DeepSeek-R1 7B** | 57 | 254 | **22.4%** |
| **Mistral Latest** | 71 | 255 | **27.8%** |

### 12.4 FCT vs FQT Gap (FCT − FQT)

*Positive = FCT harder; Negative = FQT harder.*

| Model | FCT Acc | FQT Acc | Gap |
|-------|---------|---------|-----|
| Qwen2.5 7B | 94.5% | 93.7% | **+0.8%** |
| Llama 3.1 8B | 88.2% | 95.3% | **-7.1%** |
| Gemma 7B | 69.4% | 2.7% | **+66.7%** |
| DeepSeek-R1 7B | 72.2% | 22.4% | **+49.7%** |
| Mistral Latest | 81.6% | 27.8% | **+53.7%** |

### 12.5 Universal Failures (All Models Wrong)

- **FCT:** 2 questions
- **FQT:** 5 questions

---

*Report generated by purge_benchmark_to_1000q.py*