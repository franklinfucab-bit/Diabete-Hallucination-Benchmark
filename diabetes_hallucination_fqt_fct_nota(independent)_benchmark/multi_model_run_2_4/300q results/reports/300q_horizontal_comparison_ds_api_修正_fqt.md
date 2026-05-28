# 300q Horizontal Comparison 修正 (FQT Focus)

**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q. 5 models.**

## Accuracy Table

| Model | Overall | NOTA | FQT | FCT |
|-------|---------|------|-----|-----|
| deepseek-r1_7b | 42.7% | 30.0% | 22.0% | 76.0% |
| gemma_7b | 38.7% | 27.0% | 9.0% | 80.0% |
| llama3.1_8b | 63.7% | 21.2% | 97.0% | 73.0% |
| mistral_latest | 46.0% | 26.0% | 48.0% | 64.0% |
| qwen2.5_7b | 80.7% | 57.0% | 94.0% | 91.0% |

## FQT Ranking (best first)

1. llama3.1_8b
2. qwen2.5_7b
3. mistral_latest
4. deepseek-r1_7b
5. gemma_7b

## FQT Deep Dive

### Wrong count by model


### When wrong, what did models choose? (pred->label)

- **deepseek-r1_7b**: A->D: 50, B->D: 16, C->D: 12
- **gemma_7b**: C->D: 52, A->D: 35, B->D: 4
- **llama3.1_8b**: B->D: 2, A->D: 1
- **mistral_latest**: A->D: 41, B->D: 7, C->D: 4
- **qwen2.5_7b**: A->D: 5, B->D: 1

- **deepseek-r1_7b**: 78 FQT wrong
- **gemma_7b**: 91 FQT wrong
- **llama3.1_8b**: 3 FQT wrong
- **mistral_latest**: 52 FQT wrong
- **qwen2.5_7b**: 6 FQT wrong

### Overlap: FQT questions wrong by N models

- **All models** (1): 
  FQT_034
- **wrong_by_4** (5): FQT_006, FQT_026, FQT_049, FQT_074, FQT_082
- **wrong_by_3** (43): FQT_001, FQT_004, FQT_005, FQT_007, FQT_010, FQT_012, FQT_013, FQT_014, FQT_018, FQT_019, FQT_023, FQT_024, FQT_030, FQT_031, FQT_032 ...
- **wrong_by_2** (29): FQT_002, FQT_003, FQT_008, FQT_009, FQT_016, FQT_021, FQT_025, FQT_028, FQT_029, FQT_036, FQT_043, FQT_057, FQT_061, FQT_062, FQT_064 ...
- **wrong_by_1** (18): FQT_011, FQT_015, FQT_017, FQT_020, FQT_022, FQT_048, FQT_051, FQT_056, FQT_059, FQT_065, FQT_071, FQT_073, FQT_080, FQT_084, FQT_092 ...

### Hardest FQT topics (by number of models that got them wrong)

- **SpecialPops** (5 models): FQT_002, FQT_008, FQT_009, FQT_014, FQT_018 ...
- **Retinopathy_Kidney** (5 models): FQT_006, FQT_007, FQT_020, FQT_023, FQT_025 ...
- **Neuropathy_FootCare** (4 models): FQT_001, FQT_003, FQT_004, FQT_011, FQT_013 ...
- **Acute_Hospital** (3 models): FQT_005, FQT_010, FQT_012, FQT_019, FQT_021 ...

## FQT Summary

- Best on FQT: **llama3.1_8b**
- Worst on FQT: **gemma_7b**
- FQT questions wrong by all models: 1
- FQT questions wrong by only 1 model: 18

## FQT Unexpected Results

- **Consensus wrong** (all models wrong, 1): FQT_034
- **Best model failures** (top model wrong, others correct, 2): FQT_049, FQT_086
- **Worst model succeeds** (worst model correct, others wrong, 5): FQT_022, FQT_067, FQT_071, FQT_092, FQT_094
