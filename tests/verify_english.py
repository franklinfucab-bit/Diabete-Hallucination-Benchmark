"""验证基准文件是否全部为英文"""
import json
from pathlib import Path
import re

file_path = Path("output/converted_none_of_above_benchmark.jsonl")

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print("Verifying English-only content")
print("=" * 80)
print(f"Total questions: {len(data)}")

# 检查中文
chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
issues = []

for i, item in enumerate(data):
    # 检查question
    if chinese_pattern.search(item.get('question', '')):
        issues.append(f"Question {i+1}: question contains Chinese")
    
    # 检查explanation
    if chinese_pattern.search(item.get('explanation', '')):
        issues.append(f"Question {i+1}: explanation contains Chinese")
    
    # 检查options
    for opt in item.get('options', []):
        if chinese_pattern.search(opt.get('text', '')):
            issues.append(f"Question {i+1}, Option {opt.get('option_id')}: text contains Chinese")
    
    # 检查metadata
    if 'metadata' in item:
        for key, value in item['metadata'].items():
            if isinstance(value, str) and chinese_pattern.search(value):
                issues.append(f"Question {i+1}: metadata.{key} contains Chinese")

if issues:
    print(f"\nFound {len(issues)} issues with Chinese content:")
    for issue in issues[:10]:  # 只显示前10个
        print(f"  - {issue}")
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")
else:
    print("\n✓ All content is in English!")

# 显示示例
print(f"\nSample question:")
sample = data[0]
print(f"  Question: {sample['question'][:70]}...")
print(f"  Explanation: {sample.get('explanation', 'N/A')}")
print(f"  Test purpose: {sample.get('metadata', {}).get('test_purpose', 'N/A')}")

print("\n" + "=" * 80)
