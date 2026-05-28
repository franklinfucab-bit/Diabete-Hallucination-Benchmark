"""
Main script to run the multiple-choice benchmark against AI models
"""
import argparse
from pathlib import Path
import json
from utils.model_tester import OpenAIModelTester, AnthropicModelTester
from utils.mc_model_tester import MCModelTester
from utils.mc_evaluator import MultipleChoiceEvaluator
from config import RESULTS_DIR
from datetime import datetime


def load_benchmark(benchmark_path: Path):
    """Load multiple-choice benchmark dataset from JSONL file"""
    benchmark = []
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        for line in f:
            benchmark.append(json.loads(line))
    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="Run multiple-choice hallucination benchmark against AI models"
    )
    parser.add_argument(
        "--benchmark-file",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="Path to multiple-choice benchmark JSONL file"
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
        help="Maximum number of questions to test (for quick testing)"
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
    print(f"Loaded {len(benchmark)} multiple-choice questions")
    
    # Initialize model tester
    if args.model == "openai":
        model_name = args.model_name or "gpt-4"
        base_tester = OpenAIModelTester(model=model_name)
        print(f"Testing with OpenAI model: {model_name}")
    elif args.model == "anthropic":
        model_name = args.model_name or "claude-3-opus-20240229"
        base_tester = AnthropicModelTester(model=model_name)
        print(f"Testing with Anthropic model: {model_name}")
    else:
        raise ValueError(f"Unsupported model: {args.model}")
    
    mc_tester = MCModelTester(base_tester)
    
    # Run tests
    predictions = mc_tester.test_benchmark(benchmark, max_samples=args.max_samples)
    
    # Evaluate
    print("\nEvaluating results...")
    evaluator = MultipleChoiceEvaluator()
    
    # Prepare ground truth
    ground_truth = [
        {
            'id': item['id'],
            'correct_answer': item['correct_answer'],
            'options': item['options']
        }
        for item in benchmark[:len(predictions)]
    ]
    
    # Calculate metrics
    metrics = evaluator.evaluate_model(predictions, ground_truth)
    distractor_breakdown = evaluator.evaluate_by_distractor_type(predictions, ground_truth)
    
    # Generate report
    report = evaluator.generate_report(metrics, distractor_breakdown)
    print("\n" + report)
    
    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"mc_results_{args.model}_{timestamp}.json"
    report_file = output_dir / f"mc_report_{args.model}_{timestamp}.txt"
    
    evaluator.save_results(metrics, results_file, model_name=model_name, distractor_breakdown=distractor_breakdown)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nResults saved to:")
    print(f"  - {results_file}")
    print(f"  - {report_file}")


if __name__ == "__main__":
    main()
