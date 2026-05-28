#!/usr/bin/env python3
"""
Dataset Quality Evaluation Script (DeepSeek API)

Evaluates the quality of Q&A pairs in diabetes_QA_dataset.xlsx to determine
if the data is good enough to serve as the base for a high-standard benchmark.

Usage:
    python evaluate_dataset_quality.py [filepath] [options]

Options:
    --sample N     Evaluate only first N Q&A pairs (quick check)
    --resume       Resume from checkpoint if interrupted
    --no-resume    Ignore checkpoint, evaluate from scratch

Examples:
    python evaluate_dataset_quality.py data/diabetes_QA_dataset.xlsx
    python evaluate_dataset_quality.py data/diabetes_QA_dataset.xlsx --sample 20
    python evaluate_dataset_quality.py data/diabetes_QA_dataset.xlsx --resume
"""

import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

try:
    from utils.data_loader import DiabetesQALoader
except ImportError:
    DiabetesQALoader = None

# Checkpoint file suffix
CHECKPOINT_SUFFIX = ".dataset_eval_checkpoint.json"

# Default DeepSeek API key (can be overridden by environment variable)
DEFAULT_API_KEY = "sk-c48d90ddbd4d46ad91f527582066e8ea"


def load_dataset(filepath):
    """Load Q&A pairs from Excel file."""
    if DiabetesQALoader is None:
        raise ImportError("Cannot import DiabetesQALoader. Make sure utils.data_loader is available.")
    
    loader = DiabetesQALoader(Path(filepath))
    qa_pairs = loader.get_qa_pairs()
    return qa_pairs


def save_checkpoint(checkpoint_path, evaluations, completed_ids):
    """Save progress to checkpoint file."""
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(
            {"evaluations": evaluations, "completed_ids": list(completed_ids)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_checkpoint(checkpoint_path):
    """Load checkpoint if exists. Returns (evaluations, completed_ids) or (None, None)."""
    if not os.path.exists(checkpoint_path):
        return None, None
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("evaluations", []), set(data.get("completed_ids", []))
    except Exception:
        return None, None


def evaluate_qa_pair_with_deepseek(api_key, qa_pair):
    """Evaluate a single Q&A pair via DeepSeek API."""
    api_url = "https://api.deepseek.com/v1/chat/completions"

    question = qa_pair.get("question", "")
    answer = qa_pair.get("answer", "")
    qa_id = qa_pair.get("id", "")

    prompt = f"""作为一名糖尿病专家和教育评估专家，请评估以下问答对的质量，判断其是否适合作为高质量基准测试数据集的基础。

**问答对信息：**
问题 (Question): {question}
答案 (Answer): {answer}

**评估框架（每个维度1-5分）：**

1. **医学准确性 (Medical Accuracy)**
   - 答案是否准确、符合当前医学知识和临床指南（ADA, IDF）？
   - 是否包含错误、过时或误导性的医学信息？
   - 专业术语使用是否准确？

2. **答案完整性与深度 (Answer Completeness and Depth)**
   - 答案是否充分回答了问题？
   - 是否包含必要的细节和上下文？
   - 是否过于简单或过于复杂？

3. **问题质量 (Question Quality)**
   - 问题是否清晰、具体、有意义？
   - 问题是否针对糖尿病领域的核心议题？
   - 问题表述是否专业、无歧义？

4. **适合基准测试生成 (Suitability for Benchmark Generation)**
   - 该问答对是否适合用于生成多种类型的基准测试题目（多选题、FCT、NOTA、FQT）？
   - 问题是否具有足够的深度和复杂性，能产生有挑战性的测试题目？
   - 答案是否包含足够的信息，可以生成合理的错误选项和干扰项？

5. **整体质量 (Overall Quality)**
   - 问答对整体质量如何？
   - 是否达到高质量基准测试数据集的标准？
   - 是否需要改进才能用于基准测试生成？

**特别注意：**
- 评估该问答对是否适合作为生成高质量基准测试的基础数据
- 考虑能否基于此问答对生成具有挑战性的测试题目
- 评估医学准确性、专业性和教育价值

请返回JSON格式的评估结果：
{{
  "medical_accuracy": 1-5,
  "answer_completeness": 1-5,
  "question_quality": 1-5,
  "benchmark_suitability": 1-5,
  "overall_quality": 1-5,
  "issues": ["问题1", "问题2"],
  "strengths": ["优点1", "优点2"],
  "recommendation": "改进建议或是否适合作为基准测试基础",
  "suitable_for_benchmark": true/false
}}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是一位资深的糖尿病专家和教育评估专家，擅长评估问答对的质量和是否适合用于生成高质量的基准测试数据集。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        content = re.sub(r",(\s*[}\]])", r"\1", content)
        parsed = json.loads(content)

        return {
            "medical_accuracy": float(parsed.get("medical_accuracy", 0)),
            "answer_completeness": float(parsed.get("answer_completeness", 0)),
            "question_quality": float(parsed.get("question_quality", 0)),
            "benchmark_suitability": float(parsed.get("benchmark_suitability", 0)),
            "overall_quality": float(parsed.get("overall_quality", 0)),
            "issues": parsed.get("issues", []),
            "strengths": parsed.get("strengths", []),
            "recommendation": parsed.get("recommendation", ""),
            "suitable_for_benchmark": parsed.get("suitable_for_benchmark", False),
            "success": True,
        }
    except Exception as e:
        return {
            "medical_accuracy": 0,
            "answer_completeness": 0,
            "question_quality": 0,
            "benchmark_suitability": 0,
            "overall_quality": 0,
            "issues": [f"Evaluation error: {str(e)}"],
            "strengths": [],
            "recommendation": "",
            "suitable_for_benchmark": False,
            "success": False,
            "error": str(e),
        }


def evaluate_dataset(filepath, sample=None, resume=True):
    """Evaluate all (or sampled) Q&A pairs. Supports checkpoint/resume."""
    api_key = os.getenv("DEEPSEEK_API_KEY", DEFAULT_API_KEY)
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set and no default key provided.")

    if requests is None:
        raise ImportError("Please install requests: pip install requests")

    qa_pairs = load_dataset(filepath)
    total = len(qa_pairs)
    to_eval = qa_pairs[:sample] if sample else qa_pairs
    n = len(to_eval)

    checkpoint_path = str(filepath) + CHECKPOINT_SUFFIX
    evaluations = []
    completed_ids = set()

    if resume:
        prev_evals, prev_ids = load_checkpoint(checkpoint_path)
        if prev_evals and prev_ids:
            evaluations = prev_evals
            completed_ids = prev_ids
            print(f"Resumed: {len(completed_ids)} already evaluated.")

    scores_summary = defaultdict(list)
    eval_by_id = {e.get("qa_id"): e for e in evaluations if isinstance(e, dict)}

    for idx, qa_pair in enumerate(to_eval, 1):
        qa_id = qa_pair.get("id", f"QA{idx}")
        if qa_id in completed_ids:
            e = eval_by_id.get(qa_id)
            if e and e.get("success"):
                for k in (
                    "medical_accuracy",
                    "answer_completeness",
                    "question_quality",
                    "benchmark_suitability",
                    "overall_quality",
                ):
                    if k in e:
                        scores_summary[k].append(e[k])
            print(f"Evaluating {qa_id} ({idx}/{n})... SKIP (checkpoint)")
            continue

        print(f"Evaluating {qa_id} ({idx}/{n})...", end=" ", flush=True)
        ev = evaluate_qa_pair_with_deepseek(api_key, qa_pair)

        ev["qa_id"] = qa_id
        qtext = qa_pair.get("question", "")
        ev["question"] = (qtext[:100] + "...") if len(qtext) > 100 else qtext
        atext = qa_pair.get("answer", "")
        ev["answer"] = (atext[:100] + "...") if len(atext) > 100 else atext

        if ev.get("success"):
            for k in (
                "medical_accuracy",
                "answer_completeness",
                "question_quality",
                "benchmark_suitability",
                "overall_quality",
            ):
                scores_summary[k].append(ev[k])
            suitable = "YES" if ev.get("suitable_for_benchmark", False) else "NO"
            print(f"OK (Score: {ev['overall_quality']:.2f}, Suitable: {suitable})")
        else:
            print(f"FAILED ({ev.get('error', 'Unknown')})")

        evaluations.append(ev)
        completed_ids.add(qa_id)
        eval_by_id[qa_id] = ev

        save_checkpoint(checkpoint_path, evaluations, completed_ids)
        time.sleep(1.0)

    averages = {
        k: sum(v) / len(v) if v else 0
        for k, v in scores_summary.items()
    }
    
    # Count suitable pairs
    suitable_count = sum(1 for e in evaluations if isinstance(e, dict) and e.get("success") and e.get("suitable_for_benchmark", False))
    
    return evaluations, averages, checkpoint_path, suitable_count


def reorder_dict_keys(d, first_key):
    """Reorder dictionary to put specified key first."""
    if first_key not in d:
        return d
    new_dict = {first_key: d[first_key]}
    for k, v in d.items():
        if k != first_key:
            new_dict[k] = v
    return new_dict


def generate_report(evaluations, averages, suitable_count, filepath, checkpoint_path):
    """Build report, detect low-quality Q&A pairs. Output as JSONL with low scores first."""
    successful = [e for e in evaluations if isinstance(e, dict) and e.get("success")]
    low_quality = [e for e in successful if e.get("overall_quality", 0) < 3.0]
    not_suitable = [e for e in successful if not e.get("suitable_for_benchmark", False)]

    # Sort all successful evaluations by overall_quality (lowest first)
    low_quality_sorted = sorted(low_quality, key=lambda x: x.get("overall_quality", 0))
    other_successful = sorted(
        [e for e in successful if e.get("overall_quality", 0) >= 3.0],
        key=lambda x: x.get("overall_quality", 0)
    )
    
    # Failed evaluations at the end
    failed = [e for e in evaluations if not (isinstance(e, dict) and e.get("success"))]
    
    # Combine: low quality first, then others, then failed
    sorted_evaluations = low_quality_sorted + other_successful + failed
    
    # Reorder each evaluation to put qa_id first
    sorted_evaluations = [reorder_dict_keys(e, "qa_id") for e in sorted_evaluations]

    # Write JSONL format (one JSON object per line)
    report_dir = os.path.dirname(os.path.abspath(filepath))
    base_name = os.path.basename(filepath)
    # Remove existing extensions and add evaluation report suffix
    if base_name.endswith(".xlsx"):
        report_name = base_name[:-5] + "_evaluation_report.jsonl"
    else:
        report_name = base_name + "_evaluation_report.jsonl"
    report_file = os.path.join(report_dir, report_name)
    
    with open(report_file, "w", encoding="utf-8") as f:
        # Write summary as first line (optional metadata)
        summary = {
            "summary": {
                "dataset_file": str(filepath),
                "total_qa_pairs": len(evaluations),
                "successful_evaluations": len(successful),
                "failed_evaluations": len(evaluations) - len(successful),
                "average_scores": averages,
                "low_quality_count": len(low_quality),
                "suitable_for_benchmark_count": suitable_count,
                "not_suitable_count": len(not_suitable),
                "suitability_rate": suitable_count / len(successful) if successful else 0,
            }
        }
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        
        # Write each evaluation as a separate line
        for eval_data in sorted_evaluations:
            f.write(json.dumps(eval_data, ensure_ascii=False) + "\n")

    # Remove checkpoint on successful completion
    if os.path.exists(checkpoint_path):
        try:
            os.remove(checkpoint_path)
        except OSError:
            pass

    print("\n" + "=" * 60)
    print("DATASET QUALITY EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Dataset: {filepath}")
    print(f"Total Q&A Pairs: {len(evaluations)}")
    print(f"Successful Evaluations: {len(successful)}")
    print("\nAverage Scores:")
    print(f"  Medical Accuracy:        {averages.get('medical_accuracy', 0):.2f}")
    print(f"  Answer Completeness:     {averages.get('answer_completeness', 0):.2f}")
    print(f"  Question Quality:        {averages.get('question_quality', 0):.2f}")
    print(f"  Benchmark Suitability:   {averages.get('benchmark_suitability', 0):.2f}")
    print(f"  Overall Quality:          {averages.get('overall_quality', 0):.2f}")
    print(f"\nLow Quality (< 3.0): {len(low_quality)}")
    print(f"Suitable for Benchmark: {suitable_count} ({suitable_count/len(successful)*100:.1f}%)" if successful else "Suitable for Benchmark: 0")
    print(f"Not Suitable: {len(not_suitable)}")
    print(f"\nReport (JSONL format): {report_file}")
    print(f"  - Low quality Q&A pairs appear first")
    print(f"  - Q&A pairs sorted by quality (lowest to highest)")
    print(f"  - ID field is first in each evaluation")
    print("=" * 60)

    return {
        "report_file": report_file,
        "total_qa_pairs": len(evaluations),
        "successful_evaluations": len(successful),
        "low_quality_count": len(low_quality),
        "suitable_for_benchmark_count": suitable_count,
        "suitability_rate": suitable_count / len(successful) if successful else 0,
        "average_scores": averages,
    }


def main():
    argv = sys.argv[1:]
    args = []
    sample = None
    resume = True
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--no-resume":
            resume = False
        elif a == "--resume":
            resume = True
        elif a == "--sample":
            i += 1
            if i < len(argv) and argv[i].isdigit():
                sample = int(argv[i])
        elif a.startswith("--sample="):
            try:
                sample = int(a.split("=", 1)[1])
            except ValueError:
                pass
        elif not a.startswith("--"):
            args.append(a)
        i += 1
    if "--sample" in argv and sample is None:
        print("Error: --sample requires a positive integer (e.g. --sample 20)")
        return 1

    # Default filepath
    filepath = args[0] if args else "data/diabetes_QA_dataset.xlsx"

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return 1

    print("=" * 60)
    print("Dataset Quality Evaluation")
    print("=" * 60)
    print(f"File: {filepath}")
    if sample:
        print(f"Sample: first {sample} Q&A pairs")
    print(f"Resume: {resume}")
    print("=" * 60)

    try:
        evaluations, averages, checkpoint_path, suitable_count = evaluate_dataset(
            filepath, sample=sample, resume=resume
        )
        generate_report(
            evaluations, averages, suitable_count, filepath, checkpoint_path
        )
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
