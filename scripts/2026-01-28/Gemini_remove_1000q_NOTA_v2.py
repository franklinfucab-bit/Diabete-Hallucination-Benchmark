import pandas as pd
import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_dataset():
    base = Path(__file__).resolve().parent.parent.parent  # project root
    input_file = base / "output" / "1000q_diabetes_nota_benchmark_v2.jsonl"
    output_file = base / "output" / "cleaned_diabetes_nota_seeds.jsonl"
    
    print("Loading data...")
    try:
        data = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except:
                    continue
    except FileNotFoundError:
        print(f"Error: file not found {input_file}")
        return

    df = pd.DataFrame(data)
    print(f"Original count: {len(df)}")

    # TF-IDF similarity
    print("Computing TF-IDF similarity...")
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['question'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # 执行去重逻辑 (阈值 0.85)
    kept_indices = []
    dropped_indices = set()
    threshold = 0.85

    print("Deduplicating...")
    for i in range(len(df)):
        if i in dropped_indices:
            continue
        
        kept_indices.append(i)
        
        # 找到所有相似度过高的题目，标记为删除
        similar_indices = np.where(cosine_sim[i] > threshold)[0]
        for idx in similar_indices:
            if idx != i:
                dropped_indices.add(idx)

    # 保存结果
    df_cleaned = df.iloc[kept_indices]
    df_cleaned.to_json(output_file, orient='records', lines=True, force_ascii=False)
    
    print("Done.")
    print(f"Kept: {len(df_cleaned)}")
    print(f"Output: {output_file}")

if __name__ == "__main__":
    clean_dataset()