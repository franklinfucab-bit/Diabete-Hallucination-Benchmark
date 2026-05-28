"""
Main script to run the benchmark against AI models
"""
import argparse
from pathlib import Path
import json
from utils.model_tester import OpenAIModelTester, AnthropicModelTester, test_benchmark
from utils.evaluator import HallucinationEvaluator
from config import BENCHMARK_OUTPUT, RESULTS_DIR
from datetime import datetime


def load_benchmark(benchmark_path: Path):
    """Load benchmark dataset from JSONL file"""
    benchmark = []
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        for line in f:
            benchmark.append(json.loads(line))
    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="Run hallucination benchmark against AI models"
    )
    parser.add_argument(
        "--benchmark-file",
        type=str,
        default=str(BENCHMARK_OUTPUT),
        help="Path to benchmark JSONL file"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["openai", "anthropic"],
        required=True,
        help="Model provider to test"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        help="Specific model name (e.g., 'gpt-4', 'claude-3-opus-20240229')"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum number of samples to test (for quick testing)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Directory to save results"
    )
    
    args = parser.parse_args()
    
    # Load benchmark
    print(f"Loading benchmark from {args.benchmark_file}...")
    benchmark = load_benchmark(Path(args.benchmark_file))
    print(f"Loaded {len(benchmark)} test cases")
    
    # Initialize model tester
    if args.model == "openai":
        model_name = args.model_name or "gpt-4"
        tester = OpenAIModelTester(model=model_name)
        print(f"Testing with OpenAI model: {model_name}")
    elif args.model == "anthropic":
        model_name = args.model_name or "claude-3-opus-20240229"
        tester = AnthropicModelTester(model=model_name)
        print(f"Testing with Anthropic model: {model_name}")
    else:
        raise ValueError(f"Unsupported model: {args.model}")
    
    # Run tests
    predictions = test_benchmark(tester, benchmark, max_samples=args.max_samples)
    
    # Evaluate
    print("\nEvaluating results...")
    evaluator = HallucinationEvaluator()
    
    # Prepare ground truth
    ground_truth = [
        {
            'id': item['id'],
            'is_hallucination': item['is_hallucination'],
            'hallucination_strategy': item.get('hallucination_strategy')
        }
        for item in benchmark[:len(predictions)]
    ]
    
    # Calculate metrics
    metrics = evaluator.evaluate_model(predictions, ground_truth)
    strategy_breakdown = evaluator.evaluate_by_strategy(predictions, ground_truth)
    
    # Generate report
    report = evaluator.generate_report(metrics, strategy_breakdown)
    print("\n" + report)
    
    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"results_{args.model}_{timestamp}.json"
    report_file = output_dir / f"report_{args.model}_{timestamp}.txt"
    
    evaluator.save_results(metrics, results_file, model_name=model_name, strategy_breakdown=strategy_breakdown)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nResults saved to:")
    print(f"  - {results_file}")
    print(f"  - {report_file}")


if __name__ == "__main__":
    main()
