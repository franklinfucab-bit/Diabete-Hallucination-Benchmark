# "None of the Above" 基准生成指南

生成特殊的多选题基准，用于测试模型识别无关信息的能力。

## 概述

这个基准包含多选题，其中：
- **所有选项（A, B, C）都是错误的**
- **正确答案是 D: "None of the above"（以上都不是）**
- **用于测试模型是否能识别所有选项都不正确**

## 用途

这种类型的题目测试：
1. **无关信息识别** - 模型能否识别所有选项都不相关或错误
2. **逻辑推理** - 模型能否推断出"以上都不是"是正确的
3. **医学知识深度** - 模型是否真正理解为什么所有选项都错误

## 使用方法

### 基本用法

```bash
# 生成10个问题（默认）
python generate_none_of_above_benchmark.py

# 生成指定数量的问题
python generate_none_of_above_benchmark.py --num-questions 20
```

### 自定义主题

```bash
# 指定主题
python generate_none_of_above_benchmark.py \
    --topics "糖尿病饮食" "胰岛素注射" "血糖监测" \
    --num-questions 15
```

### 完整参数

```bash
python generate_none_of_above_benchmark.py \
    --topics "主题1" "主题2" "主题3" \
    --num-questions 10 \
    --model deepseek-chat \
    --output output/my_none_of_above.jsonl \
    --api-key your_key_here
```

**参数说明:**
- `--topics`: 主题列表（默认: 5个常见主题）
- `--num-questions`: 要生成的问题数量（默认: 10）
- `--model`: DeepSeek 模型 (deepseek-chat, deepseek-reasoner)
- `--output`: 输出文件路径
- `--api-key`: API 密钥（可选，如果设置了环境变量）

## 输出格式

生成的基准文件格式：

```json
{
  "id": 0,
  "question": "关于糖尿病饮食，以下哪个说法是正确的？",
  "options": [
    {
      "option_id": "A",
      "text": "糖尿病患者应该完全避免所有碳水化合物",
      "is_correct": false
    },
    {
      "option_id": "B",
      "text": "糖尿病患者可以无限制地吃糖",
      "is_correct": false
    },
    {
      "option_id": "C",
      "text": "糖尿病患者不需要控制饮食",
      "is_correct": false
    },
    {
      "option_id": "D",
      "text": "None of the above",
      "is_correct": true
    }
  ],
  "correct_answer": "D",
  "ground_truth": "None of the above",
  "explanation": "所有选项都包含常见的糖尿病饮食误解...",
  "topic": "糖尿病饮食管理",
  "type": "none_of_above",
  "metadata": {
    "generated_by": "deepseek",
    "model": "deepseek-chat",
    "generation_timestamp": "2024-01-01T12:00:00",
    "test_purpose": "测试模型识别无关信息的能力"
  }
}
```

## 特点

### 选项设计原则

1. **错误选项（A, B, C）**:
   - 与问题主题相关但明显错误
   - 包含常见的医学误解
   - 具有迷惑性但可以被识别为错误
   - 不应该包含任何正确信息

2. **正确答案（D）**:
   - 始终是 "None of the above"
   - 表示所有选项都不正确

### 测试场景

这种基准特别适合测试：
- 模型是否会被看似相关但错误的选项误导
- 模型是否能识别"以上都不是"作为有效答案
- 模型对医学知识的理解深度

## 示例

### 示例 1: 生成10个问题

```bash
python generate_none_of_above_benchmark.py --num-questions 10
```

输出：
```
================================================================================
生成 'None of the above' 类型多选题基准
================================================================================
模型: deepseek-chat
目标问题数: 10
主题: 糖尿病饮食管理, 血糖监测, 胰岛素使用, 并发症预防, 运动建议

[1/10] 生成问题 - 主题: 糖尿病饮食管理... ✓
[2/10] 生成问题 - 主题: 血糖监测... ✓
...
```

### 示例 2: 自定义主题

```bash
python generate_none_of_above_benchmark.py \
    --topics "糖尿病并发症" "血糖控制" \
    --num-questions 5
```

## 使用生成的基准

生成后，你可以：

1. **使用测试脚本测试模型**:
```bash
# 需要修改测试脚本以支持这种格式
python test_with_deepseek.py --benchmark-type multiple-choice \
    --benchmark-file output/none_of_above_benchmark.jsonl
```

2. **手动审查**:
   - 检查生成的问题质量
   - 验证所有选项确实都是错误的
   - 确认"None of the above"是唯一正确答案

3. **添加到主基准**:
   - 可以将这些问题添加到主多选题基准
   - 或作为独立的测试集

## 注意事项

### API 限制

- **速率限制**: 建议在请求之间添加延迟（代码中已设置1.5秒）
- **Token 消耗**: 每个问题生成消耗较多 tokens
- **成本**: 注意 API 调用成本

### 质量保证

- **人工审查**: 生成的问题需要人工审查
- **验证逻辑**: 确保所有选项确实都是错误的
- **医学准确性**: 验证错误选项确实包含误解

### 最佳实践

1. **小批量测试**: 先生成少量问题测试
2. **审查质量**: 检查生成的问题是否符合要求
3. **调整提示**: 如果质量不佳，可能需要调整生成提示
4. **保存原始响应**: 保留 API 原始响应以便调试

## 故障排除

### 错误: JSON 解析失败

如果 DeepSeek 返回的格式不是标准 JSON，代码会尝试提取。如果仍然失败，检查 `raw_response` 字段。

### 错误: 选项结构不正确

代码会自动修复选项结构，确保：
- 选项 D 是 "None of the above"
- 选项 D 标记为正确
- 其他选项标记为错误

### 错误: 生成的问题质量不佳

- 尝试使用 `deepseek-reasoner` 模型（推理能力更强）
- 调整 temperature 参数
- 修改生成提示

## 与其他基准的区别

| 特征 | 标准多选题 | None of the Above |
|------|-----------|-------------------|
| 正确答案 | 选项 A/B/C/D 之一 | 总是选项 D |
| 错误选项 | 部分相关但错误 | 全部错误且相关 |
| 测试重点 | 知识准确性 | 无关信息识别 |
| 难度 | 中等 | 较高 |

## 下一步

生成基准后：
1. 审查生成的问题
2. 使用测试脚本评估模型
3. 分析模型在"None of the above"类型题目上的表现
4. 与标准多选题基准结果对比
