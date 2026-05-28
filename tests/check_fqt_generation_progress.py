"""Check progress of FQT generation"""
import json
from pathlib import Path

file_path = Path("output/fake_questions_test_benchmark.jsonl")

if not file_path.exists():
    print("File not found yet. Generation may still be in progress.")
    exit(0)

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print("Fake Questions Test Benchmark Progress")
print("=" * 80)
print(f"\nTotal questions: {len(data)}")
print(f"Target: 100 questions (10 existing + 90 new)")
print(f"Progress: {len(data)}/100 ({len(data)}%)")

if len(data) > 0:
    print(f"\nID range: {min(q.get('id', 0) for q in data)} - {max(q.get('id', 0) for q in data)}")
    
    # Count by source
    existing = [q for q in data if q.get('id', 0) <= 10]
    new = [q for q in data if q.get('id', 0) > 10]
    
    print(f"\nBreakdown:")
    print(f"  - Original 10 questions: {len(existing)}")
    print(f"  - Newly generated: {len(new)}")
    
    if new:
        print(f"\nLatest generated question:")
        latest = new[-1]
        print(f"  ID: {latest.get('id')}")
        print(f"  Question: {latest.get('question', '')[:80]}...")
        print(f"  Inspired by real question ID: {latest.get('metadata', {}).get('inspired_by_real_question_id', 'N/A')}")

print("\n" + "=" * 80)
