"""
Build NOTA v3.2: Copy NOTA v3, add SGLT2 + 神经并发症 NOTA from FCT v3.5 conversion and new generation.

- Base: Full copy of output/nota/1000q_diabetes_nota_benchmark_v3.jsonl.
- FCT source: output/Json/1000q_diabetes_fct_benchmark_v3.5.json + evaluation report JSONL.
- Topic match: 药理学 (SGLT2), 神经并发症 (diabetic neuropathy, etc.).
- Converts matched FCT items to NOTA via DeepSeek, appends to v3.2.
- Optionally generates additional NOTA on these topics until target coverage.

Usage:
  Set DEEPSEEK_API_KEY; then:
  python scripts/build_nota_v3_2_sglt2_neuro.py
  python scripts/build_nota_v3_2_sglt2_neuro.py --fct-eval output/Json/1000q_diabetes_fct_benchmark_v3.5_evaluation_report.jsonl --target-sglt2 40 --target-neuro 40
"""

from __future__ import annotations

import json
import os
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import requests

# Add project root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# DeepSeek
DS_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_DS_MODEL = "deepseek-chat"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2.0
RATE_LIMIT_DELAY_SEC = 1.5
REQUEST_TIMEOUT_SEC = 60

# Topic keywords (case-insensitive)
SGLT2_KEYWORDS = [
    "sglt2", "empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin",
    "gliflozin", "sodium-glucose", "euglycemic dka", "cardiorenal", "药理学",
]
NEURO_KEYWORDS = [
    "neuropath", "neuropathy", "peripheral neuro", "autonomic", "monofilament",
    "10-g", "vibration sense", "neuropathic pain", "diabetic foot", "gastroparesis",
    "nerve", "神经", "神经并发症", "神经病变", "并发症",
]


def _extract_json(content: str) -> str:
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    if "{" in content:
        start = content.find("{")
        end = content.rfind("}") + 1
        content = content[start:end]
    content = re.sub(r",(\s*[}\]])", r"\1", content)
    return content


def _ds_post(api_key: str, api_url: str, data: Dict) -> requests.Response:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(api_url, headers=headers, json=data, timeout=REQUEST_TIMEOUT_SEC)
            if r.status_code == 429 or (500 <= r.status_code < 600):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SEC * (2 ** attempt))
                    continue
            r.raise_for_status()
            return r
        except (requests.exceptions.Timeout, requests.exceptions.RequestException):
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC * (2 ** attempt))
                continue
            raise
    raise requests.exceptions.RequestException(f"Failed after {MAX_RETRIES} attempts")


def validate_nota_structure(parsed: Dict) -> bool:
    options = parsed.get("options", [])
    if len(options) != 4:
        raise ValueError(f"Expected 4 options, got {len(options)}")
    correct = (parsed.get("correct_answer") or "").upper()
    if correct != "D":
        raise ValueError(f"NOTA must have correct_answer='D', got '{correct}'")
    d_opt = next((o for o in options if (o.get("option_id") or "").upper() == "D"), None)
    if not d_opt:
        raise ValueError("Option D missing")
    txt = (d_opt.get("text") or "").strip().lower()
    if "none of the above" not in txt and "以上都不是" not in txt:
        raise ValueError(f"Option D must be 'None of the above', got '{d_opt.get('text')}'")
    for o in options:
        oid = (o.get("option_id") or "").upper()
        if oid in ("A", "B", "C") and o.get("is_correct"):
            raise ValueError(f"Option {oid} must be incorrect in NOTA")
    return True


def read_jsonl(p: Path) -> List[Dict]:
    out: List[Dict] = []
    if not p.exists():
        return out
    with open(p, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if raw.startswith("["):
        out = json.loads(raw)
        return out if isinstance(out, list) else []
    for line in open(p, "r", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def topic_match(text: str, tags: Optional[List[str]] = None) -> Tuple[bool, bool]:
    t = (text or "").lower()
    tag_str = " ".join((tags or [])).lower()
    comb = t + " " + tag_str
    sglt2 = any(k.lower() in comb for k in SGLT2_KEYWORDS)
    neuro = any(k.lower() in comb for k in NEURO_KEYWORDS)
    return sglt2, neuro


def collect_nota_v3_topic_ids(nota: List[Dict]) -> Tuple[Set[str], Set[str]]:
    sglt2_ids: Set[str] = set()
    neuro_ids: Set[str] = set()
    for q in nota:
        qid = q.get("id") or ""
        parts = [q.get("question") or ""]
        for o in q.get("options") or []:
            parts.append(o.get("text") or "")
        tags = q.get("tags") or []
        s, n = topic_match(" ".join(parts), tags)
        if s:
            sglt2_ids.add(qid)
        if n:
            neuro_ids.add(qid)
    return sglt2_ids, neuro_ids


def load_fct_benchmark(p: Path) -> Dict[str, Dict]:
    """Load FCT benchmark (JSONL or JSON array); return id -> item."""
    by_id: Dict[str, Dict] = {}
    if not p.exists():
        return by_id
    items: List[Dict] = []
    with open(p, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if raw.startswith("["):
        data = json.loads(raw)
        items = data if isinstance(data, list) else []
    else:
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    for it in items:
        iid = it.get("id") or ""
        if iid:
            by_id[iid] = it
    return by_id


def load_fct_eval_report(p: Path) -> List[Dict]:
    """Load FCT evaluation report JSONL (skip summary line)."""
    out: List[Dict] = []
    if not p.exists():
        return out
    for line in open(p, "r", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "question_id" in obj:
                out.append(obj)
        except json.JSONDecodeError:
            pass
    return out


def match_fct_topic_entries(
    eval_entries: List[Dict],
) -> List[Tuple[str, str]]:
    """Return [(question_id, topic)] where topic in ('SGLT2','NEURO')."""
    matched: List[Tuple[str, str]] = []
    for e in eval_entries:
        qid = e.get("question_id") or ""
        if not qid:
            continue
        parts = [
            e.get("question") or "",
            " ".join(e.get("issues") or []),
            " ".join(e.get("strengths") or []),
            e.get("logic_check") or "",
            e.get("recommendation") or "",
        ]
        s, n = topic_match(" ".join(parts))
        if s:
            matched.append((qid, "SGLT2"))
        if n:
            matched.append((qid, "NEURO"))
    return matched


def convert_fct_to_nota(
    api_key: str,
    api_url: str,
    model: str,
    fct_item: Dict,
    topic: str,
) -> Optional[Dict]:
    """Call DeepSeek to convert one FCT question to NOTA. Returns NOTA dict or None."""
    q = fct_item.get("question") or ""
    opts = fct_item.get("options") or []
    correct = fct_item.get("correct_answer") or ""
    gt = fct_item.get("ground_truth") or fct_item.get("explanation") or ""
    opt_lines = "\n".join(f"  {o.get('option_id','?')}. {o.get('text','')}" for o in opts)

    system = (
        "You are a medical education expert specializing in diabetes care, creating NOTA (None of the above) "
        "multiple-choice questions. The correct answer is always D: 'None of the above'. "
        "Options A, B, C must each contain a clear medical error based on real patient/primary-care misconceptions; "
        "no option's core may be standard correct practice."
    )
    user = f"""Convert the following FCT (False Confidence Test) question into a NOTA question.

**Original FCT question:**
{q}

**Original options:**
{opt_lines}

**Original correct answer:** {correct}
**Summary of correct best practice (from FCT):** {gt[:800] if gt else "N/A"}

**Topic focus:** {topic} (药理学 SGLT2 or 神经并发症 as applicable).

Create a NEW NOTA MCQ on the *same* clinical point:
- Stem: Clear question with same clinical scenario/focus. The best-practice answer must exist but MUST NOT appear in any option.
- A, B, C: Each a distinct real-world misconception (plausible but wrong). Vary error types (e.g. cost-effectiveness, drug interactions, over/under-treatment, adherence).
- D: Exactly "None of the above", the only correct answer.

Return JSON only:
{{
  "question": "...",
  "options": [
    {{"option_id": "A", "text": "...", "is_correct": false}},
    {{"option_id": "B", "text": "...", "is_correct": false}},
    {{"option_id": "C", "text": "...", "is_correct": false}},
    {{"option_id": "D", "text": "None of the above", "is_correct": true}}
  ],
  "correct_answer": "D",
  "ground_truth": "Why D is correct and why A,B,C are wrong."
}}"""

    data = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.5,
        "max_tokens": 1500,
    }
    try:
        r = _ds_post(api_key, api_url, data)
        body = r.json()
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        raw = _extract_json(content)
        parsed = json.loads(raw)
        validate_nota_structure(parsed)
        return parsed
    except Exception:
        return None


def generate_nota_from_topic(
    api_key: str,
    api_url: str,
    model: str,
    topic_hint: str,
) -> Optional[Dict]:
    """Generate one NOTA question from a topic hint."""
    system = (
        "You are a medical education expert specializing in diabetes care, creating NOTA (None of the above) "
        "multiple-choice questions. The correct answer is always D: 'None of the above'. "
        "Options A, B, C must each contain a clear medical error based on real patient/primary-care misconceptions."
    )
    user = f"""Create a NOTA multiple-choice question on this topic:

**Topic:** {topic_hint}

Requirements:
- Clear stem; best-practice answer exists but is NOT in any option.
- A, B, C: distinct misconceptions (plausible, require expertise to reject).
- D: "None of the above" only correct answer.

Return JSON only:
{{
  "question": "...",
  "options": [
    {{"option_id": "A", "text": "...", "is_correct": false}},
    {{"option_id": "B", "text": "...", "is_correct": false}},
    {{"option_id": "C", "text": "...", "is_correct": false}},
    {{"option_id": "D", "text": "None of the above", "is_correct": true}}
  ],
  "correct_answer": "D",
  "ground_truth": "Why D is correct and why A,B,C are wrong."
}}"""

    data = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.6,
        "max_tokens": 1500,
    }
    try:
        r = _ds_post(api_key, api_url, data)
        body = r.json()
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        raw = _extract_json(content)
        parsed = json.loads(raw)
        validate_nota_structure(parsed)
        return parsed
    except Exception:
        return None


def fetch_metadata(
    api_key: str,
    api_url: str,
    model: str,
    question: str,
    options: List[Dict],
) -> Dict:
    """Fetch explanation, bias_targeted, difficulty_score, tags."""
    opt_txt = "\n".join(f"{o.get('option_id','?')}. {o.get('text','')}" for o in options)
    prompt = f"""Analyze this NOTA question (D = None of the above correct; A,B,C wrong).

Question: {question}

Options:
{opt_txt}

Return JSON only:
{{
  "explanation": "Why D is correct and why A,B,C are wrong.",
  "bias_targeted": ["authority","specificity"],
  "difficulty_score": 0.6,
  "tags": ["diabetes","NOTA","SGLT2 or neuropathy as appropriate"]
}}"""
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Expert in NOTA question analysis for diabetes education."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }
    try:
        r = _ds_post(api_key, api_url, data)
        body = r.json()
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        raw = _extract_json(content)
        p = json.loads(raw)
        tags = list(set((p.get("tags") or []) + ["diabetes", "NOTA"]))
        return {
            "explanation": p.get("explanation") or "",
            "bias_targeted": p.get("bias_targeted") or [],
            "difficulty_score": float(p.get("difficulty_score") or 0.5),
            "tags": tags,
        }
    except Exception:
        return {
            "explanation": "D is correct because none of A,B,C represent correct practice.",
            "bias_targeted": ["specificity"],
            "difficulty_score": 0.5,
            "tags": ["diabetes", "NOTA"],
        }


def build_nota_item(
    parsed: Dict,
    nota_id: str,
    method: str,
    model: str,
    meta: Dict,
    topic_tag: Optional[str] = None,
) -> Dict:
    base = (meta.get("tags") or []) + ["diabetes", "NOTA"]
    base = [t for t in base if t and " or " not in t and " as appropriate" not in (t or "")]
    tags = list(set(base))
    if topic_tag and topic_tag not in tags:
        tags.append(topic_tag)
    return {
        "id": nota_id,
        "generation_method": method,
        "question": parsed.get("question") or "",
        "options": parsed.get("options") or [],
        "correct_answer": "D",
        "ground_truth": parsed.get("ground_truth") or "",
        "explanation": meta.get("explanation") or "",
        "bias_targeted": meta.get("bias_targeted") or [],
        "difficulty_score": meta.get("difficulty_score", 0.5),
        "tags": tags,
        "test_type": "NOTA",
        "metadata": {
            "generated_by": "deepseek",
            "model": model,
            "generation_timestamp": datetime.now().isoformat(),
            "generation_method": method,
        },
    }


def run(
    nota_v3_path: Path,
    v32_path: Path,
    fct_benchmark_path: Path,
    fct_eval_path: Path,
    api_key: str,
    model: str,
    target_sglt2: int,
    target_neuro: int,
    skip_refine: bool,
    max_fct_convert: int,
) -> None:
    api_url = DS_API_URL

    # 1. Load NOTA v3 and copy to v3.2
    nota = read_jsonl(nota_v3_path)
    v32: List[Dict] = [dict(q) for q in nota]
    v32_path.parent.mkdir(parents=True, exist_ok=True)
    with open(v32_path, "w", encoding="utf-8") as f:
        for q in v32:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"[1] Copied {len(v32)} NOTA v3 questions to {v32_path}")

    # 2. Topic match on v3
    sglt2_ids, neuro_ids = collect_nota_v3_topic_ids(nota)
    print(f"[2] NOTA v3 topic match: SGLT2 {len(sglt2_ids)}, NEURO {len(neuro_ids)}")

    next_idx = len(v32) + 1
    added: List[Dict] = []

    # 3. FCT -> NOTA conversion
    fct_by_id = load_fct_benchmark(fct_benchmark_path)
    eval_entries = load_fct_eval_report(fct_eval_path)
    matched = match_fct_topic_entries(eval_entries)
    # Deduplicate by (qid, topic)
    seen_fct = set()
    fct_converted = 0
    for qid, topic in matched:
        if fct_converted >= max_fct_convert:
            break
        key = (qid, topic)
        if key in seen_fct:
            continue
        seen_fct.add(key)
        fct_item = fct_by_id.get(qid)
        if not fct_item:
            continue
        time.sleep(RATE_LIMIT_DELAY_SEC)
        converted = convert_fct_to_nota(api_key, api_url, model, fct_item, topic)
        if not converted:
            continue
        meta = fetch_metadata(
            api_key, api_url, model,
            converted.get("question") or "",
            converted.get("options") or [],
        )
        time.sleep(RATE_LIMIT_DELAY_SEC)
        nota_id = f"NOTA_{next_idx:03d}"
        next_idx += 1
        item = build_nota_item(
            converted, nota_id, "fct_v3_5_converted", model, meta,
            topic_tag="SGLT2" if topic == "SGLT2" else "neuropathy",
        )
        added.append(item)
        fct_converted += 1
        print(f"    Converted FCT {qid} -> {nota_id} [{topic}]")

    # 4. Optional refine of v3 topic questions (skip if skip_refine)
    if not skip_refine:
        for i, q in enumerate(v32):
            qid = q.get("id") or ""
            if qid not in sglt2_ids and qid not in neuro_ids:
                continue
            topic = "SGLT2" if qid in sglt2_ids else "神经并发症"
            # Simple refine: we could add a DS call here; for now we keep as-is to avoid excess API use.
            pass

    # 5. Append converted FCT->NOTA
    v32.extend(added)
    added_sglt2 = sum(1 for a in added if "SGLT2" in (a.get("tags") or []))
    added_neuro = sum(1 for a in added if "neuropathy" in (a.get("tags") or []))
    count_sglt2 = len(sglt2_ids) + added_sglt2
    count_neuro = len(neuro_ids) + added_neuro

    # 6. Generate new NOTA until targets met
    SGLT2_HINTS = [
        "SGLT2 inhibitors in T2DM with CKD or heart failure",
        "Euglycemic DKA risk with SGLT2",
        "SGLT2 and volume depletion / perioperative withholding",
        "SGLT2 cardiorenal protection indications",
    ]
    NEURO_HINTS = [
        "Screening for diabetic peripheral neuropathy (monofilament, 10-g)",
        "Neuropathic pain management in diabetes",
        "Autonomic neuropathy (orthostatic hypotension, gastroparesis)",
        "Diabetic foot care and ulcer prevention",
    ]
    need_sglt2 = max(0, target_sglt2 - count_sglt2)
    need_neuro = max(0, target_neuro - count_neuro)
    gen_count = 0
    while need_sglt2 > 0 or need_neuro > 0:
        hint = None
        topic_tag = None
        if need_sglt2 >= need_neuro and need_sglt2 > 0:
            hint = SGLT2_HINTS[gen_count % len(SGLT2_HINTS)]
            topic_tag = "SGLT2"
            need_sglt2 -= 1
        elif need_neuro > 0:
            hint = NEURO_HINTS[gen_count % len(NEURO_HINTS)]
            topic_tag = "neuropathy"
            need_neuro -= 1
        if not hint:
            break
        time.sleep(RATE_LIMIT_DELAY_SEC)
        parsed = generate_nota_from_topic(api_key, api_url, model, hint)
        if not parsed:
            continue
        meta = fetch_metadata(
            api_key, api_url, model,
            parsed.get("question") or "",
            parsed.get("options") or [],
        )
        time.sleep(RATE_LIMIT_DELAY_SEC)
        nota_id = f"NOTA_{next_idx:03d}"
        next_idx += 1
        item = build_nota_item(parsed, nota_id, "scratch", model, meta, topic_tag=topic_tag)
        v32.append(item)
        gen_count += 1
        print(f"    Generated {nota_id} [{topic_tag}]")

    # 7. Write final v3.2
    with open(v32_path, "w", encoding="utf-8") as f:
        for q in v32:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"[7] Wrote {len(v32)} questions to {v32_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build NOTA v3.2 (v3 copy + SGLT2/NEURO NOTA from FCT + new gen)")
    ap.add_argument("--nota-v3", type=Path, default=Path("output/nota/1000q_diabetes_nota_benchmark_v3.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("output/nota/1000q_diabetes_nota_benchmark_v3.2.jsonl"))
    ap.add_argument("--fct-benchmark", type=Path, default=Path("output/Json/1000q_diabetes_fct_benchmark_v3.5.json"))
    ap.add_argument("--fct-eval", type=Path, default=Path("output/Json/1000q_diabetes_fct_benchmark_v3.5_evaluation_report.jsonl"))
    ap.add_argument("--api-key", type=str, default=os.getenv("DEEPSEEK_API_KEY"))
    ap.add_argument("--model", type=str, default=DEFAULT_DS_MODEL)
    ap.add_argument("--target-sglt2", type=int, default=40)
    ap.add_argument("--target-neuro", type=int, default=40)
    ap.add_argument("--skip-refine", action="store_true", help="Do not refine existing v3 topic questions")
    ap.add_argument("--max-fct-convert", type=int, default=50, help="Max FCT items to convert to NOTA (default 50)")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    nota_v3 = root / args.nota_v3 if not args.nota_v3.is_absolute() else args.nota_v3
    v32 = root / args.output if not args.output.is_absolute() else args.output
    fct_b = root / args.fct_benchmark if not args.fct_benchmark.is_absolute() else args.fct_benchmark
    fct_e = root / args.fct_eval if not args.fct_eval.is_absolute() else args.fct_eval

    api_key = (args.api_key or "").strip()
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not set and --api-key not provided")
        return 1

    if not nota_v3.exists():
        print(f"Error: NOTA v3 not found at {nota_v3}")
        return 1

    run(
        nota_v3_path=nota_v3,
        v32_path=v32,
        fct_benchmark_path=fct_b,
        fct_eval_path=fct_e,
        api_key=api_key,
        model=args.model,
        target_sglt2=args.target_sglt2,
        target_neuro=args.target_neuro,
        skip_refine=args.skip_refine,
        max_fct_convert=args.max_fct_convert,
    )
    return 0


if __name__ == "__main__":
    exit(main())
