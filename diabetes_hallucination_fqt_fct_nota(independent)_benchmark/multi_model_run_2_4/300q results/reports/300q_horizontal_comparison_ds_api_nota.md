# 300q Horizontal Comparison (NOTA Focus)

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
