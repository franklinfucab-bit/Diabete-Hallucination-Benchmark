# Testing Guide - Pre-Submission Checklist

Before sending your benchmark to your instructor, run these tests to ensure everything is working correctly.

## Quick Tests (Run These First)

### 1. Quick Test (Fastest - ~5 seconds)
```bash
python quick_test.py
```

**What it checks:**
- ✓ Both benchmark files exist
- ✓ Required fields are present
- ✓ Data quality (no empty fields)
- ✓ Basic statistics

**Expected output:** ✅ QUICK TEST PASSED!

---

### 2. Full Validation (Comprehensive - ~10 seconds)
```bash
python validate_benchmarks.py
```

**What it checks:**
- ✓ File structure and format
- ✓ All required fields
- ✓ Data integrity
- ✓ Statistics and distributions
- ✓ Sample questions display
- ✓ Hallucination strategy distribution

**Expected output:** ✅ All validations passed! Benchmarks are ready for review.

---

### 3. Evaluation Pipeline Test (System Test - ~5 seconds)
```bash
python test_evaluation_pipeline.py
```

**What it checks:**
- ✓ Binary evaluator works correctly
- ✓ Multiple-choice evaluator works correctly
- ✓ Metrics are calculated accurately
- ✓ No errors in evaluation logic

**Expected output:** ✅ ALL TESTS PASSED!

---

## What Each Test Validates

### Binary Benchmark Validation
- [x] File exists and is readable
- [x] 1075 samples total
- [x] ~70% correct, ~30% hallucinated (or your ratio)
- [x] All samples have: id, question, answer, ground_truth, is_hallucination
- [x] Hallucination strategies are distributed
- [x] No empty questions or answers

### Multiple-Choice Benchmark Validation
- [x] File exists and is readable
- [x] 1075 questions total
- [x] Each question has exactly 1 correct answer
- [x] Each question has 4 options (or your specified number)
- [x] correct_answer field matches an actual option
- [x] Hallucinated distractors are properly marked
- [x] Distractor types are distributed

### Evaluation System Test
- [x] Binary evaluator calculates metrics correctly
- [x] Multiple-choice evaluator calculates metrics correctly
- [x] No errors in evaluation logic
- [x] Metrics match expected values

---

## Test Results Summary

After running all tests, you should see:

### ✅ Quick Test Results
```
✓ Found 1075 samples (binary)
✓ Found 1075 questions (multiple-choice)
✓ All required fields present
✓ No empty questions or answers
```

### ✅ Validation Results
```
Binary Benchmark:
  Total: 1075
  Correct: 753 (70.0%)
  Hallucinated: 322 (30.0%)
  Strategies: contradiction, fabrication, omission, exaggeration, misattribution

Multiple-Choice Benchmark:
  Total Questions: 1075
  Total Options: 3762
  Hallucinated Options: 537
  Questions with Hallucinations: 537 (50.0%)
```

### ✅ Evaluation Test Results
```
Binary Evaluator: ✓ Passed
Multiple-Choice Evaluator: ✓ Passed
All metrics calculated correctly
```

---

## Pre-Submission Checklist

Use `pre_submission_checklist.md` for a detailed checklist. Quick version:

- [ ] Run `python quick_test.py` - All checks pass
- [ ] Run `python validate_benchmarks.py` - No errors
- [ ] Run `python test_evaluation_pipeline.py` - All tests pass
- [ ] Check file sizes are reasonable (not empty)
- [ ] Review sample questions manually
- [ ] Verify statistics match expectations

---

## If Tests Fail

### Common Issues and Fixes:

1. **File not found errors:**
   - Make sure you've run `create_benchmark.py` and `create_multiple_choice_benchmark.py`
   - Check files exist in `output/` directory

2. **Missing fields:**
   - Re-run the benchmark creation scripts
   - Check that your Excel file has the correct structure

3. **Empty questions/answers:**
   - Check your source Excel file
   - Verify data loading in `data_loader.py`

4. **Wrong statistics:**
   - Adjust hallucination ratio if needed
   - Re-run with different parameters

---

## Sample Output Files

After validation, you should have:

1. **Binary Benchmark:**
   - `output/diabetes_hallucination_benchmark.jsonl`
   - 1075 lines (one JSON object per line)

2. **Multiple-Choice Benchmark:**
   - `output/diabetes_multiple_choice_benchmark.jsonl`
   - 1075 lines (one JSON object per line)

---

## Ready for Submission?

If all three tests pass:
- ✅ Quick test: PASSED
- ✅ Validation: PASSED  
- ✅ Evaluation pipeline: PASSED

Then your benchmark is **ready for instructor review**! 🎉

---

## Additional Manual Checks (Optional)

1. **View a sample question:**
   ```bash
   python -c "import json; print(json.dumps(json.loads(open('output/diabetes_hallucination_benchmark.jsonl').readline()), indent=2))"
   ```

2. **Count lines:**
   ```bash
   python -c "print(f'Binary: {len(open(\"output/diabetes_hallucination_benchmark.jsonl\").readlines())} lines')"
   ```

3. **Check file sizes:**
   ```bash
   ls -lh output/*.jsonl
   ```

---

## Questions?

If you encounter any issues:
1. Check the error messages carefully
2. Review the validation output
3. Verify your source Excel file
4. Check that all dependencies are installed

Good luck with your submission! 🚀
