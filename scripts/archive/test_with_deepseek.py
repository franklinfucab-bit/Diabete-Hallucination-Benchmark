"""
使用 DeepSeek API 测试基准数据集
将每个问题发送到 DeepSeek API 进行检查
"""
import argparse
import json
from pathlib import Path
from utils.deepseek_tester import DeepSeekModelTester, test_benchmark_with_deepseek
from utils.evaluator import HallucinationEvaluator
from utils.mc_evaluator import MultipleChoiceEvaluator
from config import BENCHMARK_OUTPUT, RESULTS_DIR
from datetime import datetime
import os


def load_benchmark(benchmark_path: Path):
    """加载基准数据集"""
    benchmark = []
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        for line in f:
            benchmark.append(json.loads(line))
    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="使用 DeepSeek API 测试基准数据集"
    )
    parser.add_argument(
        "--benchmark-type",
        type=str,
        choices=["binary", "multiple-choice", "both"],
        default="both",
        help="要测试的基准类型"
    )
    parser.add_argument(
        "--binary-file",
        type=str,
        default=str(BENCHMARK_OUTPUT),
        help="二进制基准文件路径"
    )
    parser.add_argument(
        "--mc-file",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="多选题基准文件路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek 模型名称"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="最大测试样本数（用于快速测试）"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="API 调用间隔（秒）"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API 密钥（或设置 DEEPSEEK_API_KEY 环境变量）"
    )
    
    args = parser.parse_args()
    
    # 检查 API 密钥
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 未找到 DeepSeek API 密钥")
        print("请设置 DEEPSEEK_API_KEY 环境变量或使用 --api-key 参数")
        return 1
    
    # 初始化 DeepSeek 测试器
    tester = DeepSeekModelTester(model=args.model, api_key=api_key)
    print(f"使用 DeepSeek 模型: {args.model}")
    print(f"API 密钥: {'*' * 20}{api_key[-4:] if len(api_key) > 4 else ''}\n")
    
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 测试二进制基准
    if args.benchmark_type in ["binary", "both"]:
        print("=" * 80)
        print("测试二进制幻觉检测基准")
        print("=" * 80)
        
        binary_path = Path(args.binary_file)
        if not binary_path.exists():
            print(f"错误: 文件不存在: {binary_path}")
            return 1
        
        print(f"加载基准: {binary_path}")
        binary_benchmark = load_benchmark(binary_path)
        print(f"已加载 {len(binary_benchmark)} 个样本\n")
        
        # 测试
        predictions = test_benchmark_with_deepseek(
            binary_benchmark,
            tester,
            max_samples=args.max_samples,
            delay=args.delay
        )
        
        # 评估
        print("\n评估结果...")
        evaluator = HallucinationEvaluator()
        
        ground_truth = [
            {
                'id': item['id'],
                'is_hallucination': item['is_hallucination'],
                'hallucination_strategy': item.get('hallucination_strategy')
            }
            for item in binary_benchmark[:len(predictions)]
        ]
        
        metrics = evaluator.evaluate_model(predictions, ground_truth)
        strategy_breakdown = evaluator.evaluate_by_strategy(predictions, ground_truth)
        
        # 生成报告
        report = evaluator.generate_report(metrics, strategy_breakdown)
        print("\n" + report)
        
        # 保存结果
        results_file = results_dir / f"deepseek_binary_{timestamp}.json"
        report_file = results_dir / f"deepseek_binary_report_{timestamp}.txt"
        
        evaluator.save_results(metrics, results_file, model_name=args.model, strategy_breakdown=strategy_breakdown)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n结果已保存:")
        print(f"  - {results_file}")
        print(f"  - {report_file}")
    
    # 测试多选题基准
    if args.benchmark_type in ["multiple-choice", "both"]:
        print("\n" + "=" * 80)
        print("测试多选题基准")
        print("=" * 80)
        
        mc_path = Path(args.mc_file)
        if not mc_path.exists():
            print(f"错误: 文件不存在: {mc_path}")
            return 1
        
        print(f"加载基准: {mc_path}")
        mc_benchmark = load_benchmark(mc_path)
        print(f"已加载 {len(mc_benchmark)} 个问题\n")
        
        # 测试
        predictions = test_benchmark_with_deepseek(
            mc_benchmark,
            tester,
            max_samples=args.max_samples,
            delay=args.delay
        )
        
        # 评估
        print("\n评估结果...")
        mc_evaluator = MultipleChoiceEvaluator()
        
        ground_truth = [
            {
                'id': item['id'],
                'correct_answer': item['correct_answer'],
                'options': item['options']
            }
            for item in mc_benchmark[:len(predictions)]
        ]
        
        metrics = mc_evaluator.evaluate_model(predictions, ground_truth)
        distractor_breakdown = mc_evaluator.evaluate_by_distractor_type(predictions, ground_truth)
        
        # 生成报告
        report = mc_evaluator.generate_report(metrics, distractor_breakdown)
        print("\n" + report)
        
        # 保存结果
        results_file = results_dir / f"deepseek_mc_{timestamp}.json"
        report_file = results_dir / f"deepseek_mc_report_{timestamp}.txt"
        
        mc_evaluator.save_results(metrics, results_file, model_name=args.model, distractor_breakdown=distractor_breakdown)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n结果已保存:")
        print(f"  - {results_file}")
        print(f"  - {report_file}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
