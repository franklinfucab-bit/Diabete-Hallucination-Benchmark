# Fake Questions Test (FQT) Benchmark Guide

## Overview

The Fake Questions Test (FQT) is designed to evaluate whether AI models can correctly identify and handle fake or nonsensical medical questions. This test presents models with questions that:

- Contain made-up medical terms
- Include impossible biological processes
- Combine contradictory concepts
- Reference fictional medical treatments
- Are based on invalid premises

A competent AI model should recognize these questions as invalid or nonsensical rather than attempting to provide medical answers.

## Test Purpose

**虚假问题测试 (FQT)**: This test involves presenting the model with fake or nonsensical medical questions to examine whether it can correctly identify and handle such queries.

## Benchmark Structure

Each question in the benchmark contains:

```json
{
  "id": 1,
  "question": "The fake/nonsensical question text",
  "type": "fake_question",
  "is_fake": true,
  "why_fake": "Explanation of why the question is fake/nonsensical",
  "expected_response": "How a competent AI should respond",
  "correct_answer": "INVALID_QUESTION",
  "ground_truth": "This question is fake/nonsensical and should be identified as invalid",
  "metadata": {
    "test_type": "FQT",
    "test_purpose": "Test model ability to identify fake or nonsensical medical questions",
    "generated_by": "deepseek",
    "model": "deepseek-chat"
  }
}
```

## Generating the Benchmark

### Basic Usage

```bash
python scripts/generate_fake_questions_test.py \
    --num-questions 10 \
    --output output/fake_questions_test_benchmark.jsonl
```

### Parameters

- `--num-questions`: Number of fake questions to generate (default: 10)
- `--output`: Output file path (default: `output/fake_questions_test_benchmark.jsonl`)
- `--model`: DeepSeek model to use (`deepseek-chat` or `deepseek-reasoner`, default: `deepseek-chat`)
- `--api-key`: DeepSeek API key (or set `DEEPSEEK_API_KEY` environment variable)

### Environment Setup

Set the DeepSeek API key:

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Windows CMD
set DEEPSEEK_API_KEY=your_api_key_here

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

## Example Questions

1. **Quantum Particles Question**: Questions about "anti-glycemic quantum particles" - a made-up treatment that doesn't exist in medical science.

2. **Impossible Biological Processes**: Questions referencing "pancreatic time-reversal", "mitochondrial teleportation", or "pancreatic teleportation" - impossible biological processes.

3. **Contradictory Concepts**: Questions asking for treatments that simultaneously achieve contradictory goals (e.g., lowering glucose while increasing cellular entropy).

4. **Fictional Medical Specialties**: References to non-existent medical fields like "chrono-endocrinology".

5. **Physics Misapplication**: Questions combining theoretical physics concepts (parallel universes, dark matter) with medical treatments.

## Expected Model Behavior

A competent AI model should:

1. **Identify Invalid Concepts**: Recognize made-up medical terms, impossible biological processes, and fictional treatments.

2. **Refuse to Answer**: Decline to provide medical advice for questions based on false premises.

3. **Explain Why**: Clearly explain why the question is invalid or nonsensical.

4. **Avoid Hallucination**: Not attempt to provide answers that would require making up information.

## Evaluation Criteria

When testing models with this benchmark, evaluate:

- **Recognition Rate**: Percentage of fake questions correctly identified as invalid
- **Response Quality**: Whether the model explains why the question is invalid
- **Hallucination Avoidance**: Whether the model avoids making up answers to fake questions

## Viewing the Benchmark

To view the generated benchmark:

```bash
python tests/view_fqt_benchmark.py
```

This will display all questions with their explanations and expected responses.

## Integration with Other Benchmarks

The FQT benchmark complements other benchmark types:

- **Binary Hallucination Benchmark**: Tests detection of hallucinations in answers
- **Multiple Choice Benchmark**: Tests selection of correct answers
- **None of the Above Benchmark**: Tests identification of irrelevant options
- **Fake Questions Test**: Tests identification of invalid questions

Together, these benchmarks provide comprehensive evaluation of AI model behavior in medical contexts.

## Notes

- The benchmark uses DeepSeek API to generate diverse fake questions
- Questions are designed to be clearly nonsensical to medical experts
- The benchmark focuses on diabetes-related fake questions but the approach can be extended to other medical domains
- Some generated questions may be similar in structure - this is expected as the API generates patterns
