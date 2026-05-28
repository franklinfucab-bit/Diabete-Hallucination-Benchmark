# DeepSeek API 生成和检查指南

使用 DeepSeek API 生成新问题或检查现有问题。

## 功能

1. **生成问题** - 使用 DeepSeek API 生成新的糖尿病相关问题
2. **检查问题** - 使用 DeepSeek API 检查现有问题是否包含幻觉

## 设置

### 1. 获取 API 密钥

访问 [DeepSeek Platform](https://platform.deepseek.com/) 获取 API 密钥。

### 2. 设置环境变量

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Windows CMD
set DEEPSEEK_API_KEY=your_api_key_here

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

## 使用方法

### 模式 1: 生成问题

使用 DeepSeek API 生成新的糖尿病相关问题。

#### 基本用法

```bash
# 生成单个主题的问题
python generate_with_deepseek.py generate \
    --topics "糖尿病饮食管理" \
    --num-questions 3

# 生成多个主题的问题
python generate_with_deepseek.py generate \
    --topics "糖尿病饮食管理" "胰岛素使用" "血糖监测" \
    --num-questions 2
```

#### 从文件读取主题

创建 `topics.txt`:
```
糖尿病饮食管理
胰岛素使用
血糖监测
并发症预防
运动建议
```

然后运行:
```bash
python generate_with_deepseek.py generate \
    --topics-file topics.txt \
    --num-questions 2 \
    --output output/deepseek_generated.jsonl
```

#### 完整参数

```bash
python generate_with_deepseek.py generate \
    --topics "主题1" "主题2" \
    --num-questions 3 \
    --model deepseek-chat \
    --output output/my_questions.jsonl \
    --api-key your_key_here
```

**参数说明:**
- `--topics`: 主题列表（空格分隔）
- `--topics-file`: 包含主题的文件（每行一个）
- `--num-questions`: 每个主题生成的问题数
- `--model`: DeepSeek 模型 (deepseek-chat, deepseek-reasoner)
- `--output`: 输出文件路径
- `--api-key`: API 密钥（可选，如果设置了环境变量）

### 模式 2: 检查问题

使用 DeepSeek API 检查现有问题是否包含幻觉。

#### 基本用法

```bash
# 检查二进制基准
python generate_with_deepseek.py check \
    --input output/diabetes_hallucination_benchmark.jsonl

# 检查自定义文件
python generate_with_deepseek.py check \
    --input my_questions.jsonl \
    --check-output checked_results.jsonl
```

#### 完整参数

```bash
python generate_with_deepseek.py check \
    --input output/diabetes_hallucination_benchmark.jsonl \
    --check-output output/deepseek_checked.jsonl \
    --model deepseek-reasoner \
    --api-key your_key_here
```

**参数说明:**
- `--input`: 输入文件路径（JSONL格式）
- `--check-output`: 检查结果输出文件
- `--model`: DeepSeek 模型
- `--api-key`: API 密钥

## 输出格式

### 生成的问题格式

```json
{
  "id": 0,
  "question": "什么是糖尿病？",
  "answer": "糖尿病是一种慢性疾病...",
  "topic": "糖尿病基础知识",
  "generated_by": "deepseek",
  "model": "deepseek-chat",
  "metadata": {
    "generation_timestamp": "2024-01-01T12:00:00",
    "raw_response": "..."
  }
}
```

### 检查结果格式

```json
{
  "id": 0,
  "question": "什么是糖尿病？",
  "answer": "糖尿病是一种慢性疾病...",
  "is_hallucination": false,
  "deepseek_response": "CORRECT",
  "model": "deepseek-chat",
  "check_timestamp": "2024-01-01T12:00:00",
  "original_data": {...}
}
```

## 示例

### 示例 1: 生成5个关于饮食的问题

```bash
python generate_with_deepseek.py generate \
    --topics "糖尿病饮食管理" \
    --num-questions 5 \
    --output output/diet_questions.jsonl
```

### 示例 2: 检查现有基准

```bash
python generate_with_deepseek.py check \
    --input output/diabetes_hallucination_benchmark.jsonl \
    --check-output results/deepseek_validation.jsonl
```

### 示例 3: 批量生成多个主题

创建 `topics.txt`:
```
血糖监测
胰岛素注射
并发症预防
运动建议
```

运行:
```bash
python generate_with_deepseek.py generate \
    --topics-file topics.txt \
    --num-questions 3 \
    --model deepseek-reasoner
```

## 工作流程建议

### 工作流程 1: 生成新问题

1. 准备主题列表
2. 使用 DeepSeek 生成问题
3. 人工审查生成的问题
4. 将高质量问题添加到基准

### 工作流程 2: 验证现有问题

1. 使用 DeepSeek 检查现有问题
2. 分析检查结果
3. 标记可能有问题的项目
4. 人工审查标记的项目

### 工作流程 3: 混合使用

1. 从现有数据集开始
2. 使用 DeepSeek 检查质量
3. 识别知识空白
4. 使用 DeepSeek 生成新问题填补空白
5. 验证新生成的问题

## 注意事项

### API 限制

- **速率限制**: DeepSeek API 可能有速率限制
- **Token 限制**: 注意每次调用的 token 消耗
- **成本**: 生成和检查都会产生 API 成本

### 质量保证

- **人工审查**: 自动生成的问题需要人工审查
- **医学准确性**: DeepSeek 的回答可能不完全准确
- **验证**: 建议使用多个来源验证医学信息

### 最佳实践

1. **小批量测试**: 先测试少量问题
2. **检查质量**: 审查生成的问题质量
3. **调整提示**: 根据需要调整生成提示
4. **保存原始响应**: 保留 API 的原始响应以便调试

## 故障排除

### 错误: API 密钥未找到
```
错误: 未找到 DeepSeek API 密钥
```
**解决**: 设置环境变量或使用 `--api-key` 参数

### 错误: JSON 解析失败
生成的问题可能不是标准 JSON 格式，代码会尝试从文本中提取。

### 错误: 生成失败
检查网络连接和 API 密钥有效性。

## 与现有基准集成

生成的问题可以：
1. 直接添加到基准数据集
2. 使用 `create_benchmark.py` 转换为基准格式
3. 使用 `test_with_deepseek.py` 进行测试

## 下一步

- 生成问题后，使用验证脚本检查质量
- 将高质量问题添加到主基准数据集
- 使用检查功能验证整个基准的质量
