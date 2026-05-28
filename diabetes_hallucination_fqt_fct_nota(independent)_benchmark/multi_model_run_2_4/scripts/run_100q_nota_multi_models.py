"""
Run the 100q NOTA FCT-convert benchmark against 5 Ollama models.
"""
import http.client
import json
import re
import os
from datetime import datetime
from pathlib import Path

# --- Config ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_FILE = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"
RESULTS_DIR = BASE_DIR / "results_100q_nota"
LOG_FILE = BASE_DIR / "logs" / "100q_nota_run.log"
OLLAMA_PORT = 11434

MODELS = [
    "deepseek-r1:7b",
    "mistral:latest",
    "llama3.1:8b",
    "gemma:7b",
    "qwen2.5:7b",
]

def extract_answer(text):
    """?????,?????? A/B/C/D ???"""
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    matches = re.findall(r"\b([A-D])\b", clean_text)
    return matches[-1] if matches else "N/A"

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ????????
    if not INPUT_FILE.exists():
        print(f"? ???????: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f if line.strip()]

    n_questions = len(test_set)
    print(f"? ??? {n_questions} ???")

    for model in MODELS:
        with open(LOG_FILE, "a", encoding="utf-8") as logf:
            logf.write(f"\n[{datetime.now().isoformat()}] >>> ????: {model} <<<\n")

        print(f"\n?? ?????: {model} ({n_questions} ?)...")
        results = []
        # ?? 180s ???? DeepSeek ?????
        conn = http.client.HTTPConnection("127.0.0.1", OLLAMA_PORT, timeout=180)

        for i, data in enumerate(test_set):
            prompt = (
                "Context: You are a medical expert. Answer strictly with the letter.\n\n"
                f"Question: {data['question']}\nOptions:\n"
                + "\n".join([f"{k}. {v}" for k, v in data["options"].items()])
                + "\n\nAnswer (A, B, C, or D):"
            )
            try:
                # ??????,?????????
                os.environ['no_proxy'] = 'localhost,127.0.0.1'
                
                body = json.dumps({
                    "model": model, 
                    "prompt": prompt, 
                    "stream": False, 
                    "options": {"temperature": 0}
                })
                conn.request("POST", "/api/generate", body, {"Content-Type": "application/json"})
                resp_raw = conn.getresponse().read().decode("utf-8")
                resp = json.loads(resp_raw)
                
                raw_res = resp.get("response", "")
                pred = extract_answer(raw_res)
                
                results.append({
                    "id": data.get("id", i),
                    "pred": pred,
                    "label": data["answer"],
                    "correct": pred == data["answer"],
                })
                
                if (i + 1) % 10 == 0:
                    with open(LOG_FILE, "a", encoding="utf-8") as logf:
                        logf.write(f"[{datetime.now().strftime('%H:%M:%S')}] {model} | {i+1}/{n_questions} | pred: {pred}\n")
                    print(f"  ??: {i+1}/{n_questions}")
                    
            except Exception as e:
                with open(LOG_FILE, "a", encoding="utf-8") as logf:
                    logf.write(f"? Error Q{i}: {e}\n")
                # ???????
                conn = http.client.HTTPConnection("127.0.0.1", OLLAMA_PORT, timeout=180)

        # ????????
        correct = sum(1 for r in results if r["correct"])
        acc = (correct / n_questions * 100) if n_questions else 0
        print(f"?? {model} ??! ???: {acc:.1f}% ({correct}/{n_questions})")

        model_safe = model.replace(":", "_")
        out_path = RESULTS_DIR / f"results_{model_safe}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        # ??????????
        try:
            conn.request("POST", "/api/generate", json.dumps({"model": model, "keep_alive": 0}))
            conn.getresponse().read() # ??????
            conn.close()
        except:
            pass

    print(f"\n? ????! ??: {LOG_FILE}")

if __name__ == "__main__":
    main()