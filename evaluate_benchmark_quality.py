#!/usr/bin/env python3
"""
Benchmark Quality Evaluation Script (DeepSeek API)

Evaluates and rates benchmark questions (FCT, FQT, NOTA) using the comprehensive
diabetes assessment framework. Run after benchmark generation.

Usage:
    python evaluate_benchmark_quality.py <test_type> <domain> [filepath] [options]

Options:
    --sample N     Evaluate only first N questions (quick check)
    --resume       Resume from checkpoint if interrupted
    --no-resume    Ignore checkpoint, evaluate from scratch

Examples:
    python evaluate_benchmark_quality.py NOTA diabetes
    python evaluate_benchmark_quality.py NOTA diabetes output/converted_none_of_above_benchmark.jsonl
    python evaluate_benchmark_quality.py FCT diabetes --sample 5
    python evaluate_benchmark_quality.py NOTA diabetes --resume
"""

import json
import os
import re
import sys
import time
from collections import defaultdict

try:
    import requests
except ImportError:
    requests = None

# Checkpoint file suffix
CHECKPOINT_SUFFIX = ".eval_checkpoint.json"

# Default DeepSeek API key (can be overridden by environment variable)
DEFAULT_API_KEY = "sk-c48d90ddbd4d46ad91f527582066e8ea"


def read_benchmark(filepath):
    """Read benchmark from JSONL or JSON array."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if raw.startswith("["):
        data = json.loads(raw)
        return data
    
    # Handle JSONL format (can be single-line or multi-line JSON objects)
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        buffer = ""
        brace_count = 0
        for line in f:
            buffer += line
            # Count braces to detect complete JSON objects
            brace_count += line.count("{") - line.count("}")
            # When braces are balanced, we have a complete JSON object
            if brace_count == 0 and buffer.strip():
                try:
                    questions.append(json.loads(buffer.strip()))
                    buffer = ""
                except json.JSONDecodeError:
                    # If parsing fails, try accumulating more lines
                    continue
        # Handle any remaining buffer
        if buffer.strip():
            try:
                questions.append(json.loads(buffer.strip()))
            except json.JSONDecodeError:
                pass
    return questions


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


def has_logic_issue(eval_data, test_type):
    """Detect logic/answer confusion (FCT, NOTA only). FQT excluded."""
    if test_type == "FQT":
        return False
    text = (eval_data.get("logic_check") or "") + (eval_data.get("recommendation") or "")
    text_lower = text.lower()
    # Exclude: explicit "not confusing" / "reasonable" (avoid false positives)
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


def evaluate_question_with_deepseek(api_key, question_data, test_type, domain):
    """Evaluate a single question via DeepSeek API."""
    api_url = "https://api.deepseek.com/v1/chat/completions"

    if test_type == "FCT":
        question = question_data.get("question", "")
        options = question_data.get("options", [])
        correct_answer = question_data.get("correct_answer", "")
        suggested = question_data.get("suggested_answer") or {}
        options_text = "\n".join([f"{o['option_id']}. {o['text']}" for o in options])
        question_context = f"""
Question: {question}
Options:
{options_text}
Correct Answer: {correct_answer}
Suggested Answer: {suggested.get('option_id', '')}. {suggested.get('text', '')}
Suggested Answer is Correct: {suggested.get('is_correct', False)}
"""
    elif test_type == "FQT":
        question = question_data.get("question", "")
        why_fake = question_data.get("why_fake", "")
        question_context = f"""
Question: {question}
Why Fake: {why_fake}
Expected Response: Should identify as invalid/nonsensical
"""
    elif test_type == "NOTA":
        question = question_data.get("question", "")
        options = question_data.get("options", [])
        explanation = question_data.get("explanation", "")
        options_text = "\n".join([f"{o['option_id']}. {o['text']}" for o in options])
        question_context = f"""
Question: {question}
Options:
{options_text}
Correct Answer: D (None of the above)
Explanation: {explanation}
"""
    else:
        return None

    domain_ctx = {
        "diabetes": "糖尿病领域：血糖管理、胰岛素治疗、并发症预防、生活方式干预、药物治疗",
        "medical": "医学领域：疾病诊断、治疗管理、患者安全、临床指南",
        "general": "通用医学领域：基本医学知识、健康管理、疾病预防",
    }
    domain_desc = domain_ctx.get(domain.lower(), "糖尿病")

    prompt = f"""作为一名糖尿病专家和教育评估专家，请根据以下评估框架对这道基准测试题目进行评分。

**题目信息：**
{question_context}

**领域：** {domain_desc}
**测试类型：** {test_type}

**评估框架（每个维度1-5分）：**

1. **医学准确性 (Medical Accuracy)**
   - 知识核心：是否准确触及糖尿病管理的关键原理、临床指南（ADA, IDF）、治疗流程？
   - 场景真实：问题背景、参数（血糖值、胰岛素剂量、HbA1c）是否符合临床实际？
   - 解释深度：对答案的解释是否精准，能指出错误的根本医学原因，而非泛泛而谈？

2. **认知陷阱设计 (Cognitive Trap Design)**
   - 偏见利用：是否有效利用糖尿病领域内常见认知偏见和误解？
   - 诱惑强度：错误选项是否"半真半假"，由正确知识通过一个隐蔽的逻辑跳跃得出？

3. **难度与区分度 (Difficulty and Discrimination)**
   - 梯度合理：题目难度是否合理，能区分不同知识深度的模型？
   - 区分焦点：是否考察对多重约束的权衡、对异常或边界情况的判断，而非冷僻知识？

4. **领域相关性 (Domain Relevance)**
   - 核心议题：是否针对糖尿病管理的标志性挑战？
   - 专业语言：是否使用准确的医学术语，而非外行或模糊表述？

5. **测试有效性 (Test Effectiveness)**
   - FCT：错误选项是否比正确答案看起来"更简单、更确定、更权威"，从而诱导"虚假信心"？
   - FQT：虚假前提是否与真实概念精巧混合，需深入思考才能识破，而非明显荒谬？
   - NOTA：所有给定选项是否都基于常见误解，让"以上都不是"成为需要推理得出的结论？

**特别注意：**
- 对于FCT和NOTA题目，检查题目逻辑是否合理，但答案是否令人困惑或没有意义。
- 对于FQT题目，检查虚假前提是否足够巧妙，需要专业知识才能识别。

请返回JSON格式的评估结果：
{{
  "technical_accuracy": 1-5,
  "cognitive_trap_design": 1-5,
  "difficulty_discrimination": 1-5,
  "domain_relevance": 1-5,
  "test_effectiveness": 1-5,
  "overall_score": 1-5,
  "issues": ["问题1", "问题2"],
  "strengths": ["优点1", "优点2"],
  "logic_check": "对于FCT/NOTA：题目逻辑是否合理？答案是否令人困惑？",
  "recommendation": "改进建议"
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
                "content": "你是一位资深的糖尿病专家和教育评估专家，擅长评估测试题目的质量和有效性。",
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
            "technical_accuracy": float(parsed.get("technical_accuracy", 0)),
            "cognitive_trap_design": float(parsed.get("cognitive_trap_design", 0)),
            "difficulty_discrimination": float(parsed.get("difficulty_discrimination", 0)),
            "domain_relevance": float(parsed.get("domain_relevance", 0)),
            "test_effectiveness": float(parsed.get("test_effectiveness", 0)),
            "overall_score": float(parsed.get("overall_score", 0)),
            "issues": parsed.get("issues", []),
            "strengths": parsed.get("strengths", []),
            "logic_check": parsed.get("logic_check", ""),
            "recommendation": parsed.get("recommendation", ""),
            "success": True,
        }
    except Exception as e:
        return {
            "technical_accuracy": 0,
            "cognitive_trap_design": 0,
            "difficulty_discrimination": 0,
            "domain_relevance": 0,
            "test_effectiveness": 0,
            "overall_score": 0,
            "issues": [f"Evaluation error: {str(e)}"],
            "strengths": [],
            "logic_check": "",
            "recommendation": "",
            "success": False,
            "error": str(e),
        }


def evaluate_benchmark(filepath, test_type, domain, sample=None, resume=True):
    """Evaluate all (or sampled) questions. Supports checkpoint/resume."""
    api_key = os.getenv("DEEPSEEK_API_KEY", DEFAULT_API_KEY)
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set and no default key provided.")

    if requests is None:
        raise ImportError("Please install requests: pip install requests")

    questions = read_benchmark(filepath)
    total = len(questions)
    to_eval = questions[:sample] if sample else questions
    n = len(to_eval)

    checkpoint_path = filepath + CHECKPOINT_SUFFIX
    evaluations = []
    completed_ids = set()

    if resume:
        prev_evals, prev_ids = load_checkpoint(checkpoint_path)
        if prev_evals and prev_ids:
            evaluations = prev_evals
            completed_ids = prev_ids
            print(f"Resumed: {len(completed_ids)} already evaluated.")

    scores_summary = defaultdict(list)
    eval_by_id = {e.get("question_id"): e for e in evaluations if isinstance(e, dict)}

    for idx, question in enumerate(to_eval, 1):
        qid = question.get("id", f"Q{idx}")
        if qid in completed_ids:
            e = eval_by_id.get(qid)
            if e and e.get("success"):
                for k in (
                    "technical_accuracy",
                    "cognitive_trap_design",
                    "difficulty_discrimination",
                    "domain_relevance",
                    "test_effectiveness",
                    "overall_score",
                ):
                    if k in e:
                        scores_summary[k].append(e[k])
            print(f"Evaluating {qid} ({idx}/{n})... SKIP (checkpoint)")
            continue

        print(f"Evaluating {qid} ({idx}/{n})...", end=" ", flush=True)
        ev = evaluate_question_with_deepseek(api_key, question, test_type, domain)

        ev["question_id"] = qid
        qtext = question.get("question", "")
        ev["question"] = (qtext[:100] + "...") if len(qtext) > 100 else qtext

        if ev.get("success"):
            for k in (
                "technical_accuracy",
                "cognitive_trap_design",
                "difficulty_discrimination",
                "domain_relevance",
                "test_effectiveness",
                "overall_score",
            ):
                scores_summary[k].append(ev[k])
            print(f"OK (Score: {ev['overall_score']:.2f})")
        else:
            print(f"FAILED ({ev.get('error', 'Unknown')})")

        evaluations.append(ev)
        completed_ids.add(qid)
        eval_by_id[qid] = ev

        save_checkpoint(checkpoint_path, evaluations, completed_ids)
        time.sleep(1.0)

    averages = {
        k: sum(v) / len(v) if v else 0
        for k, v in scores_summary.items()
    }
    return evaluations, averages, checkpoint_path


def reorder_dict_keys(d, first_key):
    """Reorder dictionary to put specified key first."""
    if first_key not in d:
        return d
    new_dict = {first_key: d[first_key]}
    for k, v in d.items():
        if k != first_key:
            new_dict[k] = v
    return new_dict


def generate_report(evaluations, averages, test_type, domain, filepath, checkpoint_path):
    """Build report, detect low-score and logic-issue questions. Output as JSONL with low scores first."""
    successful = [e for e in evaluations if isinstance(e, dict) and e.get("success")]
    low_score = [e for e in successful if e.get("overall_score", 0) < 3.0]
    logic_issues = [e for e in successful if has_logic_issue(e, test_type)]

    # Sort all successful evaluations by overall_score (lowest first)
    # Low score questions (< 3.0) first, then others sorted by score
    low_score_sorted = sorted(low_score, key=lambda x: x.get("overall_score", 0))
    other_successful = sorted(
        [e for e in successful if e.get("overall_score", 0) >= 3.0],
        key=lambda x: x.get("overall_score", 0)
    )
    
    # Failed evaluations at the end
    failed = [e for e in evaluations if not (isinstance(e, dict) and e.get("success"))]
    
    # Combine: low scores first, then others, then failed
    sorted_evaluations = low_score_sorted + other_successful + failed
    
    # Reorder each evaluation to put question_id first
    sorted_evaluations = [reorder_dict_keys(e, "question_id") for e in sorted_evaluations]

    # Write JSONL format (one JSON object per line)
    report_dir = os.path.dirname(os.path.abspath(filepath))
    base_name = os.path.basename(filepath)
    # Remove existing extensions and add evaluation report suffix
    if base_name.endswith(".jsonl"):
        report_name = base_name[:-6] + "_evaluation_report.jsonl"
    elif base_name.endswith(".json"):
        report_name = base_name[:-5] + "_evaluation_report.jsonl"
    else:
        report_name = base_name + "_evaluation_report.jsonl"
    report_file = os.path.join(report_dir, report_name)
    
    with open(report_file, "w", encoding="utf-8") as f:
        # Write summary as first line (optional metadata)
        summary = {
            "summary": {
                "domain": domain,
                "test_type": test_type,
                "total_questions": len(evaluations),
                "successful_evaluations": len(successful),
                "failed_evaluations": len(evaluations) - len(successful),
                "average_scores": averages,
                "low_score_count": len(low_score),
                "logic_issue_count": len(logic_issues),
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
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Domain: {domain}")
    print(f"Test Type: {test_type}")
    print(f"Total Questions: {len(evaluations)}")
    print(f"Successful: {len(successful)}")
    print("\nAverage Scores:")
    print(f"  Technical Accuracy:      {averages.get('technical_accuracy', 0):.2f}")
    print(f"  Cognitive Trap Design:   {averages.get('cognitive_trap_design', 0):.2f}")
    print(f"  Difficulty Discrimination: {averages.get('difficulty_discrimination', 0):.2f}")
    print(f"  Domain Relevance:        {averages.get('domain_relevance', 0):.2f}")
    print(f"  Test Effectiveness:      {averages.get('test_effectiveness', 0):.2f}")
    print(f"  Overall Score:           {averages.get('overall_score', 0):.2f}")
    print(f"\nLow Score (< 3.0): {len(low_score)}")
    print(f"Logic/Answer Confusion (FCT/NOTA): {len(logic_issues)}")
    print(f"\nReport (JSONL format): {report_file}")
    print(f"  - Low score questions appear first")
    print(f"  - Questions sorted by score (lowest to highest)")
    print(f"  - ID field is first in each question")
    print("=" * 60)

    return {
        "report_file": report_file,
        "domain": domain,
        "test_type": test_type,
        "total_questions": len(evaluations),
        "successful_evaluations": len(successful),
        "low_score_count": len(low_score),
        "logic_issue_count": len(logic_issues),
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
        print("Error: --sample requires a positive integer (e.g. --sample 5)")
        return 1

    if len(args) < 2:
        print(__doc__)
        print("\nUsage: python evaluate_benchmark_quality.py <test_type> <domain> [filepath] [--sample N] [--resume|--no-resume]")
        return 1

    test_type = args[0].upper()
    domain = args[1].lower()
    filepath = args[2] if len(args) > 2 else None

    if test_type not in ("FCT", "FQT", "NOTA"):
        print("Error: test_type must be FCT, FQT, or NOTA")
        return 1

    # Default filepath detection
    if not filepath:
        if test_type == "NOTA":
            filepath = "output/converted_none_of_above_benchmark.jsonl"
        elif test_type == "FCT":
            filepath = "output/false_confidence_test_benchmark.jsonl"
        elif test_type == "FQT":
            filepath = "output/fake_questions_test_benchmark.jsonl"
        else:
            print(f"Error: Cannot determine default filepath for test_type '{test_type}'")
            return 1

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return 1

    print("=" * 60)
    print("Benchmark Quality Evaluation")
    print("=" * 60)
    print(f"Test Type: {test_type}")
    print(f"Domain: {domain}")
    print(f"File: {filepath}")
    if sample:
        print(f"Sample: first {sample} questions")
    print(f"Resume: {resume}")
    print("=" * 60)

    try:
        evaluations, averages, checkpoint_path = evaluate_benchmark(
            filepath, test_type, domain, sample=sample, resume=resume
        )
        generate_report(
            evaluations, averages, test_type, domain, filepath, checkpoint_path
        )
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
