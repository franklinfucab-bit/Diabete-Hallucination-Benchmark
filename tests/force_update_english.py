"""强制更新所有explanation和metadata为英文"""
import json
from pathlib import Path

file_path = Path("C:/Users/Frank/Diabete Hallucination Benchmark/output/converted_none_of_above_benchmark.jsonl")

print("Reading file...")
with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} questions")
print("Updating all explanations and metadata to English...")

updated = 0
for item in data:
    # 强制更新explanation为英文
    item['explanation'] = "All options (A, B, C) contain incorrect information or medical misconceptions. Therefore, the correct answer is 'None of the above'."
    
    # 强制更新metadata
    if 'metadata' in item:
        item['metadata']['test_purpose'] = "Test model ability to identify irrelevant information (converted from existing benchmark)"
    
    updated += 1

print(f"Updated {updated} questions")

# 保存
print("Saving...")
with open(file_path, 'w', encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"Done! Saved {len(data)} questions to {file_path}")
