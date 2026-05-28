import http.client
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path

# --- 配置区 ---
# 注意：这里我已经帮你把 qwen2.5:7b 删掉了，直接从 DeepSeek 开始
MODELS = ["deepseek-r1:7b", "mistral:latest", "llama3.1:8b", "gemma:7b"]
INPUT_FILE = "/work/FF/medhalt/300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
OUTPUT_BASE = Path("/work/FF/medhalt")
RESULTS_DIR = OUTPUT_BASE / "results"
LOG_FILE = OUTPUT_BASE / "run_multi_models.log"
OLLAMA_PORT = 11434

def extract_answer(text):
    # 移除 <think> 标签内容
    clean_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # 寻找最后出现的 A, B, C, D
    matches = re.findall(r'\b([A-D])\b', clean_text)
    return matches[-1] if matches else "N/A"

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f if line.strip()][:300]

    for model in MODELS:
        with open(LOG_FILE, "a") as logf:
            logf.write(f"\n[{datetime.now().isoformat()}] >>> 切换至新模型: {model} <<<\n")
        
        results = []
        conn = http.client.HTTPConnection("127.0.0.1", OLLAMA_PORT, timeout=180)

        for i, data in enumerate(test_set):
            prompt = f"Context: You are a medical expert. Answer strictly with the letter.\n\nQuestion: {data['question']}\nOptions:\n" + "\n".join([f"{k}. {v}" for k, v in data['options'].items()]) + "\n\nAnswer (A, B, C, or D):"
            try:
                # 显式发送请求
                body = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}})
                conn.request("POST", "/api/generate", body, {"Content-Type": "application/json"})
                resp = json.loads(conn.getresponse().read().decode("utf-8"))
                
                raw_res = resp.get('response', '')
                pred = extract_answer(raw_res)
                
                results.append({"id": data["id"], "pred": pred, "label": data["answer"], "correct": pred == data["answer"]})
                
                if (i + 1) % 5 == 0:
                    with open(LOG_FILE, "a") as logf:
                        logf.write(f"[{datetime.now().strftime('%H:%M:%S')}] {model} | {i+1}/300 | 预测结果: {pred}\n")
            except Exception as e:
                with open(LOG_FILE, "a") as logf:
                    logf.write(f"❌ Error Q{i}: {e}\n")
                conn = http.client.HTTPConnection("127.0.0.1", OLLAMA_PORT, timeout=180)
        
        # 保存该模型结果
        with open(RESULTS_DIR / f"results_{model.replace(':','_')}.json", "w") as f:
            json.dump(results, f, indent=4)
        
        # 释放显存
        try:
            conn.request("POST", "/api/generate", json.dumps({"model": model, "keep_alive": 0}))
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
