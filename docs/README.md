# Diabetes Hallucination Benchmark

A comprehensive benchmark framework for evaluating AI models' ability to detect medical hallucinations in diabetes-related Q&A pairs.

## Overview

This benchmark transforms your Excel dataset of 1000 diabetes Q&A pairs into a structured hallucination detection benchmark. It includes:

- **Data Processing**: Loads and processes Excel Q&A datasets
- **Hallucination Generation**: Creates synthetic hallucinations using multiple strategies
- **Model Testing**: Tests AI models (OpenAI, Anthropic, etc.) on hallucination detection
- **Evaluation Metrics**: Comprehensive metrics including accuracy, precision, recall, F1-score, and hallucination detection rate

## Features

### Hallucination Strategies

The benchmark includes five types of hallucination injection:

1. **Contradiction**: Reverses or contradicts correct information
2. **Fabrication**: Adds false medical claims or unsupported information
3. **Omission**: Removes critical information or warnings
4. **Exaggeration**: Adds absolute terms or overstates claims
5. **Misattribution**: Incorrectly attributes information to medical authorities

### Supported Models

- OpenAI (GPT-4, GPT-3.5-turbo, etc.)
- Anthropic (Claude models)
- Local models (template provided for customization)

## Installation

1. **Clone or navigate to this directory**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up API keys** (for model testing):
   - Create a `.env` file in the project root
   - Add your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```
   Or set them as environment variables.

## Benchmark Types

This framework supports **multiple types of benchmarks**:

1. **Binary Hallucination Detection** - Tests if an answer contains hallucinations (correct vs. hallucinated)
2. **Multiple-Choice Questions** - More challenging format with 4 options where models must select the correct answer among distractors (including hallucinated ones)
3. **False Confidence Test (FCT)** - Tests model's ability to evaluate suggested answers and avoid false confidence when lacking sufficient information
4. **None of the Above (NOTA)** - Tests model's ability to identify when all options are incorrect
5. **Fake Questions Test (FQT)** - Tests model's ability to identify fake or nonsensical medical questions

## Quick Start

### Step 1: Prepare Your Excel Dataset

1. Place your Excel file in the `data/` directory
2. Name it `diabetes_qa_dataset.xlsx` (or specify a custom path)
3. Ensure your Excel file has columns for questions and answers. The loader will automatically detect columns named:
   - Questions: "question", "q", "questions", "query", or "prompt"
   - Answers: "answer", "a", "answers", "response", or "ground_truth"
   - If not found, it will use the first two columns

**Example Excel structure:**
| Question | Answer |
|----------|--------|
| What is diabetes? | Diabetes is a chronic condition... |
| How is type 2 diabetes diagnosed? | Type 2 diabetes is diagnosed through... |

### Step 2: Create the Benchmark

#### Option A: Binary Hallucination Detection Benchmark

Generate the benchmark dataset with hallucinated answers:

```bash
python create_benchmark.py
```

**Options:**
- `--excel-file`: Path to your Excel file (default: `data/diabetes_qa_dataset.xlsx`)
- `--output`: Output path for benchmark JSONL (default: `output/diabetes_hallucination_benchmark.jsonl`)
- `--hallucination-ratio`: Proportion of hallucinated answers (default: 0.3 = 30%)
- `--seed`: Random seed for reproducibility (default: 42)

**Example:**
```bash
python create_benchmark.py --hallucination-ratio 0.4 --seed 123
```

This will create a benchmark with 40% hallucinated answers and 60% correct answers.

#### Option B: Multiple-Choice Benchmark (More Challenging)

Generate multiple-choice questions with challenging distractors:

```bash
python create_multiple_choice_benchmark.py
```

**Options:**
- `--excel-file`: Path to your Excel file
- `--output`: Output path (default: `output/diabetes_multiple_choice_benchmark.jsonl`)
- `--num-options`: Number of answer options per question (default: 4)
- `--hallucination-ratio`: Ratio of questions with hallucinated distractors (default: 0.5 = 50%)
- `--seed`: Random seed for reproducibility

**Example:**
```bash
python create_multiple_choice_benchmark.py --num-options 4 --hallucination-ratio 0.5
```

This creates questions with 4 options where:
- 1 option is correct
- 1 option is a hallucinated distractor (contradiction, fabrication, etc.)
- 2 options are other types of wrong answers (plausible but wrong, partially correct, etc.)

**Why Multiple-Choice is Harder:**
- Models must identify the correct answer among multiple plausible options
- Some distractors are hallucinated (false medical claims)
- Tests both knowledge and hallucination detection simultaneously

### Step 3: Run the Benchmark

#### For Binary Benchmark:

```bash
# Test with OpenAI GPT-4
python run_benchmark.py --model openai --model-name gpt-4

# Test with Anthropic Claude
python run_benchmark.py --model anthropic --model-name claude-3-opus-20240229

# Quick test on first 50 samples
python run_benchmark.py --model openai --max-samples 50
```

#### For Multiple-Choice Benchmark:

```bash
# Test with OpenAI GPT-4
python run_multiple_choice_benchmark.py --model openai --model-name gpt-4

# Test with Anthropic Claude
python run_multiple_choice_benchmark.py --model anthropic --model-name claude-3-opus-20240229

# Quick test on first 50 questions
python run_multiple_choice_benchmark.py --model openai --max-samples 50
```

**Options:**
- `--benchmark-file`: Path to benchmark JSONL file
- `--model`: Model provider (`openai` or `anthropic`)
- `--model-name`: Specific model name
- `--max-samples`: Limit number of samples (for quick testing)
- `--output-dir`: Directory to save results

#### Option C: False Confidence Test (FCT) Benchmark

Generate FCT questions that test model's ability to evaluate suggested answers:

```bash
python scripts/generate_false_confidence_test.py
```

**Options:**
- `--input`: Path to multiple-choice benchmark (default: `output/diabetes_multiple_choice_benchmark.jsonl`)
- `--output`: Output path (default: `output/diabetes_false_confidence_test_benchmark.jsonl`)
- `--num-questions`: Number of FCT questions to generate (default: 100)
- `--correct-ratio`: Ratio of questions where suggested answer is correct (0.0-1.0, default: 0.5)
- `--model`: DeepSeek model to use (`deepseek-chat` or `deepseek-reasoner`)
- `--api-key`: DeepSeek API key (or set `DEEPSEEK_API_KEY` environment variable)

**Example:**
```bash
python scripts/generate_false_confidence_test.py \
    --num-questions 100 \
    --correct-ratio 0.5 \
    --api-key YOUR_DEEPSEEK_API_KEY
```

**What FCT Tests:**
- Model's ability to evaluate suggested answers (correct or incorrect)
- Whether models provide appropriate confidence levels
- Ability to explain why answers are correct/incorrect
- Tendency to avoid false confidence when lacking information

See `docs/FALSE_CONFIDENCE_TEST_GUIDE.md` for detailed documentation.

### Step 4: View Results

Results are saved in the `results/` directory:
- `results_<model>_<timestamp>.json`: Detailed metrics in JSON format
- `report_<model>_<timestamp>.txt`: Human-readable report

## Project Structure

```
.
├── data/                          # Place your Excel file here
│   └── diabetes_qa_dataset.xlsx
├── output/                        # Generated benchmark files
│   └── diabetes_hallucination_benchmark.jsonl
├── results/                       # Evaluation results
├── config.py                      # Configuration settings
├── data_loader.py                 # Excel data loading
├── hallucination_generator.py    # Hallucination injection
├── model_tester.py               # Model testing interface
├── evaluator.py                  # Evaluation metrics
├── create_benchmark.py           # Benchmark creation script
├── run_benchmark.py              # Benchmark execution script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Benchmark Format

The benchmark JSONL file contains one JSON object per line:

```json
{
  "id": 0,
  "question": "What is diabetes?",
  "answer": "Diabetes is a chronic condition...",
  "ground_truth": "Diabetes is a chronic condition...",
  "is_hallucination": false,
  "hallucination_strategy": null,
  "metadata": {
    "source": "original",
    "original_id": 0
  }
}
```

For hallucinated examples:
```json
{
  "id": 1,
  "question": "How is diabetes diagnosed?",
  "answer": "Actually, the opposite is true: diabetes is diagnosed through...",
  "ground_truth": "Diabetes is diagnosed through blood tests...",
  "is_hallucination": true,
  "hallucination_strategy": "contradiction",
  "metadata": {
    "source": "generated",
    "original_id": 1
  }
}
```

### Multiple-Choice Format

The multiple-choice benchmark JSONL file contains one JSON object per line:

```json
{
  "id": 0,
  "question": "What is diabetes?",
  "options": [
    {
      "option_id": "A",
      "text": "Diabetes is a chronic condition...",
      "is_correct": true,
      "type": "correct",
      "is_hallucination": false
    },
    {
      "option_id": "B",
      "text": "Actually, the opposite is true: diabetes is not a chronic condition...",
      "is_correct": false,
      "type": "hallucination",
      "is_hallucination": true,
      "hallucination_strategy": "contradiction"
    },
    {
      "option_id": "C",
      "text": "Diabetes only affects blood sugar, not other organs...",
      "is_correct": false,
      "type": "plausible_wrong",
      "is_hallucination": false
    },
    {
      "option_id": "D",
      "text": "Diabetes is a chronic condition. This is the only treatment option available.",
      "is_correct": false,
      "type": "partial_correct",
      "is_hallucination": false
    }
  ],
  "correct_answer": "A",
  "ground_truth": "Diabetes is a chronic condition...",
  "metadata": {
    "num_options": 4,
    "has_hallucinated_distractors": true
  }
}
```

**Distractor Types:**
- `hallucination`: Contains false medical information (contradiction, fabrication, etc.)
- `plausible_wrong`: Related but incorrect answer
- `partial_correct`: Partially correct but incomplete or misleading
- `opposite`: Contradictory answer

## Evaluation Metrics

### Binary Benchmark Metrics:

- **Accuracy**: Overall correctness of hallucination detection
- **Precision**: Proportion of detected hallucinations that are actually hallucinations
- **Recall**: Proportion of actual hallucinations that were detected
- **F1 Score**: Harmonic mean of precision and recall
- **Hallucination Detection Rate**: Same as recall (focus on detecting hallucinations)
- **Confusion Matrix**: True/False Positives and Negatives
- **Per-Strategy Metrics**: Performance broken down by hallucination type

### Multiple-Choice Benchmark Metrics:

- **Accuracy**: Percentage of questions answered correctly
- **Hallucination Detection Accuracy**: How well the model avoids selecting hallucinated options
- **Hallucination Avoidance Rate**: Proportion of times model avoided hallucinated distractors
- **False Positive Rate**: Rate of selecting hallucinated options
- **Per-Distractor-Type Metrics**: Performance broken down by distractor type (hallucination, plausible_wrong, etc.)

## Customization

### Adding Custom Hallucination Strategies

Edit `hallucination_generator.py` and add new methods to the `HallucinationGenerator` class:

```python
def _generate_custom_strategy(self, answer: str) -> Dict[str, str]:
    # Your custom hallucination logic
    return {
        'hallucinated_answer': modified_answer,
        'strategy': 'custom',
        'is_hallucination': True
    }
```

Then add `'custom'` to `HALLUCINATION_STRATEGIES` in `config.py`.

### Testing Local Models

Implement the `LocalModelTester` class in `model_tester.py`:

```python
class LocalModelTester(ModelTester):
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        # Your model inference code
        return {'is_hallucination': result}
```

## Troubleshooting

### Excel File Not Found
- Ensure your Excel file is in the `data/` directory
- Or specify the full path with `--excel-file`

### Column Detection Issues
- The loader tries to auto-detect columns, but if it fails:
  - Rename your columns to "question" and "answer"
  - Or modify `_detect_columns()` in `data_loader.py`

### API Key Errors
- Ensure your `.env` file has the correct API keys
- Or set environment variables: `export OPENAI_API_KEY=your_key`

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## Citation

If you use this benchmark in your research, please cite:

```bibtex
@software{diabetes_hallucination_benchmark,
  title = {Diabetes Hallucination Benchmark},
  year = {2024},
  url = {https://github.com/yourusername/diabetes-hallucination-benchmark}
}
```

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Contact

[Your contact information]
