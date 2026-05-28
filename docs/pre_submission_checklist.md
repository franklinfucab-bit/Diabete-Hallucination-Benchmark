# Pre-Submission Checklist

Use this checklist before sending your benchmark to your instructor.

## ✅ File Structure

- [ ] `data/diabetes_QA_dataset.xlsx` - Original dataset is present
- [ ] `output/diabetes_hallucination_benchmark.jsonl` - Binary benchmark created
- [ ] `output/diabetes_multiple_choice_benchmark.jsonl` - Multiple-choice benchmark created
- [ ] All Python scripts are present and functional

## ✅ Validation

Run the validation script:
```bash
python validate_benchmarks.py
```

- [ ] No errors reported
- [ ] Statistics look reasonable
- [ ] Sample questions are displayed correctly

## ✅ Testing

Run the evaluation pipeline test:
```bash
python test_evaluation_pipeline.py
```

- [ ] All tests pass
- [ ] Evaluation metrics are calculated correctly

## ✅ Data Quality Checks

### Binary Benchmark
- [ ] Total samples match expected count (1075)
- [ ] Correct/hallucinated ratio is reasonable (e.g., 70/30 or 50/50)
- [ ] All required fields are present (id, question, answer, ground_truth, is_hallucination)
- [ ] Hallucination strategies are distributed

### Multiple-Choice Benchmark
- [ ] Total questions match expected count (1075)
- [ ] Each question has exactly 1 correct answer
- [ ] Each question has the expected number of options (default: 4)
- [ ] Hallucinated distractors are properly marked
- [ ] correct_answer field matches an actual option

## ✅ Documentation

- [ ] README.md is complete and accurate
- [ ] BENCHMARK_DETAILS.md explains the structure
- [ ] MULTIPLE_CHOICE_GUIDE.md explains the multiple-choice format
- [ ] Code comments are clear

## ✅ Quick Manual Checks

### Sample Binary Benchmark Entry
```bash
python -c "import json; print(json.dumps(json.loads(open('output/diabetes_hallucination_benchmark.jsonl').readline()), indent=2))"
```

Check:
- [ ] Has all required fields
- [ ] Question and answer are not empty
- [ ] is_hallucination is boolean
- [ ] If hallucinated, has hallucination_strategy

### Sample Multiple-Choice Entry
```bash
python -c "import json; print(json.dumps(json.loads(open('output/diabetes_multiple_choice_benchmark.jsonl').readline()), indent=2))"
```

Check:
- [ ] Has all required fields
- [ ] Has exactly 1 correct option
- [ ] correct_answer matches an option_id
- [ ] Options are properly formatted

## ✅ Statistics Summary

Your benchmarks should show:

**Binary Benchmark:**
- Total: 1075 samples
- Correct: ~70% (or your chosen ratio)
- Hallucinated: ~30% (or your chosen ratio)
- Strategies: contradiction, fabrication, omission, exaggeration, misattribution

**Multiple-Choice Benchmark:**
- Total: 1075 questions
- Options per question: 4
- Hallucinated distractors: ~50% of questions (or your chosen ratio)
- Distractor types: hallucination, plausible_wrong, partial_correct

## ✅ Final Steps

1. **Run full validation:**
   ```bash
   python validate_benchmarks.py
   ```

2. **Check file sizes** (should be reasonable, not empty):
   ```bash
   ls -lh output/*.jsonl
   ```

3. **Verify you can read the files:**
   ```bash
   python -c "import json; f=open('output/diabetes_hallucination_benchmark.jsonl'); print(f'Binary: {len(list(f))} lines'); f.close()"
   ```

4. **Create a summary document** for your instructor:
   - Total samples/questions
   - Hallucination ratio
   - Key statistics
   - Any known limitations

## 📝 Submission Package

When ready, you should have:

1. **Benchmark Files:**
   - `output/diabetes_hallucination_benchmark.jsonl`
   - `output/diabetes_multiple_choice_benchmark.jsonl`

2. **Documentation:**
   - README.md
   - BENCHMARK_DETAILS.md
   - MULTIPLE_CHOICE_GUIDE.md

3. **Code:**
   - All Python scripts
   - requirements.txt
   - config.py

4. **Validation Report:**
   - Output from `validate_benchmarks.py`

## ⚠️ Common Issues to Check

- [ ] No empty questions or answers
- [ ] No duplicate IDs
- [ ] JSON is valid (no syntax errors)
- [ ] File encoding is UTF-8
- [ ] All paths are relative (not absolute)
- [ ] No hardcoded paths in code

## 🎯 Ready for Submission?

If all items above are checked, your benchmark is ready for instructor review!
