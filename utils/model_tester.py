"""
Model testing interface for different AI models
"""
from typing import List, Dict, Optional
import os
from abc import ABC, abstractmethod


class ModelTester(ABC):
    """Abstract base class for testing AI models"""
    
    @abstractmethod
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        """
        Detect if an answer contains hallucinations
        
        Args:
            question: The question being answered
            answer: The answer to evaluate
            
        Returns:
            Dictionary with 'is_hallucination' (bool) and optionally 'confidence' (float)
        """
        pass


class OpenAIModelTester(ModelTester):
    """Test using OpenAI models"""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize OpenAI tester
        
        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        """Detect hallucinations using OpenAI model"""
        prompt = f"""You are a medical expert evaluating answers about diabetes. 
Determine if the following answer contains any hallucinations, misinformation, or incorrect medical information.

Question: {question}

Answer to evaluate: {answer}

Respond with ONLY "HALLUCINATION" if the answer contains false information, or "CORRECT" if the answer is accurate. 
Be strict - even minor inaccuracies or unsupported claims should be marked as HALLUCINATION."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical expert specializing in diabetes care."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            is_hallucination = "HALLUCINATION" in result
            
            return {
                'is_hallucination': is_hallucination,
                'raw_response': result,
                'model': self.model
            }
        except Exception as e:
            return {
                'is_hallucination': None,
                'error': str(e),
                'model': self.model
            }


class AnthropicModelTester(ModelTester):
    """Test using Anthropic Claude models"""
    
    def __init__(self, model: str = "claude-3-opus-20240229", api_key: Optional[str] = None):
        """
        Initialize Anthropic tester
        
        Args:
            model: Model name
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        self.model = model
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        """Detect hallucinations using Anthropic Claude"""
        prompt = f"""You are a medical expert evaluating answers about diabetes. 
Determine if the following answer contains any hallucinations, misinformation, or incorrect medical information.

Question: {question}

Answer to evaluate: {answer}

Respond with ONLY "HALLUCINATION" if the answer contains false information, or "CORRECT" if the answer is accurate. 
Be strict - even minor inaccuracies or unsupported claims should be marked as HALLUCINATION."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = message.content[0].text.strip().upper()
            is_hallucination = "HALLUCINATION" in result
            
            return {
                'is_hallucination': is_hallucination,
                'raw_response': result,
                'model': self.model
            }
        except Exception as e:
            return {
                'is_hallucination': None,
                'error': str(e),
                'model': self.model
            }


class LocalModelTester(ModelTester):
    """Template for testing local models (implement based on your setup)"""
    
    def __init__(self, model_path: str):
        """
        Initialize local model tester
        
        Args:
            model_path: Path to local model
        """
        self.model_path = model_path
        # Implement your local model loading here
    
    def detect_hallucination(self, question: str, answer: str) -> Dict:
        """Detect hallucinations using local model"""
        # Implement your local model inference here
        raise NotImplementedError("Local model testing not yet implemented. "
                                "Please implement based on your local model setup.")


def test_benchmark(
    tester: ModelTester,
    benchmark_data: List[Dict],
    max_samples: Optional[int] = None
) -> List[Dict]:
    """
    Test a model on the benchmark dataset
    
    Args:
        tester: ModelTester instance
        benchmark_data: List of benchmark test cases
        max_samples: Optional limit on number of samples to test
        
    Returns:
        List of predictions with 'id' and 'is_hallucination' fields
    """
    from tqdm import tqdm
    
    predictions = []
    test_data = benchmark_data[:max_samples] if max_samples else benchmark_data
    
    print(f"Testing model on {len(test_data)} samples...")
    
    for item in tqdm(test_data, desc="Evaluating"):
        result = tester.detect_hallucination(item['question'], item['answer'])
        
        predictions.append({
            'id': item['id'],
            'is_hallucination': result.get('is_hallucination'),
            'metadata': result
        })
    
    return predictions
