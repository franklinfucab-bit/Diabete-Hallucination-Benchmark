"""
Multiple-choice question generator for diabetes hallucination benchmark
Creates challenging multiple-choice questions with hallucinated distractors
"""
import random
from typing import List, Dict, Optional
import json
from utils.hallucination_generator import HallucinationGenerator


class MultipleChoiceGenerator:
    """Generate multiple-choice questions with challenging distractors"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the multiple-choice generator
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        self.hallucination_gen = HallucinationGenerator(seed=seed)
        
        # Common wrong answer patterns for diabetes
        self.wrong_answer_templates = [
            "The opposite is true",
            "This is not recommended",
            "This only applies to type 1 diabetes",
            "This only applies to type 2 diabetes",
            "This is outdated information",
            "This requires medical supervision",
        ]
    
    def generate_distractors(
        self,
        correct_answer: str,
        question: str,
        num_distractors: int = 3,
        include_hallucinations: bool = True
    ) -> List[Dict[str, str]]:
        """
        Generate challenging distractors for multiple-choice questions
        
        Args:
            correct_answer: The correct answer
            question: The question being asked
            num_distractors: Number of wrong answers to generate
            include_hallucinations: Whether to include hallucinated distractors
            
        Returns:
            List of distractor dictionaries with 'text' and 'type' fields
        """
        distractors = []
        strategies_used = []
        
        # Strategy 1: Hallucinated versions (using hallucination generator)
        if include_hallucinations and num_distractors >= 2:
            hallucination_strategies = ["contradiction", "fabrication", "exaggeration", "misattribution"]
            strategy = random.choice(hallucination_strategies)
            halluc_result = self.hallucination_gen.generate_hallucination(
                correct_answer, strategy, question
            )
            distractors.append({
                'text': halluc_result['hallucinated_answer'],
                'type': 'hallucination',
                'strategy': strategy,
                'is_correct': False,
                'is_hallucination': True
            })
            strategies_used.append(strategy)
        
        # Strategy 2: Plausible but wrong answers (related but incorrect)
        if num_distractors >= 2:
            wrong_answer = self._generate_plausible_wrong_answer(correct_answer, question)
            distractors.append({
                'text': wrong_answer,
                'type': 'plausible_wrong',
                'is_correct': False,
                'is_hallucination': False
            })
        
        # Strategy 3: Partially correct but incomplete/misleading
        if num_distractors >= 3:
            partial_answer = self._generate_partial_answer(correct_answer)
            distractors.append({
                'text': partial_answer,
                'type': 'partial_correct',
                'is_correct': False,
                'is_hallucination': False
            })
        
        # Strategy 4: Opposite or contradictory answer
        if num_distractors >= 4:
            opposite_answer = self._generate_opposite_answer(correct_answer, question)
            distractors.append({
                'text': opposite_answer,
                'type': 'opposite',
                'is_correct': False,
                'is_hallucination': False
            })
        
        # Shuffle and return requested number
        random.shuffle(distractors)
        return distractors[:num_distractors]
    
    def _generate_plausible_wrong_answer(self, correct_answer: str, question: str) -> str:
        """Generate a plausible but incorrect answer"""
        # Extract key concepts and create a related but wrong answer
        # This is a simplified approach - in practice, you might use NLP
        
        # Common diabetes misconceptions
        misconceptions = [
            "People with diabetes should avoid all carbohydrates",
            "Diabetes can be cured with diet alone",
            "Only overweight people get type 2 diabetes",
            "Insulin causes diabetes",
            "Natural remedies can replace medication",
            "Diabetes only affects blood sugar, not other organs",
        ]
        
        # Try to match question topic and create a related wrong answer
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['diet', 'food', 'eat', 'meal']):
            return "People with diabetes should completely eliminate all sugars and carbohydrates from their diet, as they are harmful to blood glucose control."
        elif any(word in question_lower for word in ['exercise', 'physical', 'activity']):
            return "People with diabetes should avoid exercise as it can cause dangerous blood sugar fluctuations."
        elif any(word in question_lower for word in ['medication', 'insulin', 'drug']):
            return "Diabetes medications should only be taken when blood sugar is high, not on a regular schedule."
        elif any(word in question_lower for word in ['symptom', 'sign', 'indicate']):
            return "Diabetes symptoms are always severe and immediately noticeable, making early detection easy."
        else:
            # Generic plausible wrong answer
            return random.choice(misconceptions)
    
    def _generate_partial_answer(self, correct_answer: str) -> str:
        """Generate a partially correct but incomplete or misleading answer"""
        # Take first part of answer and add misleading conclusion
        sentences = correct_answer.split('.')
        if len(sentences) > 1:
            # Use first sentence(s) but with wrong implication
            partial = '. '.join(sentences[:min(2, len(sentences)-1)])
            return f"{partial}. However, this means that no further medical care is needed."
        else:
            # Add misleading qualifier
            return f"{correct_answer} This is the only treatment option available."
    
    def _generate_opposite_answer(self, correct_answer: str, question: str) -> str:
        """Generate an answer that contradicts the correct one"""
        # Simple strategy: negate key statements
        opposite_phrases = [
            "Actually, the opposite is true:",
            "This is incorrect. In fact:",
            "Contrary to this:",
        ]
        
        prefix = random.choice(opposite_phrases)
        # Create a contradictory statement
        return f"{prefix} {correct_answer.lower().replace('should', 'should not').replace('is', 'is not').replace('can', 'cannot')}"
    
    def create_multiple_choice_question(
        self,
        qa_pair: Dict[str, str],
        num_options: int = 4,
        include_hallucinations: bool = True
    ) -> Dict:
        """
        Create a multiple-choice question from a Q&A pair
        
        Args:
            qa_pair: Dictionary with 'question' and 'answer' keys
            num_options: Total number of answer options (including correct one)
            include_hallucinations: Whether to include hallucinated distractors
            
        Returns:
            Dictionary with question and multiple choice options
        """
        question = qa_pair['question']
        correct_answer = qa_pair['answer']
        
        # Generate distractors
        num_distractors = num_options - 1
        distractors = self.generate_distractors(
            correct_answer,
            question,
            num_distractors=num_distractors,
            include_hallucinations=include_hallucinations
        )
        
        # Create all options
        all_options = [{
            'text': correct_answer,
            'type': 'correct',
            'is_correct': True,
            'is_hallucination': False
        }] + distractors
        
        # Shuffle options (so correct answer isn't always first)
        random.shuffle(all_options)
        
        # Find correct answer index
        correct_index = next(i for i, opt in enumerate(all_options) if opt['is_correct'])
        
        # Create question structure
        mc_question = {
            'id': qa_pair.get('id', random.randint(1000, 9999)),
            'question': question,
            'options': [
                {
                    'option_id': chr(65 + i),  # A, B, C, D, etc.
                    'text': opt['text'],
                    'is_correct': opt.get('is_correct', False),
                    'type': opt.get('type', 'unknown'),
                    'is_hallucination': opt.get('is_hallucination', False),
                    'hallucination_strategy': opt.get('strategy', None)
                }
                for i, opt in enumerate(all_options)
            ],
            'correct_answer': chr(65 + correct_index),  # A, B, C, or D
            'ground_truth': correct_answer,
            'metadata': {
                'num_options': num_options,
                'has_hallucinated_distractors': include_hallucinations,
                'original_id': qa_pair.get('id')
            }
        }
        
        return mc_question
    
    def create_multiple_choice_benchmark(
        self,
        qa_pairs: List[Dict[str, str]],
        num_options: int = 4,
        hallucination_ratio: float = 0.5,
        include_hallucinations: bool = True
    ) -> List[Dict]:
        """
        Create a multiple-choice benchmark dataset
        
        Args:
            qa_pairs: List of Q&A pairs
            num_options: Number of options per question
            hallucination_ratio: Ratio of questions that should have hallucinated distractors
            include_hallucinations: Whether to include hallucinated distractors
            
        Returns:
            List of multiple-choice questions
        """
        benchmark = []
        num_with_hallucinations = int(len(qa_pairs) * hallucination_ratio)
        hallucination_indices = set(random.sample(range(len(qa_pairs)), num_with_hallucinations))
        
        for idx, qa_pair in enumerate(qa_pairs):
            has_hallucinated_distractors = idx in hallucination_indices if include_hallucinations else False
            
            mc_question = self.create_multiple_choice_question(
                qa_pair,
                num_options=num_options,
                include_hallucinations=has_hallucinated_distractors
            )
            
            benchmark.append(mc_question)
        
        # Shuffle to avoid order bias
        random.shuffle(benchmark)
        
        return benchmark
