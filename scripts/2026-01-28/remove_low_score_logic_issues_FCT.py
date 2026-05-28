#!/usr/bin/env python3
"""
Remove low-score and logic-issue questions from FCT benchmark based on Concur evaluation report.

Reads:
  - output/Json/1000q_diabetes_fct_benchmark_v3.5.json
  - output/Json/1000q_diabetes_fct_benchmark_v3.5_evaluation_report.jsonl

Excludes questions that are:
  1. Low score: overall_score < 3.0
  2. Logic issue: has_logic_issue(eval_data) per Concur criteria

Writes:
  - output/Json/1000q_diabetes_fct_benchmark_v3.7.json
  - output/Json/1000q_diabetes_fct_benchmark_v3.7_evaluation_report.jsonl (derived from v3.5 report)
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BENCHMARK_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.5.json"
REPORT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.5_evaluation_report.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.7.json"
REPORT_OUTPUT_FILE = PROJECT_ROOT / "output" / "Json" / "1000q_diabetes_fct_benchmark_v3.7_evaluation_report.jsonl"

SCORE_KEYS = (
    "technical_accuracy",
    "cognitive_trap_design",
    "difficulty_discrimination",
    "domain_relevance",
    "test_effectiveness",
    "overall_score",
)

LOW_SCORE_THRESHOLD = 3.0


def has_logic_issue(eval_data: dict) -> bool:
    """Same logic as Concur_evaluate_benchmark_quality.py for FCT."""
    text = (eval_data.get("logic_check") or "") + (eval_data.get("recommendation") or "")
    text_lower = text.lower()
    # Exclude: explicit "not confusing" / "reasonable"
    if any(
        x in text
        for x in (
            "毫不令人困惑",
            "不令人困惑",
            "毫不困惑",
            "答案毫不令人困惑",
            "逻辑完全合理",
            "逻辑合理",
            "not confusing",
            "reasonable",
            "makes sense",
        )
    ):
        return False
    # Chinese: positive indicators of confusion
    if any(
        x in text
        for x in (
            "不合理",
            "令人困惑",
            "无意义",
            "没有意义",
            "逻辑不清",
            "答案令人困惑",
            "难以理解",
        )
    ):
        return True
    # English
    if any(
        x in text_lower
        for x in (
            "confusing",
            "no sense",
            "doesn't make sense",
            "illogical",
            "ambiguous",
            "unclear",
            "contradict",
            "nonsensical",
        )
    ):
        return True
    return False


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
    low_score_ids = []
    logic_issue_ids = []

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "summary" in obj:
                continue  # skip summary line
            qid = obj.get("question_id")
            if not qid:
                continue
            all_evals.append(obj)
            score = obj.get("overall_score", 0)
            is_low = score < LOW_SCORE_THRESHOLD
            is_logic = has_logic_issue(obj)
            if is_low:
                low_score_ids.append(qid)
                excluded_ids.add(qid)
            if is_logic:
                logic_issue_ids.append(qid)
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

    # 4. Write v3.7 benchmark
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for q in kept:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # 5. Filter evaluations and build v3.7 report
    kept_evals = [e for e in all_evals if e.get("question_id") not in excluded_ids]
    successful = [e for e in kept_evals if e.get("success")]
    low_score = [e for e in successful if e.get("overall_score", 0) < LOW_SCORE_THRESHOLD]
    logic_issues = [e for e in successful if has_logic_issue(e)]

    # Compute averages from kept successful evals
    scores_summary = {k: [] for k in SCORE_KEYS}
    for e in successful:
        for k in SCORE_KEYS:
            if k in e:
                scores_summary[k].append(e[k])
    averages = {
        k: sum(v) / len(v) if v else 0
        for k, v in scores_summary.items()
    }

    # Sort: lowest score first (same as Concur)
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
            "low_score_count": len(low_score),
            "logic_issue_count": len(logic_issues),
        }
    }

    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        for e in sorted_evals:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Input: {BENCHMARK_FILE.name} ({len(questions)} questions)")
    print(f"Report: {REPORT_FILE.name}")
    print(f"Low score (< {LOW_SCORE_THRESHOLD}): {len(low_score_ids)}")
    print(f"Logic issues: {len(logic_issue_ids)}")
    print(f"Excluded (union): {len(excluded_ids)}")
    print(f"Kept: {len(kept)}")
    print(f"Output benchmark: {OUTPUT_FILE}")
    print(f"Output report: {REPORT_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
