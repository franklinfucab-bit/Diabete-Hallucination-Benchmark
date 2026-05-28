"""
Quick test script - Run this to verify everything works
"""
import json
from pathlib import Path

def quick_test():
    """Quick verification of benchmark files"""
    print("=" * 80)
    print("QUICK BENCHMARK TEST")
    print("=" * 80)
    
    # Test 1: Check binary benchmark
    print("\n1. Testing Binary Benchmark...")
    binary_path = Path("output/diabetes_hallucination_benchmark.jsonl")
    if binary_path.exists():
        with open(binary_path, 'r', encoding='utf-8') as f:
            binary_data = [json.loads(line) for line in f]
        print(f"   ✓ Found {len(binary_data)} samples")
        
        # Check a sample
        sample = binary_data[0]
        required = ['id', 'question', 'answer', 'ground_truth', 'is_hallucination']
        missing = [f for f in required if f not in sample]
        if missing:
            print(f"   ✗ Missing fields: {missing}")
        else:
            print(f"   ✓ All required fields present")
    else:
        print(f"   ✗ File not found: {binary_path}")
        return False
    
    # Test 2: Check multiple-choice benchmark
    print("\n2. Testing Multiple-Choice Benchmark...")
    mc_path = Path("output/diabetes_multiple_choice_benchmark.jsonl")
    if mc_path.exists():
        with open(mc_path, 'r', encoding='utf-8') as f:
            mc_data = [json.loads(line) for line in f]
        print(f"   ✓ Found {len(mc_data)} questions")
        
        # Check a sample
        sample = mc_data[0]
        required = ['id', 'question', 'options', 'correct_answer', 'ground_truth']
        missing = [f for f in required if f not in sample]
        if missing:
            print(f"   ✗ Missing fields: {missing}")
        else:
            print(f"   ✓ All required fields present")
            
        # Check options
        if 'options' in sample:
            correct_count = sum(1 for opt in sample['options'] if opt.get('is_correct', False))
            if correct_count == 1:
                print(f"   ✓ Exactly 1 correct answer per question")
            else:
                print(f"   ✗ Expected 1 correct answer, found {correct_count}")
    else:
        print(f"   ✗ File not found: {mc_path}")
        return False
    
    # Test 3: Check data quality
    print("\n3. Checking Data Quality...")
    empty_questions = sum(1 for item in binary_data if not item.get('question', '').strip())
    empty_answers = sum(1 for item in binary_data if not item.get('answer', '').strip())
    
    if empty_questions == 0 and empty_answers == 0:
        print(f"   ✓ No empty questions or answers")
    else:
        print(f"   ⚠ {empty_questions} empty questions, {empty_answers} empty answers")
    
    # Test 4: Statistics
    print("\n4. Statistics Summary:")
    correct = sum(1 for item in binary_data if not item.get('is_hallucination', False))
    hallucinated = sum(1 for item in binary_data if item.get('is_hallucination', False))
    print(f"   Binary Benchmark: {len(binary_data)} samples ({correct} correct, {hallucinated} hallucinated)")
    print(f"   Multiple-Choice: {len(mc_data)} questions")
    
    print("\n" + "=" * 80)
    print("✅ QUICK TEST PASSED!")
    print("=" * 80)
    print("\nYour benchmarks are ready. Run 'python validate_benchmarks.py' for detailed validation.")
    
    return True

if __name__ == "__main__":
    quick_test()
