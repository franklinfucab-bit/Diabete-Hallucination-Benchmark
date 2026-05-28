"""
Fix duplicate IDs in FCT benchmark by renumbering all questions sequentially
"""
import json
from pathlib import Path

def fix_fct_ids(input_file: Path, output_file: Path = None):
    """Fix duplicate IDs by renumbering all questions sequentially"""
    if output_file is None:
        output_file = input_file
    
    print(f"Loading questions from {input_file}...")
    questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                questions.append(json.loads(line))
            except:
                pass
    
    print(f"Loaded {len(questions)} questions")
    
    # Renumber all questions sequentially
    print("Renumbering questions...")
    for i, q in enumerate(questions, 1):
        q['id'] = i
    
    # Save fixed file
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + '\n')
    
    print(f"Fixed {len(questions)} questions with IDs 1-{len(questions)}")
    
    # Verify
    ids = [q['id'] for q in questions]
    unique_ids = set(ids)
    print(f"Verification: {len(ids)} total IDs, {len(unique_ids)} unique IDs")
    if len(ids) == len(unique_ids):
        print("All IDs are unique!")
    else:
        print("Warning: Duplicate IDs still exist")
    
    # Show distribution
    correct_suggestions = sum(1 for q in questions 
                            if q['suggested_answer']['is_correct'])
    incorrect_suggestions = len(questions) - correct_suggestions
    print(f"\nDistribution:")
    print(f"  Correct suggestions: {correct_suggestions}")
    print(f"  Incorrect suggestions: {incorrect_suggestions}")

if __name__ == "__main__":
    input_file = Path("output/diabetes_false_confidence_test_benchmark.jsonl")
    fix_fct_ids(input_file)
