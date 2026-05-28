"""
Complete FCT benchmark to reach target number of questions
Generates additional questions if the benchmark is incomplete
"""
import argparse
import json
import os
import sys
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.deepseek_tester import DeepSeekModelTester
from scripts.generate_false_confidence_test import generate_fct_question


def get_existing_question_ids(benchmark_file: Path) -> Set[int]:
    """Get IDs of questions already in the benchmark"""
    if not benchmark_file.exists():
        return set()
    
    existing_ids = set()
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                q = json.loads(line)
                existing_ids.add(q['id'])
            except:
                pass
    return existing_ids


def complete_fct_benchmark(
    input_file: Path,
    output_file: Path,
    tester: DeepSeekModelTester,
    target_count: int = 100,
    correct_suggestion_ratio: float = 0.5
):
    """
    Complete FCT benchmark to reach target count
    
    Args:
        input_file: Path to multiple-choice benchmark
        output_file: Path to FCT benchmark (will append if exists)
        tester: DeepSeekModelTester instance
        target_count: Target number of questions
        correct_suggestion_ratio: Ratio of correct suggestions
    """
    print("=" * 80)
    print("Completing False Confidence Test (FCT) Benchmark")
    print("=" * 80)
    
    # Load existing questions
    existing_questions = []
    existing_ids = get_existing_question_ids(output_file)
    
    if output_file.exists():
        print(f"Loading existing benchmark from {output_file}...")
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    q = json.loads(line)
                    existing_questions.append(q)
                except:
                    pass
        print(f"Found {len(existing_questions)} existing questions")
        print(f"Existing question IDs: {sorted(existing_ids)}")
    else:
        print("No existing benchmark found, starting fresh")
    
    current_count = len(existing_questions)
    needed = target_count - current_count
    
    if needed <= 0:
        print(f"\n✓ Benchmark already has {current_count} questions (target: {target_count})")
        return existing_questions
    
    print(f"\nNeed to generate {needed} more questions to reach {target_count}")
    print()
    
    # Load multiple-choice questions
    print("Loading multiple-choice questions...")
    mc_questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            mc_questions.append(json.loads(line))
    
    print(f"Loaded {len(mc_questions)} multiple-choice questions")
    
    # Filter out questions we've already used (by original_mc_question_id)
    used_mc_ids = {q['metadata']['original_mc_question_id'] 
                   for q in existing_questions 
                   if 'original_mc_question_id' in q.get('metadata', {})}
    
    available_mc_questions = [q for q in mc_questions 
                            if q.get('id') not in used_mc_ids]
    
    print(f"Available MC questions (not yet used): {len(available_mc_questions)}")
    
    if len(available_mc_questions) < needed:
        print(f"Warning: Only {len(available_mc_questions)} available, but {needed} needed")
        needed = len(available_mc_questions)
    
    # Select questions to use
    selected_questions = random.sample(available_mc_questions, needed)
    print(f"Selected {len(selected_questions)} questions for generation\n")
    
    # Calculate how many correct/incorrect suggestions we need
    current_correct = sum(1 for q in existing_questions 
                         if q['suggested_answer']['is_correct'])
    target_correct = int(target_count * correct_suggestion_ratio)
    needed_correct = max(0, target_correct - current_correct)
    needed_incorrect = needed - needed_correct
    
    print(f"Target distribution:")
    print(f"  Correct suggestions: {target_correct}/{target_count}")
    print(f"  Incorrect suggestions: {target_count - target_correct}/{target_count}")
    print(f"\nNeed to generate:")
    print(f"  Correct suggestions: {needed_correct}")
    print(f"  Incorrect suggestions: {needed_incorrect}")
    print()
    
    # Generate new questions
    new_questions = []
    correct_generated = 0
    incorrect_generated = 0
    
    print("Generating new FCT questions...")
    for i, mc_q in enumerate(selected_questions, 1):
        question_num = current_count + i
        
        # Determine if we should suggest correct or incorrect answer
        if correct_generated < needed_correct:
            # Suggest correct answer
            suggested_id = mc_q['correct_answer']
            correct_generated += 1
        else:
            # Suggest incorrect answer
            wrong_options = [opt['option_id'] for opt in mc_q['options'] 
                           if opt['option_id'] != mc_q['correct_answer']]
            suggested_id = random.choice(wrong_options)
            incorrect_generated += 1
        
        print(f"[{i}/{needed}] Generating question {question_num} (suggested: {suggested_id})...", end=" ")
        
        result = generate_fct_question(tester, mc_q, suggested_id, question_num)
        
        if result.get('error'):
            print(f"✗ Error: {result['error']}")
            continue
        
        if result.get('fct_question'):
            new_questions.append(result['fct_question'])
            print("✓")
        else:
            print("✗ Failed to generate question")
    
    # Combine existing and new questions
    all_questions = existing_questions + new_questions
    
    # Save complete benchmark
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for q in all_questions:
            f.write(json.dumps(q, ensure_ascii=False) + '\n')
    
    print("\n" + "=" * 80)
    print("Completion Summary")
    print("=" * 80)
    print(f"Existing questions: {len(existing_questions)}")
    print(f"Newly generated: {len(new_questions)}")
    print(f"Total questions: {len(all_questions)}/{target_count}")
    print(f"Saved to: {output_file}\n")
    
    # Statistics
    correct_suggested = sum(1 for q in all_questions 
                          if q['suggested_answer']['is_correct'])
    incorrect_suggested = len(all_questions) - correct_suggested
    
    print("Final Statistics:")
    print(f"  - Questions with correct suggestions: {correct_suggested} ({correct_suggested/len(all_questions)*100:.1f}%)")
    print(f"  - Questions with incorrect suggestions: {incorrect_suggested} ({incorrect_suggested/len(all_questions)*100:.1f}%)")
    
    return all_questions


def main():
    parser = argparse.ArgumentParser(
        description="Complete FCT benchmark to reach target number of questions"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="Input file path (multiple-choice benchmark)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/diabetes_false_confidence_test_benchmark.jsonl",
        help="Output file path"
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=100,
        help="Target number of questions"
    )
    parser.add_argument(
        "--correct-ratio",
        type=float,
        default=0.5,
        help="Ratio of questions where suggested answer is correct (0.0-1.0)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek model to use"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API key (or set DEEPSEEK_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set or --api-key not provided")
        return 1
    
    tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    
    # Complete benchmark
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    complete_fct_benchmark(
        input_path,
        output_path,
        tester,
        args.target_count,
        args.correct_ratio
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
