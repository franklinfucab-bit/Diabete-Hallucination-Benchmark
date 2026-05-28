"""
Extract the chosen option (A, B, C, or D) from model output.
Used by the Ollama benchmark script to parse answers.

- Strips <think>...</think> blocks.
- Finds the last occurrence of a single letter A, B, C, or D (word boundary).
- Returns "N/A" if none found.

Usage:
  python extract_answer.py --text "The answer is B."
  echo "Some reasoning. Answer: C" | python extract_answer.py
"""
import argparse
import re
import sys


def extract_answer(text: str) -> str:
    """Extract last A/B/C/D from model response; strip <think> blocks first."""
    if not text or not text.strip():
        return "N/A"
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    matches = re.findall(r"\b([A-D])\b", clean_text, re.IGNORECASE)
    if not matches:
        return "N/A"
    return matches[-1].upper()


def main():
    parser = argparse.ArgumentParser(description="Extract A/B/C/D answer from model output")
    parser.add_argument("--text", type=str, default=None, help="Raw model output text")
    args = parser.parse_args()
    if args.text is not None:
        result = extract_answer(args.text)
        print(result)
        return
    # Read from stdin
    raw = sys.stdin.read()
    print(extract_answer(raw))


if __name__ == "__main__":
    main()
