"""
run_inference.py
----------------
Reproducibility script for executing medical hallucination benchmarks across local LLMs.
Handles API communication, zero-shot prompting, and regex-based answer extraction.
Used on SSH to run the benchmark (Ollama local API, port 11434).
"""

import http.client
import json
import re
import os
import time
from pathlib import Path

# --- Configuration (relative paths; run from dir that has data/ and results/) ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_FILE = BASE_DIR / "data" / "1000q_core_combined_test_ready.jsonl"
RESULTS_DIR = BASE_DIR / "results"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "inference_run.log"

MODELS = ["qwen2.5:7b", "llama3.1:8b", "mistral:latest", "deepseek-r1:7b", "gemma:7b"]

def extract_answer(text):
    """
    Regex parsing to extract the final multiple-choice letter.
    Strips <think> tags from models like DeepSeek-R1, then finds last A/B/C/D.
    """
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    matches = re.findall(r"\b([A-D])\b", clean_text)
    return matches[-1] if matches else "N/A"

def format_options(options_list):
    """Parses standard medical MCQs (option_id, text) into a clean text block."""
    formatted = []
    for opt in options_list:
        letter = opt.get("option_id", "")
        text = opt.get("text", "")
        formatted.append(f"{letter}. {text}")
    return "\n".join(formatted)

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        print(f"Input not found: {INPUT_FILE}. Run from a dir that has data/1000q_core_combined_test_ready.jsonl")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f if line.strip()]

    for model in MODELS:
        results = []
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=600)

        for i, data in enumerate(test_set):
            label = data.get("correct_answer")
            if label is None:
                continue
            opts = format_options(data.get("options", []))
            prompt = (
                "Context: You are a medical expert. Answer with the letter only.\n"
                f"Question: {data['question']}\nOptions:\n{opts}\n\nAnswer (A, B, C, or D):"
            )
            try:
                os.environ['no_proxy'] = 'localhost,127.0.0.1'
                body = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}})
                conn.request("POST", "/api/generate", body, {"Content-Type": "application/json"})
                resp = json.loads(conn.getresponse().read().decode("utf-8"))
                pred = extract_answer(resp.get("response", ""))
                results.append({
                    "id": data.get("id", i),
                    "category": data.get("test_type", "Unknown"),
                    "pred": pred,
                    "label": label,
                    "correct": pred == label
                })
            except Exception as e:
                time.sleep(2)
                conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=600)

        out_name = f"results_{model.replace(':', '_')}.json"
        with open(RESULTS_DIR / out_name, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  {model}: {sum(r['correct'] for r in results)}/{len(results)} -> {RESULTS_DIR / out_name}")

if __name__ == "__main__":
    main()
