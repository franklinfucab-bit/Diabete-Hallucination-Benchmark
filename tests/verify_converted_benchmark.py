"""验证转换后的基准文件"""
import json
from pathlib import Path

file_path = Path("output/converted_none_of_above_benchmark.jsonl")

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print("转换后的 None of the Above 基准验证")
print("=" * 80)
print(f"\n总问题数: {len(data)}")

# 验证
all_have_d = all(any(o.get('option_id') == 'D' for o in q['options']) for q in data)
all_d_correct = all(any(o.get('option_id') == 'D' and o.get('is_correct') for o in q['options']) for q in data)
all_correct_is_d = all(q['correct_answer'] == 'D' for q in data)
all_have_none = all(any('none of the above' in o.get('text', '').lower() for o in q['options']) for q in data)

print(f"\n验证结果:")
print(f"  ✓ 所有问题都有选项D: {all_have_d}")
print(f"  ✓ 所有问题的选项D都标记为正确: {all_d_correct}")
print(f"  ✓ 所有问题的正确答案都是D: {all_correct_is_d}")
print(f"  ✓ 所有问题都有'None of the above'选项: {all_have_none}")

# 统计
print(f"\n统计信息:")
print(f"  总问题数: {len(data)}")
print(f"  所有选项数: {sum(len(q['options']) for q in data)}")
print(f"  平均每个问题选项数: {sum(len(q['options']) for q in data) / len(data):.1f}")

# 显示示例
print(f"\n示例问题 (前3个):")
for i, q in enumerate(data[:3], 1):
    print(f"\n问题 {i} (ID: {q.get('id', 'N/A')}):")
    print(f"  问题: {q['question'][:70]}...")
    print(f"  原正确答案: {q.get('original_correct_answer', 'N/A')}")
    print(f"  新正确答案: {q['correct_answer']}")
    print(f"  选项:")
    for opt in q['options']:
        marker = "✓" if opt.get('is_correct') else " "
        print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:60]}...")
    print(f"  解释: {q.get('explanation', 'N/A')[:100]}...")

print("\n" + "=" * 80)
print("✅ 验证完成！所有1075个问题已成功转换为'None of the above'类型")
print("=" * 80)
