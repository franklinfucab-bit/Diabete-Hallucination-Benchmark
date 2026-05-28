"""监控转换进度"""
import json
from pathlib import Path
import time

def check_progress():
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
    print("转换进度")
    print("=" * 80)
    print(f"总问题数: {total}")
    print(f"已转换: {converted}")
    if total > 0:
        progress = (converted / total) * 100
        print(f"进度: {progress:.1f}%")
        remaining = total - converted
        print(f"剩余: {remaining} 个问题")
    print("=" * 80)
    
    return converted, total

if __name__ == "__main__":
    check_progress()
