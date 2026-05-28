"""
Comprehensive validation and testing script for both benchmark types
Run this before submitting to your instructor
"""
import json
from pathlib import Path
from typing import Dict, List
import sys


class BenchmarkValidator:
    """Validate benchmark files and provide quality checks"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate_binary_benchmark(self, file_path: Path) -> bool:
        """Validate the binary hallucination detection benchmark"""
        print("=" * 80)
        print("VALIDATING BINARY HALLUCINATION BENCHMARK")
        print("=" * 80)
        
        if not file_path.exists():
            self.errors.append(f"Binary benchmark file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line) for line in f]
        except Exception as e:
            self.errors.append(f"Error reading binary benchmark: {e}")
            return False
        
        print(f"\n✓ File loaded successfully: {len(data)} samples")
        
        # Validate structure
        required_fields = ['id', 'question', 'answer', 'ground_truth', 'is_hallucination']
        for i, item in enumerate(data):
            for field in required_fields:
                if field not in item:
                    self.errors.append(f"Sample {i}: Missing required field '{field}'")
        
        # Statistics
        correct_count = sum(1 for item in data if not item.get('is_hallucination', False))
        hallucinated_count = sum(1 for item in data if item.get('is_hallucination', False))
        
        self.stats['binary'] = {
            'total': len(data),
            'correct': correct_count,
            'hallucinated': hallucinated_count,
            'correct_ratio': correct_count / len(data) if data else 0,
            'hallucination_ratio': hallucinated_count / len(data) if data else 0
        }
        
        print(f"\nStatistics:")
        print(f"  Total samples: {len(data)}")
        print(f"  Correct answers: {correct_count} ({correct_count/len(data)*100:.1f}%)")
        print(f"  Hallucinated answers: {hallucinated_count} ({hallucinated_count/len(data)*100:.1f}%)")
        
        # Check hallucination strategies
        strategies = {}
        for item in data:
            if item.get('is_hallucination') and item.get('hallucination_strategy'):
                strategy = item['hallucination_strategy']
                strategies[strategy] = strategies.get(strategy, 0) + 1
        
        if strategies:
            print(f"\nHallucination strategies:")
            for strategy, count in sorted(strategies.items()):
                print(f"  {strategy}: {count}")
        
        # Validate data quality
        empty_questions = sum(1 for item in data if not item.get('question', '').strip())
        empty_answers = sum(1 for item in data if not item.get('answer', '').strip())
        
        if empty_questions:
            self.warnings.append(f"{empty_questions} samples have empty questions")
        if empty_answers:
            self.warnings.append(f"{empty_answers} samples have empty answers")
        
        # Check for matching ground truth
        mismatches = 0
        for item in data:
            if not item.get('is_hallucination', False):
                # Correct answers should match ground truth
                if item.get('answer', '') != item.get('ground_truth', ''):
                    mismatches += 1
        
        if mismatches > 0:
            self.warnings.append(f"{mismatches} correct answers don't match ground truth")
        
        # Sample questions
        print(f"\nSample Questions:")
        print("-" * 80)
        for i, item in enumerate(data[:3]):
            print(f"\nSample {i+1}:")
            print(f"  Question: {item['question'][:70]}...")
            print(f"  Is Hallucination: {item['is_hallucination']}")
            if item.get('hallucination_strategy'):
                print(f"  Strategy: {item['hallucination_strategy']}")
        
        return len(self.errors) == 0
    
    def validate_multiple_choice_benchmark(self, file_path: Path) -> bool:
        """Validate the multiple-choice benchmark"""
        print("\n" + "=" * 80)
        print("VALIDATING MULTIPLE-CHOICE BENCHMARK")
        print("=" * 80)
        
        if not file_path.exists():
            self.errors.append(f"Multiple-choice benchmark file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line) for line in f]
        except Exception as e:
            self.errors.append(f"Error reading multiple-choice benchmark: {e}")
            return False
        
        print(f"\n✓ File loaded successfully: {len(data)} questions")
        
        # Validate structure
        required_fields = ['id', 'question', 'options', 'correct_answer', 'ground_truth']
        for i, item in enumerate(data):
            for field in required_fields:
                if field not in item:
                    self.errors.append(f"Question {i}: Missing required field '{field}'")
            
            # Validate options
            if 'options' in item:
                if len(item['options']) < 2:
                    self.errors.append(f"Question {i}: Must have at least 2 options")
                
                correct_count = sum(1 for opt in item['options'] if opt.get('is_correct', False))
                if correct_count != 1:
                    self.errors.append(f"Question {i}: Must have exactly 1 correct answer, found {correct_count}")
                
                # Check correct_answer matches an option
                correct_answer = item.get('correct_answer', '').upper()
                option_ids = [opt.get('option_id', '').upper() for opt in item['options']]
                if correct_answer not in option_ids:
                    self.errors.append(f"Question {i}: correct_answer '{correct_answer}' doesn't match any option")
        
        # Statistics
        total_options = sum(len(item['options']) for item in data)
        total_hallucinated = sum(
            sum(1 for opt in item['options'] if opt.get('is_hallucination', False))
            for item in data
        )
        questions_with_halluc = sum(
            1 for item in data
            if any(opt.get('is_hallucination', False) for opt in item['options'])
        )
        
        self.stats['multiple_choice'] = {
            'total_questions': len(data),
            'total_options': total_options,
            'avg_options_per_question': total_options / len(data) if data else 0,
            'hallucinated_options': total_hallucinated,
            'questions_with_hallucinations': questions_with_halluc
        }
        
        print(f"\nStatistics:")
        print(f"  Total questions: {len(data)}")
        print(f"  Total options: {total_options}")
        print(f"  Average options per question: {total_options/len(data):.1f}")
        print(f"  Hallucinated options: {total_hallucinated}")
        print(f"  Questions with hallucinated distractors: {questions_with_halluc} ({questions_with_halluc/len(data)*100:.1f}%)")
        
        # Distractor type breakdown
        distractor_types = {}
        for item in data:
            for opt in item['options']:
                if not opt.get('is_correct', False):
                    dist_type = opt.get('type', 'unknown')
                    distractor_types[dist_type] = distractor_types.get(dist_type, 0) + 1
        
        if distractor_types:
            print(f"\nDistractor types:")
            for dist_type, count in sorted(distractor_types.items()):
                print(f"  {dist_type}: {count}")
        
        # Hallucination strategy breakdown
        hallucination_strategies = {}
        for item in data:
            for opt in item['options']:
                if opt.get('is_hallucination', False):
                    strategy = opt.get('hallucination_strategy', 'unknown')
                    hallucination_strategies[strategy] = hallucination_strategies.get(strategy, 0) + 1
        
        if hallucination_strategies:
            print(f"\nHallucination strategies:")
            for strategy, count in sorted(hallucination_strategies.items()):
                print(f"  {strategy}: {count}")
        
        # Sample questions
        print(f"\nSample Questions:")
        print("-" * 80)
        for i, item in enumerate(data[:2]):
            print(f"\nQuestion {i+1}:")
            print(f"  {item['question'][:70]}...")
            print(f"  Correct Answer: {item['correct_answer']}")
            print(f"  Options:")
            for opt in item['options']:
                marker = "✓" if opt.get('is_correct') else " "
                hall_marker = " [HALLUCINATION]" if opt.get('is_hallucination') else ""
                print(f"    {marker} {opt.get('option_id', '?')}. {opt.get('text', '')[:60]}...{hall_marker}")
        
        return len(self.errors) == 0
    
    def generate_report(self) -> str:
        """Generate a validation report"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("VALIDATION REPORT")
        report.append("=" * 80)
        
        if self.errors:
            report.append(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                report.append(f"  - {error}")
        else:
            report.append("\n✓ No errors found!")
        
        if self.warnings:
            report.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                report.append(f"  - {warning}")
        else:
            report.append("\n✓ No warnings!")
        
        if self.stats:
            report.append("\n📊 STATISTICS:")
            if 'binary' in self.stats:
                report.append("\nBinary Benchmark:")
                stats = self.stats['binary']
                report.append(f"  Total: {stats['total']}")
                report.append(f"  Correct: {stats['correct']} ({stats['correct_ratio']*100:.1f}%)")
                report.append(f"  Hallucinated: {stats['hallucinated']} ({stats['hallucination_ratio']*100:.1f}%)")
            
            if 'multiple_choice' in self.stats:
                report.append("\nMultiple-Choice Benchmark:")
                stats = self.stats['multiple_choice']
                report.append(f"  Total Questions: {stats['total_questions']}")
                report.append(f"  Total Options: {stats['total_options']}")
                report.append(f"  Hallucinated Options: {stats['hallucinated_options']}")
                report.append(f"  Questions with Hallucinations: {stats['questions_with_hallucinations']}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        from config import BENCHMARK_OUTPUT
        
        binary_path = Path(BENCHMARK_OUTPUT)
        mc_path = Path("output/diabetes_multiple_choice_benchmark.jsonl")
        
        binary_valid = self.validate_binary_benchmark(binary_path)
        mc_valid = self.validate_multiple_choice_benchmark(mc_path)
        
        print(self.generate_report())
        
        return binary_valid and mc_valid and len(self.errors) == 0


def main():
    """Main validation function"""
    print("\n" + "=" * 80)
    print("BENCHMARK VALIDATION AND TESTING")
    print("=" * 80)
    print("\nThis script validates both benchmark types and checks data quality.")
    print("Run this before submitting to your instructor.\n")
    
    validator = BenchmarkValidator()
    success = validator.run_all_checks()
    
    if success:
        print("\n✅ All validations passed! Benchmarks are ready for review.")
        return 0
    else:
        print("\n❌ Validation failed. Please fix the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
