"""
DeepSeek API integration for testing benchmarks
"""
import os
import requests
from typing import Dict, Optional
import time
import json


class DeepSeekModelTester:
    """Test using DeepSeek API"""
    
    def __init__(self, model: str = "deepseek-chat", api_key: Optional[str] = None):
        """
        Initialize DeepSeek tester
        
        Args:
            model: Model name (deepseek-chat, deepseek-reasoner)
            api_key: DeepSeek API key (or set DEEPSEEK_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable.")
    
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        """Detect hallucinations using DeepSeek model"""
        prompt = f"""你是医学专家，专门评估关于糖尿病的答案。

请判断以下答案是否包含幻觉、错误信息或误导性内容。

问题: {question}

要评估的答案: {answer}

请只回复 "HALLUCINATION"（如果答案包含错误信息）或 "CORRECT"（如果答案准确）。
请严格判断 - 即使是轻微的不准确或未经支持的声明也应标记为 HALLUCINATION。"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专门从事糖尿病护理的医学专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            raw_answer = result['choices'][0]['message']['content'].strip().upper()
            is_hallucination = "HALLUCINATION" in raw_answer or "幻觉" in raw_answer or "错误" in raw_answer
            
            return {
                'is_hallucination': is_hallucination,
                'raw_response': raw_answer,
                'model': self.model
            }
        except Exception as e:
            return {
                'is_hallucination': None,
                'error': str(e),
                'model': self.model
            }
    
    def generate_question(self, topic: str, context: Optional[str] = None) -> Dict:
        """
        Generate a diabetes-related question using DeepSeek API
        
        Args:
            topic: The topic or area for the question
            context: Optional context or additional information
            
        Returns:
            Dictionary with generated question and answer
        """
        prompt = f"""你是医学教育专家，专门设计关于糖尿病的教育问题。

请基于以下主题生成一个关于糖尿病的教育性问题及其准确答案。

主题: {topic}
{f'上下文: {context}' if context else ''}

请生成：
1. 一个清晰、具体的问题
2. 一个准确、详细的医学答案

请以JSON格式回复，包含以下字段：
- "question": 问题文本
- "answer": 答案文本

确保答案基于准确的医学知识，适合糖尿病患者教育。"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个医学教育专家，专门设计准确、教育性的糖尿病相关问题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            raw_response = result['choices'][0]['message']['content'].strip()
            
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in markdown code blocks
                if '```json' in raw_response:
                    json_start = raw_response.find('```json') + 7
                    json_end = raw_response.find('```', json_start)
                    raw_response = raw_response[json_start:json_end].strip()
                elif '```' in raw_response:
                    json_start = raw_response.find('```') + 3
                    json_end = raw_response.find('```', json_start)
                    raw_response = raw_response[json_start:json_end].strip()
                
                parsed = json.loads(raw_response)
                return {
                    'question': parsed.get('question', ''),
                    'answer': parsed.get('answer', ''),
                    'raw_response': raw_response,
                    'model': self.model
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract question and answer from text
                lines = raw_response.split('\n')
                question = ''
                answer = ''
                in_answer = False
                
                for line in lines:
                    if 'question' in line.lower() or '问题' in line:
                        question = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
                    elif 'answer' in line.lower() or '答案' in line:
                        in_answer = True
                        answer = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
                    elif in_answer:
                        answer += ' ' + line.strip()
                
                return {
                    'question': question or raw_response,
                    'answer': answer or raw_response,
                    'raw_response': raw_response,
                    'model': self.model,
                    'note': 'Response was not in JSON format, extracted from text'
                }
                
        except Exception as e:
            return {
                'question': None,
                'answer': None,
                'error': str(e),
                'model': self.model
            }
    
    def generate_multiple_choice_options(
        self,
        question: str,
        correct_answer: str,
        num_distractors: int = 3
    ) -> Dict:
        """
        Generate multiple-choice distractors using DeepSeek API
        
        Args:
            question: The question text
            correct_answer: The correct answer
            num_distractors: Number of wrong options to generate
            
        Returns:
            Dictionary with generated options
        """
        prompt = f"""你是医学教育专家，设计多选题的干扰项。

问题: {question}
正确答案: {correct_answer}

请生成 {num_distractors} 个干扰项（错误选项），包括：
1. 一个包含医学错误信息的选项（幻觉类型）
2. 一个看似合理但错误的选项
3. 一个部分正确但误导的选项

请以JSON格式回复，包含：
- "distractors": 干扰项数组，每个包含 "text" 和 "type" 字段
  - type可以是: "hallucination", "plausible_wrong", "partial_correct"

确保干扰项具有挑战性但明显错误。"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个医学教育专家，设计准确、具有教育性的多选题干扰项。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 600
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            raw_response = result['choices'][0]['message']['content'].strip()
            
            # Try to parse JSON
            try:
                if '```json' in raw_response:
                    json_start = raw_response.find('```json') + 7
                    json_end = raw_response.find('```', json_start)
                    raw_response = raw_response[json_start:json_end].strip()
                elif '```' in raw_response:
                    json_start = raw_response.find('```') + 3
                    json_end = raw_response.find('```', json_start)
                    raw_response = raw_response[json_start:json_end].strip()
                
                parsed = json.loads(raw_response)
                return {
                    'distractors': parsed.get('distractors', []),
                    'raw_response': raw_response,
                    'model': self.model
                }
            except json.JSONDecodeError:
                return {
                    'distractors': [],
                    'raw_response': raw_response,
                    'error': 'Failed to parse JSON response',
                    'model': self.model
                }
                
        except Exception as e:
            return {
                'distractors': [],
                'error': str(e),
                'model': self.model
            }
    
    def answer_multiple_choice(self, question: str, options: list) -> Dict:
        """Answer multiple-choice question using DeepSeek"""
        options_text = "\n".join([
            f"{opt['option_id']}. {opt['text']}"
            for opt in options
        ])
        
        prompt = f"""你是医学专家，评估一个关于糖尿病的多选题。

问题: {question}

选项:
{options_text}

请选择正确答案，只回复选项字母（A, B, C, D 等）。
你的回复应该只是一个字母。"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专门从事糖尿病护理的医学专家。准确回答多选题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 10
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            raw_answer = result['choices'][0]['message']['content'].strip().upper()
            
            # Extract option letter
            selected_option = None
            for char in raw_answer:
                if char.isalpha() and char.upper() in [opt['option_id'].upper() for opt in options]:
                    selected_option = char.upper()
                    break
            
            return {
                'selected_option': selected_option,
                'raw_response': raw_answer,
                'model': self.model
            }
        except Exception as e:
            return {
                'selected_option': None,
                'error': str(e),
                'model': self.model
            }


def test_benchmark_with_deepseek(
    benchmark_data: list,
    tester: DeepSeekModelTester,
    max_samples: Optional[int] = None,
    delay: float = 1.0
) -> list:
    """
    Test benchmark with DeepSeek API
    
    Args:
        benchmark_data: List of benchmark items
        tester: DeepSeekModelTester instance
        max_samples: Optional limit on number of samples
        delay: Delay between API calls (seconds)
    
    Returns:
        List of predictions
    """
    from tqdm import tqdm
    
    predictions = []
    test_data = benchmark_data[:max_samples] if max_samples else benchmark_data
    
    print(f"使用 DeepSeek API 测试 {len(test_data)} 个样本...")
    print(f"模型: {tester.model}")
    print(f"API 调用间隔: {delay} 秒\n")
    
    for i, item in enumerate(tqdm(test_data, desc="测试中")):
        try:
            if 'options' in item:
                # Multiple-choice question
                result = tester.answer_multiple_choice(item['question'], item['options'])
                predictions.append({
                    'id': item['id'],
                    'selected_option': result.get('selected_option'),
                    'metadata': result
                })
            else:
                # Binary question
                result = tester.detect_hallucination(item['question'], item['answer'])
                predictions.append({
                    'id': item['id'],
                    'is_hallucination': result.get('is_hallucination'),
                    'metadata': result
                })
            
            # Rate limiting
            if i < len(test_data) - 1:  # Don't delay after last item
                time.sleep(delay)
                
        except Exception as e:
            print(f"\n错误处理样本 {item.get('id', 'unknown')}: {e}")
            predictions.append({
                'id': item.get('id'),
                'error': str(e)
            })
    
    return predictions
