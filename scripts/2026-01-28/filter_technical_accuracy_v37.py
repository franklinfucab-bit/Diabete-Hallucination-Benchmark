#!/usr/bin/env python3
"""
Remove questions with low technical_accuracy or medical-accuracy defects from FCT v3.7.

Reads:
  - output/Json/1000q_diabetes_fct_benchmark_v3.7.json
  - output/Json/1000q_diabetes_fct_benchmark_v3.7_evaluation_report.jsonl

Excludes questions that have:
  1. technical_accuracy < 3.0, OR
  2. "医学准确性存在严重缺陷" or "医学准确性存在严重问题" in issues/logic_check/recommendation/strengths

Writes:
  - output/Json/1000q_diabetes_fct_benchmark_v3.8.json
  - output/Json/1000q_diabetes_fct_benchmark_v3.8_evaluation_report.jsonl
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BENCHMARK_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.7.json"
REPORT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.7_evaluation_report.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.8.json"
REPORT_OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.8_evaluation_report.jsonl"

SCORE_KEYS = (
    "technical_accuracy",
    "cognitive_trap_design",
    "difficulty_discrimination",
    "domain_relevance",
    "test_effectiveness",
    "overall_score",
)

TECH_ACCURACY_THRESHOLD = 3.0

MEDICAL_ACCURACY_DEFECT_PHRASES = (
    "医学准确性存在严重缺陷",
    "医学准确性存在严重问题",
)


def has_medical_accuracy_defect(eval_data: dict) -> bool:
    """Check if evaluation mentions serious medical accuracy defect."""
    parts = []
    for key in ("issues", "logic_check", "recommendation", "strengths"):
        val = eval_data.get(key)
        if isinstance(val, list):
            parts.append(" ".join(str(x) for x in val))
        elif val:
            parts.append(str(val))
    text = " ".join(parts)
    return any(phrase in text for phrase in MEDICAL_ACCURACY_DEFECT_PHRASES)


def reorder_dict_keys(d: dict, first_key: str) -> dict:
    """Reorder dict to put specified key first (matches Concur report format)."""
    if first_key not in d:
        return d
    out = {first_key: d[first_key]}
    for k, v in d.items():
        if k != first_key:
            out[k] = v
    return out


def main():
    # 1. Parse evaluation report: collect evals and excluded question_ids
    all_evals = []
    excluded_ids = set()
    low_tech_ids = []
    medical_defect_ids = []

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "summary" in obj:
                continue
            qid = obj.get("question_id")
            if not qid:
                continue
            all_evals.append(obj)
            tech = obj.get("technical_accuracy", 0)
            is_low_tech = tech < TECH_ACCURACY_THRESHOLD
            is_defect = has_medical_accuracy_defect(obj)
            if is_low_tech:
                low_tech_ids.append(qid)
                excluded_ids.add(qid)
            if is_defect:
                medical_defect_ids.append(qid)
                excluded_ids.add(qid)

    # 2. Load benchmark
    questions = []
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))

    # 3. Filter benchmark
    kept = [q for q in questions if q.get("id") not in excluded_ids]

    # 4. Write v3.8 benchmark
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for q in kept:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # 5. Filter evaluations and build v3.8 report
    kept_evals = [e for e in all_evals if e.get("question_id") not in excluded_ids]
    successful = [e for e in kept_evals if e.get("success")]
    low_tech = [e for e in successful if e.get("technical_accuracy", 0) < TECH_ACCURACY_THRESHOLD]
    medical_defects = [e for e in successful if has_medical_accuracy_defect(e)]

    scores_summary = {k: [] for k in SCORE_KEYS}
    for e in successful:
        for k in SCORE_KEYS:
            if k in e:
                scores_summary[k].append(e[k])
    averages = {
        k: sum(v) / len(v) if v else 0
        for k, v in scores_summary.items()
    }

    sorted_evals = sorted(kept_evals, key=lambda x: x.get("overall_score", 0))
    sorted_evals = [reorder_dict_keys(e, "question_id") for e in sorted_evals]

    summary = {
        "summary": {
            "domain": "diabetes",
            "test_type": "FCT",
            "total_questions": len(kept_evals),
            "successful_evaluations": len(successful),
            "failed_evaluations": len(kept_evals) - len(successful),
            "average_scores": averages,
            "low_score_count": 0,
            "logic_issue_count": 0,
        }
    }

    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        for e in sorted_evals:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Input: {BENCHMARK_FILE.name} ({len(questions)} questions)")
    print(f"Report: {REPORT_FILE.name}")
    print(f"Low technical_accuracy (< {TECH_ACCURACY_THRESHOLD}): {len(low_tech_ids)}")
    print(f"Medical accuracy defect: {len(medical_defect_ids)}")
    print(f"Excluded (union): {len(excluded_ids)}")
    print(f"Kept: {len(kept)}")
    print(f"Output benchmark: {OUTPUT_FILE}")
    print(f"Output report: {REPORT_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
