"""
Main script to create the hallucination benchmark from Excel dataset
"""
import argparse
from pathlib import Path
from utils.data_loader import DiabetesQALoader
from utils.hallucination_generator import HallucinationGenerator
from config import EXCEL_FILE, BENCHMARK_OUTPUT, HALLUCINATION_STRATEGIES
import json


def main():
    parser = argparse.ArgumentParser(
        description="Create diabetes hallucination benchmark from Excel dataset"
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
        default=str(BENCHMARK_OUTPUT),
        help="Output path for benchmark JSONL file"
    )
    parser.add_argument(
        "--hallucination-ratio",
        type=float,
        default=0.3,
        help="Ratio of answers that should be hallucinated (0.0-1.0)"
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
    
    # Generate benchmark
    print(f"Generating benchmark with {args.hallucination_ratio*100:.1f}% hallucination ratio...")
    generator = HallucinationGenerator(seed=args.seed)
    benchmark = generator.create_benchmark_dataset(
        qa_pairs,
        hallucination_ratio=args.hallucination_ratio,
        strategies=HALLUCINATION_STRATEGIES
    )
    
    # Save benchmark
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in benchmark:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Print statistics
    num_hallucinations = sum(1 for item in benchmark if item['is_hallucination'])
    num_correct = len(benchmark) - num_hallucinations
    
    print(f"\nBenchmark created successfully!")
    print(f"Total samples: {len(benchmark)}")
    print(f"  - Correct answers: {num_correct}")
    print(f"  - Hallucinated answers: {num_hallucinations}")
    print(f"\nSaved to: {output_path}")
    
    # Print strategy breakdown
    strategy_counts = {}
    for item in benchmark:
        if item.get('hallucination_strategy'):
            strategy = item['hallucination_strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    if strategy_counts:
        print("\nHallucination strategy breakdown:")
        for strategy, count in strategy_counts.items():
            print(f"  - {strategy}: {count}")


if __name__ == "__main__":
    main()
