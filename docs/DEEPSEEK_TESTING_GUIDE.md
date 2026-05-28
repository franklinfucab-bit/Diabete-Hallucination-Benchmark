# DeepSeek API 测试指南

使用 DeepSeek API 测试你的基准数据集。

## 设置

### 1. 获取 DeepSeek API 密钥

1. 访问 [DeepSeek API 网站](https://platform.deepseek.com/)
2. 注册/登录账户
3. 获取 API 密钥

### 2. 设置 API 密钥

**方法 1: 环境变量（推荐）**
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Windows CMD
set DEEPSEEK_API_KEY=your_api_key_here

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

**方法 2: 使用参数**
```bash
python test_with_deepseek.py --api-key your_api_key_here
```

### 3. 安装依赖

```bash
pip install requests
```

## 使用方法

### 基本用法

**测试二进制基准（幻觉检测）:**
```bash
python test_with_deepseek.py --benchmark-type binary --max-samples 10
```

**测试多选题基准:**
```bash
python test_with_deepseek.py --benchmark-type multiple-choice --max-samples 10
```

**测试两种基准:**
```bash
python test_with_deepseek.py --benchmark-type both --max-samples 10
```

### 完整参数

```bash
python test_with_deepseek.py \
    --benchmark-type both \
    --model deepseek-chat \
    --max-samples 50 \
    --delay 1.0 \
    --api-key your_key_here
```

**参数说明:**
- `--benchmark-type`: 基准类型 (binary, multiple-choice, both)
- `--model`: DeepSeek 模型 (deepseek-chat, deepseek-reasoner)
- `--max-samples`: 最大测试样本数（用于快速测试）
- `--delay`: API 调用间隔（秒，避免速率限制）
- `--api-key`: API 密钥（可选，如果设置了环境变量）

## 示例

### 示例 1: 快速测试（10 个样本）

```bash
python test_with_deepseek.py --benchmark-type binary --max-samples 10
```

输出:
```
使用 DeepSeek 模型: deepseek-chat
测试 10 个样本...
[进度条显示]
评估结果...
[报告显示]
```

### 示例 2: 完整测试（所有样本）

```bash
python test_with_deepseek.py --benchmark-type both --delay 1.5
```

**注意:** 完整测试 1075 个样本可能需要较长时间（约 18-27 分钟，取决于延迟设置）

### 示例 3: 使用推理模型

```bash
python test_with_deepseek.py --model deepseek-reasoner --max-samples 20
```

## 输出结果

测试完成后，结果保存在 `results/` 目录:

1. **JSON 文件**: 详细指标数据
   - `deepseek_binary_YYYYMMDD_HHMMSS.json`
   - `deepseek_mc_YYYYMMDD_HHMMSS.json`

2. **报告文件**: 人类可读的报告
   - `deepseek_binary_report_YYYYMMDD_HHMMSS.txt`
   - `deepseek_mc_report_YYYYMMDD_HHMMSS.txt`

## 速率限制和成本

### API 速率限制
- DeepSeek API 可能有速率限制
- 建议设置 `--delay 1.0` 或更高（1-2 秒）
- 如果遇到 429 错误，增加延迟时间

### 成本估算
- 每个问题大约消耗 100-500 tokens
- 1075 个问题大约需要 100,000 - 500,000 tokens
- 具体成本请查看 DeepSeek 定价页面

## 故障排除

### 错误: API 密钥未找到
```
错误: 未找到 DeepSeek API 密钥
```
**解决:** 设置环境变量或使用 `--api-key` 参数

### 错误: 请求超时
```
TimeoutError: ...
```
**解决:** 
- 检查网络连接
- 增加超时时间（修改 `deepseek_tester.py` 中的 `timeout=30`）

### 错误: 速率限制
```
429 Too Many Requests
```
**解决:** 增加 `--delay` 参数值（例如 `--delay 2.0`）

### 错误: 模块未找到
```
ModuleNotFoundError: No module named 'requests'
```
**解决:** 运行 `pip install requests`

## 最佳实践

1. **先小规模测试**: 使用 `--max-samples 10` 测试少量样本
2. **检查结果质量**: 查看报告，确认模型判断合理
3. **调整参数**: 根据需要调整模型类型和延迟
4. **保存结果**: 结果自动保存，可以用于后续分析
5. **批量处理**: 对于大量数据，考虑分批处理

## 结果解读

### 二进制基准指标

- **Accuracy (准确率)**: 模型正确判断的比例
- **Precision (精确率)**: 模型标记为幻觉的答案中，真正是幻觉的比例
- **Recall (召回率)**: 所有真正的幻觉中，被模型检测到的比例
- **F1 Score**: 精确率和召回率的调和平均

### 多选题基准指标

- **Accuracy**: 正确回答的问题比例
- **Hallucination Avoidance Rate**: 避免选择幻觉选项的比例
- **False Positive Rate**: 选择幻觉选项的比例

## 下一步

测试完成后，你可以:
1. 查看结果报告
2. 分析模型性能
3. 与你的导师分享结果
4. 根据结果调整基准

## 支持

如果遇到问题:
1. 检查 API 密钥是否正确
2. 确认网络连接正常
3. 查看错误消息
4. 参考 DeepSeek API 文档
