"""
更新基准文件，将所有中文内容改为英文
"""
import json
from pathlib import Path

input_file = Path("C:/Users/Frank/Diabete Hallucination Benchmark/output/converted_none_of_above_benchmark.jsonl")
output_file = Path("C:/Users/Frank/Diabete Hallucination Benchmark/output/converted_none_of_above_benchmark.jsonl")

print("=" * 80)
print("Updating benchmark to English only")
print("=" * 80)

# 读取所有问题
with open(input_file, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} questions")

# 更新每个问题
updated_count = 0
for item in data:
    updated = False
    
    # 更新explanation为英文
    if item.get('explanation'):
        chinese_explanation = item['explanation']
        # 检查是否包含中文
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in chinese_explanation)
        if has_chinese:
            item['explanation'] = "All options (A, B, C) contain incorrect information or medical misconceptions. Therefore, the correct answer is 'None of the above'."
            updated = True
    
    # 更新metadata中的test_purpose
    if 'metadata' in item and 'test_purpose' in item['metadata']:
        test_purpose = item['metadata']['test_purpose']
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in test_purpose)
        if has_chinese:
            item['metadata']['test_purpose'] = "Test model ability to identify irrelevant information (converted from existing benchmark)"
            updated = True
    
    if updated:
        updated_count += 1

print(f"Updated {updated_count} questions")

# 保存更新后的文件
with open(output_file, 'w', encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\nSaved to: {output_file}")
print("=" * 80)
print("Update complete!")
