"""
生成高级"None of the above"类型多选题基准
包含更复杂的幻觉干扰项，并使用DeepSeek API标记幻觉类型
"""
import argparse
import json
from pathlib import Path
from utils.deepseek_tester import DeepSeekModelTester
import os
from datetime import datetime
import time


def classify_hallucination_type(tester: DeepSeekModelTester, question: str, option_text: str) -> str:
    """
    使用DeepSeek API分类幻觉类型
    
    Args:
        tester: DeepSeekModelTester实例
        question: 问题文本
        option_text: 选项文本
        
    Returns:
        幻觉类型: contradiction, fabrication, exaggeration, misattribution, 或 plausible_wrong
    """
    prompt = f"""你是医学专家，分析以下选项中的错误类型。

问题: {question}
选项: {option_text}

请判断这个选项的错误类型，只回复一个词：
- "contradiction" - 与正确信息矛盾
- "fabrication" - 包含虚假的医学声明或数据
- "exaggeration" - 夸大或绝对化表述
- "misattribution" - 错误归因给医学机构或研究
- "plausible_wrong" - 看似合理但事实错误
- "partial_correct" - 部分正确但误导

只回复类型名称，不要其他内容。"""

    headers = {
        'Authorization': f'Bearer {tester.api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "你是医学专家，专门分析医学信息的错误类型。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 20
    }
    
    try:
        import requests
        response = requests.post(tester.api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        raw_response = result['choices'][0]['message']['content'].strip().lower()
        
        # 提取类型
        types = ['contradiction', 'fabrication', 'exaggeration', 'misattribution', 'plausible_wrong', 'partial_correct']
        for t in types:
            if t in raw_response:
                return t
        
        return 'plausible_wrong'  # 默认
    except:
        return 'plausible_wrong'  # 如果API失败，返回默认值


def generate_advanced_none_of_above_question(
    tester: DeepSeekModelTester,
    topic: str,
    question_num: int,
    classify_hallucinations: bool = True
) -> dict:
    """
    生成一个高级"None of the above"类型的问题，包含更复杂的幻觉干扰项
    
    Args:
        tester: DeepSeekModelTester实例
        topic: 主题
        question_num: 问题编号
        classify_hallucinations: 是否使用DeepSeek分类幻觉类型
        
    Returns:
        包含问题和选项的字典
    """
    prompt = f"""你是医学教育专家，设计一个具有挑战性的糖尿病多选题。

要求：
1. 创建一个关于"{topic}"的糖尿病相关问题
2. 生成3个高难度错误选项（A, B, C），这些选项应该：
   - 包含微妙的医学幻觉，不是明显错误
   - 使用看似专业的医学术语
   - 包含部分正确信息但混合错误信息
   - 可能包含：虚假的研究数据、错误归因、夸大表述、或与事实矛盾的细微错误
   - 具有高度迷惑性，需要深入医学知识才能识别
3. 正确答案是 D: "None of the above"（以上都不是）

选项应该足够复杂，让AI模型难以判断，需要真正的医学知识才能识别错误。

请以JSON格式回复：
{{
  "question": "问题文本",
  "options": [
    {{"option_id": "A", "text": "包含微妙幻觉的错误选项A（使用专业术语，部分正确但混合错误）", "is_correct": false}},
    {{"option_id": "B", "text": "包含微妙幻觉的错误选项B（可能包含虚假数据或错误归因）", "is_correct": false}},
    {{"option_id": "C", "text": "包含微妙幻觉的错误选项C（夸大表述或细微矛盾）", "is_correct": false}},
    {{"option_id": "D", "text": "None of the above", "is_correct": true}}
  ],
  "explanation": "详细解释为什么所有选项都包含错误或幻觉"
}}"""

    headers = {
        'Authorization': f'Bearer {tester.api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": tester.model,
        "messages": [
            {"role": "system", "content": "你是一个医学教育专家，设计具有挑战性的多选题，包含微妙的医学幻觉和错误信息，需要深入医学知识才能识别。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1000
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
                options = parsed['options']
                
                # Ensure "None of the above" is option D and is correct
                none_option = None
                for opt in options:
                    if opt.get('option_id') == 'D' or 'none of the above' in opt.get('text', '').lower():
                        none_option = opt
                        break
                
                if not none_option:
                    options.append({
                        'option_id': 'D',
                        'text': 'None of the above',
                        'is_correct': True
                    })
                else:
                    none_option['is_correct'] = True
                    none_option['option_id'] = 'D'
                    if 'none of the above' not in none_option.get('text', '').lower():
                        none_option['text'] = 'None of the above'
                
                # Ensure other options are marked as incorrect
                for opt in options:
                    if opt.get('option_id') != 'D':
                        opt['is_correct'] = False
                
                # Classify hallucination types for wrong options
                if classify_hallucinations:
                    question_text = parsed['question']
                    for opt in options:
                        if opt.get('option_id') != 'D' and not opt.get('is_correct'):
                            print(f"      分类选项 {opt.get('option_id')} 的幻觉类型...", end=" ")
                            hallucination_type = classify_hallucination_type(
                                tester, question_text, opt.get('text', '')
                            )
                            opt['type'] = hallucination_type
                            opt['is_hallucination'] = True if hallucination_type in [
                                'contradiction', 'fabrication', 'exaggeration', 'misattribution'
                            ] else False
                            print(f"{hallucination_type}")
                            time.sleep(0.5)  # Small delay between classifications
                
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


def create_advanced_none_of_above_benchmark(
    topics: list,
    output_file: Path,
    tester: DeepSeekModelTester,
    num_questions: int = 10,
    classify_hallucinations: bool = True
):
    """
    创建高级"None of the above"类型的基准数据集
    
    Args:
        topics: 主题列表
        output_file: 输出文件路径
        tester: DeepSeekModelTester实例
        num_questions: 要生成的问题数量
        classify_hallucinations: 是否使用DeepSeek分类幻觉类型
    """
    print("=" * 80)
    print("生成高级 'None of the above' 类型多选题基准")
    print("=" * 80)
    print(f"模型: {tester.model}")
    print(f"目标问题数: {num_questions}")
    print(f"分类幻觉类型: {'是' if classify_hallucinations else '否'}")
    print(f"主题: {', '.join(topics)}\n")
    
    benchmark = []
    topic_index = 0
    
    for q_num in range(1, num_questions + 1):
        # 循环使用主题
        topic = topics[topic_index % len(topics)]
        topic_index += 1
        
        print(f"[{q_num}/{num_questions}] 生成问题 - 主题: {topic}...", end=" ")
        
        result = generate_advanced_none_of_above_question(
            tester, topic, q_num, classify_hallucinations
        )
        
        if result.get('success') and result.get('question') and result.get('options'):
            # Create benchmark entry
            question_entry = {
                'id': q_num - 1,
                'question': result['question'],
                'options': result['options'],
                'correct_answer': 'D',
                'ground_truth': 'None of the above',
                'explanation': result.get('explanation', ''),
                'topic': topic,
                'type': 'none_of_above',
                'difficulty': 'advanced',
                'metadata': {
                    'generated_by': 'deepseek',
                    'model': tester.model,
                    'generation_timestamp': datetime.now().isoformat(),
                    'test_purpose': '测试模型识别复杂幻觉和无关信息的能力',
                    'has_hallucination_classification': classify_hallucinations
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
            time.sleep(2.0)  # Longer delay for more complex generation
    
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
        # Statistics
        hallucination_types = {}
        for item in benchmark:
            for opt in item['options']:
                if opt.get('type') and opt.get('option_id') != 'D':
                    t = opt.get('type', 'unknown')
                    hallucination_types[t] = hallucination_types.get(t, 0) + 1
        
        if hallucination_types:
            print(f"\n幻觉类型统计:")
            for t, count in sorted(hallucination_types.items()):
                print(f"  {t}: {count}")
        
        print(f"\n示例问题:")
        sample = benchmark[0]
        print(f"  问题: {sample['question']}")
        print(f"  选项:")
        for opt in sample['options']:
            marker = "✓" if opt.get('is_correct') else " "
            hall_type = f" [{opt.get('type', 'N/A')}]" if opt.get('type') else ""
            print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:60]}...{hall_type}")
    
    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="生成高级'None of the above'类型的多选题基准（包含复杂幻觉）"
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
        default="output/advanced_none_of_above_benchmark.jsonl",
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
        "--no-classify",
        action="store_true",
        help="不分类幻觉类型（加快生成速度）"
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
    create_advanced_none_of_above_benchmark(
        args.topics,
        Path(args.output),
        tester,
        args.num_questions,
        classify_hallucinations=not args.no_classify
    )
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
