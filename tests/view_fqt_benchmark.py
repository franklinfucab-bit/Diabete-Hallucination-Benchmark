"""View Fake Questions Test benchmark"""
import json
from pathlib import Path

file_path = Path("output/fake_questions_test_benchmark.jsonl")

print("=" * 80)
print("Fake Questions Test (FQT) Benchmark")
print("=" * 80)

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"\nTotal questions: {len(data)}\n")

for i, item in enumerate(data, 1):
    print(f"{'='*80}")
    print(f"Question {i} (ID: {item.get('id', 'N/A')})")
    print(f"{'='*80}")
    print(f"\nQuestion: {item['question']}")
    print(f"\nWhy it's fake:")
    print(f"  {item.get('why_fake', 'N/A')}")
    print(f"\nExpected response:")
    print(f"  {item.get('expected_response', 'N/A')}")
    print(f"\nType: {item.get('type', 'N/A')}")
    print(f"Correct answer: {item.get('correct_answer', 'N/A')}")
    print()

print("=" * 80)
print("Summary")
print("=" * 80)
print(f"Total fake questions: {len(data)}")
print(f"All questions marked as fake: {all(item.get('is_fake', False) for item in data)}")
print(f"All have expected responses: {all(item.get('expected_response') for item in data)}")
