"""
Data loader for processing Excel Q&A dataset
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import json


class DiabetesQALoader:
    """Load and process diabetes Q&A dataset from Excel"""
    
    def __init__(self, excel_path: Path):
        """
        Initialize the loader
        
        Args:
            excel_path: Path to the Excel file containing Q&A pairs
        """
        self.excel_path = excel_path
        self.data = None
        
    def load(self) -> pd.DataFrame:
        """
        Load the Excel file
        
        Returns:
            DataFrame with Q&A pairs
        """
        if not self.excel_path.exists():
            raise FileNotFoundError(
                f"Excel file not found at {self.excel_path}. "
                f"Please place your diabetes Q&A dataset at this location."
            )
        
        # Try to read Excel file
        try:
            self.data = pd.read_excel(self.excel_path)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")
        
        # Validate required columns
        required_columns = self._detect_columns()
        missing = [col for col in required_columns.values() if col not in self.data.columns]
        
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Found columns: {list(self.data.columns)}. "
                f"Expected columns: {list(required_columns.values())}"
            )
        
        return self.data
    
    def _detect_columns(self) -> Dict[str, str]:
        """
        Detect column names (supports various naming conventions)
        
        Returns:
            Dictionary mapping standard names to actual column names
        """
        columns = {col.lower(): col for col in self.data.columns}
        
        # Try to find question column
        question_col = None
        for key in ['question', 'q', 'questions', 'query', 'prompt']:
            if key in columns:
                question_col = columns[key]
                break
        
        # Try to find answer column
        answer_col = None
        for key in ['answer', 'a', 'answers', 'response', 'ground_truth']:
            if key in columns:
                answer_col = columns[key]
                break
        
        if question_col is None or answer_col is None:
            # If not found, assume first two columns
            question_col = self.data.columns[0]
            answer_col = self.data.columns[1]
        
        return {
            'question': question_col,
            'answer': answer_col
        }
    
    def get_qa_pairs(self) -> List[Dict[str, str]]:
        """
        Extract Q&A pairs from the loaded data
        
        Returns:
            List of dictionaries with 'question' and 'answer' keys
        """
        if self.data is None:
            self.load()
        
        columns = self._detect_columns()
        qa_pairs = []
        
        for idx, row in self.data.iterrows():
            qa_pairs.append({
                'id': idx,
                'question': str(row[columns['question']]).strip(),
                'answer': str(row[columns['answer']]).strip(),
                'source': 'original'
            })
        
        return qa_pairs
    
    def save_jsonl(self, output_path: Path, qa_pairs: List[Dict]):
        """
        Save Q&A pairs to JSONL format
        
        Args:
            output_path: Path to save the JSONL file
            qa_pairs: List of Q&A dictionaries
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in qa_pairs:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"Saved {len(qa_pairs)} Q&A pairs to {output_path}")
