# Project Structure

This document describes the organization of the Diabetes Hallucination Benchmark project.

## Directory Structure

```
Diabete Hallucination Benchmark/
├── config.py                 # Configuration file (paths, settings)
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
│
├── data/                    # Input data
│   └── diabetes_QA_dataset.xlsx
│
├── diabetes_hallucination_fqt_fct_nota_benchmark/  # Release benchmark (FQT, FCT, NOTA)
│   ├── fqt/
│   ├── fct/
│   ├── nota/
│   ├── README.md
│   └── 说明.md
│
├── output/                   # Generated benchmark files and artifacts
│   ├── Json/                 # Current 1000q FQT & FCT benchmarks
│   ├── nota/                 # Current 1000q NOTA benchmarks
│   ├── archive/              # Old versions, samples, logs, reports
│   ├── logs/
│   ├── reports/
│   ├── 2026-01-27/           # Historical outputs
│   ├── binary/               # Legacy benchmarks
│   ├── fake_questions_test/
│   ├── multiple_choice/
│   └── none_of_above/
│
├── results/                  # Evaluation results
│
├── scripts/                  # Main execution scripts
│   ├── create_benchmark.py              # Create binary hallucination benchmark
│   ├── create_multiple_choice_benchmark.py  # Create multiple choice benchmark
│   ├── convert_to_none_of_above.py      # Convert to "None of the above" format
│   ├── generate_none_of_above_benchmark.py
│   ├── generate_advanced_none_of_above.py
│   ├── generate_with_deepseek.py
│   ├── run_benchmark.py                  # Run binary benchmark
│   ├── run_multiple_choice_benchmark.py  # Run multiple choice benchmark
│   └── test_with_deepseek.py             # Test with DeepSeek API
│
├── utils/                    # Utility modules and classes
│   ├── data_loader.py                    # Load Excel data
│   ├── hallucination_generator.py        # Generate hallucinations
│   ├── multiple_choice_generator.py     # Generate multiple choice questions
│   ├── evaluator.py                      # Binary benchmark evaluator
│   ├── mc_evaluator.py                   # Multiple choice evaluator
│   ├── model_tester.py                   # Model testing interface
│   ├── mc_model_tester.py                # Multiple choice model tester
│   └── deepseek_tester.py                # DeepSeek API integration
│
├── tests/                    # Testing and validation scripts
│   ├── validate_benchmarks.py
│   ├── test_evaluation_pipeline.py
│   ├── quick_test.py
│   ├── verify_converted_benchmark.py
│   ├── verify_english.py
│   └── ... (other verification scripts)
│
├── examples/                 # Example usage scripts
│   ├── example_usage.py
│   └── example_deepseek_test.py
│
└── docs/                     # Documentation
    ├── README.md
    ├── BENCHMARK_DETAILS.md
    ├── MULTIPLE_CHOICE_GUIDE.md
    ├── NONE_OF_ABOVE_GUIDE.md
    ├── DEEPSEEK_TESTING_GUIDE.md
    ├── TESTING_GUIDE.md
    └── ... (other documentation)
```

## Quick Start

### Creating Benchmarks

1. **Binary Hallucination Benchmark:**
   ```bash
   python scripts/create_benchmark.py
   ```

2. **Multiple Choice Benchmark:**
   ```bash
   python scripts/create_multiple_choice_benchmark.py
   ```

3. **None of the Above Benchmark:**
   ```bash
   python scripts/convert_to_none_of_above.py --input output/diabetes_multiple_choice_benchmark.jsonl
   ```

### Running Benchmarks

1. **Binary Benchmark:**
   ```bash
   python scripts/run_benchmark.py
   ```

2. **Multiple Choice Benchmark:**
   ```bash
   python scripts/run_multiple_choice_benchmark.py
   ```

### Testing and Validation

```bash
python tests/validate_benchmarks.py
python tests/quick_test.py
```

## Import Paths

After reorganization, scripts should import from `utils`:

```python
from utils.data_loader import DataLoader
from utils.hallucination_generator import HallucinationGenerator
from utils.model_tester import ModelTester
```

## File Organization Principles

- **scripts/**: Executable scripts that create or run benchmarks
- **utils/**: Reusable modules and classes
- **tests/**: Validation and testing scripts
- **examples/**: Example usage demonstrations
- **docs/**: All documentation files
- **output/**: Generated benchmark files (JSONL format)
- **results/**: Evaluation results and reports
- **data/**: Input data files (Excel dataset)
