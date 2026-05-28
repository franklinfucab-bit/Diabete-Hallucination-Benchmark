import json

with open(r'output\converted_none_of_above_benchmark.jsonl', 'r', encoding='utf-8') as f:
    data = [json.loads(l) for l in f]

print(f"成功生成 {len(data)} 个问题\n")
print("=" * 80)

for i, q in enumerate(data[:3], 1):
    print(f"\n问题 {i}:")
    print(f"  问题: {q['question']}")
    print(f"  原正确答案: {q.get('original_correct_answer', 'N/A')}")
    print(f"  新正确答案: {q['correct_answer']}")
    print(f"  选项:")
    for opt in q['options']:
        marker = "✓" if opt.get('is_correct') else " "
        print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:70]}...")
    print(f"  解释: {q.get('explanation', 'N/A')[:200]}...")

print(f"\n总共: {len(data)} 个问题")
