"""
Example: Using the False Confidence Test (FCT) Benchmark

This example shows how to use the FCT benchmark to test a model's ability
to evaluate suggested answers and avoid false confidence.
"""
import json
from pathlib import Path


def view_fct_benchmark(file_path: Path, num_samples: int = 3):
    """View sample questions from the FCT benchmark"""
    print("=" * 80)
    print("False Confidence Test (FCT) Benchmark - Sample Questions")
    print("=" * 80)
    print()
    
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
    print(f"Total questions in benchmark: {len(questions)}\n")
    
    for i, q in enumerate(questions[:num_samples], 1):
        print(f"Question {i}:")
        print("-" * 80)
        print(f"Question: {q['question']}")
        print()
        print("Options:")
        for opt in q['options']:
            marker = "✓" if opt['is_correct'] else " "
            print(f"  {marker} {opt['option_id']}. {opt['text']}")
        print()
        print(f"Correct Answer: {q['correct_answer']}")
        print()
        print(f"Suggested Answer: {q['suggested_answer']['option_id']} "
              f"({'CORRECT' if q['suggested_answer']['is_correct'] else 'INCORRECT'})")
        print(f"  Text: {q['suggested_answer']['text']}")
        print()
        print("Model Evaluation:")
        print(f"  Evaluation: {q['model_evaluation']['evaluation']}")
        print(f"  Confidence: {q['model_evaluation']['confidence_level']}")
        print(f"  Explanation: {q['model_evaluation']['explanation_for_suggested'][:200]}...")
        print()
        print("=" * 80)
        print()


def analyze_fct_benchmark(file_path: Path):
    """Analyze the FCT benchmark statistics"""
    print("=" * 80)
    print("FCT Benchmark Analysis")
    print("=" * 80)
    print()
    
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
    total = len(questions)
    correct_suggestions = sum(1 for q in questions 
                            if q['suggested_answer']['is_correct'])
    incorrect_suggestions = total - correct_suggestions
    
    # Count evaluations
    evaluations = {}
    confidence_levels = {}
    
    for q in questions:
        eval_type = q['model_evaluation']['evaluation']
        evaluations[eval_type] = evaluations.get(eval_type, 0) + 1
        
        conf = q['model_evaluation']['confidence_level']
        confidence_levels[conf] = confidence_levels.get(conf, 0) + 1
    
    print(f"Total Questions: {total}")
    print()
    print("Suggested Answer Distribution:")
    print(f"  Correct suggestions: {correct_suggestions} ({correct_suggestions/total*100:.1f}%)")
    print(f"  Incorrect suggestions: {incorrect_suggestions} ({incorrect_suggestions/total*100:.1f}%)")
    print()
    print("Model Evaluations:")
    for eval_type, count in evaluations.items():
        print(f"  {eval_type}: {count} ({count/total*100:.1f}%)")
    print()
    print("Confidence Levels:")
    for conf, count in confidence_levels.items():
        print(f"  {conf}: {count} ({count/total*100:.1f}%)")
    print()
    
    # Check for false confidence cases
    false_confidence = 0
    for q in questions:
        if (not q['suggested_answer']['is_correct'] and 
            q['model_evaluation']['evaluation'].upper() == 'CORRECT' and
            q['model_evaluation']['confidence_level'].lower() == 'high'):
            false_confidence += 1
    
    print(f"False Confidence Cases: {false_confidence}")
    print(f"  (Incorrect suggestions accepted with high confidence)")
    print()


if __name__ == "__main__":
    benchmark_file = Path("output/diabetes_false_confidence_test_benchmark.jsonl")
    
    if not benchmark_file.exists():
        print(f"Error: Benchmark file not found: {benchmark_file}")
        print("\nTo generate the benchmark, run:")
        print("  python scripts/generate_false_confidence_test.py")
        exit(1)
    
    # View sample questions
    view_fct_benchmark(benchmark_file, num_samples=3)
    
    # Analyze benchmark
    analyze_fct_benchmark(benchmark_file)
