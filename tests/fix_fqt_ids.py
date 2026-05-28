"""
Fix duplicate IDs in fake_questions_test_benchmark.jsonl
Renumbers all questions sequentially to ensure unique IDs
"""
import json
from pathlib import Path

def fix_ids(input_file: Path, output_file: Path = None):
    """Fix duplicate IDs by renumbering all questions sequentially"""
    if output_file is None:
        output_file = input_file
    
    print(f"Loading questions from {input_file}...")
    questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
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

if __name__ == "__main__":
    input_file = Path("output/fake_questions_test_benchmark.jsonl")
    fix_ids(input_file)
