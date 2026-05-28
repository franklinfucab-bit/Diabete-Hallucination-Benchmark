"""
Filter FCT, NOTA, and AOTA to Category A only (Hard/Clinical/Binary).
Uses filter_category_ab_config.json for keep/remove tags and optional keywords.
Outputs kept_fct_ids, filtered NOTA/FCT/AOTA lists, and optional JSONL files + report.
"""
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "filter_category_ab_config.json"
FCT_SOURCE_300Q = BASE_DIR / "300q_diabetes_topic_balanced_benchmark_combined_ready.jsonl"
NOTA_SOURCE = BASE_DIR / "results_100q_nota" / "100q_nota_fct_convert_benchmark.jsonl"
AOTA_SOURCE = BASE_DIR / "100q AOTA Correct from FCT" / "100q_aota_from_fct_benchmark.jsonl"
OUTPUT_DIR = BASE_DIR / "benchmark"
FILTERED_NOTA_PATH = OUTPUT_DIR / "100q_nota_filtered.jsonl"
FILTERED_FCT_PATH = OUTPUT_DIR / "100q_fct_filtered.jsonl"
FILTERED_AOTA_PATH = OUTPUT_DIR / "100q_aota_filtered.jsonl"
FILTER_REPORT_PATH = OUTPUT_DIR / "filter_category_a_report.json"


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def extract_topic_fct(q: dict, generic_tags: set[str]) -> str:
    """First non-generic tag from metadata.tags or metadata.topic_hint."""
    tags = q.get("metadata") or {}
    tag_list = tags.get("tags") or []
    for t in tag_list:
        t_str = str(t).strip()
        if t_str and t_str.lower() not in generic_tags:
            return t_str
    hint = tags.get("topic_hint")
    if hint and str(hint).strip() and str(hint).strip().lower() not in generic_tags:
        return str(hint).strip()
    return "Other"


def classify_question(
    topic: str,
    question_text: str,
    config: dict,
) -> bool:
    """
    Return True to keep (Category A), False to remove (Category B).
    Uses tag first, then optional keyword fallback, then unmapped_default.
    """
    keep_tags = {t.lower() for t in config.get("keep_tags", [])}
    remove_tags = {t.lower() for t in config.get("remove_tags", [])}
    remove_kw = config.get("remove_keywords", [])
    keep_kw = config.get("keep_keywords", [])
    default_keep = config.get("unmapped_default", "keep").lower() == "keep"

    topic_lower = topic.lower()

    if topic_lower in keep_tags:
        return True
    if topic_lower in remove_tags:
        return False

    text_lower = (question_text or "").lower()
    for kw in remove_kw:
        if kw.lower() in text_lower:
            return False
    for kw in keep_kw:
        if kw.lower() in text_lower:
            return True

    return default_keep


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    generic = set(t.lower() for t in config.get("generic_tags", ["diabetes", "fct", "nota", "fqt", "fqt_v2"]))

    # Load 300q and get FCT block (lines 201-300, 0-based index 200:300)
    all_300q = load_jsonl(FCT_SOURCE_300Q)
    if len(all_300q) < 300:
        raise ValueError(f"300q file has {len(all_300q)} lines, expected at least 300")
    fct_items = all_300q[200:300]
    if len(fct_items) != 100 or any(r.get("task") != "FCT" for r in fct_items):
        raise ValueError(f"Expected 100 FCT items at lines 201-300, got {len(fct_items)}")

    # Classify each FCT
    kept_ids = set()
    removed_ids = []
    topic_to_decision = {}
    for q in fct_items:
        qid = q.get("id", "")
        topic = extract_topic_fct(q, generic)
        question_text = q.get("question", "")
        keep = classify_question(topic, question_text, config)
        topic_to_decision[topic] = "keep" if keep else "remove"
        if keep:
            kept_ids.add(qid)
        else:
            removed_ids.append(qid)

    kept_ids = sorted(kept_ids, key=lambda x: int(x.split("_")[1]))
    removed_ids = sorted(removed_ids, key=lambda x: int(x.split("_")[1]))

    # Filter NOTA and AOTA by derived_from; keep only FCT IDs that have all three
    nota_all = load_jsonl(NOTA_SOURCE)
    aota_all = load_jsonl(AOTA_SOURCE)
    kept_set = set(kept_ids)
    nota_filtered = [r for r in nota_all if (r.get("metadata") or {}).get("derived_from") in kept_set]
    aota_filtered = [r for r in aota_all if (r.get("metadata") or {}).get("derived_from") in kept_set]
    fct_filtered = [r for r in fct_items if r.get("id") in kept_set]

    # Build id -> record; use first occurrence if duplicate derived_from
    id_to_nota = {}
    for r in nota_filtered:
        fid = (r.get("metadata") or {}).get("derived_from")
        if fid and fid not in id_to_nota:
            id_to_nota[fid] = r
    id_to_aota = {}
    for r in aota_filtered:
        fid = (r.get("metadata") or {}).get("derived_from")
        if fid and fid not in id_to_aota:
            id_to_aota[fid] = r
    id_to_fct = {r.get("id"): r for r in fct_filtered}

    # Only keep FCT IDs that have NOTA, FCT, and AOTA (intersection)
    kept_ids_final = [fid for fid in kept_ids if fid in id_to_nota and fid in id_to_fct and fid in id_to_aota]
    nota_filtered = [id_to_nota[fid] for fid in kept_ids_final]
    aota_filtered = [id_to_aota[fid] for fid in kept_ids_final]
    fct_filtered = [id_to_fct[fid] for fid in kept_ids_final]
    K = len(kept_ids_final)

    # Output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write filtered JSONL
    for path, items in [
        (FILTERED_NOTA_PATH, nota_filtered),
        (FILTERED_FCT_PATH, fct_filtered),
        (FILTERED_AOTA_PATH, aota_filtered),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            for rec in items:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Wrote {path} ({len(items)} items)")

    # Report
    dropped_no_triplet = sorted(set(kept_ids) - set(kept_ids_final), key=lambda x: int(x.split("_")[1]))
    report = {
        "kept_fct_ids": kept_ids_final,
        "removed_fct_ids": removed_ids,
        "dropped_kept_ids_missing_triplet": dropped_no_triplet,
        "kept_count": K,
        "removed_count": len(removed_ids),
        "total_fct": 100,
        "filtered_nota_count": len(nota_filtered),
        "filtered_fct_count": len(fct_filtered),
        "filtered_aota_count": len(aota_filtered),
        "topic_decisions": topic_to_decision,
    }
    with open(FILTER_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {FILTER_REPORT_PATH}")

    print(f"\nCategory A filter: kept {K} FCT (with NOTA+AOTA), removed {len(removed_ids)}.")
    if dropped_no_triplet:
        print(f"Dropped (missing NOTA or AOTA): {dropped_no_triplet}")
    print(f"Removed IDs: {removed_ids[:20]}{'...' if len(removed_ids) > 20 else ''}")

    return kept_ids_final, nota_filtered, fct_filtered, aota_filtered, report


if __name__ == "__main__":
    main()
