# 300q Horizontal Comparison (Overall: NOTA, FQT, FCT)

## Accuracy Table

| Model | Overall | NOTA | FQT | FCT |
|-------|---------|------|-----|-----|
| deepseek-r1_7b | 41.8% | 27.3% | 22.0% | 76.0% |
| gemma_7b | 33.3% | 11.0% | 9.0% | 80.0% |
| llama3.1_8b | 61.3% | 14.0% | 97.0% | 73.0% |
| mistral_latest | 40.3% | 9.0% | 48.0% | 64.0% |
| qwen2.5_7b | 70.7% | 27.0% | 94.0% | 91.0% |
| deepseek_chat | 95.7% | 95.0% | 99.0% | 93.0% |

## NOTA Ranking (best first)

1. deepseek_chat
2. deepseek-r1_7b
3. qwen2.5_7b
4. llama3.1_8b
5. gemma_7b
6. mistral_latest

## NOTA Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 72 NOTA wrong
- **gemma_7b**: 89 NOTA wrong
- **llama3.1_8b**: 86 NOTA wrong
- **mistral_latest**: 91 NOTA wrong
- **qwen2.5_7b**: 73 NOTA wrong
- **deepseek_chat**: 5 NOTA wrong

### Overlap: NOTA questions wrong by N models

- **All models** (5): 
  NOTA_003, NOTA_021, NOTA_025, NOTA_028, NOTA_070
- **wrong_by_5** (39): NOTA_004, NOTA_005, NOTA_007, NOTA_008, NOTA_010, NOTA_016, NOTA_017, NOTA_019, NOTA_026, NOTA_029, NOTA_033, NOTA_037, NOTA_040, NOTA_045, NOTA_047 ...
- **wrong_by_4** (33): NOTA_001, NOTA_006, NOTA_011, NOTA_012, NOTA_013, NOTA_015, NOTA_018, NOTA_020, NOTA_022, NOTA_023, NOTA_030, NOTA_031, NOTA_032, NOTA_036, NOTA_038 ...
- **wrong_by_3** (15): NOTA_002, NOTA_014, NOTA_024, NOTA_027, NOTA_035, NOTA_043, NOTA_048, NOTA_062, NOTA_079, NOTA_081, NOTA_085, NOTA_087, NOTA_096, NOTA_098, NOTA_099
- **wrong_by_2** (6): NOTA_009, NOTA_041, NOTA_053, NOTA_055, NOTA_088, NOTA_089
- **wrong_by_1** (2): NOTA_034, NOTA_049

### Hardest NOTA topics (by number of models that got them wrong)

- **monogenic diabetes** (6 models): NOTA_003
- **type 1 diabetes** (6 models): NOTA_021
- **Wagner classification** (6 models): NOTA_025
- **type 2 diabetes** (6 models): NOTA_028
- **glycemic targets** (5 models): NOTA_004
- **MODY maturity-onset diabetes of the young** (5 models): NOTA_005
- **phlebotomy** (5 models): NOTA_007
- **Autonomic neuropathy orthostatic hypotension** (5 models): NOTA_008
- **SGLT2 inhibitors** (5 models): NOTA_010
- **hypoglycemia** (5 models): NOTA_016
- **pharmacology** (5 models): NOTA_017
- **emergency_medicine** (5 models): NOTA_019
- **GLP-1 receptor agonists and gastroparesis contraindication** (5 models): NOTA_026
- **SGLT2 inhibitors in CKD with proteinuria** (5 models): NOTA_029
- **LADA latent autoimmune diabetes misdiagnosed as type 2** (5 models): NOTA_033

## NOTA Summary

- Best on NOTA: **deepseek_chat**
- Worst on NOTA: **mistral_latest**
- NOTA questions wrong by all models: 5
- NOTA questions wrong by only 1 model: 2

## NOTA Unexpected Results

- **Consensus wrong** (all models wrong, 5): NOTA_003, NOTA_021, NOTA_025, NOTA_028, NOTA_070
- **Best model failures** (top model wrong, others correct, 0): (none)
- **Worst model succeeds** (worst model correct, others wrong, 9): NOTA_009, NOTA_014, NOTA_034, NOTA_041, NOTA_049, NOTA_053, NOTA_055, NOTA_081, NOTA_085


## FQT Ranking (best first)

1. deepseek_chat
2. llama3.1_8b
3. qwen2.5_7b
4. mistral_latest
5. deepseek-r1_7b
6. gemma_7b

## FQT Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 78 FQT wrong
- **gemma_7b**: 91 FQT wrong
- **llama3.1_8b**: 3 FQT wrong
- **mistral_latest**: 52 FQT wrong
- **qwen2.5_7b**: 6 FQT wrong
- **deepseek_chat**: 1 FQT wrong

### Overlap: FQT questions wrong by N models

- **All models** (0): 
- **wrong_by_5** (2): FQT_034, FQT_082
- **wrong_by_4** (4): FQT_006, FQT_026, FQT_049, FQT_074
- **wrong_by_3** (43): FQT_001, FQT_004, FQT_005, FQT_007, FQT_010, FQT_012, FQT_013, FQT_014, FQT_018, FQT_019, FQT_023, FQT_024, FQT_030, FQT_031, FQT_032 ...
- **wrong_by_2** (29): FQT_002, FQT_003, FQT_008, FQT_009, FQT_016, FQT_021, FQT_025, FQT_028, FQT_029, FQT_036, FQT_043, FQT_057, FQT_061, FQT_062, FQT_064 ...
- **wrong_by_1** (18): FQT_011, FQT_015, FQT_017, FQT_020, FQT_022, FQT_048, FQT_051, FQT_056, FQT_059, FQT_065, FQT_071, FQT_073, FQT_080, FQT_084, FQT_092 ...

### Hardest FQT topics (by number of models that got them wrong)

- **SpecialPops** (5 models): FQT_002, FQT_008, FQT_009, FQT_014, FQT_018 ...
- **Retinopathy_Kidney** (5 models): FQT_006, FQT_007, FQT_020, FQT_023, FQT_025 ...
- **Neuropathy_FootCare** (4 models): FQT_001, FQT_003, FQT_004, FQT_011, FQT_013 ...
- **Acute_Hospital** (3 models): FQT_005, FQT_010, FQT_012, FQT_019, FQT_021 ...
- **Other** (1 models): FQT_082

## FQT Summary

- Best on FQT: **deepseek_chat**
- Worst on FQT: **gemma_7b**
- FQT questions wrong by all models: 0
- FQT questions wrong by only 1 model: 18

## FQT Unexpected Results

- **Consensus wrong** (all models wrong, 0): (none)
- **Best model failures** (top model wrong, others correct, 1): FQT_082
- **Worst model succeeds** (worst model correct, others wrong, 5): FQT_022, FQT_067, FQT_071, FQT_092, FQT_094


## FCT Ranking (best first)

1. deepseek_chat
2. qwen2.5_7b
3. gemma_7b
4. deepseek-r1_7b
5. llama3.1_8b
6. mistral_latest

## FCT Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 24 FCT wrong
- **gemma_7b**: 20 FCT wrong
- **llama3.1_8b**: 27 FCT wrong
- **mistral_latest**: 36 FCT wrong
- **qwen2.5_7b**: 9 FCT wrong
- **deepseek_chat**: 7 FCT wrong

### Overlap: FCT questions wrong by N models

- **All models** (2): 
  FCT_064, FCT_074
- **wrong_by_5** (6): FCT_002, FCT_033, FCT_038, FCT_039, FCT_054, FCT_093
- **wrong_by_4** (3): FCT_011, FCT_048, FCT_050
- **wrong_by_3** (6): FCT_013, FCT_014, FCT_025, FCT_030, FCT_061, FCT_079
- **wrong_by_2** (14): FCT_008, FCT_015, FCT_019, FCT_021, FCT_023, FCT_037, FCT_043, FCT_044, FCT_049, FCT_055, FCT_085, FCT_089, FCT_095, FCT_100
- **wrong_by_1** (23): FCT_001, FCT_003, FCT_010, FCT_012, FCT_032, FCT_034, FCT_041, FCT_045, FCT_051, FCT_052, FCT_053, FCT_057, FCT_058, FCT_060, FCT_066 ...

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
- **insulin storage** (3 models): FCT_061
- **misconceptions** (2 models): FCT_015
- **clinical trials** (2 models): FCT_021

## FCT Summary

- Best on FCT: **deepseek_chat**
- Worst on FCT: **mistral_latest**
- FCT questions wrong by all models: 2
- FCT questions wrong by only 1 model: 23

## FCT Unexpected Results

- **Consensus wrong** (all models wrong, 2): FCT_064, FCT_074
- **Best model failures** (top model wrong, others correct, 5): FCT_038, FCT_061, FCT_066, FCT_071, FCT_088
- **Worst model succeeds** (worst model correct, others wrong, 15): FCT_010, FCT_012, FCT_021, FCT_032, FCT_034, FCT_037, FCT_041, FCT_043, FCT_051, FCT_052, FCT_053, FCT_057, FCT_070, FCT_075, FCT_089
