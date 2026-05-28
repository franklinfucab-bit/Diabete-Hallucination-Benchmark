"""
Evaluation framework for hallucination detection
"""
from typing import List, Dict, Optional
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pandas as pd


class HallucinationEvaluator:
    """Evaluate AI model performance on hallucination detection"""
    
    def __init__(self):
        """Initialize the evaluator"""
        self.results = []
    
    def evaluate_model(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, float]:
        """
        Evaluate model predictions against ground truth
        
        Args:
            predictions: List of model predictions with 'id' and 'is_hallucination' fields
            ground_truth: List of ground truth labels with 'id' and 'is_hallucination' fields
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Create mapping for quick lookup
        gt_dict = {item['id']: item['is_hallucination'] for item in ground_truth}
        pred_dict = {item['id']: item['is_hallucination'] for item in predictions}
        
        # Align predictions with ground truth
        y_true = []
        y_pred = []
        
        for item_id in gt_dict.keys():
            if item_id in pred_dict:
                y_true.append(1 if gt_dict[item_id] else 0)
                y_pred.append(1 if pred_dict[item_id] else 0)
        
        if len(y_true) == 0:
            raise ValueError("No matching predictions found for ground truth")
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # Calculate hallucination detection rate (recall for hallucination class)
        hallucination_detection_rate = recall
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'hallucination_detection_rate': float(hallucination_detection_rate),
            'true_positives': int(tp),
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'total_samples': len(y_true)
        }
        
        return metrics
    
    def evaluate_by_strategy(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate performance broken down by hallucination strategy
        
        Args:
            predictions: List of model predictions
            ground_truth: List of ground truth labels with 'hallucination_strategy' field
            
        Returns:
            Dictionary mapping strategy to metrics
        """
        strategy_metrics = {}
        
        # Group by strategy
        strategies = set()
        for item in ground_truth:
            if item.get('hallucination_strategy'):
                strategies.add(item['hallucination_strategy'])
        
        for strategy in strategies:
            # Filter by strategy
            gt_filtered = [item for item in ground_truth 
                          if item.get('hallucination_strategy') == strategy]
            pred_filtered = [item for item in predictions 
                           if item['id'] in [gt['id'] for gt in gt_filtered]]
            
            if len(gt_filtered) > 0:
                strategy_metrics[strategy] = self.evaluate_model(pred_filtered, gt_filtered)
        
        return strategy_metrics
    
    def save_results(
        self,
        metrics: Dict[str, float],
        output_path: Path,
        model_name: str = "unknown",
        strategy_breakdown: Optional[Dict] = None
    ):
        """
        Save evaluation results to file
        
        Args:
            metrics: Overall evaluation metrics
            output_path: Path to save results
            model_name: Name of the evaluated model
            strategy_breakdown: Optional per-strategy metrics
        """
        results = {
            'model_name': model_name,
            'overall_metrics': metrics,
            'strategy_breakdown': strategy_breakdown or {}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {output_path}")
    
    def generate_report(
        self,
        metrics: Dict[str, float],
        strategy_breakdown: Optional[Dict] = None
    ) -> str:
        """
        Generate a human-readable evaluation report
        
        Args:
            metrics: Overall evaluation metrics
            strategy_breakdown: Optional per-strategy metrics
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("HALLUCINATION DETECTION BENCHMARK RESULTS")
        report.append("=" * 60)
        report.append("")
        
        report.append("Overall Metrics:")
        report.append("-" * 60)
        report.append(f"Accuracy:                    {metrics['accuracy']:.4f}")
        report.append(f"Precision:                   {metrics['precision']:.4f}")
        report.append(f"Recall:                      {metrics['recall']:.4f}")
        report.append(f"F1 Score:                    {metrics['f1_score']:.4f}")
        report.append(f"Hallucination Detection Rate: {metrics['hallucination_detection_rate']:.4f}")
        report.append("")
        report.append("Confusion Matrix:")
        report.append(f"  True Positives:  {metrics['true_positives']}")
        report.append(f"  True Negatives:  {metrics['true_negatives']}")
        report.append(f"  False Positives: {metrics['false_positives']}")
        report.append(f"  False Negatives: {metrics['false_negatives']}")
        report.append(f"  Total Samples:   {metrics['total_samples']}")
        report.append("")
        
        if strategy_breakdown:
            report.append("Performance by Hallucination Strategy:")
            report.append("-" * 60)
            for strategy, strat_metrics in strategy_breakdown.items():
                report.append(f"\n{strategy.upper()}:")
                report.append(f"  Accuracy: {strat_metrics['accuracy']:.4f}")
                report.append(f"  F1 Score: {strat_metrics['f1_score']:.4f}")
                report.append(f"  Detection Rate: {strat_metrics['hallucination_detection_rate']:.4f}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
