"""查看高级基准文件"""
import json
from pathlib import Path

file_path = Path("output/advanced_none_of_above_benchmark.jsonl")

if not file_path.exists():
    print("文件不存在!")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print(f"高级 None of the Above 基准 - {len(data)} 个问题")
print("=" * 80)

for i, q in enumerate(data, 1):
    print(f"\n问题 {i}:")
    print(f"  主题: {q.get('topic', 'N/A')}")
    print(f"  问题: {q['question']}")
    print(f"  选项:")
    for opt in q['options']:
        marker = "✓" if opt.get('is_correct') else " "
        hall_type = f" [{opt.get('type', 'N/A')}]" if opt.get('type') else ""
        is_hall = " [HALLUCINATION]" if opt.get('is_hallucination') else ""
        print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:80]}...{hall_type}{is_hall}")
    
    if 'explanation' in q:
        print(f"  解释: {q['explanation'][:100]}...")

# 统计
print("\n" + "=" * 80)
print("幻觉类型统计:")
hall_types = {}
for q in data:
    for opt in q['options']:
        if opt.get('type') and opt.get('option_id') != 'D':
            t = opt.get('type', 'unknown')
            hall_types[t] = hall_types.get(t, 0) + 1

for t, count in sorted(hall_types.items()):
    print(f"  {t}: {count}")
