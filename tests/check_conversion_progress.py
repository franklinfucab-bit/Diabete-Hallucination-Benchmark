"""检查转换进度"""
import json
from pathlib import Path
import time

output_file = Path("output/converted_none_of_above_benchmark.jsonl")
input_file = Path("output/diabetes_multiple_choice_benchmark.jsonl")

# 计算总数
total = 0
if input_file.exists():
    with open(input_file, 'r', encoding='utf-8') as f:
        total = sum(1 for _ in f)

# 检查已转换数量
converted = 0
if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        converted = sum(1 for _ in f)

print("=" * 80)
print("转换进度监控")
print("=" * 80)
print(f"总问题数: {total}")
print(f"已转换: {converted}")
if total > 0:
    progress = (converted / total) * 100
    print(f"进度: {progress:.1f}%")
    remaining = total - converted
    print(f"剩余: {remaining} 个问题")
    
    # 估算剩余时间（假设每个问题2秒）
    if converted > 0 and converted < total:
        estimated_seconds = remaining * 2
        estimated_minutes = estimated_seconds / 60
        print(f"预计剩余时间: {estimated_minutes:.1f} 分钟")
else:
    print("无法确定总数")

print("=" * 80)
print(f"输出文件: {output_file}")
print(f"文件存在: {output_file.exists()}")

if output_file.exists() and converted > 0:
    print(f"\n最后转换的问题:")
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            print(f"  ID: {last.get('id', 'N/A')}")
            print(f"  问题: {last.get('question', 'N/A')[:60]}...")
