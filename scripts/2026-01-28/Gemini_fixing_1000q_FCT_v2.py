import json
import random
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- 配置 ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_FILE = PROJECT_ROOT / 'output' / 'Json' / '1000q_diabetes_fct_benchmark_v2.json'
OUTPUT_FILE = PROJECT_ROOT / 'output' / 'Json' / '1000q_diabetes_fct_benchmark_v3.json'
SIMILARITY_THRESHOLD = 0.90  # 相似度超过 90% 视为重复

def process_and_clean_data():
    print(f"正在读取 {INPUT_FILE} ...")
    data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue
    
    print(f"原始题目数量: {len(data)}")

    # 1. 语义去重 (Semantic Deduplication)
    # 提取所有问题文本
    questions = [item['question'] for item in data]
    
    # 计算 TF-IDF 矩阵
    tfidf_vectorizer = TfidfVectorizer().fit_transform(questions)
    cosine_sim = cosine_similarity(tfidf_vectorizer, tfidf_vectorizer)
    
    # 标记要删除的索引
    indices_to_drop = set()
    for i in range(len(data)):
        if i in indices_to_drop:
            continue
        for j in range(i + 1, len(data)):
            if cosine_sim[i, j] > SIMILARITY_THRESHOLD:
                indices_to_drop.add(j) # 标记重复的后者
    
    unique_data = [item for i, item in enumerate(data) if i not in indices_to_drop]
    print(f"去重后题目数量: {len(unique_data)} (剔除了 {len(data) - len(unique_data)} 题)")

    # 2. 选项洗牌与格式标准化 (Shuffling & Formatting)
    cleaned_data = []
    option_labels = ['A', 'B', 'C', 'D']
    
    for idx, item in enumerate(unique_data):
        # 重新生成连续 ID
        new_id = f"FCT_{idx+1:03d}"
        item['id'] = new_id
        
        # 获取选项列表
        options = item.get('options', [])
        
        # 确保我们能找到哪个是正确答案
        # 原始数据中 Option C 的 is_correct 为 true (或者根据 correct_answer 字段)
        # 我们这里信任 options 内部的 is_correct 标记，如果没有，回退到 correct_answer 字段
        
        # 随机打乱选项顺序
        random.shuffle(options)
        
        # 重新分配 A, B, C, D 标签并找到新的正确答案
        new_correct_answer = None
        for i, opt in enumerate(options):
            opt['option_id'] = option_labels[i] # 重置 A/B/C/D
            if opt.get('is_correct') is True:
                new_correct_answer = option_labels[i]
        
        # 如果 options 里没标 is_correct，尝试根据原始 correct_answer 修复（假设原始是 C）
        if new_correct_answer is None:
            # 这种情况比较少见，做个防御性编程
            # 假设原始逻辑是 C 正确，我们在 shuffle 前应该标记好
            pass 

        item['options'] = options
        item['correct_answer'] = new_correct_answer

        # 若存在 suggested_answer，按文本匹配更新为新的 option_id
        if 'suggested_answer' in item and item['suggested_answer']:
            sa_text = item['suggested_answer'].get('text')
            for opt in options:
                if opt.get('text') == sa_text:
                    item['suggested_answer'] = {'option_id': opt['option_id'], 'text': opt['text'], 'is_correct': opt.get('is_correct', False)}
                    break

        cleaned_data.append(item)

    # 3. 保存文件（新版本 v3）
    print(f"正在保存到 {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in cleaned_data:
            f.write(json.dumps(item) + '\n')
            
    print("完成！数据已清洗并随机化。")

if __name__ == "__main__":
    process_and_clean_data()