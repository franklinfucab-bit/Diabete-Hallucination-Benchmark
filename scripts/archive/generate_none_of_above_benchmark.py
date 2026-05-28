"""
生成"None of the above"类型的多选题基准
用于测试模型识别无关信息的能力
"""
import argparse
import json
from pathlib import Path
from utils.deepseek_tester import DeepSeekModelTester
import os
from datetime import datetime
import time


def generate_none_of_above_question(
    tester: DeepSeekModelTester,
    topic: str,
    question_num: int
) -> dict:
    """
    生成一个"None of the above"类型的问题
    
    Args:
        tester: DeepSeekModelTester 实例
        topic: 主题
        question_num: 问题编号
        
    Returns:
        包含问题和选项的字典
    """
    prompt = f"""你是医学教育专家，设计一个特殊的糖尿病多选题。

要求：
1. 创建一个关于"{topic}"的糖尿病相关问题
2. 生成3个错误选项（A, B, C），这些选项应该：
   - 与问题主题相关但明显错误
   - 包含常见的医学误解或无关信息
   - 具有迷惑性但可以被识别为错误
3. 正确答案是 D: "None of the above"（以上都不是）

请以JSON格式回复：
{{
  "question": "问题文本",
  "options": [
    {{"option_id": "A", "text": "错误选项A", "is_correct": false}},
    {{"option_id": "B", "text": "错误选项B", "is_correct": false}},
    {{"option_id": "C", "text": "错误选项C", "is_correct": false}},
    {{"option_id": "D", "text": "None of the above", "is_correct": true}}
  ],
  "explanation": "为什么以上选项都不正确"
}}"""

    headers = {
        'Authorization': f'Bearer {tester.api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "你是一个医学教育专家，设计准确、具有教育性的多选题。特别注意设计'None of the above'类型的问题来测试对无关信息的识别能力。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        import requests
        response = requests.post(tester.api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        raw_response = result['choices'][0]['message']['content'].strip()
        
        # Try to parse JSON
        try:
            # Extract JSON if wrapped in markdown code blocks
            if '```json' in raw_response:
                json_start = raw_response.find('```json') + 7
                json_end = raw_response.find('```', json_start)
                json_text = raw_response[json_start:json_end].strip()
            elif '```' in raw_response:
                json_start = raw_response.find('```') + 3
                json_end = raw_response.find('```', json_start)
                json_text = raw_response[json_start:json_end].strip()
            else:
                json_text = raw_response
            
            # Try to find JSON object
            if '{' in json_text:
                json_start = json_text.find('{')
                json_end = json_text.rfind('}') + 1
                json_text = json_text[json_start:json_end]
            
            parsed = json.loads(json_text)
            
            # Validate structure
            if 'question' in parsed and 'options' in parsed:
                # Ensure "None of the above" is option D and is correct
                options = parsed['options']
                
                # Find or create "None of the above" option
                none_option = None
                for opt in options:
                    if opt.get('option_id') == 'D' or 'none of the above' in opt.get('text', '').lower():
                        none_option = opt
                        break
                
                if not none_option:
                    # Add "None of the above" as option D
                    options.append({
                        'option_id': 'D',
                        'text': 'None of the above',
                        'is_correct': True
                    })
                else:
                    # Ensure it's marked as correct
                    none_option['is_correct'] = True
                    none_option['option_id'] = 'D'
                    if 'none of the above' not in none_option.get('text', '').lower():
                        none_option['text'] = 'None of the above'
                
                # Ensure other options are marked as incorrect
                for opt in options:
                    if opt.get('option_id') != 'D':
                        opt['is_correct'] = False
                
                # Sort options by option_id
                options.sort(key=lambda x: x.get('option_id', ''))
                
                return {
                    'question': parsed['question'],
                    'options': options,
                    'explanation': parsed.get('explanation', ''),
                    'raw_response': raw_response,
                    'success': True
                }
            else:
                return {
                    'question': None,
                    'options': [],
                    'error': 'Invalid JSON structure',
                    'raw_response': raw_response,
                    'success': False
                }
                
        except json.JSONDecodeError as e:
            return {
                'question': None,
                'options': [],
                'error': f'JSON parse error: {str(e)}',
                'raw_response': raw_response,
                'success': False
            }
            
    except Exception as e:
        return {
            'question': None,
            'options': [],
            'error': str(e),
            'raw_response': '',
            'success': False
        }


def create_none_of_above_benchmark(
    topics: list,
    output_file: Path,
    tester: DeepSeekModelTester,
    num_questions: int = 10
):
    """
    创建"None of the above"类型的基准数据集
    
    Args:
        topics: 主题列表
        output_file: 输出文件路径
        tester: DeepSeekModelTester 实例
        num_questions: 要生成的问题数量
    """
    print("=" * 80)
    print("生成 'None of the above' 类型多选题基准")
    print("=" * 80)
    print(f"模型: {tester.model}")
    print(f"目标问题数: {num_questions}")
    print(f"主题: {', '.join(topics)}\n")
    
    benchmark = []
    topic_index = 0
    
    for q_num in range(1, num_questions + 1):
        # 循环使用主题
        topic = topics[topic_index % len(topics)]
        topic_index += 1
        
        print(f"[{q_num}/{num_questions}] 生成问题 - 主题: {topic}...", end=" ")
        
        result = generate_none_of_above_question(tester, topic, q_num)
        
        if result.get('success') and result.get('question') and result.get('options'):
            # Create benchmark entry
            question_entry = {
                'id': q_num - 1,
                'question': result['question'],
                'options': result['options'],
                'correct_answer': 'D',  # Always D for "None of the above"
                'ground_truth': 'None of the above',
                'explanation': result.get('explanation', ''),
                'topic': topic,
                'type': 'none_of_above',
                'metadata': {
                    'generated_by': 'deepseek',
                    'model': tester.model,
                    'generation_timestamp': datetime.now().isoformat(),
                    'test_purpose': '测试模型识别无关信息的能力'
                }
            }
            
            benchmark.append(question_entry)
            print("✓")
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"✗ 失败: {error_msg}")
            if result.get('raw_response'):
                print(f"   原始响应: {result['raw_response'][:100]}...")
        
        # Rate limiting
        if q_num < num_questions:
            time.sleep(1.5)  # Delay between API calls
    
    # Save benchmark
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in benchmark:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print("\n" + "=" * 80)
    print("生成完成!")
    print("=" * 80)
    print(f"成功生成: {len(benchmark)}/{num_questions} 个问题")
    print(f"保存到: {output_file}")
    
    if len(benchmark) > 0:
        print(f"\n示例问题:")
        sample = benchmark[0]
        print(f"  问题: {sample['question']}")
        print(f"  选项:")
        for opt in sample['options']:
            marker = "✓" if opt.get('is_correct') else " "
            print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:60]}...")
    
    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="生成'None of the above'类型的多选题基准"
    )
    parser.add_argument(
        "--topics",
        type=str,
        nargs="+",
        default=[
            "糖尿病饮食管理",
            "血糖监测",
            "胰岛素使用",
            "并发症预防",
            "运动建议"
        ],
        help="主题列表"
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=10,
        help="要生成的问题数量（默认: 10）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/none_of_above_benchmark.jsonl",
        help="输出文件路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek 模型"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API 密钥（或设置 DEEPSEEK_API_KEY 环境变量）"
    )
    
    args = parser.parse_args()
    
    # Check API key
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 未找到 DeepSeek API 密钥")
        print("请设置 DEEPSEEK_API_KEY 环境变量或使用 --api-key 参数")
        return 1
    
    # Initialize tester
    tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    
    # Generate benchmark
    create_none_of_above_benchmark(
        args.topics,
        Path(args.output),
        tester,
        args.num_questions
    )
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
