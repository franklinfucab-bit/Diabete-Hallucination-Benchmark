"""
Model tester for multiple-choice questions
"""
from typing import List, Dict, Optional
import os
from utils.model_tester import ModelTester


class MCModelTester:
    """Test AI models on multiple-choice questions"""
    
    def __init__(self, base_tester: ModelTester):
        """
        Initialize multiple-choice model tester
        
        Args:
            base_tester: Base ModelTester instance (OpenAI, Anthropic, etc.)
        """
        self.base_tester = base_tester
    
    def answer_multiple_choice(
        self,
        question: str,
        options: List[Dict[str, str]]
    ) -> Dict:
        """
        Get model's answer to a multiple-choice question
        
        Args:
            question: The question text
            options: List of option dictionaries with 'option_id' and 'text'
            
        Returns:
            Dictionary with 'selected_option' and metadata
        """
        # Format options for the prompt
        options_text = "\n".join([
            f"{opt['option_id']}. {opt['text']}"
            for opt in options
        ])
        
        prompt = f"""You are a medical expert evaluating a multiple-choice question about diabetes.

Question: {question}

Options:
{options_text}

Please select the correct answer by responding with ONLY the letter (A, B, C, D, etc.) of the correct option.
Your response should be a single letter."""

        try:
            # Use the base tester's client to get response
            if hasattr(self.base_tester, 'client'):
                if hasattr(self.base_tester.client, 'chat'):
                    # OpenAI
                    response = self.base_tester.client.chat.completions.create(
                        model=self.base_tester.model,
                        messages=[
                            {"role": "system", "content": "You are a medical expert specializing in diabetes care. Answer multiple-choice questions accurately."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=5
                    )
                    raw_answer = response.choices[0].message.content.strip().upper()
                elif hasattr(self.base_tester.client, 'messages'):
                    # Anthropic
                    message = self.base_tester.client.messages.create(
                        model=self.base_tester.model,
                        max_tokens=5,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    raw_answer = message.content[0].text.strip().upper()
                else:
                    raise ValueError("Unknown client type")
                
                # Extract option letter
                selected_option = None
                for char in raw_answer:
                    if char.isalpha() and char.upper() in [opt['option_id'].upper() for opt in options]:
                        selected_option = char.upper()
                        break
                
                return {
                    'selected_option': selected_option,
                    'raw_response': raw_answer,
                    'model': self.base_tester.model
                }
            else:
                raise ValueError("Base tester does not have a client")
                
        except Exception as e:
            return {
                'selected_option': None,
                'error': str(e),
                'model': getattr(self.base_tester, 'model', 'unknown')
            }
    
    def test_benchmark(
        self,
        benchmark_data: List[Dict],
        max_samples: Optional[int] = None
    ) -> List[Dict]:
        """
        Test model on multiple-choice benchmark
        
        Args:
            benchmark_data: List of multiple-choice questions
            max_samples: Optional limit on number of questions to test
            
        Returns:
            List of predictions with 'id' and 'selected_option'
        """
        from tqdm import tqdm
        
        predictions = []
        test_data = benchmark_data[:max_samples] if max_samples else benchmark_data
        
        print(f"Testing model on {len(test_data)} multiple-choice questions...")
        
        for item in tqdm(test_data, desc="Evaluating"):
            result = self.answer_multiple_choice(item['question'], item['options'])
            
            predictions.append({
                'id': item['id'],
                'selected_option': result.get('selected_option'),
                'metadata': result
            })
        
        return predictions
