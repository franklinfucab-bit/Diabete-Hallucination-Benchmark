"""
DeepSeek API 测试示例
快速测试脚本，展示如何使用 DeepSeek API 测试基准
"""
import os
from deepseek_tester import DeepSeekModelTester
import json

def example_test():
    """示例：测试单个问题"""
    
    # 检查 API 密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 请先设置 DEEPSEEK_API_KEY 环境变量")
        print("例如: export DEEPSEEK_API_KEY='your_key_here'")
        return
    
    # 初始化测试器
    print("初始化 DeepSeek 测试器...")
    tester = DeepSeekModelTester(model="deepseek-chat", api_key=api_key)
    
    # 测试示例 1: 二进制幻觉检测
    print("\n" + "=" * 60)
    print("示例 1: 测试二进制幻觉检测")
    print("=" * 60)
    
    question = "什么是糖尿病？"
    correct_answer = "糖尿病是一种慢性疾病，影响身体如何将食物转化为能量。"
    hallucinated_answer = "实际上，相反的是：糖尿病不是一种疾病，而是一种生活方式选择。"
    
    print(f"\n问题: {question}")
    print(f"\n正确答案: {correct_answer}")
    result1 = tester.detect_hallucination(question, correct_answer)
    print(f"结果: {'幻觉' if result1.get('is_hallucination') else '正确'}")
    print(f"原始回复: {result1.get('raw_response', 'N/A')}")
    
    print(f"\n幻觉答案: {hallucinated_answer}")
    result2 = tester.detect_hallucination(question, hallucinated_answer)
    print(f"结果: {'幻觉' if result2.get('is_hallucination') else '正确'}")
    print(f"原始回复: {result2.get('raw_response', 'N/A')}")
    
    # 测试示例 2: 多选题
    print("\n" + "=" * 60)
    print("示例 2: 测试多选题")
    print("=" * 60)
    
    mc_question = "正常空腹血糖水平是多少？"
    options = [
        {'option_id': 'A', 'text': '正常空腹血糖通常在 70-100 mg/dL 之间。', 'is_correct': True},
        {'option_id': 'B', 'text': '实际上，正常血糖水平高于 200 mg/dL。', 'is_correct': False},
        {'option_id': 'C', 'text': '糖尿病患者应该完全避免所有碳水化合物。', 'is_correct': False},
        {'option_id': 'D', 'text': '血糖水平不重要，可以忽略。', 'is_correct': False},
    ]
    
    print(f"\n问题: {mc_question}")
    print("选项:")
    for opt in options:
        marker = "✓" if opt['is_correct'] else " "
        print(f"  {marker} {opt['option_id']}. {opt['text']}")
    
    result3 = tester.answer_multiple_choice(mc_question, options)
    print(f"\n选择的答案: {result3.get('selected_option', 'N/A')}")
    print(f"原始回复: {result3.get('raw_response', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ 示例测试完成!")
    print("=" * 60)
    print("\n要测试完整基准，运行:")
    print("  python test_with_deepseek.py --benchmark-type binary --max-samples 10")


if __name__ == "__main__":
    example_test()
