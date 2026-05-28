"""
Generate NOTA (None of the Above) Benchmark — 1000q run with DeepSeek API.

Same as generate_nota_benchmark_v2_concurrent, plus:
- CRITICAL STOP LIST: Forbidden topics (insulin pump troubleshooting, sick day/ketones, Ramadan, 15g hypoglycemia).
- FOCUS AREAS: Must generate only from Gestational Diabetes, Diabetic Foot, Technology Interference, Rare Complications.

Target: up to 1000 questions. Use --use-focus-topics (default) to force topic/scratch from FOCUS areas only.
"""
import json
import os
import re
import random
import time
import argparse
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# DeepSeek API constants
DS_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_DS_MODEL = "deepseek-chat"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2.0
RATE_LIMIT_DELAY_SEC = 0.5  # Reduced since we have semaphore control
REQUEST_TIMEOUT_SEC = 60
MAX_CONCURRENT_REQUESTS = 4  # Default max concurrent API calls

# --- CRITICAL STOP LIST & FOCUS AREAS (must be included in prompts) ---
CRITICAL_STOP_LIST = """
# CRITICAL STOP LIST (Do NOT Generate)
The following topics are OVER-REPRESENTED in the seed data. You are strictly FORBIDDEN from generating any more questions about them:
1. Insulin Pump Failure / Troubleshooting (We already have 73!)
2. Sick Day Rules / Ketones (We already have 68!)
3. Ramadan Fasting
4. Hypoglycemia treatment with 15g carbs
"""

FOCUS_AREAS_INTRO = """
# FOCUS AREAS (MUST Generate)
You MUST strictly focus on these topics only. Generate questions from ONE of:
1. Gestational Diabetes (GDM): Metformin safety in pregnancy, time in range targets.
2. Diabetic Foot: Wagner grade, Charcot foot diagnosis.
3. Technology Interference: Vitamin C effects on CGM, Acetaminophen interference.
4. Rare Complications: Gastroparesis (GLP-1 contradiction), Necrobiosis Lipoidica.
"""

# Expanded topic hints for topic/scratch methods (more variety)
FOCUS_TOPICS_EXPANDED = [
    "Gestational diabetes: metformin safety in pregnancy",
    "Gestational diabetes: time in range targets in GDM",
    "Diabetic foot: Wagner grade classification",
    "Diabetic foot: Charcot foot diagnosis",
    "CGM technology: Vitamin C effects on CGM accuracy",
    "CGM technology: Acetaminophen interference with CGM",
    "Rare complications: Gastroparesis and GLP-1 contraindication",
    "Rare complications: Necrobiosis lipoidica",
]

# --- v3.1 Task topics (A: 200, B: 100, C: 115 = 415 questions) ---
V31_FOCUS_AREAS_INTRO = """
# v3.1 FOCUS AREAS (MUST Generate from these three tasks only)

**Task A — Cardio-Renal-Metabolic (200 questions)**  
Keywords to include: SGLT2 inhibitors, Euglycemic DKA, Fournier's Gangrene, GLP-1 and Gastroparesis, Semaglutide in Retinopathy (SUSTAIN-6 signal).  
Scenarios: Heart failure HFpEF, CKD with proteinuria.

**Task B — Neuro/Ophtho (100 questions)**  
Keywords: Autonomic Neuropathy (orthostatic hypotension, erectile dysfunction), Proliferative Diabetic Retinopathy (Anti-VEGF vs Laser).

**Task C — The Long Tail / Differential & Rare (115 questions)**  
Keywords: LADA (misdiagnosed as type 2), MODY, Hemochromatosis (bronze diabetes), Steroid-induced hyperglycemia.
"""

# Topic hints for v3.1: 200 A + 100 B + 115 C (repeated for variety)
_V31_TASK_A_HINTS = [
    "SGLT2 inhibitors in heart failure HFpEF",
    "SGLT2 inhibitors in CKD with proteinuria",
    "Euglycemic diabetic ketoacidosis with SGLT2",
    "Fournier's gangrene and SGLT2 inhibitors",
    "GLP-1 receptor agonists and gastroparesis contraindication",
    "Semaglutide and retinopathy SUSTAIN-6 signal",
    "SGLT2 and acute kidney injury / volume depletion",
    "GLP-1 in cardiovascular outcomes",
    "HFpEF and diabetes pharmacotherapy",
    "CKD proteinuria and SGLT2",
]
_V31_TASK_B_HINTS = [
    "Autonomic neuropathy orthostatic hypotension",
    "Diabetic autonomic neuropathy erectile dysfunction",
    "Proliferative diabetic retinopathy Anti-VEGF",
    "Proliferative retinopathy laser vs Anti-VEGF",
    "Gastroparesis and diabetic neuropathy",
    "Cardiovascular autonomic neuropathy",
    "Neuropathic pain and diabetes",
]
_V31_TASK_C_HINTS = [
    "LADA latent autoimmune diabetes misdiagnosed as type 2",
    "MODY maturity-onset diabetes of the young",
    "Hemochromatosis bronze diabetes",
    "Steroid-induced hyperglycemia",
    "LADA vs type 2 differential",
    "MODY genetic testing",
    "Steroid-induced diabetes management",
]
# Exact counts: 200 (A) + 100 (B) + 115 (C) = 415
V31_TOPICS_EXPANDED = (
    (_V31_TASK_A_HINTS * 20)[:200]
    + (_V31_TASK_B_HINTS * 15)[:100]
    + (_V31_TASK_C_HINTS * 17)[:115]
)


def read_jsonl(filepath: Path) -> List[Dict]:
    """Read JSONL or JSON file and return list of questions"""
    questions = []
    if not filepath.exists():
        return questions
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if content.startswith('['):
            # JSON array format
            data = json.loads(content)
            for item in data:
                questions.append(item)
        else:
            # JSONL format
            f.seek(0)
            for line in f:
                if line.strip():
                    questions.append(json.loads(line))
    return questions


def extract_json_from_response(content: str) -> str:
    """Extract JSON from response, handling markdown code blocks and common issues"""
    # Extract JSON if wrapped in markdown code blocks
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    
    # Try to find JSON object
    if '{' in content:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        content = content[json_start:json_end]
    
    # Fix common JSON issues: remove trailing commas before closing braces/brackets
    content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    return content


async def _ds_post_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    data: Dict,
    semaphore: asyncio.Semaphore,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY_SEC
) -> Dict:
    """
    Make DeepSeek API POST request asynchronously with retry logic and exponential backoff
    
    Args:
        session: aiohttp ClientSession
        api_key: DeepSeek API key
        api_url: API endpoint URL
        data: Request payload
        semaphore: Semaphore to limit concurrent requests
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (seconds)
    
    Returns:
        Response JSON dictionary
    
    Raises:
        aiohttp.ClientError: If all retries fail
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    async with semaphore:  # Limit concurrent requests
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SEC)
                async with session.post(
                    api_url,
                    headers=headers,
                    json=data,
                    timeout=timeout
                ) as response:
                    # Retry on rate limit (429) or server errors (5xx)
                    if response.status == 429:
                        wait_time = retry_delay * (2 ** attempt)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(wait_time)
                            continue
                    
                    if 500 <= response.status < 600:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
                raise
            
            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
                raise
        
        raise aiohttp.ClientError(f"Failed after {max_retries} attempts")


def validate_nota_structure(parsed: Dict) -> bool:
    """
    Validate that the generated question follows NOTA structure:
    - D is always correct ("None of the above")
    - A, B, C are all incorrect
    
    Args:
        parsed: Parsed JSON response from API
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    options = parsed.get("options", [])
    if len(options) != 4:
        raise ValueError(f"Expected 4 options, got {len(options)}")
    
    correct_id = parsed.get("correct_answer", "").upper()
    if correct_id != "D":
        raise ValueError(f"NOTA questions must have correct_answer='D', got '{correct_id}'")
    
    # Check that D is "None of the above"
    d_option = next((opt for opt in options if opt.get('option_id', '').upper() == 'D'), None)
    if not d_option:
        raise ValueError("Option D is missing")
    
    d_text = d_option.get('text', '').strip().lower()
    if 'none of the above' not in d_text and '以上都不是' not in d_text:
        raise ValueError(f"Option D must be 'None of the above', got '{d_option.get('text', '')}'")
    
    # Ensure all options have correct structure
    for opt in options:
        if 'option_id' not in opt:
            raise ValueError("Option missing option_id")
        if 'text' not in opt:
            raise ValueError(f"Option {opt.get('option_id')} missing text")
        if 'is_correct' not in opt:
            opt['is_correct'] = (opt['option_id'].upper() == 'D')
    
    # Verify A, B, C are all incorrect
    for opt in options:
        opt_id = opt.get('option_id', '').upper()
        if opt_id in ['A', 'B', 'C']:
            if opt.get('is_correct', False):
                raise ValueError(f"Option {opt_id} must be incorrect in NOTA format")
    
    return True


async def generate_nota_mc_with_deepseek_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    input_context: str,
    method: str,
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.6,
    focus_areas_intro: Optional[str] = None,
) -> Dict:
    """
    Core async function using DeepSeek API to create NOTA multiple-choice questions
    
    Args:
        session: aiohttp ClientSession
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name (deepseek-chat or deepseek-reasoner)
        input_context: Context based on generation method (topic, seed QA, existing MC, or scratch)
        method: Generation method name
        question_num: Question number for tracking
        semaphore: Semaphore to limit concurrent requests
        temperature: Temperature for generation (0.5-0.7)
    
    Returns:
        Dictionary with question, options, correct_answer, ground_truth, success, error
    """
    focus_intro = focus_areas_intro if focus_areas_intro is not None else FOCUS_AREAS_INTRO
    system = (
        "You are a medical education expert specializing in diabetes care, creating NOTA (None of the Above) multiple-choice questions. "
        "The correct answer is always D: 'None of the above'. Options A, B, C must each contain a clear medical error based on real patient/primary-care misconceptions; no option's core may be standard correct practice."
        + CRITICAL_STOP_LIST
        + focus_intro
    )

    # Base requirements for NOTA questions
    base_req = """
Requirements for the question:
1. **Question Stem**: 
   - Clear, specific question testing one core clinical knowledge point
   - Must have a clear best-practice answer (not explicitly presented in any option)
   - May include brief but complete clinical scenario
   - Avoid vague or double-negative phrasing
   - Vary patient demographics across questions. Use diverse ages (e.g., 30s-80s, not always 68-year-old), genders, and backgrounds. Avoid repetitive patterns like repeatedly using the same age or gender.

2. **Options A, B, C (All Incorrect)**:
   - Each MUST contain a clear, professional medical error rooted in real patient or primary-care misconceptions
   - Errors should appear plausible but require expertise to identify
   - Avoid obviously absurd or off-topic statements
   - While options may include partially correct information, they must be fundamentally flawed
   - No option's core statement should represent standard correct clinical practice
   - Each error should reflect a typical cognitive bias or misconception

3. **Option D (Always Correct)**:
   - Must be exactly "None of the above"
   - This is the sole correct answer

4. **Validation**:
   - Selecting D must necessitate the exclusion of all seemingly plausible but incorrect options
   - Each error in A, B, C should reflect a typical cognitive bias or misconception in diabetes care
"""
    
    json_spec = """
Return JSON format:
{
  "question": "Question stem with optional clinical context",
  "options": [
    {"option_id": "A", "text": "Option A with clear medical error/misconception", "is_correct": false},
    {"option_id": "B", "text": "Option B with clear medical error/misconception", "is_correct": false},
    {"option_id": "C", "text": "Option C with clear medical error/misconception", "is_correct": false},
    {"option_id": "D", "text": "None of the above", "is_correct": true}
  ],
  "correct_answer": "D",
  "ground_truth": "Detailed explanation of why D is correct and why A, B, C are all wrong"
}"""
    
    # Build prompt based on method
    if method == "topic":
        prompt = f"""{system}

Topic: {input_context}

{base_req}

{json_spec}"""

    elif method == "seed_qa":
        # Parse input_context as JSON with question and answer
        try:
            qa_data = json.loads(input_context) if isinstance(input_context, str) else input_context
            question_text = qa_data.get('question', '')
            answer_text = qa_data.get('answer', qa_data.get('output', ''))
        except:
            question_text = input_context.split('\n')[0] if '\n' in input_context else input_context
            answer_text = ""
        
        prompt = f"""{system}

Convert the following Q&A pair into a NOTA multiple-choice question.

Original Question: {question_text}
Original Answer: {answer_text}

{base_req}

Note: The original answer represents the correct best practice, but it should NOT appear in any of options A, B, C. Instead, create three incorrect options based on common misconceptions related to this topic.

{json_spec}"""

    elif method == "existing_mc":
        # Parse input_context as existing MC question
        try:
            mc_data = json.loads(input_context) if isinstance(input_context, str) else input_context
            existing_question = mc_data.get('question', '')
            existing_options = mc_data.get('options', [])
            existing_correct = mc_data.get('correct_answer', '')
        except:
            existing_question = input_context
            existing_options = []
            existing_correct = ''
        
        options_text = "\n".join([f"{opt.get('option_id', '?')}. {opt.get('text', '')}" for opt in existing_options])
        
        prompt = f"""{system}

Transform the following multiple-choice question into NOTA format.

Existing Question: {existing_question}

Existing Options:
{options_text}

Current Correct Answer: {existing_correct}

{base_req}

Important: Transform this question so that D ("None of the above") becomes the correct answer. Ensure that options A, B, C all contain clear medical errors/misconceptions, and that the actual correct answer is not explicitly stated in any option.

{json_spec}"""

    else:  # scratch
        prompt = f"""{system}

Create a completely new NOTA multiple-choice question.

Topic area (optional): {input_context if input_context else "Any important diabetes clinical topic"}

{base_req}

{json_spec}"""

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1500
    }
    
    try:
        response_json = await _ds_post_async(session, api_key, api_url, data, semaphore)
        content = response_json['choices'][0]['message']['content']
        
        # Extract and parse JSON
        json_content = extract_json_from_response(content)
        parsed = json.loads(json_content)
        
        # Validate NOTA structure
        validate_nota_structure(parsed)
        
        return {
            "question": parsed.get("question", ""),
            "options": parsed.get("options", []),
            "correct_answer": "D",
            "ground_truth": parsed.get("ground_truth", ""),
            "success": True,
            "error": None,
            "raw_response": content
        }
    except Exception as e:
        return {
            "question": "",
            "options": [],
            "correct_answer": None,
            "ground_truth": "",
            "success": False,
            "error": str(e),
            "raw_response": ""
        }


async def generate_nota_metadata_with_deepseek_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    question: str,
    options: List[Dict],
    correct_answer: str,
    semaphore: asyncio.Semaphore,
    original_tags: List[str] = None
) -> Dict:
    """
    Generate explanation, bias_targeted, difficulty_score, and tags using DeepSeek API for NOTA questions (async)
    
    Args:
        session: aiohttp ClientSession
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        question: Question text
        options: List of option dictionaries
        correct_answer: Correct answer ID (should always be "D" for NOTA)
        semaphore: Semaphore to limit concurrent requests
        original_tags: Original tags to merge
    
    Returns:
        Dictionary with explanation, bias_targeted, difficulty_score, tags, success
    """
    options_text = "\n".join([f"{opt['option_id']}. {opt['text']}" for opt in options])
    
    prompt = f"""Analyze this NOTA (None of the Above) multiple-choice question about diabetes and provide detailed metadata.

Question: {question}

Options:
{options_text}

Correct Answer: D. None of the above

This is a NOTA question, meaning:
- Option D ("None of the above") is the correct answer
- Options A, B, C all contain medical errors/misconceptions
- Selecting D requires recognizing that all other options are flawed

Provide:
1. A clear explanation of why D is correct (because none of A, B, C represent correct practice) and why each of A, B, C is wrong (identify the specific error/misconception in each)
2. Identify cognitive biases this question targets (e.g., "authority", "specificity", "confirmation", "anchoring", "availability", "representativeness")
3. Estimate difficulty score (0.0 to 1.0, where 0.0 is very easy and 1.0 is very hard)
4. Suggest relevant tags (include domain tags like "diabetes", "NOTA", and topic tags)

Return JSON ONLY:
{{
  "explanation": "Detailed explanation of why D is correct and why A, B, C are all wrong...",
  "bias_targeted": ["authority", "specificity"],
  "difficulty_score": 0.7,
  "tags": ["diabetes", "NOTA", "treatment", "type2"]
}}"""

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert in educational assessment and cognitive bias analysis for medical education, specializing in NOTA question analysis."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }
    
    try:
        response_json = await _ds_post_async(session, api_key, api_url, data, semaphore)
        content = response_json['choices'][0]['message']['content']
        
        # Extract and parse JSON
        json_content = extract_json_from_response(content)
        parsed = json.loads(json_content)
        
        # Merge with original tags
        tags = list(set(parsed.get("tags", []) + (original_tags or [])))
        if "diabetes" not in tags:
            tags.append("diabetes")
        if "NOTA" not in tags:
            tags.append("NOTA")
        
        return {
            "explanation": parsed.get("explanation", ""),
            "bias_targeted": parsed.get("bias_targeted", []),
            "difficulty_score": float(parsed.get("difficulty_score", 0.5)),
            "tags": tags,
            "success": True
        }
    except Exception as e:
        # Fallback values
        tags = ["diabetes", "NOTA"] + (original_tags or [])
        return {
            "explanation": f"Option D is correct because none of the options A, B, C represent correct clinical practice. Each contains a medical error or misconception.",
            "bias_targeted": ["specificity"],
            "difficulty_score": 0.5,
            "tags": list(set(tags)),
            "success": False,
            "error": str(e)
        }


async def generate_nota_from_topic_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    topic: str,
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.6,
    focus_areas_intro: Optional[str] = None,
) -> Optional[Dict]:
    """
    Generate NOTA question from a topic (async)
    
    Args:
        session: aiohttp ClientSession
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        topic: Topic string
        question_num: Question number
        semaphore: Semaphore to limit concurrent requests
        temperature: Temperature for generation
        focus_areas_intro: Optional override for FOCUS_AREAS in system prompt (e.g. v3.1 tasks)
    
    Returns:
        NOTA question dictionary or None if failed
    """
    mc_result = await generate_nota_mc_with_deepseek_async(
        session, api_key, api_url, model, topic, "topic", question_num, semaphore, temperature,
        focus_areas_intro=focus_areas_intro,
    )
    
    if not mc_result.get("success"):
        return None
    
    return {
        "generation_method": "topic",
        "question": mc_result["question"],
        "options": mc_result["options"],
        "correct_answer": mc_result["correct_answer"],
        "ground_truth": mc_result["ground_truth"],
        "raw_mc_response": mc_result.get("raw_response", "")
    }


async def generate_nota_from_seed_qa_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    seed_qa: Dict,
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.6,
    focus_areas_intro: Optional[str] = None,
) -> Optional[Dict]:
    """
    Generate NOTA question from seed Q&A pair (async)
    """
    input_context = json.dumps({
        "question": seed_qa.get("question", seed_qa.get("input", "")),
        "answer": seed_qa.get("answer", seed_qa.get("output", ""))
    })
    
    mc_result = await generate_nota_mc_with_deepseek_async(
        session, api_key, api_url, model, input_context, "seed_qa", question_num, semaphore, temperature,
        focus_areas_intro=focus_areas_intro,
    )
    
    if not mc_result.get("success"):
        return None
    
    return {
        "generation_method": "seed_qa",
        "question": mc_result["question"],
        "options": mc_result["options"],
        "correct_answer": mc_result["correct_answer"],
        "ground_truth": mc_result["ground_truth"],
        "raw_mc_response": mc_result.get("raw_response", ""),
        "original_question": seed_qa.get("question", seed_qa.get("input", "")),
        "original_answer": seed_qa.get("answer", seed_qa.get("output", ""))
    }


async def generate_nota_from_existing_mc_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    existing_mc: Dict,
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.6,
    focus_areas_intro: Optional[str] = None,
) -> Optional[Dict]:
    """
    Generate NOTA question by transforming existing MC question (async)
    
    Args:
        session: aiohttp ClientSession
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        existing_mc: Existing multiple-choice question dictionary
        question_num: Question number
        semaphore: Semaphore to limit concurrent requests
        temperature: Temperature for generation
    
    Returns:
        NOTA question dictionary or None if failed
    """
    input_context = json.dumps({
        "question": existing_mc.get("question", ""),
        "options": existing_mc.get("options", []),
        "correct_answer": existing_mc.get("correct_answer", "")
    })
    
    mc_result = await generate_nota_mc_with_deepseek_async(
        session, api_key, api_url, model, input_context, "existing_mc", question_num, semaphore, temperature,
        focus_areas_intro=focus_areas_intro,
    )
    
    if not mc_result.get("success"):
        return None
    
    return {
        "generation_method": "existing_mc",
        "question": mc_result["question"],
        "options": mc_result["options"],
        "correct_answer": mc_result["correct_answer"],
        "ground_truth": mc_result["ground_truth"],
        "raw_mc_response": mc_result.get("raw_response", ""),
        "original_id": existing_mc.get("id", ""),
        "original_question": existing_mc.get("question", "")
    }


async def generate_nota_from_scratch_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    topic_hint: str,
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.7,
    focus_areas_intro: Optional[str] = None,
) -> Optional[Dict]:
    """
    Generate NOTA question from scratch (async)
    """
    mc_result = await generate_nota_mc_with_deepseek_async(
        session, api_key, api_url, model, topic_hint, "scratch", question_num, semaphore, temperature,
        focus_areas_intro=focus_areas_intro,
    )
    
    if not mc_result.get("success"):
        return None
    
    return {
        "generation_method": "scratch",
        "question": mc_result["question"],
        "options": mc_result["options"],
        "correct_answer": mc_result["correct_answer"],
        "ground_truth": mc_result["ground_truth"],
        "raw_mc_response": mc_result.get("raw_response", ""),
        "topic_hint": topic_hint
    }


# Scratch topic hints (used only when not use_focus_topics)
SCRATCH_TOPIC_HINTS = [
    "Type 2 diabetes initial treatment",
    "Diabetic retinopathy screening",
    "Diabetic foot care",
    "Gestational diabetes management",
]


async def generate_single_question_async(
    session: aiohttp.ClientSession,
    api_key: str,
    api_url: str,
    model: str,
    method: str,
    method_data: Dict,
    method_locks: Dict[str, asyncio.Lock],
    question_num: int,
    semaphore: asyncio.Semaphore,
    temperature: float = 0.6
) -> Tuple[Optional[Dict], str, int]:
    """
    Generate a single NOTA question asynchronously
    
    Returns:
        Tuple of (nota_data dict, method name, question_num)
    """
    lock = method_locks.get(method)
    
    if method == "topic":
        async with lock:
            topic_idx = method_data["topic"]["index"] % len(method_data["topic"]["items"])
            topic = method_data["topic"]["items"][topic_idx]
            method_data["topic"]["index"] += 1
        focus_intro = method_data.get("_focus_areas_intro")
        nota_data = await generate_nota_from_topic_async(
            session, api_key, api_url, model, topic, question_num, semaphore, temperature,
            focus_areas_intro=focus_intro,
        )
    
    elif method == "seed_qa":
        async with lock:
            qa_idx = method_data["seed_qa"]["index"] % len(method_data["seed_qa"]["items"])
            seed_qa = method_data["seed_qa"]["items"][qa_idx]
            method_data["seed_qa"]["index"] += 1
        focus_intro = method_data.get("_focus_areas_intro")
        nota_data = await generate_nota_from_seed_qa_async(
            session, api_key, api_url, model, seed_qa, question_num, semaphore, temperature,
            focus_areas_intro=focus_intro,
        )
    
    elif method == "existing_mc":
        async with lock:
            mc_idx = method_data["existing_mc"]["index"] % len(method_data["existing_mc"]["items"])
            existing_mc = method_data["existing_mc"]["items"][mc_idx]
            method_data["existing_mc"]["index"] += 1
        focus_intro = method_data.get("_focus_areas_intro")
        nota_data = await generate_nota_from_existing_mc_async(
            session, api_key, api_url, model, existing_mc, question_num, semaphore, temperature,
            focus_areas_intro=focus_intro,
        )
    
    else:  # scratch
        async with lock:
            hint_idx = method_data["scratch"]["index"] % len(method_data["scratch"]["items"])
            topic_hint = method_data["scratch"]["items"][hint_idx]
            method_data["scratch"]["index"] += 1
        focus_intro = method_data.get("_focus_areas_intro")
        nota_data = await generate_nota_from_scratch_async(
            session, api_key, api_url, model, topic_hint, question_num, semaphore, temperature,
            focus_areas_intro=focus_intro,
        )
    
    return nota_data, method, question_num


async def create_nota_benchmark_v2_concurrent(
    api_key: str,
    api_url: str,
    model: str,
    methods: List[str] = ["all"],
    topics_file: Optional[Path] = None,
    seed_qa_file: Optional[Path] = None,
    existing_mc_file: Optional[Path] = None,
    num_questions: int = 100,
    temperature: float = 0.6,
    output_file: Optional[Path] = None,
    checkpoint_interval: int = 10,
    max_concurrent: int = MAX_CONCURRENT_REQUESTS,
    use_focus_topics: bool = False,
    topic_set: str = "focus",
) -> Tuple[List[Dict], Dict]:
    """
    Main orchestration function to create NOTA benchmark with concurrent processing
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        methods: List of methods to use (["all"] or ["topic", "seed_qa", "existing_mc", "scratch"])
        topics_file: Path to topics file (one per line)
        seed_qa_file: Path to seed Q&A JSONL file
        existing_mc_file: Path to existing MC benchmark JSONL file
        num_questions: Total number of questions to generate
        temperature: Temperature for generation
        output_file: Output file path
        checkpoint_interval: Save checkpoint every N questions
        max_concurrent: Maximum concurrent API requests
    
    Returns:
        Tuple of (list of NOTA questions, statistics dictionary)
    """
    if "all" in methods:
        methods = ["topic", "seed_qa", "existing_mc", "scratch"]
    
    # Load input data
    topics = []
    seed_qa_pairs = []
    existing_mc_questions = []
    
    if "topic" in methods:
        if topic_set == "v3.1":
            topics = V31_TOPICS_EXPANDED.copy()
        elif use_focus_topics:
            topics = FOCUS_TOPICS_EXPANDED.copy()
        elif topics_file and topics_file.exists():
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics = [line.strip() for line in f if line.strip()]
    
    if "seed_qa" in methods and seed_qa_file and seed_qa_file.exists():
        for item in read_jsonl(seed_qa_file):
            ans = item.get("answer") or item.get("output") or item.get("ground_truth")
            if "question" in item and ans:
                seed_qa_pairs.append({**item, "answer": ans if isinstance(ans, str) else ""})
    
    if "existing_mc" in methods and existing_mc_file and existing_mc_file.exists():
        existing_mc_questions = read_jsonl(existing_mc_file)
        random.shuffle(existing_mc_questions)
    
    # Filter out methods that don't have input data
    available_methods = []
    for method in methods:
        if method == "topic" and topics:
            available_methods.append(method)
        elif method == "seed_qa" and seed_qa_pairs:
            available_methods.append(method)
        elif method == "existing_mc" and existing_mc_questions:
            available_methods.append(method)
        elif method == "scratch":
            available_methods.append(method)
    
    if not available_methods:
        raise ValueError("No methods available with input data. Please provide input files or use 'scratch' method.")
    
    # Calculate questions per method based on available methods only
    questions_per_method = num_questions // len(available_methods)
    remainder = num_questions % len(available_methods)
    
    # Statistics tracking
    stats = {
        "total_requested": num_questions,
        "total_generated": 0,
        "methods": {}
    }
    
    for method in available_methods:
        stats["methods"][method] = {
            "requested": questions_per_method + (1 if available_methods.index(method) < remainder else 0),
            "generated": 0,
            "failed": 0,
            "avg_time": 0.0,
            "avg_difficulty": 0.0,
            "bias_distribution": defaultdict(int),
            "times": []
        }
    
    # Prepare method-specific data structures
    method_data = {}
    method_locks = {}  # Locks for thread-safe index updates
    if "topic" in available_methods:
        random.shuffle(topics)
        method_data["topic"] = {"items": topics, "index": 0}
        method_locks["topic"] = asyncio.Lock()
    if "seed_qa" in available_methods:
        random.shuffle(seed_qa_pairs)
        method_data["seed_qa"] = {"items": seed_qa_pairs, "index": 0}
        method_locks["seed_qa"] = asyncio.Lock()
    if "existing_mc" in available_methods:
        method_data["existing_mc"] = {"items": existing_mc_questions, "index": 0}
        method_locks["existing_mc"] = asyncio.Lock()
    if "scratch" in available_methods:
        if topic_set == "v3.1":
            topic_hints = V31_TOPICS_EXPANDED.copy()
        else:
            topic_hints = (FOCUS_TOPICS_EXPANDED if use_focus_topics else SCRATCH_TOPIC_HINTS).copy()
        random.shuffle(topic_hints)
        method_data["scratch"] = {"items": topic_hints, "index": 0}
        method_locks["scratch"] = asyncio.Lock()
    if topic_set == "v3.1":
        method_data["_focus_areas_intro"] = V31_FOCUS_AREAS_INTRO
    else:
        method_data["_focus_areas_intro"] = None
    
    nota_questions = []
    question_counter = 0
    random.seed(42)
    
    print("=" * 80)
    print("Generating NOTA Benchmark v2 (Concurrent)")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Available methods: {', '.join(available_methods)}")
    print(f"Total questions: {num_questions}")
    print(f"Temperature: {temperature}")
    print(f"Max concurrent requests: {max_concurrent}")
    print()
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Prepare question assignments (method, question_num pairs)
    method_question_counts = {method: 0 for method in available_methods}
    method_index = 0
    question_assignments = []  # List of (method, question_num) tuples
    
    for q_num in range(1, num_questions + 1):
        # Select method in round-robin fashion
        method = available_methods[method_index % len(available_methods)]
        method_index += 1
        
        method_stats = stats["methods"][method]
        
        # Check if this method has reached its quota
        if method_question_counts[method] >= method_stats["requested"]:
            # Find next available method
            for m in available_methods:
                if method_question_counts[m] < stats["methods"][m]["requested"]:
                    method = m
                    break
            else:
                continue  # All methods at quota
        
        method_question_counts[method] += 1
        question_assignments.append((method, q_num))
    
    print(f"Generating {num_questions} questions concurrently (max {max_concurrent} parallel)...")
    
    # Execute tasks concurrently with session management
    async with aiohttp.ClientSession() as session:
        # Process in batches to allow checkpointing and better progress tracking
        batch_size = max_concurrent * 2  # Process in batches
        
        for batch_start in range(0, len(question_assignments), batch_size):
            batch = question_assignments[batch_start:batch_start + batch_size]
            
            # Create tasks for this batch
            batch_tasks = []
            batch_info = []
            
            for method, q_num in batch:
                task = generate_single_question_async(
                    session, api_key, api_url, model, method, method_data, method_locks, q_num, semaphore, temperature
                )
                batch_tasks.append(task)
                batch_info.append((method, q_num))
            
            # Execute batch concurrently
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                method, q_num = batch_info[i]
                method_stats = stats["methods"][method]
                start_time = time.time()
                
                if isinstance(result, Exception):
                    print(f"  [{q_num}/{num_questions}] [{method.upper()}] ERROR: {str(result)}")
                    method_stats["failed"] += 1
                    continue
                
                nota_data, actual_method, actual_q_num = result
                
                if not nota_data:
                    print(f"  [{actual_q_num}/{num_questions}] [{actual_method.upper()}] FAILED: Failed to generate MC question")
                    method_stats["failed"] += 1
                    continue
                
                # Generate metadata (also async)
                try:
                    metadata = await generate_nota_metadata_with_deepseek_async(
                        session, api_key, api_url, model,
                        nota_data["question"],
                        nota_data["options"],
                        nota_data["correct_answer"],
                        semaphore,
                        nota_data.get("tags", [])
                    )
                except Exception as e:
                    print(f"  [{actual_q_num}/{num_questions}] [{actual_method.upper()}] Metadata generation failed: {str(e)}")
                    # Use fallback metadata
                    metadata = {
                        "explanation": f"Option D is correct because none of the options A, B, C represent correct clinical practice.",
                        "bias_targeted": ["specificity"],
                        "difficulty_score": 0.5,
                        "tags": ["diabetes", "NOTA"],
                        "success": False
                    }
                
                # Create final NOTA question
                nota_question = {
                    "id": f"NOTA_{actual_q_num:03d}",
                    "generation_method": actual_method,
                    "question": nota_data["question"],
                    "options": nota_data["options"],
                    "correct_answer": nota_data["correct_answer"],
                    "ground_truth": nota_data["ground_truth"],
                    "explanation": metadata["explanation"],
                    "bias_targeted": metadata["bias_targeted"],
                    "difficulty_score": metadata["difficulty_score"],
                    "tags": metadata["tags"],
                    "test_type": "NOTA",
                    "metadata": {
                        "generated_by": "deepseek",
                        "model": model,
                        "generation_timestamp": datetime.now().isoformat(),
                        "generation_method": actual_method
                    }
                }
                
                # Add method-specific metadata
                if actual_method == "seed_qa":
                    nota_question["metadata"]["original_question"] = nota_data.get("original_question", "")
                    nota_question["metadata"]["original_answer"] = nota_data.get("original_answer", "")
                elif actual_method == "existing_mc":
                    nota_question["metadata"]["original_id"] = nota_data.get("original_id", "")
                    nota_question["metadata"]["original_question"] = nota_data.get("original_question", "")
                elif actual_method == "scratch":
                    nota_question["metadata"]["topic_hint"] = nota_data.get("topic_hint", "")
                
                nota_questions.append(nota_question)
                
                # Update statistics
                elapsed_time = time.time() - start_time
                method_stats["generated"] += 1
                method_stats["times"].append(elapsed_time)
                method_stats["avg_time"] = sum(method_stats["times"]) / len(method_stats["times"])
                method_stats["avg_difficulty"] = (
                    (method_stats["avg_difficulty"] * (method_stats["generated"] - 1) + metadata["difficulty_score"]) 
                    / method_stats["generated"]
                )
                for bias in metadata["bias_targeted"]:
                    method_stats["bias_distribution"][bias] += 1
                
                print(f"  [{actual_q_num}/{num_questions}] [{actual_method.upper()}] OK (difficulty: {metadata['difficulty_score']:.2f}, time: {elapsed_time:.1f}s)")
                
                # Save checkpoint
                if output_file and len(nota_questions) % checkpoint_interval == 0:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for q in nota_questions:
                            f.write(json.dumps(q, ensure_ascii=False) + '\n')
                    print(f"    [Checkpoint] Saved {len(nota_questions)} questions")
    
    # Final statistics
    stats["total_generated"] = len(nota_questions)
    
    # Convert defaultdict to regular dict for JSON serialization
    for method in stats["methods"]:
        stats["methods"][method]["bias_distribution"] = dict(stats["methods"][method]["bias_distribution"])
    
    return nota_questions, stats


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate NOTA (None of the Above) Benchmark v2 using DeepSeek API (Concurrent Version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 questions using all methods with concurrent processing
  python scripts/generate_nota_benchmark_v2_concurrent.py --method all --num-questions 100
  
  # Generate with custom concurrency limit
  python scripts/generate_nota_benchmark_v2_concurrent.py --method all --num-questions 100 --max-concurrent 5
  
  # Generate only from topics
  python scripts/generate_nota_benchmark_v2_concurrent.py --method topic --topics-file data/nota_topics.txt --num-questions 25
        """
    )
    
    parser.add_argument(
        "--method",
        type=str,
        nargs="+",
        default=["topic", "scratch"],
        choices=["all", "topic", "seed_qa", "existing_mc", "scratch"],
        help="Generation method(s) to use (default: topic scratch for 1000q focus run)"
    )
    
    parser.add_argument(
        "--topics-file",
        type=str,
        default="data/nota_topics.txt",
        help="Path to topics file (one topic per line). Required for 'topic' method."
    )
    
    parser.add_argument(
        "--seed-qa-file",
        type=str,
        default="output/cleaned_diabetes_nota_seeds.jsonl",
        help="Path to seed Q&A JSONL (question + answer/ground_truth). Used for 'seed_qa' method."
    )
    
    parser.add_argument(
        "--existing-mc-file",
        type=str,
        default="output/diabetes_multiple_choice_benchmark.jsonl",
        help="Path to existing multiple-choice benchmark JSONL file. Used for 'existing_mc' method."
    )
    
    parser.add_argument(
        "--num-questions",
        type=int,
        default=1000,
        help="Total number of questions to generate (default: 1000)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output/1000q_diabetes_nota_benchmark_v2_deepseek.jsonl",
        help="Output file path (default: output/1000q_diabetes_nota_benchmark_v2_deepseek.jsonl)"
    )
    
    parser.add_argument(
        "--use-focus-topics",
        action="store_true",
        default=True,
        help="Use FOCUS AREAS only for topic/scratch; forbid CRITICAL STOP topics (default: True)"
    )
    
    parser.add_argument(
        "--no-use-focus-topics",
        action="store_false",
        dest="use_focus_topics",
        help="Disable focus topics (use provided topics file / scratch hints)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="DeepSeek model to use (default: deepseek-chat)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Temperature for question generation (0.5-0.7 recommended, default: 0.6)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API key (or set DEEPSEEK_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=10,
        help="Save checkpoint every N questions (default: 10)"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=MAX_CONCURRENT_REQUESTS,
        help=f"Maximum concurrent API requests (default: {MAX_CONCURRENT_REQUESTS}). Higher values = faster but may hit rate limits."
    )
    parser.add_argument(
        "--append-to-v3",
        type=str,
        default=None,
        metavar="PATH",
        help="Generate and append directly to v3 file. Reads existing, generates (target-total - current) questions, appends, renumbers IDs, writes back. Use with --target-total."
    )
    parser.add_argument(
        "--target-total",
        type=int,
        default=1000,
        help="When using --append-to-v3, fill up to this many questions (default: 1000)."
    )
    parser.add_argument(
        "--topic-set",
        type=str,
        default="focus",
        choices=["focus", "v3.1"],
        help="Topic set: 'focus' (GDM/foot/tech/rare) or 'v3.1' (Task A/B/C: cardio-renal, neuro-ophtho, long tail). Use v3.1 with --append-to-v3 for v3.1 file."
    )
    args = parser.parse_args()
    
    # Get API key (use DEEPSEEK_API_KEY env or --api-key)
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set or --api-key not provided")
        return 1
    
    api_url = DS_API_URL
    project_root = Path(__file__).resolve().parent.parent.parent  # script -> 2026-01-28 -> scripts -> project
    
    # Convert method to list if single string
    methods = args.method if isinstance(args.method, list) else [args.method]
    
    # Convert file paths to Path objects (resolve relative to project root)
    def _p(p: str) -> Optional[Path]:
        if not p:
            return None
        path = Path(p)
        return path if path.is_absolute() else project_root / p
    topics_file = _p(args.topics_file) if args.topics_file else None
    seed_qa_file = _p(args.seed_qa_file) if args.seed_qa_file else None
    existing_mc_file = _p(args.existing_mc_file) if args.existing_mc_file else None
    output_file = _p(args.output) or project_root / "output" / "1000q_diabetes_nota_benchmark_v2_deepseek.jsonl"
    
    # --- Append-to-v3 mode: generate and write directly into v3 file ---
    append_to_v3 = _p(args.append_to_v3) if getattr(args, "append_to_v3", None) else None
    target_total = getattr(args, "target_total", 1000)
    if append_to_v3:
        # Load existing v3 (or fallback to cleaned seeds if v3 missing)
        if append_to_v3.exists():
            existing = read_jsonl(append_to_v3)
        else:
            cleaned_path = project_root / "output" / "cleaned_diabetes_nota_seeds.jsonl"
            existing = read_jsonl(cleaned_path) if cleaned_path.exists() else []
        num_to_generate = max(0, target_total - len(existing))
        if num_to_generate == 0:
            print(f"Already at target ({len(existing)} questions). Nothing to generate.")
            return 0
        print(f"Append-to-v3: {append_to_v3}")
        print(f"Existing: {len(existing)}, target: {target_total}, will generate: {num_to_generate}")
        # Checkpoint to temp file so we don't overwrite v3 with partial results
        import tempfile
        tmp_fd, tmp_path_str = tempfile.mkstemp(suffix=".jsonl", prefix="nota_gen_")
        os.close(tmp_fd)
        checkpoint_path = Path(tmp_path_str)
        try:
            nota_questions, stats = asyncio.run(
                create_nota_benchmark_v2_concurrent(
                    api_key=api_key,
                    api_url=api_url,
                    model=args.model,
                    methods=methods,
                    topics_file=topics_file,
                    seed_qa_file=seed_qa_file,
                    existing_mc_file=existing_mc_file,
                    num_questions=num_to_generate,
                    temperature=args.temperature,
                    output_file=checkpoint_path,
                    checkpoint_interval=args.checkpoint_interval,
                    max_concurrent=args.max_concurrent,
                    use_focus_topics=getattr(args, "use_focus_topics", True),
                    topic_set=getattr(args, "topic_set", "focus"),
                )
            )
            merged = existing + nota_questions
            for i, q in enumerate(merged, start=1):
                q["id"] = f"NOTA_{i:03d}"
            append_to_v3.parent.mkdir(parents=True, exist_ok=True)
            with open(append_to_v3, "w", encoding="utf-8") as f:
                for q in merged:
                    f.write(json.dumps(q, ensure_ascii=False) + "\n")
            print("\n" + "=" * 80)
            print("Append-to-v3 complete!")
            print("=" * 80)
            print(f"Generated: {len(nota_questions)} new questions")
            print(f"Total in v3: {len(merged)}")
            print(f"Written to: {append_to_v3}")
            return 0
        finally:
            if checkpoint_path.exists():
                checkpoint_path.unlink()
    
    try:
        # Generate benchmark using async function
        nota_questions, stats = asyncio.run(
            create_nota_benchmark_v2_concurrent(
                api_key=api_key,
                api_url=api_url,
                model=args.model,
                methods=methods,
                topics_file=topics_file,
                seed_qa_file=seed_qa_file,
                existing_mc_file=existing_mc_file,
                num_questions=args.num_questions,
                temperature=args.temperature,
                output_file=output_file,
                checkpoint_interval=args.checkpoint_interval,
                max_concurrent=args.max_concurrent,
                use_focus_topics=getattr(args, "use_focus_topics", True),
                topic_set=getattr(args, "topic_set", "focus"),
            )
        )
        
        # Save final output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for q in nota_questions:
                f.write(json.dumps(q, ensure_ascii=False) + '\n')
        
        # Save comparison report
        report_file = output_file.parent / "nota_generation_comparison_report_concurrent.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 80)
        print("Generation Complete!")
        print("=" * 80)
        print(f"Total questions generated: {len(nota_questions)}/{args.num_questions}")
        print(f"Output file: {output_file}")
        print(f"Comparison report: {report_file}")
        print()
        
        print("Statistics by Method:")
        print("-" * 80)
        for method, method_stats in stats["methods"].items():
            print(f"\n{method.upper()}:")
            print(f"  Generated: {method_stats['generated']}/{method_stats['requested']}")
            print(f"  Failed: {method_stats['failed']}")
            if method_stats['generated'] > 0:
                print(f"  Avg generation time: {method_stats['avg_time']:.2f}s")
                print(f"  Avg difficulty score: {method_stats['avg_difficulty']:.2f}")
                print(f"  Bias distribution: {dict(method_stats['bias_distribution'])}")
        
        print("\n" + "=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user.")
        if output_file.exists():
            print(f"Partial results saved to: {output_file}")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
