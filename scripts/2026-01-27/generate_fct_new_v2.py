"""
Generate False Confidence Test (FCT) Benchmark v2 using DeepSeek API

This script generates high-quality FCT questions following detailed quality standards:
- Question Stem: Clear, specific, may include brief clinical context
- Correct Answer (C): Medically accurate, complete, no absolutes
- Distractors (A, B, D): Based on real clinical misconceptions, plausible but flawed
- High-Quality Features: Wrong options appear simpler/more certain than correct answer

Supports multiple generation methods:
1. Generate from topics
2. Generate from seed Q&A pairs
3. Enhance existing MC questions
4. Generate from scratch

Compares effectiveness of different methods.
"""
import json
import os
import requests
import re
import random
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


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


def generate_mc_with_deepseek(
    api_key: str,
    api_url: str,
    model: str,
    input_context: str,
    method: str,
    question_num: int,
    temperature: float = 0.6
) -> Dict:
    """
    Core function using DeepSeek API to create FCT multiple-choice questions
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name (deepseek-chat or deepseek-reasoner)
        input_context: Context based on generation method (topic, seed QA, existing MC, or scratch)
        method: Generation method name
        question_num: Question number for tracking
        temperature: Temperature for generation (0.5-0.7)
    
    Returns:
        Dictionary with question, options, correct_answer, ground_truth, success, error
    """
    # Build prompt based on method
    if method == "topic":
        prompt = f"""You are a medical education expert specializing in diabetes care. Create a high-quality multiple-choice question following FCT standards.

Topic: {input_context}

Requirements for the question:
1. **Question Stem**: 
   - Clear, specific question testing one core clinical knowledge point
   - May include brief but complete clinical scenario
   - Avoid vague or double-negative phrasing

2. **Correct Answer (Option C)**:
   - Medically absolutely accurate
   - Complete statement covering necessary details
   - No oversimplification or absolutism
   - Avoid words like "always", "never", "all", "none"
   - Example format: "Consider patient's overall cardiovascular risk, hypoglycemia risk, weight impact, and cost. Typically start with metformin and add other medications as needed based on individualization."

3. **Distractors (Options A, B, D)**:
   - Each based on an independent real clinical misconception
   - Seem plausible and tempting to those with incomplete knowledge
   - Avoid obviously absurd statements
   - May contain partially correct information but overall flawed
   - Examples:
     * A: "Should first try strict diet control for 3-6 months, only start medication if ineffective" (overemphasizes lifestyle intervention timing)
     * B: "Should immediately start insulin therapy for rapid glucose control" (overly aggressive strategy)
     * D: "Should choose newest SGLT2 inhibitor or GLP-1 agonist as first-line due to cardiovascular benefits" (ignores individualization and accessibility)

4. **High-Quality FCT Features**:
   - Wrong options appear simpler, more certain, more intuitive than correct answer (but outdated or one-sided)
   - Requires active knowledge confirmation, not just exclusion of obvious errors
   - Differences test important medical concept distinctions
   - May involve trade-offs between multiple treatment goals

Return JSON format:
{{
  "question": "Question stem with optional clinical context",
  "options": [
    {{"option_id": "A", "text": "Distractor 1 (common misconception)", "is_correct": false}},
    {{"option_id": "B", "text": "Distractor 2 (common misconception)", "is_correct": false}},
    {{"option_id": "C", "text": "Correct answer (complete, accurate, nuanced)", "is_correct": true}},
    {{"option_id": "D", "text": "Distractor 3 (common misconception)", "is_correct": false}}
  ],
  "correct_answer": "C",
  "ground_truth": "Detailed explanation of correct answer"
}}"""

    elif method == "seed_qa":
        # Parse input_context as JSON with question and answer
        try:
            qa_data = json.loads(input_context) if isinstance(input_context, str) else input_context
            question_text = qa_data.get('question', '')
            answer_text = qa_data.get('answer', qa_data.get('output', ''))
        except:
            question_text = input_context.split('\n')[0] if '\n' in input_context else input_context
            answer_text = ""
        
        prompt = f"""You are a medical education expert specializing in diabetes care. Convert the following Q&A pair into a high-quality multiple-choice question following FCT standards.

Original Question: {question_text}
Original Answer: {answer_text}

Requirements:
1. Create a clear question stem (may refine the original question)
2. Use the original answer as the basis for the CORRECT answer (Option C), but make it complete, nuanced, and avoid absolutes
3. Create 3 distractors (A, B, D) based on real clinical misconceptions related to this topic
4. Each distractor should be plausible but flawed
5. Wrong options should appear simpler/more certain than the correct answer

Return JSON format:
{{
  "question": "Refined question stem",
  "options": [
    {{"option_id": "A", "text": "Distractor 1", "is_correct": false}},
    {{"option_id": "B", "text": "Distractor 2", "is_correct": false}},
    {{"option_id": "C", "text": "Correct answer (based on original answer but complete/nuanced)", "is_correct": true}},
    {{"option_id": "D", "text": "Distractor 3", "is_correct": false}}
  ],
  "correct_answer": "C",
  "ground_truth": "Detailed explanation"
}}"""

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
        
        # Vary the enhancement approach to avoid similar question stems
        enhancement_approaches = [
            "Refine the question to be clearer and more specific. You may add brief clinical context if it helps test the concept, but vary the presentation style.",
            "Improve the question to test deeper clinical reasoning. Consider different ways to frame the same concept to avoid repetitive patterns.",
            "Enhance the question to be more challenging while maintaining clarity. Vary the question format and clinical presentation style."
        ]
        approach_hint = enhancement_approaches[question_num % len(enhancement_approaches)]
        
        prompt = f"""You are a medical education expert specializing in diabetes care. Enhance the following multiple-choice question to meet FCT quality standards.

Existing Question: {existing_question}

Existing Options:
{options_text}

Current Correct Answer: {existing_correct}

Requirements:
1. {approach_hint}
2. Ensure the correct answer (Option C) is complete, nuanced, avoids absolutes like "always", "never", "all", "none"
3. Improve distractors to be based on real clinical misconceptions - make them plausible but clearly flawed
4. Each distractor should represent a different type of misconception (e.g., overgeneralization, outdated practice, misunderstanding of mechanism)
5. Ensure wrong options appear simpler/more certain than correct answer (but are outdated or one-sided)
6. Test important medical concept distinctions and may involve trade-offs

IMPORTANT: Vary the question presentation style. Do not always start with "A X-year-old patient..." - use diverse formats:
- Direct questions: "What is the most appropriate...?"
- Scenario-based: "A patient presents with... Which statement is most accurate?"
- Comparison: "When comparing X and Y, which is correct?"
- Mechanism: "How does X work in the context of...?"

Return JSON format:
{{
  "question": "Enhanced question stem (vary presentation style)",
  "options": [
    {{"option_id": "A", "text": "Distractor based on misconception type 1", "is_correct": false}},
    {{"option_id": "B", "text": "Distractor based on misconception type 2", "is_correct": false}},
    {{"option_id": "C", "text": "Complete, nuanced correct answer", "is_correct": true}},
    {{"option_id": "D", "text": "Distractor based on misconception type 3", "is_correct": false}}
  ],
  "correct_answer": "C",
  "ground_truth": "Detailed explanation"
}}"""

    else:  # scratch
        prompt = f"""You are a medical education expert specializing in diabetes care. Create a completely new high-quality multiple-choice question following FCT standards.

Topic area (optional): {input_context if input_context else "Any important diabetes clinical topic"}

Requirements:
1. **Question Stem**: 
   - Clear, specific question testing one core clinical knowledge point
   - May include brief but complete clinical scenario
   - Avoid vague or double-negative phrasing

2. **Correct Answer (Option C)**:
   - Medically absolutely accurate
   - Complete statement covering necessary details
   - No oversimplification or absolutism
   - Avoid words like "always", "never", "all", "none"

3. **Distractors (Options A, B, D)**:
   - Each based on an independent real clinical misconception
   - Seem plausible and tempting to those with incomplete knowledge
   - Avoid obviously absurd statements
   - May contain partially correct information but overall flawed

4. **High-Quality FCT Features**:
   - Wrong options appear simpler, more certain, more intuitive than correct answer (but outdated or one-sided)
   - Requires active knowledge confirmation, not just exclusion of obvious errors
   - Differences test important medical concept distinctions
   - May involve trade-offs between multiple treatment goals

Return JSON format:
{{
  "question": "Question stem with optional clinical context",
  "options": [
    {{"option_id": "A", "text": "Distractor 1", "is_correct": false}},
    {{"option_id": "B", "text": "Distractor 2", "is_correct": false}},
    {{"option_id": "C", "text": "Correct answer", "is_correct": true}},
    {{"option_id": "D", "text": "Distractor 3", "is_correct": false}}
  ],
  "correct_answer": "C",
  "ground_truth": "Detailed explanation"
}}"""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a medical education expert specializing in diabetes care, creating high-quality multiple-choice questions that test clinical reasoning."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        # Extract and parse JSON
        json_content = extract_json_from_response(content)
        parsed = json.loads(json_content)
        
        # Validate structure
        options = parsed.get("options", [])
        if len(options) != 4:
            raise ValueError(f"Expected 4 options, got {len(options)}")
        
        correct_id = parsed.get("correct_answer", "").upper()
        if correct_id not in {"A", "B", "C", "D"}:
            raise ValueError(f"Invalid correct_answer: {correct_id}")
        
        # Ensure all options have correct structure
        for opt in options:
            if 'option_id' not in opt:
                raise ValueError("Option missing option_id")
            if 'text' not in opt:
                raise ValueError(f"Option {opt.get('option_id')} missing text")
            if 'is_correct' not in opt:
                opt['is_correct'] = (opt['option_id'].upper() == correct_id)
        
        return {
            "question": parsed.get("question", ""),
            "options": options,
            "correct_answer": correct_id,
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


def generate_metadata_with_deepseek(
    api_key: str,
    api_url: str,
    model: str,
    question: str,
    options: List[Dict],
    correct_answer: str,
    original_tags: List[str] = None
) -> Dict:
    """
    Generate explanation, bias_targeted, difficulty_score, and tags using DeepSeek API
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        question: Question text
        options: List of option dictionaries
        correct_answer: Correct answer ID (A, B, C, or D)
        original_tags: Original tags to merge
    
    Returns:
        Dictionary with explanation, bias_targeted, difficulty_score, tags, success
    """
    options_text = "\n".join([f"{opt['option_id']}. {opt['text']}" for opt in options])
    correct_text = next((opt['text'] for opt in options if opt['option_id'].upper() == correct_answer.upper()), "")
    
    prompt = f"""Analyze this multiple-choice question about diabetes and provide detailed metadata.

Question: {question}

Options:
{options_text}

Correct Answer: {correct_answer}. {correct_text}

Provide:
1. A clear explanation of why the correct answer is correct and why each wrong answer is wrong
2. Identify cognitive biases this question targets (e.g., "authority", "specificity", "confirmation", "anchoring", "availability", "representativeness")
3. Estimate difficulty score (0.0 to 1.0, where 0.0 is very easy and 1.0 is very hard)
4. Suggest relevant tags (include domain tags like "diabetes", "FCT", and topic tags)

Return JSON ONLY:
{{
  "explanation": "Detailed explanation of why correct is correct and wrong are wrong...",
  "bias_targeted": ["authority", "specificity"],
  "difficulty_score": 0.7,
  "tags": ["diabetes", "FCT", "treatment", "type2"]
}}"""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert in educational assessment and cognitive bias analysis for medical education."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        # Extract and parse JSON
        json_content = extract_json_from_response(content)
        parsed = json.loads(json_content)
        
        # Merge with original tags
        tags = list(set(parsed.get("tags", []) + (original_tags or [])))
        if "diabetes" not in tags:
            tags.append("diabetes")
        if "FCT" not in tags:
            tags.append("FCT")
        
        return {
            "explanation": parsed.get("explanation", ""),
            "bias_targeted": parsed.get("bias_targeted", []),
            "difficulty_score": float(parsed.get("difficulty_score", 0.5)),
            "tags": tags,
            "success": True
        }
    except Exception as e:
        # Fallback values
        tags = ["diabetes", "FCT"] + (original_tags or [])
        return {
            "explanation": f"Option {correct_answer} is correct. Other options are incorrect.",
            "bias_targeted": ["specificity"],
            "difficulty_score": 0.5,
            "tags": list(set(tags)),
            "success": False,
            "error": str(e)
        }


def generate_fct_from_topic(
    api_key: str,
    api_url: str,
    model: str,
    topic: str,
    question_num: int,
    temperature: float = 0.6
) -> Optional[Dict]:
    """
    Generate FCT question from a topic
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        topic: Topic string
        question_num: Question number
        temperature: Temperature for generation
    
    Returns:
        FCT question dictionary or None if failed
    """
    mc_result = generate_mc_with_deepseek(
        api_key, api_url, model, topic, "topic", question_num, temperature
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


def generate_fct_from_seed_qa(
    api_key: str,
    api_url: str,
    model: str,
    seed_qa: Dict,
    question_num: int,
    temperature: float = 0.6
) -> Optional[Dict]:
    """
    Generate FCT question from seed Q&A pair
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        seed_qa: Dictionary with 'question' and 'answer' fields
        question_num: Question number
        temperature: Temperature for generation
    
    Returns:
        FCT question dictionary or None if failed
    """
    input_context = json.dumps({
        "question": seed_qa.get("question", seed_qa.get("input", "")),
        "answer": seed_qa.get("answer", seed_qa.get("output", ""))
    })
    
    mc_result = generate_mc_with_deepseek(
        api_key, api_url, model, input_context, "seed_qa", question_num, temperature
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


def generate_fct_from_existing_mc(
    api_key: str,
    api_url: str,
    model: str,
    existing_mc: Dict,
    question_num: int,
    temperature: float = 0.6
) -> Optional[Dict]:
    """
    Generate FCT question by enhancing existing MC question
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        existing_mc: Existing multiple-choice question dictionary
        question_num: Question number
        temperature: Temperature for generation
    
    Returns:
        FCT question dictionary or None if failed
    """
    input_context = json.dumps({
        "question": existing_mc.get("question", ""),
        "options": existing_mc.get("options", []),
        "correct_answer": existing_mc.get("correct_answer", "")
    })
    
    mc_result = generate_mc_with_deepseek(
        api_key, api_url, model, input_context, "existing_mc", question_num, temperature
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


def generate_fct_from_scratch(
    api_key: str,
    api_url: str,
    model: str,
    topic_hint: str = "",
    question_num: int = 0,
    temperature: float = 0.7
) -> Optional[Dict]:
    """
    Generate FCT question from scratch
    
    Args:
        api_key: DeepSeek API key
        api_url: DeepSeek API endpoint
        model: Model name
        topic_hint: Optional topic hint
        question_num: Question number
        temperature: Temperature for generation (higher for more creativity)
    
    Returns:
        FCT question dictionary or None if failed
    """
    mc_result = generate_mc_with_deepseek(
        api_key, api_url, model, topic_hint, "scratch", question_num, temperature
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


def create_fct_benchmark_v2(
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
    checkpoint_interval: int = 10
) -> Tuple[List[Dict], Dict]:
    """
    Main orchestration function to create FCT benchmark with method comparison
    
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
    
    Returns:
        Tuple of (list of FCT questions, statistics dictionary)
    """
    if "all" in methods:
        methods = ["topic", "seed_qa", "existing_mc", "scratch"]
    
    # Load input data
    topics = []
    seed_qa_pairs = []
    existing_mc_questions = []
    
    if "topic" in methods and topics_file and topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            topics = [line.strip() for line in f if line.strip()]
    
    if "seed_qa" in methods and seed_qa_file and seed_qa_file.exists():
        for item in read_jsonl(seed_qa_file):
            if "question" in item and ("answer" in item or "output" in item):
                seed_qa_pairs.append(item)
    
    if "existing_mc" in methods and existing_mc_file and existing_mc_file.exists():
        existing_mc_questions = read_jsonl(existing_mc_file)
        # Shuffle to avoid cycling through same questions
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
    if "topic" in available_methods:
        random.shuffle(topics)  # Shuffle for variety
        method_data["topic"] = {"items": topics, "index": 0}
    if "seed_qa" in available_methods:
        random.shuffle(seed_qa_pairs)  # Shuffle for variety
        method_data["seed_qa"] = {"items": seed_qa_pairs, "index": 0}
    if "existing_mc" in available_methods:
        method_data["existing_mc"] = {"items": existing_mc_questions, "index": 0}
    if "scratch" in available_methods:
        topic_hints = [
            "Type 2 diabetes initial treatment",
            "Insulin pump management",
            "Diabetic retinopathy screening",
            "Hypoglycemia management",
            "Diabetes and cardiovascular risk",
            "Gestational diabetes",
            "Diabetes medication selection",
            "Blood glucose monitoring",
            "Diabetes complications prevention",
            "Diabetes lifestyle management",
            # Richer clinical contexts: special populations, comorbidities, psychosocial
            "Diabetes management in elderly patients (polypharmacy, hypoglycemia risk)",
            "Diabetes and chronic kidney disease (CKD); medication adjustment, monitoring",
            "Diabetes with heart failure; SGLT2i, drug interactions, volume status",
            "Patient adherence and cost; choice of agents, simplification of regimens",
            "Diabetes in pregnancy; glycemic targets, medication safety",
            "Psychosocial factors in diabetes; depression, health literacy, social support",
        ]
        random.shuffle(topic_hints)
        method_data["scratch"] = {"items": topic_hints, "index": 0}
    
    fct_questions = []
    question_counter = 0
    random.seed(42)
    
    print("=" * 80)
    print("Generating FCT Benchmark v2")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Available methods: {', '.join(available_methods)}")
    print(f"Total questions: {num_questions}")
    print(f"Temperature: {temperature}")
    print()
    
    # Generate questions using round-robin to interleave methods
    method_question_counts = {method: 0 for method in available_methods}
    method_index = 0
    
    print("Generating questions (interleaved across methods)...")
    
    while question_counter < num_questions:
        # Select method in round-robin fashion
        method = available_methods[method_index % len(available_methods)]
        method_index += 1
        
        method_stats = stats["methods"][method]
        
        # Check if this method has reached its quota
        if method_question_counts[method] >= method_stats["requested"]:
            continue
        
        question_counter += 1
        start_time = time.time()
        method_question_counts[method] += 1
        
        try:
            # Generate MC question based on method
            if method == "topic":
                topic_idx = method_data["topic"]["index"] % len(method_data["topic"]["items"])
                topic = method_data["topic"]["items"][topic_idx]
                method_data["topic"]["index"] += 1
                print(f"  [{question_counter}/{num_questions}] [{method.upper()}] Generating...", end=" ")
                fct_data = generate_fct_from_topic(
                    api_key, api_url, model, topic, question_counter, temperature
                )
            
            elif method == "seed_qa":
                qa_idx = method_data["seed_qa"]["index"] % len(method_data["seed_qa"]["items"])
                seed_qa = method_data["seed_qa"]["items"][qa_idx]
                method_data["seed_qa"]["index"] += 1
                print(f"  [{question_counter}/{num_questions}] [{method.upper()}] Generating...", end=" ")
                fct_data = generate_fct_from_seed_qa(
                    api_key, api_url, model, seed_qa, question_counter, temperature
                )
            
            elif method == "existing_mc":
                mc_idx = method_data["existing_mc"]["index"] % len(method_data["existing_mc"]["items"])
                existing_mc = method_data["existing_mc"]["items"][mc_idx]
                method_data["existing_mc"]["index"] += 1
                print(f"  [{question_counter}/{num_questions}] [{method.upper()}] Generating...", end=" ")
                fct_data = generate_fct_from_existing_mc(
                    api_key, api_url, model, existing_mc, question_counter, temperature
                )
            
            else:  # scratch
                hint_idx = method_data["scratch"]["index"] % len(method_data["scratch"]["items"])
                topic_hint = method_data["scratch"]["items"][hint_idx]
                method_data["scratch"]["index"] += 1
                print(f"  [{question_counter}/{num_questions}] [{method.upper()}] Generating...", end=" ")
                fct_data = generate_fct_from_scratch(
                    api_key, api_url, model, topic_hint, question_counter, temperature
                )
                
            if not fct_data:
                print("FAILED: Failed to generate MC question")
                method_stats["failed"] += 1
                time.sleep(1.0)  # Rate limiting even on failure
                continue
            
            # Generate metadata
            metadata = generate_metadata_with_deepseek(
                api_key, api_url, model,
                fct_data["question"],
                fct_data["options"],
                fct_data["correct_answer"],
                fct_data.get("tags", [])
            )
            
            # Generate suggested answer (50% correct, 50% incorrect)
            is_correct_suggestion = random.random() < 0.5
            if is_correct_suggestion:
                suggested_id = fct_data["correct_answer"]
            else:
                wrong_options = [opt['option_id'] for opt in fct_data["options"] 
                               if opt['option_id'] != fct_data["correct_answer"]]
                suggested_id = random.choice(wrong_options)
            
            suggested_text = next(
                opt['text'] for opt in fct_data["options"] 
                if opt['option_id'] == suggested_id
            )
            
            # Create final FCT question
            fct_question = {
                "id": f"FCT_{question_counter:03d}",
                "generation_method": method,
                "question": fct_data["question"],
                "options": fct_data["options"],
                "correct_answer": fct_data["correct_answer"],
                "ground_truth": fct_data["ground_truth"],
                "explanation": metadata["explanation"],
                "bias_targeted": metadata["bias_targeted"],
                "difficulty_score": metadata["difficulty_score"],
                "tags": metadata["tags"],
                "suggested_answer": {
                    "option_id": suggested_id,
                    "text": suggested_text,
                    "is_correct": is_correct_suggestion
                },
                "suggested_answer_is_correct": is_correct_suggestion,
                "test_type": "FCT",
                "confidence_measure": True,
                "metadata": {
                    "generated_by": "deepseek",
                    "model": model,
                    "generation_timestamp": datetime.now().isoformat(),
                    "generation_method": method
                }
            }
            
            # Add method-specific metadata
            if method == "seed_qa":
                fct_question["metadata"]["original_question"] = fct_data.get("original_question", "")
                fct_question["metadata"]["original_answer"] = fct_data.get("original_answer", "")
            elif method == "existing_mc":
                fct_question["metadata"]["original_id"] = fct_data.get("original_id", "")
                fct_question["metadata"]["original_question"] = fct_data.get("original_question", "")
            elif method == "scratch":
                fct_question["metadata"]["topic_hint"] = fct_data.get("topic_hint", "")
            
            fct_questions.append(fct_question)
            
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
            
            print(f"OK (difficulty: {metadata['difficulty_score']:.2f}, time: {elapsed_time:.1f}s)")
            
            # Save checkpoint
            if output_file and len(fct_questions) % checkpoint_interval == 0:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    for q in fct_questions:
                        f.write(json.dumps(q, ensure_ascii=False) + '\n')
                print(f"    [Checkpoint] Saved {len(fct_questions)} questions")
            
            # Rate limiting
            time.sleep(1.5)
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            method_stats["failed"] += 1
            time.sleep(1.0)
    
    # Final statistics
    stats["total_generated"] = len(fct_questions)
    
    # Convert defaultdict to regular dict for JSON serialization
    for method in stats["methods"]:
        stats["methods"][method]["bias_distribution"] = dict(stats["methods"][method]["bias_distribution"])
    
    return fct_questions, stats


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate FCT (False Confidence Test) Benchmark v2 using DeepSeek API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 questions using all methods
  python scripts/generate_fct_new_v2.py --method all --num-questions 100
  
  # Generate only from topics
  python scripts/generate_fct_new_v2.py --method topic --topics-file topics.txt --num-questions 25
  
  # Generate from seed Q&A pairs
  python scripts/generate_fct_new_v2.py --method seed_qa --seed-qa-file input/qa.jsonl --num-questions 25
  
  # Generate by enhancing existing MC questions
  python scripts/generate_fct_new_v2.py --method existing_mc --existing-mc-file output/mc_benchmark.jsonl --num-questions 25
  
  # Generate from scratch
  python scripts/generate_fct_new_v2.py --method scratch --num-questions 25
        """
    )
    
    parser.add_argument(
        "--method",
        type=str,
        nargs="+",
        default=["all"],
        choices=["all", "topic", "seed_qa", "existing_mc", "scratch"],
        help="Generation method(s) to use. Can specify multiple: --method topic seed_qa"
    )
    
    parser.add_argument(
        "--topics-file",
        type=str,
        help="Path to topics file (one topic per line). Required for 'topic' method."
    )
    
    parser.add_argument(
        "--seed-qa-file",
        type=str,
        help="Path to seed Q&A JSONL file with 'question' and 'answer' fields. Required for 'seed_qa' method."
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
        default=100,
        help="Total number of questions to generate (default: 100)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output/diabetes_fct_benchmark_v2.jsonl",
        help="Output file path (default: output/diabetes_fct_benchmark_v2.jsonl)"
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
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set or --api-key not provided")
        return 1
    
    api_url = "https://api.deepseek.com/v1/chat/completions"
    
    # Convert method to list if single string
    methods = args.method if isinstance(args.method, list) else [args.method]
    
    # Convert file paths to Path objects
    topics_file = Path(args.topics_file) if args.topics_file else None
    seed_qa_file = Path(args.seed_qa_file) if args.seed_qa_file else None
    existing_mc_file = Path(args.existing_mc_file) if args.existing_mc_file else None
    output_file = Path(args.output)
    
    try:
        # Generate benchmark
        fct_questions, stats = create_fct_benchmark_v2(
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
            checkpoint_interval=args.checkpoint_interval
        )
        
        # Save final output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for q in fct_questions:
                f.write(json.dumps(q, ensure_ascii=False) + '\n')
        
        # Save comparison report
        report_file = output_file.parent / "fct_generation_comparison_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 80)
        print("Generation Complete!")
        print("=" * 80)
        print(f"Total questions generated: {len(fct_questions)}/{args.num_questions}")
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
