"""
Hallucination generator for creating benchmark test cases
"""
import random
from typing import List, Dict, Optional
import json


class HallucinationGenerator:
    """Generate hallucinated versions of answers for benchmark testing"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the hallucination generator
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        
        # Common medical misinformation patterns
        self.contradiction_patterns = [
            "Actually, the opposite is true:",
            "Recent studies have shown that:",
            "Contrary to popular belief:",
        ]
        
        self.fabrication_patterns = [
            "A 2023 study found that",
            "According to the latest research",
            "Medical experts now recommend",
        ]
        
        self.exaggeration_patterns = [
            "always",
            "never",
            "completely",
            "absolutely",
            "guaranteed",
        ]
    
    def generate_hallucination(
        self, 
        original_answer: str, 
        strategy: str,
        question: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a hallucinated version of an answer
        
        Args:
            original_answer: The correct answer
            strategy: Type of hallucination to inject
            question: Optional question context
            
        Returns:
            Dictionary with hallucinated answer and metadata
        """
        if strategy == "contradiction":
            return self._generate_contradiction(original_answer)
        elif strategy == "fabrication":
            return self._generate_fabrication(original_answer, question)
        elif strategy == "omission":
            return self._generate_omission(original_answer)
        elif strategy == "exaggeration":
            return self._generate_exaggeration(original_answer)
        elif strategy == "misattribution":
            return self._generate_misattribution(original_answer)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _generate_contradiction(self, answer: str) -> Dict[str, str]:
        """Generate a contradictory answer"""
        # Simple strategy: reverse key statements
        # In a real implementation, you might use NLP to identify key claims
        hallucinated = f"Actually, the opposite is true. {answer.lower()}"
        
        return {
            'hallucinated_answer': hallucinated,
            'strategy': 'contradiction',
            'is_hallucination': True
        }
    
    def _generate_fabrication(self, answer: str, question: Optional[str]) -> Dict[str, str]:
        """Generate an answer with fabricated information"""
        # Add false medical claims
        false_claims = [
            "A recent study published in Nature Medicine found that",
            "The FDA has recently approved a new treatment that",
            "Clinical trials have shown that 95% of patients experience",
        ]
        
        prefix = random.choice(false_claims)
        hallucinated = f"{prefix} {answer}. However, this is not supported by current medical evidence."
        
        return {
            'hallucinated_answer': hallucinated,
            'strategy': 'fabrication',
            'is_hallucination': True
        }
    
    def _generate_omission(self, answer: str) -> Dict[str, str]:
        """Generate an answer with critical information omitted"""
        # Remove important qualifiers and warnings
        # In practice, you'd use NLP to identify critical information
        sentences = answer.split('.')
        if len(sentences) > 1:
            # Remove last sentence (often contains important warnings)
            hallucinated = '. '.join(sentences[:-1]) + '.'
        else:
            hallucinated = answer  # Can't omit if only one sentence
        
        return {
            'hallucinated_answer': hallucinated,
            'strategy': 'omission',
            'is_hallucination': True,
            'note': 'Critical information may have been omitted'
        }
    
    def _generate_exaggeration(self, answer: str) -> Dict[str, str]:
        """Generate an answer with exaggerated claims"""
        # Add absolute terms
        exaggeration_words = ["always", "never", "completely", "absolutely"]
        words = answer.split()
        
        # Insert exaggeration words (simplified approach)
        if len(words) > 3:
            insert_pos = random.randint(1, min(3, len(words) - 1))
            words.insert(insert_pos, random.choice(exaggeration_words))
            hallucinated = ' '.join(words)
        else:
            hallucinated = f"{random.choice(exaggeration_words).capitalize()} {answer}"
        
        return {
            'hallucinated_answer': hallucinated,
            'strategy': 'exaggeration',
            'is_hallucination': True
        }
    
    def _generate_misattribution(self, answer: str) -> Dict[str, str]:
        """Generate an answer with misattributed information"""
        false_sources = [
            "According to the American Diabetes Association guidelines from 2024",
            "The World Health Organization's latest report states",
            "The CDC recommends",
        ]
        
        hallucinated = f"{random.choice(false_sources)}: {answer}"
        
        return {
            'hallucinated_answer': hallucinated,
            'strategy': 'misattribution',
            'is_hallucination': True,
            'note': 'Source attribution may be incorrect'
        }
    
    def create_benchmark_dataset(
        self,
        qa_pairs: List[Dict[str, str]],
        hallucination_ratio: float = 0.3,
        strategies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Create a benchmark dataset with both correct and hallucinated answers
        
        Args:
            qa_pairs: List of original Q&A pairs
            hallucination_ratio: Proportion of answers that should be hallucinated
            strategies: List of hallucination strategies to use
            
        Returns:
            List of benchmark test cases
        """
        if strategies is None:
            from config import HALLUCINATION_STRATEGIES
            strategies = HALLUCINATION_STRATEGIES
        
        benchmark = []
        num_hallucinations = int(len(qa_pairs) * hallucination_ratio)
        hallucination_indices = set(random.sample(range(len(qa_pairs)), num_hallucinations))
        
        for idx, qa_pair in enumerate(qa_pairs):
            if idx in hallucination_indices:
                # Generate hallucinated version
                strategy = random.choice(strategies)
                hallucination = self.generate_hallucination(
                    qa_pair['answer'],
                    strategy,
                    qa_pair['question']
                )
                
                benchmark_item = {
                    'id': qa_pair.get('id', idx),
                    'question': qa_pair['question'],
                    'answer': hallucination['hallucinated_answer'],
                    'ground_truth': qa_pair['answer'],
                    'is_hallucination': True,
                    'hallucination_strategy': strategy,
                    'metadata': {
                        'source': 'generated',
                        'original_id': qa_pair.get('id', idx)
                    }
                }
            else:
                # Keep original (correct) answer
                benchmark_item = {
                    'id': qa_pair.get('id', idx),
                    'question': qa_pair['question'],
                    'answer': qa_pair['answer'],
                    'ground_truth': qa_pair['answer'],
                    'is_hallucination': False,
                    'hallucination_strategy': None,
                    'metadata': {
                        'source': 'original',
                        'original_id': qa_pair.get('id', idx)
                    }
                }
            
            benchmark.append(benchmark_item)
        
        # Shuffle to avoid order bias
        random.shuffle(benchmark)
        
        return benchmark
