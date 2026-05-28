"""
使用 DeepSeek API 生成问题和检查
可以生成新的问题，也可以检查现有问题
"""
import argparse
import json
from pathlib import Path
from utils.deepseek_tester import DeepSeekModelTester
import os
from datetime import datetime


def generate_questions_with_deepseek(
    topics: list,
    output_file: Path,
    tester: DeepSeekModelTester,
    num_questions_per_topic: int = 1
):
    """
    使用 DeepSeek API 生成问题
    
    Args:
        topics: 主题列表
        output_file: 输出文件路径
        tester: DeepSeekModelTester 实例
        num_questions_per_topic: 每个主题生成的问题数
    """
    print(f"使用 DeepSeek API 生成问题...")
    print(f"模型: {tester.model}")
    print(f"主题数: {len(topics)}")
    print(f"每个主题生成: {num_questions_per_topic} 个问题\n")
    
    generated_qa = []
    
    for topic_idx, topic in enumerate(topics, 1):
        print(f"[{topic_idx}/{len(topics)}] 生成主题: {topic}")
        
        for q_num in range(num_questions_per_topic):
            print(f"  生成问题 {q_num + 1}/{num_questions_per_topic}...", end=" ")
            
            result = tester.generate_question(topic)
            
            if result.get('error'):
                print(f"❌ 错误: {result['error']}")
                continue
            
            if result.get('question') and result.get('answer'):
                qa_pair = {
                    'id': len(generated_qa),
                    'question': result['question'],
                    'answer': result['answer'],
                    'topic': topic,
                    'generated_by': 'deepseek',
                    'model': tester.model,
                    'metadata': {
                        'generation_timestamp': datetime.now().isoformat(),
                        'raw_response': result.get('raw_response', '')
                    }
                }
                generated_qa.append(qa_pair)
                print("✓")
            else:
                print("⚠️ 生成失败（未获得有效问题/答案）")
    
    # 保存生成的问题
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for qa in generated_qa:
            f.write(json.dumps(qa, ensure_ascii=False) + '\n')
    
    print(f"\n✅ 生成完成!")
    print(f"总共生成: {len(generated_qa)} 个问题")
    print(f"保存到: {output_file}")
    
    return generated_qa


def check_questions_with_deepseek(
    input_file: Path,
    output_file: Path,
    tester: DeepSeekModelTester
):
    """
    使用 DeepSeek API 检查现有问题
    
    Args:
        input_file: 输入文件路径（JSONL格式）
        output_file: 输出文件路径（检查结果）
        tester: DeepSeekModelTester 实例
    """
    print(f"使用 DeepSeek API 检查问题...")
    print(f"模型: {tester.model}")
    print(f"输入文件: {input_file}\n")
    
    # 加载问题
    questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
    print(f"加载了 {len(questions)} 个问题\n")
    
    checked_results = []
    
    for idx, qa in enumerate(questions, 1):
        question = qa.get('question', '')
        answer = qa.get('answer', '') or qa.get('ground_truth', '')
        
        if not question or not answer:
            print(f"[{idx}/{len(questions)}] ⚠️ 跳过：缺少问题或答案")
            continue
        
        print(f"[{idx}/{len(questions)}] 检查: {question[:50]}...", end=" ")
        
        result = tester.detect_hallucination(question, answer)
        
        checked_result = {
            'id': qa.get('id', idx - 1),
            'question': question,
            'answer': answer,
            'is_hallucination': result.get('is_hallucination'),
            'deepseek_response': result.get('raw_response', ''),
            'model': tester.model,
            'check_timestamp': datetime.now().isoformat(),
            'original_data': qa
        }
        
        checked_results.append(checked_result)
        
        status = "❌ 幻觉" if result.get('is_hallucination') else "✓ 正确"
        print(status)
    
    # 保存检查结果
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in checked_results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    # 统计
    total = len(checked_results)
    hallucinations = sum(1 for r in checked_results if r.get('is_hallucination'))
    correct = total - hallucinations
    
    print(f"\n✅ 检查完成!")
    print(f"总共检查: {total} 个问题")
    print(f"正确: {correct} ({correct/total*100:.1f}%)")
    print(f"检测到幻觉: {hallucinations} ({hallucinations/total*100:.1f}%)")
    print(f"保存到: {output_file}")
    
    return checked_results


def main():
    parser = argparse.ArgumentParser(
        description="使用 DeepSeek API 生成问题或检查问题"
    )
    parser.add_argument(
        "mode",
        choices=["generate", "check"],
        help="模式: generate (生成问题) 或 check (检查问题)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API 密钥（或设置 DEEPSEEK_API_KEY 环境变量）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek 模型"
    )
    
    # 生成模式参数
    parser.add_argument(
        "--topics",
        type=str,
        nargs="+",
        help="生成问题的主题列表（用于 generate 模式）"
    )
    parser.add_argument(
        "--topics-file",
        type=str,
        help="包含主题列表的文件（每行一个主题）"
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=1,
        help="每个主题生成的问题数（默认: 1）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/deepseek_generated_questions.jsonl",
        help="输出文件路径（用于 generate 模式）"
    )
    
    # 检查模式参数
    parser.add_argument(
        "--input",
        type=str,
        help="输入文件路径（用于 check 模式）"
    )
    parser.add_argument(
        "--check-output",
        type=str,
        default="output/deepseek_checked_questions.jsonl",
        help="检查结果输出文件路径（用于 check 模式）"
    )
    
    args = parser.parse_args()
    
    # 检查 API 密钥
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 未找到 DeepSeek API 密钥")
        print("请设置 DEEPSEEK_API_KEY 环境变量或使用 --api-key 参数")
        return 1
    
    # 初始化测试器
    tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    
    if args.mode == "generate":
        # 获取主题列表
        topics = []
        if args.topics:
            topics = args.topics
        elif args.topics_file:
            with open(args.topics_file, 'r', encoding='utf-8') as f:
                topics = [line.strip() for line in f if line.strip()]
        else:
            print("错误: 请提供 --topics 或 --topics-file")
            return 1
        
        if not topics:
            print("错误: 没有找到主题")
            return 1
        
        # 生成问题
        generate_questions_with_deepseek(
            topics,
            Path(args.output),
            tester,
            args.num_questions
        )
    
    elif args.mode == "check":
        if not args.input:
            print("错误: check 模式需要 --input 参数")
            return 1
        
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误: 文件不存在: {input_path}")
            return 1
        
        # 检查问题
        check_questions_with_deepseek(
            input_path,
            Path(args.check_output),
            tester
        )
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
