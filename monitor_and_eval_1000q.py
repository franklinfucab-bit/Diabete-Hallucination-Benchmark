"""
Monitor FCT generation progress and automatically run concurrent evaluation when complete
"""
import json
import os
import time
import subprocess
from pathlib import Path

TARGET_FILE = "output/1000q_diabetes_fct_benchmark_v2.jsonl"
TARGET_COUNT = 1000
CHECK_INTERVAL = 30  # Check every 30 seconds
MAX_WAIT_TIME = 7200  # Maximum wait time: 2 hours

def count_questions(filepath):
    """Count questions in JSONL file"""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            count = sum(1 for line in f if line.strip())
        return count
    except:
        return 0

def run_evaluation():
    """Run concurrent evaluation"""
    print("\n" + "=" * 80)
    print("Generation Complete! Starting Concurrent Evaluation...")
    print("=" * 80)
    
    cmd = [
        "python", 
        "Concur_evaluate_benchmark_quality.py",
        "FCT",
        "diabetes",
        TARGET_FILE,
        "--no-resume",
        "--workers", "5"
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def main():
    print("=" * 80)
    print("Monitoring FCT Generation Progress")
    print("=" * 80)
    print(f"Target file: {TARGET_FILE}")
    print(f"Target questions: {TARGET_COUNT}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("=" * 80)
    
    start_time = time.time()
    last_count = 0
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > MAX_WAIT_TIME:
            print(f"\n[WARNING] Maximum wait time ({MAX_WAIT_TIME}s) exceeded!")
            print("Stopping monitoring. Please check generation manually.")
            break
        
        current_count = count_questions(TARGET_FILE)
        
        if current_count > last_count:
            rate = current_count / elapsed if elapsed > 0 else 0
            remaining = TARGET_COUNT - current_count
            eta = remaining / rate if rate > 0 else 0
            
            print(f"\n[{time.strftime('%H:%M:%S')}] Progress: {current_count}/{TARGET_COUNT} questions "
                  f"({current_count/TARGET_COUNT*100:.1f}%)")
            print(f"  Rate: {rate:.2f} questions/sec")
            if eta > 0:
                print(f"  ETA: {eta/60:.1f} minutes")
            
            last_count = current_count
        
        if current_count >= TARGET_COUNT:
            print(f"\n[SUCCESS] All {TARGET_COUNT} questions generated!")
            print(f"Total time: {elapsed/60:.1f} minutes")
            
            # Wait a bit for file to be fully written
            time.sleep(5)
            
            # Verify final count
            final_count = count_questions(TARGET_FILE)
            if final_count >= TARGET_COUNT:
                # Run evaluation
                success = run_evaluation()
                if success:
                    print("\n[SUCCESS] Evaluation completed!")
                else:
                    print("\n[ERROR] Evaluation failed!")
                break
            else:
                print(f"[WARNING] File count ({final_count}) doesn't match target ({TARGET_COUNT})")
                print("Waiting for file to be finalized...")
                time.sleep(10)
                continue
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user.")
        current = count_questions(TARGET_FILE)
        print(f"Current progress: {current}/{TARGET_COUNT} questions")
