# Diabetes Hallucination Benchmark - Detailed Structure

## Overview

Your benchmark contains **a mix of both correct and hallucinated answers**. This is intentional and necessary for evaluating AI models' ability to detect hallucinations.

## Benchmark Composition

### Total Samples: 1,075

- **753 Correct Answers (70%)**: Original, accurate answers from your dataset
- **322 Hallucinated Answers (30%)**: Artificially modified answers containing misinformation

## Why This Mix?

A hallucination detection benchmark needs both:
1. **Correct answers** - to test that the model doesn't falsely flag accurate information
2. **Hallucinated answers** - to test that the model can identify misinformation

This allows us to measure:
- **True Positives**: Correctly identifying hallucinations
- **True Negatives**: Correctly identifying accurate information
- **False Positives**: Incorrectly flagging correct answers as hallucinations
- **False Negatives**: Missing actual hallucinations

## Structure of Each Benchmark Entry

Each entry in the benchmark JSONL file contains:

```json
{
  "id": 251,                                    // Unique identifier
  "question": "What are the potential...",      // The question
  "answer": "Without a diabetes-specific...",   // The answer to evaluate
  "ground_truth": "Without a diabetes-specific...", // The correct answer
  "is_hallucination": false,                    // TRUE = hallucinated, FALSE = correct
  "hallucination_strategy": null,                // Type of hallucination (if applicable)
  "metadata": {
    "source": "original",                       // "original" or "generated"
    "original_id": 251                          // ID from original dataset
  }
}
```

## Examples from Your Benchmark

### Example 1: Correct Answer (No Hallucination)
```json
{
  "id": 251,
  "question": "What are the potential consequences of not having a diabetes management disaster kit?",
  "answer": "Without a diabetes-specific disaster kit, individuals with diabetes may face serious health complications during emergencies...",
  "ground_truth": "Without a diabetes-specific disaster kit, individuals with diabetes may face serious health complications during emergencies...",
  "is_hallucination": false,
  "hallucination_strategy": null
}
```
**Note**: `answer` and `ground_truth` are identical - this is a correct answer.

### Example 2: Hallucinated Answer (Contradiction Strategy)
```json
{
  "id": 864,
  "question": "How can technology assist individuals with diabetes in managing their condition?",
  "answer": "Actually, the opposite is true. answer: technology offers valuable tools...",
  "ground_truth": "Answer: Technology offers valuable tools for managing diabetes...",
  "is_hallucination": true,
  "hallucination_strategy": "contradiction"
}
```
**Note**: The answer contradicts the correct information by saying "the opposite is true."

### Example 3: Hallucinated Answer (Fabrication Strategy)
```json
{
  "id": 206,
  "question": "What are the signs and symptoms of hypoglycemia?",
  "answer": "Clinical trials have shown that 95% of patients experience Hypoglycemia can manifest as hunger... However, this is not supported by current medical evidence.",
  "ground_truth": "Hypoglycemia can manifest as hunger, dizziness, shakiness...",
  "is_hallucination": true,
  "hallucination_strategy": "fabrication"
}
```
**Note**: False medical claims are added (the "95% of patients" statistic is fabricated).

### Example 4: Hallucinated Answer (Exaggeration Strategy)
```json
{
  "id": 1,
  "question": "Why is it important for individuals with diabetes to drink plenty of fluids when they are sick?",
  "answer": "Staying hydrated is completely crucial for regulating blood glucose levels...",
  "ground_truth": "Staying hydrated is crucial for regulating blood glucose levels...",
  "is_hallucination": true,
  "hallucination_strategy": "exaggeration"
}
```
**Note**: The word "completely" is added, making the statement more absolute than it should be.

## Hallucination Strategy Breakdown

Your benchmark includes 322 hallucinated answers distributed across 5 strategies:

| Strategy | Count | Description |
|----------|-------|-------------|
| **Contradiction** | 49 | Reverses or contradicts correct information |
| **Fabrication** | 64 | Adds false medical claims or unsupported information |
| **Omission** | 56 | Removes critical information or warnings |
| **Exaggeration** | 81 | Adds absolute terms or overstates claims |
| **Misattribution** | 72 | Incorrectly attributes information to medical authorities |

## How the Benchmark is Used

When testing an AI model:

1. **The model receives**: Question + Answer (without knowing if it's hallucinated)
2. **The model predicts**: Whether the answer contains hallucinations
3. **We compare**: Model's prediction vs. the `is_hallucination` field (ground truth)
4. **We calculate metrics**: Accuracy, Precision, Recall, F1-score, etc.

## Key Fields Explained

- **`answer`**: The answer the AI model should evaluate (may be correct or hallucinated)
- **`ground_truth`**: The correct, original answer from your dataset
- **`is_hallucination`**: 
  - `false` = The answer is correct (matches ground_truth)
  - `true` = The answer is hallucinated (modified from ground_truth)
- **`hallucination_strategy`**: 
  - `null` = Correct answer (no strategy applied)
  - One of: "contradiction", "fabrication", "omission", "exaggeration", "misattribution"

## Creating Different Ratios

You can adjust the hallucination ratio when creating the benchmark:

```bash
# 50% correct, 50% hallucinated
python create_benchmark.py --hallucination-ratio 0.5

# 80% correct, 20% hallucinated
python create_benchmark.py --hallucination-ratio 0.2

# 90% correct, 10% hallucinated
python create_benchmark.py --hallucination-ratio 0.1
```

## Why This Structure is Important

This balanced structure (70% correct, 30% hallucinated) is standard for hallucination detection benchmarks because:

1. **Real-world scenario**: Most AI-generated content is correct, but some contains hallucinations
2. **Balanced evaluation**: Tests both detection of hallucinations AND avoiding false alarms
3. **Comprehensive metrics**: Allows calculation of precision, recall, and F1-score
4. **Strategy analysis**: Enables evaluation of which types of hallucinations are easier/harder to detect

## Next Steps

- **View specific examples**: Open `output/diabetes_hallucination_benchmark.jsonl` in a text editor
- **Test a model**: Run `python run_benchmark.py --model openai --model-name gpt-4`
- **Create custom benchmarks**: Adjust the hallucination ratio or strategies as needed
