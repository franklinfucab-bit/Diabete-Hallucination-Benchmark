"""
Test the evaluation pipeline with sample data
This creates a mock test to verify the evaluation system works
"""
import json
from pathlib import Path
from evaluator import HallucinationEvaluator
from mc_evaluator import MultipleChoiceEvaluator


def test_binary_evaluator():
    """Test the binary evaluation pipeline"""
    print("=" * 80)
    print("TESTING BINARY EVALUATION PIPELINE")
    print("=" * 80)
    
    # Create sample ground truth
    ground_truth = [
        {'id': 1, 'is_hallucination': False},
        {'id': 2, 'is_hallucination': True},
        {'id': 3, 'is_hallucination': False},
        {'id': 4, 'is_hallucination': True},
        {'id': 5, 'is_hallucination': False},
    ]
    
    # Create mock predictions (simulating a model that's 80% accurate)
    predictions = [
        {'id': 1, 'is_hallucination': False},  # Correct
        {'id': 2, 'is_hallucination': True},   # Correct
        {'id': 3, 'is_hallucination': False},  # Correct
        {'id': 4, 'is_hallucination': False},  # Wrong (missed hallucination)
        {'id': 5, 'is_hallucination': False},  # Correct
    ]
    
    evaluator = HallucinationEvaluator()
    metrics = evaluator.evaluate_model(predictions, ground_truth)
    
    print(f"\nTest Results:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")
    print(f"  True Positives: {metrics['true_positives']}")
    print(f"  True Negatives: {metrics['true_negatives']}")
    print(f"  False Positives: {metrics['false_positives']}")
    print(f"  False Negatives: {metrics['false_negatives']}")
    
    # Expected: 4/5 correct = 0.8 accuracy
    assert metrics['accuracy'] == 0.8, f"Expected accuracy 0.8, got {metrics['accuracy']}"
    print("\n✓ Binary evaluator test passed!")
    
    return True


def test_multiple_choice_evaluator():
    """Test the multiple-choice evaluation pipeline"""
    print("\n" + "=" * 80)
    print("TESTING MULTIPLE-CHOICE EVALUATION PIPELINE")
    print("=" * 80)
    
    # Create sample ground truth
    ground_truth = [
        {
            'id': 1,
            'correct_answer': 'A',
            'options': [
                {'option_id': 'A', 'is_correct': True, 'is_hallucination': False},
                {'option_id': 'B', 'is_correct': False, 'is_hallucination': True},
                {'option_id': 'C', 'is_correct': False, 'is_hallucination': False},
                {'option_id': 'D', 'is_correct': False, 'is_hallucination': False},
            ]
        },
        {
            'id': 2,
            'correct_answer': 'B',
            'options': [
                {'option_id': 'A', 'is_correct': False, 'is_hallucination': False},
                {'option_id': 'B', 'is_correct': True, 'is_hallucination': False},
                {'option_id': 'C', 'is_correct': False, 'is_hallucination': True},
                {'option_id': 'D', 'is_correct': False, 'is_hallucination': False},
            ]
        },
        {
            'id': 3,
            'correct_answer': 'C',
            'options': [
                {'option_id': 'A', 'is_correct': False, 'is_hallucination': False},
                {'option_id': 'B', 'is_correct': False, 'is_hallucination': True},
                {'option_id': 'C', 'is_correct': True, 'is_hallucination': False},
                {'option_id': 'D', 'is_correct': False, 'is_hallucination': False},
            ]
        },
    ]
    
    # Create mock predictions
    predictions = [
        {'id': 1, 'selected_option': 'A'},  # Correct
        {'id': 2, 'selected_option': 'B'},  # Correct
        {'id': 3, 'selected_option': 'B'},  # Wrong (selected hallucinated option)
    ]
    
    evaluator = MultipleChoiceEvaluator()
    metrics = evaluator.evaluate_model(predictions, ground_truth)
    
    print(f"\nTest Results:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Correct Predictions: {metrics['correct_predictions']}/{metrics['total_questions']}")
    print(f"  Hallucination Avoidance Rate: {metrics['hallucination_avoidance_rate']:.4f}")
    print(f"  False Positive Rate: {metrics['false_positive_rate']:.4f}")
    
    # Expected: 2/3 correct = 0.6667 accuracy
    assert abs(metrics['accuracy'] - 0.6667) < 0.01, f"Expected accuracy ~0.6667, got {metrics['accuracy']}"
    print("\n✓ Multiple-choice evaluator test passed!")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("EVALUATION PIPELINE TESTS")
    print("=" * 80)
    print("\nTesting the evaluation systems with mock data...\n")
    
    try:
        test_binary_evaluator()
        test_multiple_choice_evaluator()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe evaluation pipeline is working correctly.")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
