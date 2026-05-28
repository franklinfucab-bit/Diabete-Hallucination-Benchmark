# Diabetes Hallucination Benchmark

A benchmark suite for evaluating large language models (LLMs) on diabetes-related medical knowledge and their ability to resist hallucination, false confidence, and misleading premises.

## Overview

This benchmark contains three complementary test types, each targeting different failure modes of medical AI:

| Test Type | Acronym | Questions | Description |
|-----------|---------|-----------|-------------|
| **Fake Questions Test** | FQT | 1,000 | Questions with fabricated concepts embedded in plausible clinical scenarios. Correct answer challenges the false premise. |
| **False Confidence Test** | FCT | 962 | Standard multiple-choice questions with one correct answer. Tests factual accuracy and overconfidence. |
| **None of the Above** | NOTA | 1,000 | All options are incorrect; correct answer is "None of the above." Tests resistance to plausible-sounding but wrong choices. |

## Directory Structure

```
diabetes_hallucination_fqt_fct_nota_benchmark/
├── fqt/                    # Fake Questions Test
│   ├── diabetes_fqt_benchmark.jsonl
│   └── diabetes_fqt_benchmark_evaluation_report.jsonl
├── fct/                    # False Confidence Test
│   ├── diabetes_fct_benchmark.jsonl
│   └── diabetes_fct_benchmark_evaluation_report.jsonl
├── nota/                   # None of the Above
│   ├── diabetes_nota_benchmark.jsonl
│   └── diabetes_nota_benchmark_evaluation_report.jsonl
├── README.md
└── 说明.md
```

## File Formats

### Benchmark Files

- **FQT, FCT & NOTA**: JSONL (one JSON object per line)

Each question object typically includes:
- `id`: Unique identifier
- `question`: Question text
- `options`: Array of choices with `option_id`, `text`, `is_correct`
- `correct_answer`: Correct option ID
- `ground_truth`: Explanation of why the correct answer is right
- `metadata`: Generation info (model, timestamp, topic, etc.)

### Evaluation Reports

JSONL format with:
- First line: Summary (total questions, scores, success/failure counts)
- Subsequent lines: Per-question evaluation with quality scores and feedback

## Usage

1. Load the benchmark file for your test type.
2. For each question, present the question and options to the model.
3. Compare the model's selected answer to `correct_answer`.
4. Optionally use the evaluation report for quality metrics and per-question analysis.

## Evaluation Metrics

- **FQT**: concept_fidelity, sycophancy_trap, authority_bias, precision_of_refusal, difficulty_discrimination
- **FCT**: technical_accuracy, cognitive_trap_design, difficulty_discrimination, domain_relevance, test_effectiveness
- **NOTA**: technical_accuracy, cognitive_trap_design, difficulty_discrimination, domain_relevance, test_effectiveness

## License & Citation

Please cite this benchmark if you use it in research or model evaluation.
