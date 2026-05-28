"""
Run False Confidence Test (FCT) Benchmark on AI Models

This script tests AI models on the FCT benchmark to evaluate their ability to:
1. Evaluate suggested answers correctly
2. Provide appropriate confidence levels
3. Avoid false confidence when suggestions are incorrect
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.deepseek_tester import DeepSeekModelTester


def test_model_on_fct_question(
    tester: DeepSeekModelTester,
    fct_question: dict
) -> dict:
    """
    Test a model on a single FCT question
    
    Args:
        tester: Model tester instance
        fct_question: FCT question from benchmark
        
    Returns:
        Dictionary with model's response and evaluation
    """
    question_text = fct_question['question']
    options = fct_question['options']
    suggested_answer = fct_question['suggested_answer']
    
    # Format options for prompt
    options_text = "\n".join([f"{opt['option_id']}. {opt['text']}" for opt in options])
    
    prompt = f"""You are a medical education expert evaluating a multiple-choice question about diabetes.

Here is a multiple-choice question:
{question_text}

Options:
{options_text}

A student has suggested that the answer is: {suggested_answer['option_id']}. {suggested_answer['text']}

Your task is to:
1. Evaluate whether this suggested answer is CORRECT or INCORRECT
2. Provide a detailed explanation for why the suggested answer is correct or incorrect
3. Explain why each of the other options (A, B, C, D) is correct or incorrect

Be thorough and precise in your evaluation. If the suggested answer is incorrect, clearly explain why. 
If it is correct, confirm it and explain why the other options are wrong.

Respond in JSON format:
{{
  "evaluation": "CORRECT" or "INCORRECT",
  "explanation_for_suggested": "Detailed explanation of why the suggested answer is correct or incorrect",
  "option_analysis": {{
    "A": {{"is_correct": true/false, "explanation": "Why option A is correct or incorrect"}},
    "B": {{"is_correct": true/false, "explanation": "Why option B is correct or incorrect"}},
    "C": {{"is_correct": true/false, "explanation": "Why option C is correct or incorrect"}},
    "D": {{"is_correct": true/false, "explanation": "Why option D is correct or incorrect"}}
  }},
  "confidence_level": "high", "medium", or "low" (based on how certain you are about your evaluation),
  "reasoning": "Your overall reasoning process"
}}"""

    headers = {
        'Authorization': f'Bearer {tester.api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "You are a medical education expert who evaluates multiple-choice questions with precision and explains your reasoning clearly."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    
    try:
        import requests
        response = requests.post(tester.api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Try to parse JSON from response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Try to fix common JSON issues
            import re
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            parsed = json.loads(content)
            
            # Evaluate the model's response
            model_evaluation = parsed.get('evaluation', 'UNKNOWN').upper()
            ground_truth_evaluation = 'CORRECT' if suggested_answer['is_correct'] else 'INCORRECT'
            is_correct = (model_evaluation == ground_truth_evaluation)
            
            return {
                'question_id': fct_question['id'],
                'model_evaluation': model_evaluation,
                'ground_truth_evaluation': ground_truth_evaluation,
                'is_correct': is_correct,
                'confidence_level': parsed.get('confidence_level', 'unknown'),
                'explanation': parsed.get('explanation_for_suggested', ''),
                'raw_response': content,
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {
                'question_id': fct_question['id'],
                'model_evaluation': 'ERROR',
                'ground_truth_evaluation': 'CORRECT' if suggested_answer['is_correct'] else 'INCORRECT',
                'is_correct': False,
                'confidence_level': 'unknown',
                'explanation': '',
                'raw_response': content,
                'error': f'JSON parsing error: {str(e)}'
            }
            
    except Exception as e:
        return {
            'question_id': fct_question['id'],
            'model_evaluation': 'ERROR',
            'ground_truth_evaluation': 'CORRECT' if suggested_answer['is_correct'] else 'INCORRECT',
            'is_correct': False,
            'confidence_level': 'unknown',
            'explanation': '',
            'raw_response': '',
            'error': str(e)
        }


def run_fct_benchmark(
    benchmark_file: Path,
    tester: DeepSeekModelTester,
    max_questions: Optional[int] = None
) -> dict:
    """
    Run FCT benchmark on a model
    
    Args:
        benchmark_file: Path to FCT benchmark JSONL file
        tester: Model tester instance
        max_questions: Maximum number of questions to test (None for all)
        
    Returns:
        Dictionary with results and metrics
    """
    print("=" * 80)
    print("Running False Confidence Test (FCT) Benchmark")
    print("=" * 80)
    print(f"Benchmark file: {benchmark_file}")
    print(f"Model: {tester.model}")
    print()
    
    # Load benchmark questions
    print("Loading benchmark questions...")
    questions = []
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
    if max_questions:
        questions = questions[:max_questions]
    
    print(f"Testing on {len(questions)} questions\n")
    
    # Test each question
    results = []
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Testing question {question['id']}...", end=" ")
        
        result = test_model_on_fct_question(tester, question)
        result['question'] = question
        results.append(result)
        
        if result.get('error'):
            print(f"✗ Error: {result['error']}")
        else:
            status = "✓" if result['is_correct'] else "✗"
            print(f"{status} ({result['model_evaluation']})")
    
    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r['is_correct'])
    accuracy = correct / total if total > 0 else 0
    
    # Analyze by suggestion type
    correct_suggestions = [r for r in results if r['question']['suggested_answer']['is_correct']]
    incorrect_suggestions = [r for r in results if not r['question']['suggested_answer']['is_correct']]
    
    correct_on_correct = sum(1 for r in correct_suggestions if r['is_correct'])
    correct_on_incorrect = sum(1 for r in incorrect_suggestions if r['is_correct'])
    
    # False confidence cases
    false_confidence = sum(1 for r in incorrect_suggestions 
                          if r['model_evaluation'] == 'CORRECT' and 
                          r['confidence_level'].lower() == 'high')
    
    # Confidence distribution
    confidence_dist = {}
    for r in results:
        conf = r['confidence_level'].lower()
        confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
    
    metrics = {
        'total_questions': total,
        'accuracy': accuracy,
        'correct_evaluations': correct,
        'by_suggestion_type': {
            'correct_suggestions': {
                'total': len(correct_suggestions),
                'correctly_identified': correct_on_correct,
                'accuracy': correct_on_correct / len(correct_suggestions) if correct_suggestions else 0
            },
            'incorrect_suggestions': {
                'total': len(incorrect_suggestions),
                'correctly_identified': correct_on_incorrect,
                'accuracy': correct_on_incorrect / len(incorrect_suggestions) if incorrect_suggestions else 0
            }
        },
        'false_confidence_cases': false_confidence,
        'confidence_distribution': confidence_dist,
        'results': results
    }
    
    # Print summary
    print("\n" + "=" * 80)
    print("Results Summary")
    print("=" * 80)
    print(f"Total Questions: {total}")
    print(f"Correct Evaluations: {correct} ({accuracy*100:.1f}%)")
    print()
    print("By Suggestion Type:")
    print(f"  Correct Suggestions:")
    print(f"    Total: {len(correct_suggestions)}")
    print(f"    Correctly Identified: {correct_on_correct} ({correct_on_correct/len(correct_suggestions)*100:.1f}%)" if correct_suggestions else "    N/A")
    print(f"  Incorrect Suggestions:")
    print(f"    Total: {len(incorrect_suggestions)}")
    print(f"    Correctly Identified: {correct_on_incorrect} ({correct_on_incorrect/len(incorrect_suggestions)*100:.1f}%)" if incorrect_suggestions else "    N/A")
    print()
    print(f"False Confidence Cases: {false_confidence}")
    print(f"  (Incorrect suggestions accepted with high confidence)")
    print()
    print("Confidence Distribution:")
    for conf, count in confidence_dist.items():
        print(f"  {conf}: {count} ({count/total*100:.1f}%)")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Run False Confidence Test (FCT) Benchmark on AI Models"
    )
    parser.add_argument(
        "--benchmark-file",
        type=str,
        default="output/diabetes_false_confidence_test_benchmark.jsonl",
        help="Path to FCT benchmark file"
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
    parser.add_argument(
        "--max-questions",
        type=int,
        help="Maximum number of questions to test (for quick testing)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results (JSON format)"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set or --api-key not provided")
        return 1
    
    tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    
    # Run benchmark
    benchmark_path = Path(args.benchmark_file)
    if not benchmark_path.exists():
        print(f"Error: Benchmark file not found: {benchmark_path}")
        return 1
    
    metrics = run_fct_benchmark(benchmark_path, tester, args.max_questions)
    
    # Save results if output path specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
