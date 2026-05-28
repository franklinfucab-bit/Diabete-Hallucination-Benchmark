# What are the `tmp_nota_v3_*` files?

## Short answer

They are **temporary output files** from running the NOTA generator script multiple times to produce "additions" (new questions). Each run wrote to a different filename. None of them are needed for the final benchmark; only the merged file matters.

## The flow

1. **Base:** `cleaned_diabetes_nota_seeds.jsonl` = 336 questions (deduplicated seeds).
2. **Goal:** Get to 1000 total = 336 + **664 new** questions.
3. **How new questions are created:** Run `generate_nota_1000q_deepseek.py` with `--num-questions N` and `--output some_file.jsonl`. That creates a file with N new NOTA questions.
4. **Tmp files** = those "some_file.jsonl" outputs from different runs (different N and different names). They were used as **additions** to be appended after the 336 seeds.

## What each tmp file is

| File | Meaning |
|------|--------|
| `tmp_nota_v3_additions_100.jsonl` | Output from a run that was supposed to generate 100 new questions. |
| `tmp_nota_v3_additions_more_65.jsonl` | Another run: 65 more questions. |
| `tmp_nota_v3_additions_more_55.jsonl` | Another run: 55 more (may be partial). |
| `tmp_nota_v3_additions_10a.jsonl` | Small test run: 10 questions. |
| `tmp_nota_v3_additions_chunk1_20.jsonl` | Another batch: 20 questions. |

So: **multiple runs with different batch sizes and filenames** → several tmp files. No single "correct" tmp file; they're just candidate addition sets.

## What actually matters

- **Final benchmark:** `1000q_diabetes_nota_benchmark_v3.jsonl`
- It is built by **merge_nota_v3.py**:  
  `cleaned_diabetes_nota_seeds.jsonl` + **one or more** addition files → renumber IDs → write v3.

So the tmp files are only **inputs** to that merge. You can:
- **Keep** them as a record of what was generated, or
- **Delete** them once v3 is built and you no longer need to re-merge.

## How to get to 1000

1. Run the generator to create **one** (or more) addition files, e.g.  
   `--num-questions 664 --output output/nota_additions_664.jsonl`
2. Point **merge_nota_v3.py** at that file (and any others you want).
3. Run the merge script → `1000q_diabetes_nota_benchmark_v3.jsonl` with 336 + 664 = 1000 questions.

You don’t need all the tmp files; you just need one merged set that sums to 1000.
