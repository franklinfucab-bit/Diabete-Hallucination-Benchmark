"""
基于现有多选题基准转换为"None of the above"类型
将正确答案替换为"None of the above"，并添加解释
"""
import json
from pathlib import Path
from utils.deepseek_tester import DeepSeekModelTester
import os
from datetime import datetime
import time


def generate_explanation(tester: DeepSeekModelTester, question: str, options: list) -> str:
    """
    使用DeepSeek API生成解释，说明为什么所有选项都不正确
    
    Args:
        tester: DeepSeekModelTester实例
        question: 问题文本
        options: 选项列表（A, B, C都是错误的）
        
    Returns:
        解释文本
    """
    options_text = "\n".join([
        f"{opt.get('option_id', '?')}. {opt.get('text', '')}"
        for opt in options if opt.get('option_id') != 'D'
    ])
    
    prompt = f"""你是医学专家，分析以下多选题。

问题: {question}

选项:
{options_text}

这些选项（A, B, C）都包含错误或幻觉信息。请简要解释为什么所有选项都不正确，以及为什么正确答案应该是"None of the above"。

请用中文回复，简洁明了（2-3句话）。"""

    headers = {
        'Authorization': f'Bearer {tester.api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "你是医学专家，专门分析医学信息的准确性。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }
    
    try:
        import requests
        response = requests.post(tester.api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        explanation = result['choices'][0]['message']['content'].strip()
        return explanation
    except Exception as e:
        return f"所有选项都包含错误信息或医学误解，因此正确答案是'None of the above'。错误: {str(e)}"


def convert_question_to_none_of_above(
    original_question: dict,
    tester: DeepSeekModelTester = None,
    generate_explanation_with_api: bool = False
) -> dict:
    """
    将标准多选题转换为"None of the above"类型
    
    Args:
        original_question: 原始问题字典
        tester: DeepSeekModelTester实例（用于生成解释）
        generate_explanation_with_api: 是否使用API生成解释
        
    Returns:
        转换后的问题字典
    """
    # 找到原来的正确答案
    original_correct_option = None
    for opt in original_question['options']:
        if opt.get('is_correct', False):
            original_correct_option = opt
            break
    
    # 创建新的选项列表
    new_options = []
    
    # 将所有原选项标记为错误（包括原来的正确答案）
    for opt in original_question['options']:
        if opt.get('option_id') != original_question.get('correct_answer', ''):
            new_opt = opt.copy()
            new_opt['is_correct'] = False
            # 保留原有的幻觉类型信息
            if 'type' not in new_opt:
                new_opt['type'] = 'plausible_wrong' if not new_opt.get('is_hallucination') else 'hallucination'
            new_options.append(new_opt)
    
    # 将原来的正确答案也添加为错误选项
    if original_correct_option:
        wrong_correct_opt = original_correct_option.copy()
        wrong_correct_opt['is_correct'] = False
        wrong_correct_opt['type'] = 'plausible_wrong'
        wrong_correct_opt['is_hallucination'] = False
        # 确保选项ID正确
        if len(new_options) < 3:
            wrong_correct_opt['option_id'] = chr(65 + len(new_options))  # A, B, C
            new_options.append(wrong_correct_opt)
    
    # 确保有3个错误选项
    while len(new_options) < 3:
        new_options.append({
            'option_id': chr(65 + len(new_options)),
            'text': 'This option contains incorrect information',
            'is_correct': False,
            'type': 'plausible_wrong',
            'is_hallucination': False
        })
    
    # 只保留前3个选项（A, B, C）
    new_options = new_options[:3]
    for i, opt in enumerate(new_options):
        opt['option_id'] = chr(65 + i)  # A, B, C
    
    # 添加"None of the above"选项
    new_options.append({
        'option_id': 'D',
        'text': 'None of the above',
        'is_correct': True,
        'type': 'correct',
        'is_hallucination': False
    })
    
    # 生成解释（不使用API，直接生成简单解释）
    explanation = "All options (A, B, C) contain incorrect information or medical misconceptions. Therefore, the correct answer is 'None of the above'."
    
    # 创建新问题
    converted_question = {
        'id': original_question.get('id', 0),
        'question': original_question['question'],
        'options': new_options,
        'correct_answer': 'D',
        'ground_truth': 'None of the above',
        'original_correct_answer': original_question.get('correct_answer', ''),
        'original_ground_truth': original_question.get('ground_truth', ''),
        'explanation': explanation,
        'topic': original_question.get('topic', original_question.get('metadata', {}).get('original_id', '')),
        'type': 'none_of_above',
        'difficulty': 'converted',
            'metadata': {
                'converted_from': 'diabetes_multiple_choice_benchmark',
                'original_id': original_question.get('id'),
                'test_purpose': 'Test model ability to identify irrelevant information (converted from existing benchmark)'
            }
    }
    
    return converted_question


def convert_benchmark(
    input_file: Path,
    output_file: Path,
    tester: DeepSeekModelTester = None,
    max_questions: int = None,
    generate_explanation_with_api: bool = False
):
    """
    转换整个基准文件
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        tester: DeepSeekModelTester实例
        max_questions: 最大转换问题数（None表示全部）
        generate_explanation_with_api: 是否使用API生成解释
    """
    print("=" * 80)
    print("Converting Multiple Choice Benchmark to 'None of the above' Type")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Use API for explanation: {'Yes' if generate_explanation_with_api else 'No'}")
    if max_questions:
        print(f"Max questions: {max_questions}")
    print()
    
    # 加载原始基准
    original_questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            original_questions.append(json.loads(line))
    
    print(f"Loaded {len(original_questions)} original questions")
    
    if max_questions:
        original_questions = original_questions[:max_questions]
        print(f"Converting first {max_questions} questions\n")
    
    # 转换问题
    converted_questions = []
    
    for i, orig_q in enumerate(original_questions, 1):
        print(f"[{i}/{len(original_questions)}] Converting question {orig_q.get('id', i-1)}...", end=" ")
        
        try:
            converted = convert_question_to_none_of_above(
                orig_q,
                tester,
                generate_explanation_with_api
            )
            converted_questions.append(converted)
            
            # 每10个问题保存一次（防止数据丢失）
            if i % 10 == 0:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    for item in converted_questions:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                print(f"✓ (saved {i})")
            else:
                print("✓")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            # 继续处理下一个问题
            continue
    
    # 保存转换后的基准
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_questions:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print("\n" + "=" * 80)
    print("Conversion Complete!")
    print("=" * 80)
    print(f"Successfully converted: {len(converted_questions)}/{len(original_questions)} questions")
    print(f"Saved to: {output_file}")
    
    # 统计
    if converted_questions:
        print(f"\nSample question:")
        sample = converted_questions[0]
        print(f"  Question: {sample['question'][:70]}...")
        print(f"  Original correct answer: {sample.get('original_correct_answer', 'N/A')}")
        print(f"  New correct answer: {sample['correct_answer']}")
        print(f"  Number of options: {len(sample['options'])}")
        print(f"  Explanation: {sample.get('explanation', 'N/A')[:100]}...")
    
    return converted_questions


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert multiple choice benchmark to 'None of the above' type"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="Input file path"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/converted_none_of_above_benchmark.jsonl",
        help="Output file path"
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        help="Maximum number of questions to convert (default: all)"
    )
    parser.add_argument(
        "--use-api-explanation",
        action="store_true",
        help="Use DeepSeek API to generate explanations (requires API key)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek model (for generating explanations)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API key (or set DEEPSEEK_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # 初始化tester（如果需要API）
    tester = None
    if args.use_api_explanation:
        api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("Error: --use-api-explanation requires DEEPSEEK_API_KEY environment variable or --api-key parameter")
            return 1
        tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    
    # 转换基准
    convert_benchmark(
        Path(args.input),
        Path(args.output),
        tester,
        args.max_questions,
        args.use_api_explanation
    )
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
