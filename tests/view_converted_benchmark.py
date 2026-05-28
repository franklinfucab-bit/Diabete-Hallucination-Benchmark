"""查看转换后的基准文件"""
import json
from pathlib import Path

file_path = Path("output/converted_none_of_above_benchmark.jsonl")

if not file_path.exists():
    print("文件不存在!")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print(f"转换后的 None of the Above 基准 - {len(data)} 个问题")
print("=" * 80)

for i, q in enumerate(data[:3], 1):  # 显示前3个
    print(f"\n问题 {i} (ID: {q.get('id', 'N/A')}):")
    print(f"  问题: {q['question']}")
    print(f"  原正确答案: {q.get('original_correct_answer', 'N/A')}")
    print(f"  新正确答案: {q['correct_answer']}")
    print(f"  选项:")
    for opt in q['options']:
        marker = "✓" if opt.get('is_correct') else " "
        opt_type = opt.get('type', 'N/A')
        print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:70]}... [{opt_type}]")
    
    if 'explanation' in q:
        print(f"  解释: {q['explanation']}")

print("\n" + "=" * 80)
print("统计:")
print(f"  总问题数: {len(data)}")
print(f"  所有问题的正确答案都是: D (None of the above)")
