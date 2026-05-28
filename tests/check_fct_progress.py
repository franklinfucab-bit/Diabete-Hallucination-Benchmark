"""
Check progress of FCT benchmark generation
"""
import json
from pathlib import Path

def check_progress(file_path: Path):
    """Check how many questions have been generated"""
    if not file_path.exists():
        print(f"Benchmark file not found: {file_path}")
        return
    
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                questions.append(json.loads(line))
            except:
                pass
    
    total = len(questions)
    correct_suggestions = sum(1 for q in questions 
                            if q['suggested_answer']['is_correct'])
    incorrect_suggestions = total - correct_suggestions
    
    print("=" * 80)
    print("FCT Benchmark Generation Progress")
    print("=" * 80)
    print(f"Total questions generated: {total}/100")
    print(f"Progress: {total}%")
    print()
    print("Distribution:")
    print(f"  Correct suggestions: {correct_suggestions}")
    print(f"  Incorrect suggestions: {incorrect_suggestions}")
    print()
    
    if total > 0:
        print("Latest question:")
        latest = questions[-1]
        print(f"  ID: {latest['id']}")
        print(f"  Question: {latest['question'][:60]}...")
        print(f"  Suggested: {latest['suggested_answer']['option_id']} "
              f"({'CORRECT' if latest['suggested_answer']['is_correct'] else 'INCORRECT'})")
        print(f"  Evaluation: {latest['model_evaluation']['evaluation']}")

if __name__ == "__main__":
    benchmark_file = Path("output/diabetes_false_confidence_test_benchmark.jsonl")
    check_progress(benchmark_file)
