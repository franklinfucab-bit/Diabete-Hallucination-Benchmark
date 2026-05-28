"""移除conversion_timestamp字段"""
import json
from pathlib import Path

file_path = Path("C:/Users/Frank/Diabete Hallucination Benchmark/output/converted_none_of_above_benchmark.jsonl")

print("Removing conversion_timestamp from all questions...")

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} questions")

# 移除timestamp
for item in data:
    if 'metadata' in item and 'conversion_timestamp' in item['metadata']:
        del item['metadata']['conversion_timestamp']

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"Removed conversion_timestamp from all questions")
print(f"Saved to: {file_path}")
