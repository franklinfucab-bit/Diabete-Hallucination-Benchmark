"""
Collect all question topic tags from a combined benchmark JSONL file.

Extracts:
- tags (top-level array, used by FCT/NOTA)
- metadata.topic, metadata.topic_short, metadata.topic_hint (used by FQT/FCT)

Usage:
  python collect_topic_tags.py
  python collect_topic_tags.py --input 102q_combined_benchmark_v1.jsonl -o topic_tags_report.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BENCHMARK_DIR = BASE_DIR / "benchmark"
ANALYSIS_DIR = BASE_DIR / "analysis"
# Try 102q file first, fallback to v1_102q (both are valid 102-question benchmarks)
DEFAULT_INPUT = BENCHMARK_DIR / "102q_combined_benchmark_v1.jsonl"
ALT_INPUT = BENCHMARK_DIR / "v1_102q_combined_benchmark_full_info.jsonl"


def collect_from_record(record: dict) -> Tuple[List[str], List[str]]:
    """
    Extract tags and topics from a single record.
    Returns (tags_list, topics_list).
    """
    tags = []
    topics = []

    # Top-level tags array (FCT, NOTA)
    if "tags" in record and isinstance(record["tags"], list):
        tags.extend(t for t in record["tags"] if isinstance(t, str))

    # metadata.tags (diabetes_combined_ready format)
    metadata = record.get("metadata") or {}
    if "tags" in metadata and isinstance(metadata["tags"], list):
        tags.extend(t for t in metadata["tags"] if isinstance(t, str))

    # metadata.topic, metadata.topic_short, metadata.topic_hint (FQT)
    for key in ("topic", "topic_short", "topic_hint"):
        val = metadata.get(key)
        if val and isinstance(val, str):
            topics.append(val)

    return tags, topics


def main():
    parser = argparse.ArgumentParser(description="Collect all question topic tags from benchmark JSONL")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT,
                        help=f"Input JSONL file (default: {DEFAULT_INPUT.name})")
    parser.add_argument("--output", "-o", type=Path, default=ANALYSIS_DIR / "topic_tags_report.json",
                        help="Output JSON report file")
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else (BASE_DIR / args.input)
    candidates = [
        BENCHMARK_DIR / "v1_102q_combined_benchmark_full_info.jsonl",
        ALT_INPUT,
        BENCHMARK_DIR / "102q_combined_benchmark_v1.jsonl",
        BASE_DIR / "diabetes_combined_ready.jsonl",  # fallback: has metadata.tags
    ]
    if input_path.exists():
        # Check file has content
        if input_path.stat().st_size > 0:
            input_path = input_path.resolve()
        else:
            input_path = None
    else:
        input_path = None

    if input_path is None:
        for candidate in candidates:
            if candidate.exists() and candidate.stat().st_size > 0:
                input_path = candidate.resolve()
                print(f"Using: {input_path.name}")
                break
        if input_path is None:
            print("Error: No input file found with content. Tried:")
            for c in candidates:
                sz = c.stat().st_size if c.exists() else -1
                print(f"  - {c}: exists={c.exists()}, size={sz}")
            return 1

    all_tags = set()
    all_topics = set()
    tag_to_questions = defaultdict(list)
    topic_to_questions = defaultdict(list)

    # Read line by line for reliability (handles large files, encoding)
    lines = []
    for enc in ("utf-8", "utf-8-sig"):
        try:
            with open(str(input_path), "r", encoding=enc) as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            break
        except (UnicodeDecodeError, OSError):
            continue

    if not lines:
        print(f"Error: No content in file ({input_path})")
        return 1

    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Warning: Skip invalid JSON: {e}")

    for record in records:
        if not isinstance(record, dict):
            continue
        qid = record.get("id", "?")
        tags, topics = collect_from_record(record)

        for t in tags:
            all_tags.add(t)
            tag_to_questions[t].append(qid)

        for t in topics:
            all_topics.add(t)
            topic_to_questions[t].append(qid)

    # Build report
    tag_counts = {t: len(tag_to_questions[t]) for t in sorted(all_tags)}
    topic_counts = {t: len(topic_to_questions[t]) for t in sorted(all_topics)}
    questions_by_tag = {t: tag_to_questions[t] for t in sorted(all_tags)}
    questions_by_topic = {t: topic_to_questions[t] for t in sorted(all_topics)}

    report = {
        "unique_tags": sorted(all_tags),
        "unique_topics": sorted(all_topics),
        "tag_counts": tag_counts,
        "topic_counts": topic_counts,
        "questions_by_tag": questions_by_tag,
        "questions_by_topic": questions_by_topic,
    }

    # Print to stdout (use ensure_ascii for Windows console compatibility)
    print(f"\nProcessed: {input_path.name}")
    print(f"Unique tags: {len(all_tags)}")
    print(f"Unique topics: {len(all_topics)}")
    print("Sample tags:", json.dumps(sorted(all_tags)[:15], ensure_ascii=True))
    if all_topics:
        print("Topics:", json.dumps(sorted(all_topics), ensure_ascii=True))
    print("Tag counts (top 15):", json.dumps(dict(list(tag_counts.items())[:15]), ensure_ascii=True))

    # Write JSON report
    if args.output:
        out_path = args.output if args.output.is_absolute() else (ANALYSIS_DIR / args.output.name)
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {out_path}")

    return 0


if __name__ == "__main__":
    exit(main())
