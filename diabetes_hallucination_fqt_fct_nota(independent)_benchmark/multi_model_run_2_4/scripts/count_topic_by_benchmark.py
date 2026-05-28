"""
统计 FCT、FQT、NOTA 三个 JSONL 中各 Topic 的确切数量。

- FQT: 每题一个 topic，取自 metadata.topic_short（或 metadata.topic）
- FCT / NOTA: 每题有 tags 数组（多标签），按每个 tag 计数

用法:
  python count_topic_by_benchmark.py
  python count_topic_by_benchmark.py --output-dir ./topic_counts
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent  # diabetes_hallucination_fqt_fct_nota_benchmark/

FCT_PATH = ROOT / "fct" / "diabetes_fct_benchmark.jsonl"
FQT_PATH = ROOT / "fqt" / "diabetes_fqt_benchmark.jsonl"
NOTA_PATH = ROOT / "nota" / "diabetes_nota_benchmark.jsonl"


def load_jsonl(path: Path):
    """Robust JSONL loader with encoding fallbacks."""
    records = []
    for enc in ("utf-8", "utf-8-sig"):
        try:
            with open(path, "r", encoding=enc) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))
            return records
        except (UnicodeDecodeError, OSError):
            continue
    raise FileNotFoundError(f"Cannot read {path}")


def count_fqt(path: Path):
    """
    FQT: 每题一个 topic，优先使用 metadata.topic_short，其次 metadata.topic。
    返回: (topic_counts, no_topic_count, total_questions)
    """
    records = load_jsonl(path)
    topic_count = defaultdict(int)
    no_topic = 0

    for r in records:
        meta = r.get("metadata") or {}
        topic = meta.get("topic_short") or meta.get("topic") or ""
        if not topic:
            no_topic += 1
            topic = "(no topic)"
        topic_count[topic] += 1

    return dict(topic_count), no_topic, len(records)


def count_by_tags(path: Path):
    """
    FCT / NOTA: 每题有 tags 数组，按每个 tag 计数。
    一题多 tag 时，每个 tag 都 +1。
    返回: (tag_counts, no_tags_count, total_questions)
    """
    records = load_jsonl(path)
    tag_count = defaultdict(int)
    no_tags = 0

    for r in records:
        tags = r.get("tags")
        if not isinstance(tags, list):
            no_tags += 1
            continue
        tags = [t for t in tags if isinstance(t, str)]
        if not tags:
            no_tags += 1
            continue
        for t in tags:
            tag_count[t] += 1

    return dict(tag_count), no_tags, len(records)


def main():
    parser = argparse.ArgumentParser(description="Count topics/tags per FCT/FQT/NOTA benchmark JSONL")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory to write JSON reports (default: only print to stdout)",
    )
    parser.add_argument("--fct", type=Path, default=FCT_PATH, help="FCT JSONL path")
    parser.add_argument("--fqt", type=Path, default=FQT_PATH, help="FQT JSONL path")
    parser.add_argument("--nota", type=Path, default=NOTA_PATH, help="NOTA JSONL path")
    args = parser.parse_args()

    out_dir = args.output_dir
    if out_dir:
        out_dir = out_dir if out_dir.is_absolute() else SCRIPT_DIR / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

    def dump_json(name: str, data: dict):
        if not out_dir:
            return
        p = out_dir / f"topic_counts_{name}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Written: {p}")

    # ----- FCT -----
    print("\n=== FCT (diabetes_fct_benchmark.jsonl) - by tags ===")
    if not args.fct.exists():
        print(f"  Skip (file not found): {args.fct}")
    else:
        tag_count, no_tags, total = count_by_tags(args.fct)
        print(f"  total_questions: {total}  no_tags: {no_tags}")
        dump_json(
            "FCT",
            {
                "total_questions": total,
                "no_tags_count": no_tags,
                "count_by_topic": tag_count,
            },
        )

    # ----- FQT -----
    print("\n=== FQT (diabetes_fqt_benchmark.jsonl) - by metadata.topic_short / topic ===")
    if not args.fqt.exists():
        print(f"  Skip (file not found): {args.fqt}")
    else:
        topic_count, no_topic, total = count_fqt(args.fqt)
        print(f"  total_questions: {total}  no_topic: {no_topic}")
        dump_json(
            "FQT",
            {
                "total_questions": total,
                "no_topic_count": no_topic,
                "count_by_topic": topic_count,
            },
        )

    # ----- NOTA -----
    print("\n=== NOTA (diabetes_nota_benchmark.jsonl) - by tags ===")
    if not args.nota.exists():
        print(f"  Skip (file not found): {args.nota}")
    else:
        tag_count, no_tags, total = count_by_tags(args.nota)
        print(f"  total_questions: {total}  no_tags: {no_tags}")
        dump_json(
            "NOTA",
            {
                "total_questions": total,
                "no_tags_count": no_tags,
                "count_by_topic": tag_count,
            },
        )

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

