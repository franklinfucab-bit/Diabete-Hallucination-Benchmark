import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_FILE = BASE_DIR / "diabetes_combined_ready.jsonl"

def check_balance():
    trap_count = 0    # User suggested Wrong answer
    control_count = 0 # User suggested Right answer
    total = 0
    
    print(f"{'ID':<10} | {'Suggestion':<10} | {'Truth':<5} | {'Type'}")
    print("-" * 50)

    try:
        with open(INPUT_FILE, 'r') as f:
            for line in f:
                data = json.loads(line)
                if data['task'] == 'FCT':
                    total += 1
                    question_text = data['question']
                    ground_truth = data['answer'] # The correct answer (A, B, C, or D)
                    
                    # Extract the letter the User suggested
                    # Regex looks for "answer is X" or "Answer is X" inside the suggestion
                    match = re.search(r"answer is ([A-D])", question_text, re.IGNORECASE)
                    
                    if match:
                        user_suggestion = match.group(1).upper()
                        
                        if user_suggestion != ground_truth:
                            trap_count += 1
                            row_type = "🪤 TRAP"
                        else:
                            control_count += 1
                            row_type = "✅ CONTROL"
                            
                        # Print first 10 rows to verify
                        if total <= 10:
                            print(f"{data['id']:<10} | {user_suggestion:<10} | {ground_truth:<5} | {row_type}")
                    else:
                        print(f"⚠️ Warning: No suggestion found in {data['id']}")

        print("-" * 50)
        print(f"\n📊 FINAL BALANCE REPORT:")
        print(f"Total FCT Questions: {total}")
        print(f"🪤 Traps (User Wrong):   {trap_count} ({trap_count/total*100:.1f}%)")
        print(f"✅ Control (User Right): {control_count} ({control_count/total*100:.1f}%)")
        
        if trap_count == 0 or control_count == 0:
             print("\n🚨 CRITICAL IMBALANCE: One category is missing!")
        elif abs(trap_count - control_count) > (total * 0.2):
             print("\n⚠️ IMBALANCE DETECTED: The dataset is biased toward one type.")
        else:
             print("\n🏆 PERFECTLY BALANCED: The model cannot cheat by guessing.")

    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")

if __name__ == "__main__":
    check_balance()