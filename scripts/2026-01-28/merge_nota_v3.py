import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        raise FileNotFoundError(str(path))
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def renumber_ids_in_order(items: list[dict], prefix: str = "NOTA_") -> None:
    for i, obj in enumerate(items, start=1):
        obj["id"] = f"{prefix}{i:03d}"


def main() -> int:
    """
    Build NOTA v3 = cleaned seeds (336) + all listed addition files, then renumber IDs.
    Addition files are the tmp_nota_v3_*.jsonl outputs from generate_nota_1000q_deepseek.py.
    See output/NOTA_V3_TMP_FILES_README.md for what those tmp files are.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    cleaned_path = project_root / "output" / "cleaned_diabetes_nota_seeds.jsonl"
    # Merge all tmp_nota_v3_* addition files (order: 100, more_65, more_55, chunk1_20, 10a)
    output_dir = project_root / "output"
    additions_paths = [
        output_dir / "tmp_nota_v3_additions_100.jsonl",
        output_dir / "tmp_nota_v3_additions_more_65.jsonl",
        output_dir / "tmp_nota_v3_additions_more_55.jsonl",
        output_dir / "tmp_nota_v3_additions_chunk1_20.jsonl",
        output_dir / "tmp_nota_v3_additions_10a.jsonl",
    ]
    out_path = output_dir / "1000q_diabetes_nota_benchmark_v3.jsonl"

    cleaned = read_jsonl(cleaned_path)
    additions: list[dict] = []
    for p in additions_paths:
        if p.exists():
            items = read_jsonl(p)
            additions.extend(items)
            print(f"  + {p.name}: {len(items)}")

    merged = cleaned + additions
    renumber_ids_in_order(merged, prefix="NOTA_")
    write_jsonl(out_path, merged)

    print(f"Cleaned: {len(cleaned)}")
    print(f"Additions: {len(additions)}")
    print(f"Total v3: {len(merged)}")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
