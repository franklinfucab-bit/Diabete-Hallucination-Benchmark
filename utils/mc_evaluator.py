"""
Evaluator for multiple-choice hallucination benchmark
"""
from typing import List, Dict, Optional
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pandas as pd


class MultipleChoiceEvaluator:
    """Evaluate AI model performance on multiple-choice hallucination detection"""
    
    def __init__(self):
        """Initialize the evaluator"""
        self.results = []
    
    def evaluate_model(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, float]:
        """
        Evaluate model predictions on multiple-choice questions
        
        Args:
            predictions: List of model predictions with 'id' and 'selected_option' fields
            ground_truth: List of ground truth with 'id' and 'correct_answer' fields
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Create mapping for quick lookup
        gt_dict = {item['id']: item['correct_answer'] for item in ground_truth}
        pred_dict = {item['id']: item['selected_option'] for item in predictions}
        
        # Align predictions with ground truth
        y_true = []
        y_pred = []
        
        correct_predictions = 0
        total_questions = 0
        
        for item_id in gt_dict.keys():
            if item_id in pred_dict:
                correct_answer = gt_dict[item_id].upper()
                predicted_answer = pred_dict[item_id].upper() if pred_dict[item_id] else None
                
                is_correct = (predicted_answer == correct_answer)
                y_true.append(1 if is_correct else 0)
                y_pred.append(1 if is_correct else 0)
                
                if is_correct:
                    correct_predictions += 1
                total_questions += 1
        
        if total_questions == 0:
            raise ValueError("No matching predictions found for ground truth")
        
        # Calculate accuracy
        accuracy = correct_predictions / total_questions
        
        # For hallucination detection: check if model selected a hallucinated option
        hallucination_metrics = self._evaluate_hallucination_detection(predictions, ground_truth)
        
        metrics = {
            'accuracy': float(accuracy),
            'correct_predictions': correct_predictions,
            'total_questions': total_questions,
            'hallucination_detection_accuracy': hallucination_metrics.get('accuracy', 0.0),
            'hallucination_avoidance_rate': hallucination_metrics.get('avoidance_rate', 0.0),
            'false_positive_rate': hallucination_metrics.get('false_positive_rate', 0.0),
        }
        
        return metrics
    
    def _evaluate_hallucination_detection(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, float]:
        """
        Evaluate how well the model avoids selecting hallucinated options
        
        Args:
            predictions: Model predictions
            ground_truth: Ground truth with option details
            
        Returns:
            Metrics about hallucination detection
        """
        # Create mapping
        gt_dict = {item['id']: item for item in ground_truth}
        pred_dict = {item['id']: item['selected_option'] for item in predictions}
        
        total_hallucinated_options = 0
        hallucinated_options_selected = 0
        correct_options_selected = 0
        total_questions = 0
        
        for item_id, gt_item in gt_dict.items():
            if item_id not in pred_dict:
                continue
            
            selected_option = pred_dict[item_id].upper() if pred_dict[item_id] else None
            if not selected_option:
                continue
            
            # Find the selected option in ground truth
            selected_opt_data = None
            for opt in gt_item['options']:
                if opt['option_id'].upper() == selected_option:
                    selected_opt_data = opt
                    break
            
            if selected_opt_data:
                total_questions += 1
                
                # Count hallucinated options in this question
                hallucinated_opts = [opt for opt in gt_item['options'] if opt.get('is_hallucination', False)]
                total_hallucinated_options += len(hallucinated_opts)
                
                # Check if selected option is hallucinated
                if selected_opt_data.get('is_hallucination', False):
                    hallucinated_options_selected += 1
                
                # Check if selected option is correct
                if selected_opt_data.get('is_correct', False):
                    correct_options_selected += 1
        
        avoidance_rate = 0.0
        if total_questions > 0:
            avoidance_rate = (total_questions - hallucinated_options_selected) / total_questions
        
        false_positive_rate = 0.0
        if total_questions > 0:
            false_positive_rate = hallucinated_options_selected / total_questions
        
        accuracy = correct_options_selected / total_questions if total_questions > 0 else 0.0
        
        return {
            'accuracy': accuracy,
            'avoidance_rate': avoidance_rate,
            'false_positive_rate': false_positive_rate,
            'hallucinated_options_selected': hallucinated_options_selected,
            'total_questions': total_questions
        }
    
    def evaluate_by_distractor_type(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate performance broken down by distractor type
        
        Args:
            predictions: Model predictions
            ground_truth: Ground truth with distractor types
            
        Returns:
            Dictionary mapping distractor type to metrics
        """
        type_metrics = {}
        
        # Group by distractor type
        distractor_types = set()
        for item in ground_truth:
            for opt in item['options']:
                if not opt['is_correct']:
                    distractor_types.add(opt.get('type', 'unknown'))
        
        for dist_type in distractor_types:
            # Filter questions that have this distractor type
            relevant_questions = [
                item for item in ground_truth
                if any(opt.get('type') == dist_type for opt in item['options'] if not opt['is_correct'])
            ]
            
            if len(relevant_questions) > 0:
                # Filter predictions for these questions
                relevant_predictions = [
                    pred for pred in predictions
                    if pred['id'] in [q['id'] for q in relevant_questions]
                ]
                
                # Calculate how often model selected this distractor type
                selected_count = 0
                for pred in relevant_predictions:
                    selected_option = pred.get('selected_option', '').upper()
                    for q in relevant_questions:
                        if q['id'] == pred['id']:
                            for opt in q['options']:
                                if opt['option_id'].upper() == selected_option and opt.get('type') == dist_type:
                                    selected_count += 1
                                    break
                
                type_metrics[dist_type] = {
                    'questions_with_this_distractor': len(relevant_questions),
                    'times_selected': selected_count,
                    'selection_rate': selected_count / len(relevant_questions) if relevant_questions else 0.0
                }
        
        return type_metrics
    
    def save_results(
        self,
        metrics: Dict[str, float],
        output_path: Path,
        model_name: str = "unknown",
        distractor_breakdown: Optional[Dict] = None
    ):
        """
        Save evaluation results to file
        
        Args:
            metrics: Overall evaluation metrics
            output_path: Path to save results
            model_name: Name of the evaluated model
            distractor_breakdown: Optional per-distractor-type metrics
        """
        results = {
            'model_name': model_name,
            'overall_metrics': metrics,
            'distractor_breakdown': distractor_breakdown or {}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {output_path}")
    
    def generate_report(
        self,
        metrics: Dict[str, float],
        distractor_breakdown: Optional[Dict] = None
    ) -> str:
        """
        Generate a human-readable evaluation report
        
        Args:
            metrics: Overall evaluation metrics
            distractor_breakdown: Optional per-distractor-type metrics
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("MULTIPLE-CHOICE HALLUCINATION BENCHMARK RESULTS")
        report.append("=" * 60)
        report.append("")
        
        report.append("Overall Metrics:")
        report.append("-" * 60)
        report.append(f"Accuracy:                        {metrics['accuracy']:.4f}")
        report.append(f"Correct Predictions:              {metrics['correct_predictions']}/{metrics['total_questions']}")
        report.append(f"Hallucination Detection Accuracy: {metrics['hallucination_detection_accuracy']:.4f}")
        report.append(f"Hallucination Avoidance Rate:     {metrics['hallucination_avoidance_rate']:.4f}")
        report.append(f"False Positive Rate:              {metrics['false_positive_rate']:.4f}")
        report.append("")
        
        if distractor_breakdown:
            report.append("Performance by Distractor Type:")
            report.append("-" * 60)
            for dist_type, dist_metrics in distractor_breakdown.items():
                report.append(f"\n{dist_type.upper()}:")
                report.append(f"  Questions with this distractor: {dist_metrics['questions_with_this_distractor']}")
                report.append(f"  Times selected: {dist_metrics['times_selected']}")
                report.append(f"  Selection rate: {dist_metrics['selection_rate']:.4f}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
