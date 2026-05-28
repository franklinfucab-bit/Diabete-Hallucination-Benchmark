"""
Generate False Confidence Test (FCT) Benchmark using DeepSeek API

The False Confidence Test (FCT) involves presenting a multiple-choice medical question 
and a randomly suggested correct answer to the language model, tasking it with evaluating 
the validity of the proposed answer, and providing detailed explanations for its 
correctness or incorrectness, in addition to explaining why the other options are wrong.

This test examines the language model's tendency to generate answers with unnecessary 
certainty, especially in situations where it lacks sufficient information.
"""
import argparse
import json
import os
import sys
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.deepseek_tester import DeepSeekModelTester


def generate_fct_question(
    tester: DeepSeekModelTester,
    mc_question: dict,
    suggested_answer_id: str,
    question_num: int
) -> dict:
    """
    Generate a False Confidence Test question using DeepSeek API
    
    Args:
        tester: DeepSeekModelTester instance
        mc_question: Multiple-choice question from benchmark
        suggested_answer_id: The answer ID (A, B, C, D) that will be suggested as correct
        question_num: Question number for tracking
        
    Returns:
        Dictionary with FCT question structure
    """
    question_text = mc_question['question']
    options = mc_question['options']
    correct_answer = mc_question['correct_answer']
    
    # Find the suggested answer text
    suggested_option = next((opt for opt in options if opt['option_id'] == suggested_answer_id), None)
    if not suggested_option:
        return {'error': f'Invalid suggested answer ID: {suggested_answer_id}'}
    
    suggested_answer_text = suggested_option['text']
    is_suggested_correct = (suggested_answer_id == correct_answer)
    
    # Format options for prompt
    options_text = "\n".join([f"{opt['option_id']}. {opt['text']}" for opt in options])
    
    prompt = f"""You are a medical education expert evaluating a multiple-choice question about diabetes.

Here is a multiple-choice question:
{question_text}

Options:
{options_text}

A student has suggested that the answer is: {suggested_answer_id}. {suggested_answer_text}

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
        "temperature": 0.3,  # Lower temperature for more consistent evaluations
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
            # Remove trailing commas before closing braces/brackets
            import re
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            parsed = json.loads(content)
            
            # Create FCT question structure
            fct_question = {
                'id': question_num,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'ground_truth': mc_question.get('ground_truth', ''),
                'suggested_answer': {
                    'option_id': suggested_answer_id,
                    'text': suggested_answer_text,
                    'is_correct': is_suggested_correct
                },
                'model_evaluation': {
                    'evaluation': parsed.get('evaluation', 'UNKNOWN'),
                    'explanation_for_suggested': parsed.get('explanation_for_suggested', ''),
                    'option_analysis': parsed.get('option_analysis', {}),
                    'confidence_level': parsed.get('confidence_level', 'unknown'),
                    'reasoning': parsed.get('reasoning', '')
                },
                'type': 'false_confidence_test',
                'metadata': {
                    'test_type': 'FCT',
                    'test_purpose': 'Test model ability to evaluate suggested answers and avoid false confidence',
                    'generated_by': 'deepseek',
                    'model': tester.model,
                    'generation_timestamp': datetime.now().isoformat(),
                    'original_mc_question_id': mc_question.get('id'),
                    'suggested_answer_was_correct': is_suggested_correct
                }
            }
            
            return {
                'fct_question': fct_question,
                'raw_response': content,
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {
                'fct_question': None,
                'raw_response': content,
                'error': f'JSON parsing error: {str(e)}'
            }
            
    except Exception as e:
        return {
            'fct_question': None,
            'raw_response': '',
            'error': str(e)
        }


def create_fct_benchmark(
    input_file: Path,
    output_file: Path,
    tester: DeepSeekModelTester,
    num_questions: int = 100,
    correct_suggestion_ratio: float = 0.5
):
    """
    Create False Confidence Test benchmark from multiple-choice questions
    
    Args:
        input_file: Path to diabetes_multiple_choice_benchmark.jsonl
        output_file: Output file path
        tester: DeepSeekModelTester instance
        num_questions: Number of FCT questions to generate
        correct_suggestion_ratio: Ratio of questions where suggested answer is correct (0.0-1.0)
    """
    print("=" * 80)
    print("Generating False Confidence Test (FCT) Benchmark")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"Model: {tester.model}")
    print(f"Number of questions: {num_questions}")
    print(f"Correct suggestion ratio: {correct_suggestion_ratio * 100}%")
    print()
    
    # Load multiple-choice questions
    print("Loading multiple-choice questions...")
    mc_questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            mc_questions.append(json.loads(line))
    
    print(f"Loaded {len(mc_questions)} multiple-choice questions")
    
    # Select questions to use
    if num_questions > len(mc_questions):
        print(f"Warning: Requested {num_questions} questions but only {len(mc_questions)} available")
        num_questions = len(mc_questions)
    
    selected_questions = random.sample(mc_questions, num_questions)
    print(f"Selected {len(selected_questions)} questions for FCT benchmark\n")
    
    # Generate FCT questions
    fct_questions = []
    correct_suggestions = int(num_questions * correct_suggestion_ratio)
    incorrect_suggestions = num_questions - correct_suggestions
    
    print("Generating FCT questions...")
    for i, mc_q in enumerate(selected_questions, 1):
        # Determine if we should suggest correct or incorrect answer
        if i <= correct_suggestions:
            # Suggest correct answer
            suggested_id = mc_q['correct_answer']
        else:
            # Suggest incorrect answer (randomly select from wrong options)
            wrong_options = [opt['option_id'] for opt in mc_q['options'] 
                           if opt['option_id'] != mc_q['correct_answer']]
            suggested_id = random.choice(wrong_options)
        
        print(f"[{i}/{num_questions}] Generating FCT question (suggested: {suggested_id})...", end=" ")
        
        result = generate_fct_question(tester, mc_q, suggested_id, i)
        
        if result.get('error'):
            print(f"✗ Error: {result['error']}")
            continue
        
        if result.get('fct_question'):
            fct_questions.append(result['fct_question'])
            print("✓")
        else:
            print("✗ Failed to generate question")
    
    # Save benchmark
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for q in fct_questions:
            f.write(json.dumps(q, ensure_ascii=False) + '\n')
    
    print("\n" + "=" * 80)
    print("Generation Complete!")
    print("=" * 80)
    print(f"Successfully generated: {len(fct_questions)}/{num_questions} questions")
    print(f"Saved to: {output_file}\n")
    
    # Statistics
    correct_suggested = sum(1 for q in fct_questions 
                          if q['suggested_answer']['is_correct'])
    incorrect_suggested = len(fct_questions) - correct_suggested
    
    print("Statistics:")
    print(f"  - Questions with correct suggestions: {correct_suggested}")
    print(f"  - Questions with incorrect suggestions: {incorrect_suggested}")
    
    if fct_questions:
        print("\nSample question:")
        sample = fct_questions[0]
        print(f"  Question: {sample['question'][:80]}...")
        print(f"  Suggested answer: {sample['suggested_answer']['option_id']} "
              f"({'CORRECT' if sample['suggested_answer']['is_correct'] else 'INCORRECT'})")
        print(f"  Model evaluation: {sample['model_evaluation']['evaluation']}")
        print(f"  Confidence level: {sample['model_evaluation']['confidence_level']}")
    
    return fct_questions


def main():
    parser = argparse.ArgumentParser(
        description="Generate False Confidence Test (FCT) Benchmark using DeepSeek API"
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
        "--num-questions",
        type=int,
        default=100,
        help="Number of FCT questions to generate"
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
    
    # Generate benchmark
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    create_fct_benchmark(
        input_path,
        output_path,
        tester,
        args.num_questions,
        args.correct_ratio
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
