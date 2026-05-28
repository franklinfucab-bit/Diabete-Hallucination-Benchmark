"""
Script to create multiple-choice benchmark from Excel dataset
"""
import argparse
from pathlib import Path
from utils.data_loader import DiabetesQALoader
from utils.multiple_choice_generator import MultipleChoiceGenerator
from config import EXCEL_FILE
import json


def main():
    parser = argparse.ArgumentParser(
        description="Create multiple-choice diabetes hallucination benchmark from Excel dataset"
    )
    parser.add_argument(
        "--excel-file",
        type=str,
        default=str(EXCEL_FILE),
        help="Path to Excel file with Q&A pairs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="Output path for benchmark JSONL file"
    )
    parser.add_argument(
        "--num-options",
        type=int,
        default=4,
        help="Number of answer options per question (default: 4)"
    )
    parser.add_argument(
        "--hallucination-ratio",
        type=float,
        default=0.5,
        help="Ratio of questions with hallucinated distractors (0.0-1.0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from {args.excel_file}...")
    loader = DiabetesQALoader(Path(args.excel_file))
    qa_pairs = loader.get_qa_pairs()
    print(f"Loaded {len(qa_pairs)} Q&A pairs")
    
    # Generate multiple-choice benchmark
    print(f"\nGenerating multiple-choice benchmark...")
    print(f"  - Options per question: {args.num_options}")
    print(f"  - Questions with hallucinated distractors: {args.hallucination_ratio*100:.1f}%")
    
    generator = MultipleChoiceGenerator(seed=args.seed)
    benchmark = generator.create_multiple_choice_benchmark(
        qa_pairs,
        num_options=args.num_options,
        hallucination_ratio=args.hallucination_ratio,
        include_hallucinations=True
    )
    
    # Save benchmark
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in benchmark:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Print statistics
    total_questions = len(benchmark)
    questions_with_hallucinations = sum(
        1 for item in benchmark 
        if any(opt.get('is_hallucination', False) for opt in item['options'])
    )
    
    total_options = sum(len(item['options']) for item in benchmark)
    total_hallucinated_options = sum(
        sum(1 for opt in item['options'] if opt.get('is_hallucination', False))
        for item in benchmark
    )
    
    print(f"\n{'='*60}")
    print(f"Multiple-Choice Benchmark Created Successfully!")
    print(f"{'='*60}")
    print(f"Total questions: {total_questions}")
    print(f"Questions with hallucinated distractors: {questions_with_hallucinations}")
    print(f"Total answer options: {total_options}")
    print(f"Hallucinated options: {total_hallucinated_options}")
    print(f"\nSaved to: {output_path}")
    
    # Print distractor type breakdown
    distractor_types = {}
    for item in benchmark:
        for opt in item['options']:
            if not opt['is_correct']:
                dist_type = opt.get('type', 'unknown')
                distractor_types[dist_type] = distractor_types.get(dist_type, 0) + 1
    
    if distractor_types:
        print(f"\nDistractor type breakdown:")
        for dist_type, count in sorted(distractor_types.items()):
            print(f"  - {dist_type}: {count}")
    
    # Print hallucination strategy breakdown
    hallucination_strategies = {}
    for item in benchmark:
        for opt in item['options']:
            if opt.get('is_hallucination'):
                strategy = opt.get('hallucination_strategy', 'unknown')
                hallucination_strategies[strategy] = hallucination_strategies.get(strategy, 0) + 1
    
    if hallucination_strategies:
        print(f"\nHallucination strategy breakdown:")
        for strategy, count in sorted(hallucination_strategies.items()):
            print(f"  - {strategy}: {count}")


if __name__ == "__main__":
    main()
