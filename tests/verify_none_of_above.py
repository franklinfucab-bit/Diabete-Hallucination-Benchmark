"""验证 None of the above 基准文件"""
import json
from pathlib import Path

file_path = Path("output/none_of_above_benchmark.jsonl")

if not file_path.exists():
    print("文件不存在!")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print("=" * 80)
print("None of the Above 基准文件验证")
print("=" * 80)
print(f"\n总问题数: {len(data)}")
print(f"文件路径: {file_path}")

# 验证每个问题
errors = []
for i, item in enumerate(data):
    # 检查必需字段
    if 'question' not in item:
        errors.append(f"问题 {i}: 缺少 'question' 字段")
    if 'options' not in item:
        errors.append(f"问题 {i}: 缺少 'options' 字段")
    if 'correct_answer' not in item:
        errors.append(f"问题 {i}: 缺少 'correct_answer' 字段")
    
    # 检查选项
    if 'options' in item:
        options = item['options']
        if len(options) != 4:
            errors.append(f"问题 {i}: 应该有4个选项，实际有 {len(options)} 个")
        
        # 检查是否有且仅有一个正确答案
        correct_count = sum(1 for opt in options if opt.get('is_correct', False))
        if correct_count != 1:
            errors.append(f"问题 {i}: 应该有1个正确答案，实际有 {correct_count} 个")
        
        # 检查选项D是否是"None of the above"且正确
        d_option = next((opt for opt in options if opt.get('option_id') == 'D'), None)
        if not d_option:
            errors.append(f"问题 {i}: 缺少选项 D")
        elif not d_option.get('is_correct', False):
            errors.append(f"问题 {i}: 选项 D 应该标记为正确")
        elif 'none of the above' not in d_option.get('text', '').lower():
            errors.append(f"问题 {i}: 选项 D 应该是 'None of the above'")

if errors:
    print("\n发现错误:")
    for error in errors:
        print(f"  - {error}")
else:
    print("\n✓ 所有验证通过!")

# 显示示例
if len(data) > 0:
    print("\n" + "=" * 80)
    print("示例问题:")
    print("=" * 80)
    sample = data[0]
    print(f"\n问题: {sample['question']}")
    print(f"主题: {sample.get('topic', 'N/A')}")
    print(f"正确答案: {sample['correct_answer']}")
    print("\n选项:")
    for opt in sample['options']:
        marker = "✓" if opt.get('is_correct') else " "
        print(f"  {marker} {opt.get('option_id', '?')}. {opt.get('text', '')}")
    
    if 'explanation' in sample:
        print(f"\n解释: {sample['explanation']}")

print("\n" + "=" * 80)
