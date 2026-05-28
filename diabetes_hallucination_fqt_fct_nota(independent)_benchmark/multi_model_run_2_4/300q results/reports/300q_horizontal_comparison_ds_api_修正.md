# 300q Horizontal Comparison 修正 (Overall: NOTA, FQT, FCT)

**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q. 5 models.**

## Accuracy Table

| Model | Overall | NOTA | FQT | FCT |
|-------|---------|------|-----|-----|
| deepseek-r1_7b | 42.7% | 30.0% | 22.0% | 76.0% |
| gemma_7b | 38.7% | 27.0% | 9.0% | 80.0% |
| llama3.1_8b | 63.7% | 21.2% | 97.0% | 73.0% |
| mistral_latest | 46.0% | 26.0% | 48.0% | 64.0% |
| qwen2.5_7b | 80.7% | 57.0% | 94.0% | 91.0% |

## Model Performance Profiles

- **deepseek-r1_7b**: Best at FCT (76.0%), worst at FQT (22.0%). Spread: 54.0% (specialist)
- **gemma_7b**: Best at FCT (80.0%), worst at FQT (9.0%). Spread: 71.0% (specialist)
- **llama3.1_8b**: Best at FQT (97.0%), worst at NOTA (21.2%). Spread: 75.8% (specialist)
- **mistral_latest**: Best at FCT (64.0%), worst at NOTA (26.0%). Spread: 38.0% (balanced)
- **qwen2.5_7b**: Best at FQT (94.0%), worst at NOTA (57.0%). Spread: 37.0% (balanced)


## NOTA Ranking (best first)

1. qwen2.5_7b
2. deepseek-r1_7b
3. gemma_7b
4. mistral_latest
5. llama3.1_8b

## NOTA Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 70 NOTA wrong
- **gemma_7b**: 73 NOTA wrong
- **llama3.1_8b**: 78 NOTA wrong
- **mistral_latest**: 74 NOTA wrong
- **qwen2.5_7b**: 43 NOTA wrong

### Overlap: NOTA questions wrong by N models

- **All models** (30): 
  NOTA_004, NOTA_014, NOTA_018, NOTA_019, NOTA_023, NOTA_025, NOTA_026, NOTA_027, NOTA_030, NOTA_036, NOTA_037, NOTA_038, NOTA_039, NOTA_040, NOTA_041, NOTA_043, NOTA_045, NOTA_054, NOTA_064, NOTA_067 ...
- **wrong_by_4** (22): NOTA_001, NOTA_002, NOTA_011, NOTA_013, NOTA_016, NOTA_022, NOTA_033, NOTA_035, NOTA_042, NOTA_044, NOTA_048, NOTA_049, NOTA_050, NOTA_057, NOTA_060 ...
- **wrong_by_3** (19): NOTA_003, NOTA_005, NOTA_006, NOTA_008, NOTA_031, NOTA_034, NOTA_052, NOTA_056, NOTA_059, NOTA_062, NOTA_063, NOTA_066, NOTA_069, NOTA_073, NOTA_089 ...
- **wrong_by_2** (15): NOTA_007, NOTA_009, NOTA_010, NOTA_012, NOTA_020, NOTA_024, NOTA_028, NOTA_046, NOTA_047, NOTA_058, NOTA_061, NOTA_068, NOTA_077, NOTA_082, NOTA_084
- **wrong_by_1** (13): NOTA_015, NOTA_017, NOTA_021, NOTA_029, NOTA_032, NOTA_051, NOTA_053, NOTA_055, NOTA_072, NOTA_075, NOTA_086, NOTA_087, NOTA_092

### Hardest NOTA topics (by number of models that got them wrong)

- **integrated_care** (5 models): NOTA_004
- **insulin pump therapy** (5 models): NOTA_014
- **acute decompensated heart failure** (5 models): NOTA_018
- **specialpops** (5 models): NOTA_019
- **guideline-based management** (5 models): NOTA_023
- **SGLT2 inhibitors** (5 models): NOTA_025
- **metformin** (5 models): NOTA_026
- **sulfonylureas** (5 models): NOTA_027
- **emergency medicine** (5 models): NOTA_030
- **GLP-1 agonist** (5 models): NOTA_036
- **preventive care** (5 models): NOTA_037
- **basal rate adjustment** (5 models): NOTA_038
- **renal protection** (5 models): NOTA_039
- **bolus adjustment** (5 models): NOTA_040
- **cardiorenal syndrome** (5 models): NOTA_041

## NOTA Summary

- Best on NOTA: **qwen2.5_7b**
- Worst on NOTA: **llama3.1_8b**
- NOTA questions wrong by all models: 30
- NOTA questions wrong by only 1 model: 13

## NOTA Unexpected Results

- **Consensus wrong** (all models wrong, 30): NOTA_004, NOTA_014, NOTA_018, NOTA_019, NOTA_023, NOTA_025, NOTA_026, NOTA_027, NOTA_030, NOTA_036, NOTA_037, NOTA_038, NOTA_039, NOTA_040, NOTA_041 ...
- **Best model failures** (top model wrong, others correct, 13): NOTA_001, NOTA_002, NOTA_011, NOTA_016, NOTA_022, NOTA_033, NOTA_042, NOTA_048, NOTA_049, NOTA_057, NOTA_058, NOTA_081, NOTA_095
- **Worst model succeeds** (worst model correct, others wrong, 18): NOTA_008, NOTA_015, NOTA_017, NOTA_021, NOTA_029, NOTA_032, NOTA_046, NOTA_051, NOTA_055, NOTA_059, NOTA_068, NOTA_072, NOTA_073, NOTA_075, NOTA_084 ...


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


## FCT Ranking (best first)

1. qwen2.5_7b
2. gemma_7b
3. deepseek-r1_7b
4. llama3.1_8b
5. mistral_latest

## FCT Deep Dive

### Wrong count by model


### When wrong, what did models choose? (pred->label)

- **deepseek-r1_7b**: A->D: 4, B->D: 3, D->B: 3, C->B: 3, C->D: 2, D->C: 2, B->C: 2, C->A: 2 ...
- **gemma_7b**: A->D: 5, D->C: 3, B->D: 2, C->B: 2, B->C: 2, C->A: 2, A->C: 1, A->B: 1 ...
- **llama3.1_8b**: C->D: 6, D->A: 6, D->C: 3, B->C: 3, B->D: 2, A->D: 2, D->B: 2, A->B: 1 ...
- **mistral_latest**: D->B: 6, D->C: 6, D->A: 5, B->D: 4, A->D: 4, C->B: 4, C->D: 3, B->C: 2 ...
- **qwen2.5_7b**: B->D: 2, D->C: 2, A->D: 1, B->C: 1, C->D: 1, C->A: 1, D->B: 1

- **deepseek-r1_7b**: 24 FCT wrong
- **gemma_7b**: 20 FCT wrong
- **llama3.1_8b**: 27 FCT wrong
- **mistral_latest**: 36 FCT wrong
- **qwen2.5_7b**: 9 FCT wrong

### Overlap: FCT questions wrong by N models

- **All models** (7): 
  FCT_002, FCT_033, FCT_039, FCT_054, FCT_064, FCT_074, FCT_093
- **wrong_by_4** (4): FCT_011, FCT_038, FCT_048, FCT_050
- **wrong_by_3** (5): FCT_013, FCT_014, FCT_025, FCT_030, FCT_079
- **wrong_by_2** (15): FCT_008, FCT_015, FCT_019, FCT_021, FCT_023, FCT_037, FCT_043, FCT_044, FCT_049, FCT_055, FCT_061, FCT_085, FCT_089, FCT_095, FCT_100
- **wrong_by_1** (20): FCT_001, FCT_003, FCT_010, FCT_012, FCT_032, FCT_034, FCT_041, FCT_045, FCT_051, FCT_052, FCT_053, FCT_057, FCT_058, FCT_060, FCT_068 ...

### Hardest FCT topics (by number of models that got them wrong)

- **Hypoglycemia management** (5 models): FCT_064
- **Insulin pump management** (5 models): FCT_014, FCT_038, FCT_079, FCT_093
- **Blood glucose monitoring** (5 models): FCT_002, FCT_080
- **Diabetes with heart failure; SGLT2i, drug interactions, volume status** (5 models): FCT_025, FCT_039, FCT_041, FCT_044
- **Diabetic Retinopathy & Kidney Disease** (5 models): FCT_033
- **pathophysiology** (5 models): FCT_054
- **Diabetic Neuropathy & Foot Care** (5 models): FCT_074
- **Diabetes and cardiovascular risk** (4 models): FCT_011, FCT_083, FCT_100
- **Diabetes and chronic kidney disease (CKD); medication adjustment, monitoring** (4 models): FCT_048
- **Diabetes complications prevention** (4 models): FCT_050, FCT_085, FCT_095
- **medical documentation** (3 models): FCT_013
- **emergency medicine** (3 models): FCT_030
- **misconceptions** (2 models): FCT_015
- **clinical trials** (2 models): FCT_021
- **preventive care** (2 models): FCT_037

## FCT Summary

- Best on FCT: **qwen2.5_7b**
- Worst on FCT: **mistral_latest**
- FCT questions wrong by all models: 7
- FCT questions wrong by only 1 model: 20

## FCT Unexpected Results

- **Consensus wrong** (all models wrong, 7): FCT_002, FCT_033, FCT_039, FCT_054, FCT_064, FCT_074, FCT_093
- **Best model failures** (top model wrong, others correct, 2): FCT_011, FCT_030
- **Worst model succeeds** (worst model correct, others wrong, 15): FCT_010, FCT_012, FCT_021, FCT_032, FCT_034, FCT_037, FCT_041, FCT_043, FCT_051, FCT_052, FCT_053, FCT_057, FCT_070, FCT_075, FCT_089
