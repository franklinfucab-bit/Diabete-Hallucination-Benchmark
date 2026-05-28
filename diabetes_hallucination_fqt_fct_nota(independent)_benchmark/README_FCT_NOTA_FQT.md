# Diabetes Hallucination Benchmark: FCT, NOTA & FQT

This document describes the test types in the diabetes benchmark: **FCT** (False Confidence Test), **NOTA** (None of the Above), **FQT** (Fake Questions Test), and **AOTA** (All of the Above with correct answer). The work is based on the **浙江中医医院** (Zhejiang Provincial Hospital of Traditional Chinese Medicine) Q&A dataset; we build the **FCT** from this dataset and derive NOTA and AOTA from FCT where applicable. It covers how each test type works, how items are generated, and the guidelines and standards used.

---

## Overview

| Test Type | Acronym | Purpose |
|-----------|---------|---------|
| **False Confidence Test** | FCT | Standard multiple-choice with one correct answer; tests factual accuracy and resistance to overconfidence. |
| **None of the Above** | NOTA | All given options (A/B/C) are incorrect; correct answer is D = "None of the above." Tests resistance to plausible-but-wrong choices. |
| **Fake Questions Test** | FQT | The question embeds a **fabricated premise** (e.g. fake guideline or score). The correct answer (D) **challenges the premise** and refuses the false concept. |
| **All of the Above (with correct answer)** | AOTA | Options A, B, C are three statements (one correct, two wrong); D is always "All of the above." The **correct answer is A, B, or C** (the single correct statement). Tests resistance to sycophancy (rejecting "All of the above" when it is wrong). |

All items are 4-option multiple choice (A, B, C, D), diabetes-domain, and stored as JSONL (one JSON object per line).

---

## 1. FCT — False Confidence Test

### How it works

- Each question has **exactly one correct answer** among A, B, C, D.
- The stem is a realistic clinical or educational scenario; options are plausible but only one is evidence-based and correct.
- Design goal: the **correct** answer may look more nuanced or qualified; **distractors** are written to look simple, confident, or “obvious” to induce false confidence when wrong.

### Item structure (benchmark JSONL)

- `id`: e.g. `FCT_001`
- `question`: stem text
- `options`: array of `{ "option_id": "A"|"B"|"C"|"D", "text": "...", "is_correct": true|false }`
- `correct_answer`: `"A"` | `"B"` | `"C"` | `"D"`
- `ground_truth`: Authoritative explanation of why the correct answer is right and others wrong
- `explanation`: Shorter rationale for correct and distractor analysis
- `bias_targeted`: e.g. `["overconfidence","availability","representativeness"]`
- `difficulty_score`: 0–1
- `tags`: Topic/label list
- `suggested_answer`: Optional “trap” answer (often what an overconfident or biased responder might pick)
- `test_type`: `"FCT"`
- `metadata`: Includes `generation_method`, `generated_by`, `generation_timestamp`

### Generation

- **Source dataset**: FCT items are built from the **浙江中医医院** (Zhejiang Provincial Hospital of Traditional Chinese Medicine) Q&A dataset.
- **Existing MC (`existing_mc`)**: Items are adapted from this diabetes QA/MC bank; stems and options are refined for clarity and trap design.
- **Scratch (`scratch`)**: Items are written from scratch from a topic hint, with full question + options + ground truth.
- Generation is done with an LLM (e.g. DeepSeek) and then reviewed; metadata records `generation_method` and source.

### Guidelines and standards

- **Medical accuracy**: Correct answer must align with current guidelines (e.g. ADA, AACE, ACOG) and evidence.
- **Cognitive trap design**: Distractors should reflect common misconceptions or biases (overconfidence, anchoring, availability) and be plausible, not obviously absurd.
- **Difficulty**: Ranges from straightforward recall to nuanced clinical reasoning; `difficulty_score` and evaluation dimensions reflect this.
- **Evaluation dimensions** (in the FCT evaluation report):  
  `technical_accuracy`, `cognitive_trap_design`, `difficulty_discrimination`, `domain_relevance`, `test_effectiveness`.

---

## 2. NOTA — None of the Above

### How it works

- Options **A, B, and C are all incorrect** in the given context.
- The correct answer is always **D: "None of the above."**
- The model must recognize that no offered option is acceptable, rather than choosing the “least wrong” or most plausible distractor.

### Item structure (benchmark JSONL)

- `id`: e.g. `NOTA_001`
- `question`: clinical or educational scenario
- `options`: A, B, C are wrong; D is `"None of the above"` with `is_correct: true`
- `correct_answer`: `"D"`
- `ground_truth`: Explanation that all of A/B/C are wrong and why D is correct
- `explanation`: Per-option breakdown of why each is incorrect
- `bias_targeted`: e.g. `["anchoring","availability","representativeness"]`
- `difficulty_score`: 0–1
- `tags`: Topic labels
- `test_type`: `"NOTA"`
- `metadata`: `generation_method`, `generated_by`; for seed-based items, `original_question` / `original_answer` may appear

### Generation

- **Topic (`topic`)**: Item built from a topic or category (e.g. insulin pump troubleshooting, sick-day management).
- **Seed QA (`seed_qa`)**: Starts from an existing Q&A pair; converted into a NOTA item with three wrong options and D = "None of the above."
- **Scratch (`scratch`)**: Written from scratch from a topic hint.
- All three wrong options must be defensibly incorrect (misleading, incomplete, or dangerous); correct response is always D.

### Guidelines and standards

- **No “best of bad”**: A/B/C must each be clearly wrong; the right response is to refuse all three, not to pick the least bad.
- **Plausibility**: Wrong options should sound reasonable enough to tempt models or humans who do not have solid knowledge.
- **Clinical safety**: Distractors should not promote harmful actions; ground truth should state correct practice where relevant.
- **Evaluation dimensions** (NOTA evaluation report): Same as FCT:  
  `technical_accuracy`, `cognitive_trap_design`, `difficulty_discrimination`, `domain_relevance`, `test_effectiveness`.

---

## 3. FQT — Fake Questions Test

### How it works

- The question is built around a **fabricated premise**: a fake guideline, score, biomarker, or criterion that does **not** exist in real guidelines (e.g. a fake “Neuropathy Progression Score (NPS)” or “Diabetic Foot Severity Index (DFSI)”).
- Options **A, B, C** are plausible **if the premise were true** (they often reference real treatments or workups).
- The **correct answer is D**: a statement that **challenges the premise** (e.g. “Current guidelines do not define or use …”) and points to real standards.

A model that “goes along” with the fake premise will choose A, B, or C; a model that recognizes the premise as false should choose D.

### Item structure (benchmark JSONL)

- `id`: e.g. `FQT_001`
- `question`: stem that embeds the false premise (e.g. “The 2024 ADA guidelines introduced the 'Neuropathy Progression Score' (NPS)…”)
- `options`: A/B/C consistent with the false premise; D refuses the premise and cites real guidelines
- `correct_answer`: `"D"`
- `ground_truth`: Short note that the premise is fabricated and D correctly challenges it
- `test_type`: `"FQT_v2"` (or similar)
- `metadata`: `false_premise` (description of the fabricated concept), `topic`, `topic_short`, `generated_by`, `generation_timestamp`

### Generation

- A **false premise** is defined (fake score, fake biomarker, fake guideline criterion).
- The stem is written to present that premise as if it were real (often with fake “ADA 2024” or “IWGDF” style wording).
- Distractors A/B/C are written so they are logically consistent with the false premise and use real clinical concepts (e.g. real drugs, real tests).
- Option D is written to: (1) state that the premise is not in current authoritative guidelines, and (2) briefly indicate what real guidelines or standards actually say.

### Guidelines and standards

- **Concept fidelity**: The fake concept should look like real clinical terminology (names, numbers, thresholds) so that accepting the premise is tempting.
- **Authority bias**: Stems may cite fake guideline years or bodies to increase the tendency to accept the premise.
- **Precision of refusal**: D must clearly reject the premise and, where useful, point to real guidelines or practices; it should not be a vague “none of the above.”
- **Evaluation dimensions** (FQT evaluation report):  
  `concept_fidelity`, `sycophancy_trap`, `authority_bias`, `precision_of_refusal`, `difficulty_discrimination`.

---

## 4. AOTA — All of the Above (with correct answer)

### How it works

- Each question has **three substantive options (A, B, C)** and a fourth option **D: "All of the above."**
- **Exactly one** of A, B, or C is correct; the other two are wrong. Option D is **always wrong** (it is not the case that all three statements are correct).
- The **correct_answer** is **A**, **B**, or **C**—the single correct statement. The model must select that one and **reject** "All of the above."
- Design goal: **anti-sycophancy**. A model that tends to agree with everything or pick the most inclusive option will incorrectly choose D; a model that reasons about each statement will choose the one correct option (A, B, or C).

### Item structure (benchmark JSONL)

- `id`: e.g. `AOTA_001`
- `question`: stem text (same clinical scenario as in the source FCT item)
- `options`: object `{ "A": "...", "B": "...", "C": "...", "D": "All of the above" }` — three substantive statements plus D
- `answer` or `correct_answer`: `"A"` | `"B"` | `"C"` (never D)
- `task`: `"AOTA"`
- `metadata`: `derived_from` (source FCT id), `most_incorrect_replaced` (which original option was removed to make room for D), `difficulty`, `tags`

### Generation

- AOTA items **with correct_answer** are **derived from FCT** items (not written from scratch).
- From each FCT item:
  1. Identify the **most incorrect** option (e.g. the FCT `suggested_answer` when it is wrong, or one wrong option).
  2. **Remove** that option and keep the other three (one correct, two wrong).
  3. **Reorder** the remaining three as A, B, C and set **D = "All of the above."**
  4. Map the original correct answer to the new letter (A, B, or C); that is the AOTA `correct_answer`.
- The result is a 100q AOTA benchmark (e.g. `100q_aota_from_fct_benchmark.jsonl`) where every item has a single correct answer among A/B/C and D is always the wrong, sycophantic choice.

### Guidelines and standards

- **Single correct answer**: The correct answer must be exactly one of A, B, or C; D is never correct.
- **D is invariant**: Option D is always the literal text "All of the above" so that choosing D is interpretable as sycophancy or over-inclusion.
- **Traceability**: `metadata.derived_from` links back to the source FCT id for auditing and consistency.
- **Same medical bar as FCT**: The one correct statement (A, B, or C) must remain medically accurate per the original FCT ground truth.

---

## File layout

```
diabetes_hallucination_fqt_fct_nota_benchmark/
├── fct/
│   ├── diabetes_fct_benchmark.jsonl              # FCT items
│   └── diabetes_fct_benchmark_evaluation_report.jsonl  # Quality scores & comments
├── nota/
│   ├── diabetes_nota_benchmark.jsonl             # NOTA items
│   └── diabetes_nota_benchmark_evaluation_report.jsonl
├── fqt/
│   ├── diabetes_fqt_benchmark.jsonl              # FQT items
│   └── diabetes_fqt_benchmark_evaluation_report.jsonl
├── multi_model_run_2_4/
│   └── 100q AOTA Correct from FCT/
│       └── 100q_aota_from_fct_benchmark.jsonl   # AOTA items (correct_answer = A/B/C)
└── README_FCT_NOTA_FQT.md                        # This file
```

---

## Evaluation reports

Each test type has an **evaluation report** (JSONL) produced by a separate evaluation step (e.g. LLM or rubric-based):

- **First line**: Summary (counts, average scores per dimension, low-score and logic-issue counts).
- **Following lines**: One record per question with dimension scores, `issues`, `strengths`, `logic_check`, and `recommendation`.

Scores are typically on a scale (e.g. 1–5). Low scores or logic issues are used to flag items for revision or exclusion.

---

## Usage

1. **Load** the appropriate benchmark JSONL (`fct/`, `nota/`, or `fqt/`).
2. **Present** each question and options to the model (no extra hint about test type).
3. **Compare** the model’s chosen option to `correct_answer`.
4. **Optionally** use the evaluation reports to filter or weight items by quality.

For combined runs (e.g. 102q, 300q, or 400q benchmarks), items from FCT, NOTA, FQT, and AOTA are often mixed in a single JSONL with a `task` or `test_type` field set to `"FCT"`, `"NOTA"`, `"FQT"`, or `"AOTA"` so that accuracy can be reported per type. For AOTA, compare the model output to `answer` or `correct_answer` (always A, B, or C—never D).
