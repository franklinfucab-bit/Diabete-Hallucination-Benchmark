"""
Example usage script demonstrating how to use the benchmark framework
"""
from pathlib import Path
from data_loader import DiabetesQALoader
from hallucination_generator import HallucinationGenerator
from evaluator import HallucinationEvaluator
from model_tester import OpenAIModelTester, test_benchmark
import json


def example_create_benchmark():
    """Example: Create a benchmark from Excel data"""
    print("=" * 60)
    print("Example 1: Creating a benchmark from Excel data")
    print("=" * 60)
    
    # Load data
    excel_path = Path("data/diabetes_qa_dataset.xlsx")
    loader = DiabetesQALoader(excel_path)
    qa_pairs = loader.get_qa_pairs()
    print(f"Loaded {len(qa_pairs)} Q&A pairs")
    
    # Generate benchmark
    generator = HallucinationGenerator(seed=42)
    benchmark = generator.create_benchmark_dataset(
        qa_pairs,
        hallucination_ratio=0.3,  # 30% hallucinated
        strategies=["contradiction", "fabrication", "omission"]
    )
    
    # Save benchmark
    output_path = Path("output/example_benchmark.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in benchmark:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Created benchmark with {len(benchmark)} samples")
    print(f"  - Correct: {sum(1 for item in benchmark if not item['is_hallucination'])}")
    print(f"  - Hallucinated: {sum(1 for item in benchmark if item['is_hallucination'])}")
    print(f"Saved to: {output_path}\n")


def example_test_model():
    """Example: Test a model on the benchmark"""
    print("=" * 60)
    print("Example 2: Testing a model on the benchmark")
    print("=" * 60)
    
    # Load benchmark
    benchmark_path = Path("output/example_benchmark.jsonl")
    if not benchmark_path.exists():
        print(f"Benchmark file not found: {benchmark_path}")
        print("Please run example_create_benchmark() first or create a benchmark manually.\n")
        return
    
    benchmark = []
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        for line in f:
            benchmark.append(json.loads(line))
    
    print(f"Loaded benchmark with {len(benchmark)} samples")
    
    # Initialize model tester (requires API key)
    try:
        tester = OpenAIModelTester(model="gpt-4")
        print("Testing with OpenAI GPT-4...")
        
        # Test on first 5 samples (for demonstration)
        predictions = test_benchmark(tester, benchmark, max_samples=5)
        
        # Evaluate
        evaluator = HallucinationEvaluator()
        ground_truth = [
            {
                'id': item['id'],
                'is_hallucination': item['is_hallucination'],
                'hallucination_strategy': item.get('hallucination_strategy')
            }
            for item in benchmark[:len(predictions)]
        ]
        
        metrics = evaluator.evaluate_model(predictions, ground_truth)
        report = evaluator.generate_report(metrics)
        print("\n" + report)
        
    except Exception as e:
        print(f"Error testing model: {e}")
        print("Make sure you have set your OPENAI_API_KEY environment variable.\n")


def example_custom_hallucination():
    """Example: Generate a single hallucination"""
    print("=" * 60)
    print("Example 3: Generating a custom hallucination")
    print("=" * 60)
    
    generator = HallucinationGenerator(seed=42)
    
    question = "What is the normal blood glucose level?"
    correct_answer = "Normal fasting blood glucose is typically between 70-100 mg/dL."
    
    print(f"Question: {question}")
    print(f"Correct Answer: {correct_answer}\n")
    
    strategies = ["contradiction", "fabrication", "omission", "exaggeration", "misattribution"]
    
    for strategy in strategies:
        result = generator.generate_hallucination(correct_answer, strategy, question)
        print(f"{strategy.upper()}:")
        print(f"  {result['hallucinated_answer']}\n")


if __name__ == "__main__":
    print("\nDiabetes Hallucination Benchmark - Example Usage\n")
    
    # Uncomment the examples you want to run:
    
    # example_create_benchmark()
    # example_test_model()
    # example_custom_hallucination()
    
    print("\nTo run examples, uncomment them in the script.")
