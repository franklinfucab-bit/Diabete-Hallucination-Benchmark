# 300q Horizontal Comparison 修正 (FCT Focus)

**NOTA = 100q NOTA (FCT-derived); FQT/FCT = 300q. 5 models.**

## Accuracy Table

| Model | Overall | NOTA | FQT | FCT |
|-------|---------|------|-----|-----|
| deepseek-r1_7b | 42.7% | 30.0% | 22.0% | 76.0% |
| gemma_7b | 38.7% | 27.0% | 9.0% | 80.0% |
| llama3.1_8b | 63.7% | 21.2% | 97.0% | 73.0% |
| mistral_latest | 46.0% | 26.0% | 48.0% | 64.0% |
| qwen2.5_7b | 80.7% | 57.0% | 94.0% | 91.0% |

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
