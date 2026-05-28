# 400q Diabetes Benchmark – Model Comparison

**295 questions: 65 NOTA + 100 FQT + 65 FCT + 65 AOTA. 5 models.**

## Accuracy Table

| Model | Overall | NOTA | FQT | FCT | AOTA |
|-------|---------|------|-----|-----|------|
| deepseek-r1_7b | 45.1% | 21.5% | 22.0% | 67.7% | 81.5% |
| gemma_7b | 31.2% | 21.5% | 8.0% | 75.4% | 32.3% |
| llama3.1_8b | 68.4% | 17.2% | 96.0% | 72.3% | 72.3% |
| mistral_latest | 51.9% | 16.9% | 49.0% | 53.8% | 89.2% |
| qwen2.5_7b | 80.0% | 41.5% | 93.0% | 84.6% | 93.8% |

## Model Performance Profiles

- **deepseek-r1_7b**: Best at AOTA (81.5%), worst at NOTA (21.5%). Spread: 60.0% (specialist)
- **gemma_7b**: Best at FCT (75.4%), worst at FQT (8.0%). Spread: 67.4% (specialist)
- **llama3.1_8b**: Best at FQT (96.0%), worst at NOTA (17.2%). Spread: 78.8% (specialist)
- **mistral_latest**: Best at AOTA (89.2%), worst at NOTA (16.9%). Spread: 72.3% (specialist)
- **qwen2.5_7b**: Best at AOTA (93.8%), worst at NOTA (41.5%). Spread: 52.3% (specialist)


## NOTA Ranking (best first)

1. qwen2.5_7b
2. deepseek-r1_7b
3. gemma_7b
4. llama3.1_8b
5. mistral_latest

## NOTA Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 51 NOTA wrong
- **gemma_7b**: 51 NOTA wrong
- **llama3.1_8b**: 53 NOTA wrong
- **mistral_latest**: 54 NOTA wrong
- **qwen2.5_7b**: 38 NOTA wrong

### Overlap: questions wrong by N models

- **All models** (27): NOTA_014, NOTA_018, NOTA_019, NOTA_023, NOTA_025, NOTA_026, NOTA_027, NOTA_030, NOTA_036, NOTA_038, NOTA_039, NOTA_040, NOTA_041, NOTA_045, NOTA_054...
- **4 models** (18): NOTA_001, NOTA_002, NOTA_011, NOTA_016, NOTA_033, NOTA_035, NOTA_042, NOTA_044, NOTA_048, NOTA_049, NOTA_050, NOTA_060, NOTA_081, NOTA_085, NOTA_088...
- **3 models** (6): NOTA_031, NOTA_052, NOTA_070, NOTA_089, NOTA_094, NOTA_096
- **2 models** (9): NOTA_007, NOTA_010, NOTA_028, NOTA_046, NOTA_047, NOTA_061, NOTA_073, NOTA_082, NOTA_100
- **1 models** (4): NOTA_029, NOTA_051, NOTA_068, NOTA_075

### Hardest topics (all models wrong)

- **GLP-1 receptor agonists** (1): NOTA_091
- **acute decompensated heart failure** (1): NOTA_018
- **hypoglycemia** (1): NOTA_064
- **antepartum_care** (1): NOTA_057
- **type 2 diabetes management** (1): NOTA_045
- **nephrology** (1): NOTA_076
- **renal protection** (1): NOTA_039
- **SGLT2 inhibitors** (1): NOTA_025
- **guideline-based management** (1): NOTA_023
- **neuropathy_footcare** (1): NOTA_074


## FQT Ranking (best first)

1. llama3.1_8b
2. qwen2.5_7b
3. mistral_latest
4. deepseek-r1_7b
5. gemma_7b

## FQT Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 78 FQT wrong
- **gemma_7b**: 92 FQT wrong
- **llama3.1_8b**: 4 FQT wrong
- **mistral_latest**: 51 FQT wrong
- **qwen2.5_7b**: 7 FQT wrong

### Overlap: questions wrong by N models

- **All models** (1): FQT_034
- **4 models** (7): FQT_006, FQT_018, FQT_026, FQT_049, FQT_052, FQT_074, FQT_082
- **3 models** (40): FQT_001, FQT_004, FQT_005, FQT_007, FQT_010, FQT_012, FQT_013, FQT_014, FQT_019, FQT_023, FQT_024, FQT_030, FQT_031, FQT_032, FQT_033...
- **2 models** (31): FQT_002, FQT_003, FQT_008, FQT_009, FQT_016, FQT_021, FQT_025, FQT_028, FQT_029, FQT_036, FQT_043, FQT_057, FQT_061, FQT_062, FQT_064...
- **1 models** (17): FQT_011, FQT_015, FQT_017, FQT_020, FQT_022, FQT_048, FQT_051, FQT_056, FQT_059, FQT_065, FQT_071, FQT_073, FQT_080, FQT_084, FQT_092...

### Hardest topics (all models wrong)

- **Other** (1): FQT_034


## FCT Ranking (best first)

1. qwen2.5_7b
2. gemma_7b
3. llama3.1_8b
4. deepseek-r1_7b
5. mistral_latest

## FCT Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 21 FCT wrong
- **gemma_7b**: 16 FCT wrong
- **llama3.1_8b**: 18 FCT wrong
- **mistral_latest**: 30 FCT wrong
- **qwen2.5_7b**: 10 FCT wrong

### Overlap: questions wrong by N models

- **All models** (8): FCT_002, FCT_033, FCT_038, FCT_039, FCT_054, FCT_064, FCT_074, FCT_093
- **4 models** (2): FCT_011, FCT_048
- **3 models** (6): FCT_014, FCT_019, FCT_030, FCT_050, FCT_085, FCT_100
- **2 models** (9): FCT_023, FCT_025, FCT_044, FCT_049, FCT_061, FCT_079, FCT_083, FCT_089, FCT_095
- **1 models** (11): FCT_010, FCT_027, FCT_031, FCT_045, FCT_051, FCT_052, FCT_068, FCT_070, FCT_080, FCT_088, FCT_091

### Hardest topics (all models wrong)

- **continuous glucose monitoring** (1): FCT_093
- **retinopathy_kidney** (1): FCT_033
- **SMBG** (1): FCT_002
- **basal rate adjustment** (1): FCT_038
- **hypoglycemia** (1): FCT_064
- **neuropathy_footcare** (1): FCT_074
- **renal protection** (1): FCT_039
- **pathophysiology** (1): FCT_054


## AOTA Ranking (best first)

1. qwen2.5_7b
2. mistral_latest
3. deepseek-r1_7b
4. llama3.1_8b
5. gemma_7b

## AOTA Deep Dive

### Wrong count by model

- **deepseek-r1_7b**: 12 AOTA wrong
- **gemma_7b**: 44 AOTA wrong
- **llama3.1_8b**: 18 AOTA wrong
- **mistral_latest**: 7 AOTA wrong
- **qwen2.5_7b**: 4 AOTA wrong

### Overlap: questions wrong by N models

- **All models** (0): 
- **4 models** (2): AOTA_072, AOTA_088
- **3 models** (4): AOTA_010, AOTA_067, AOTA_080, AOTA_084
- **2 models** (19): AOTA_002, AOTA_016, AOTA_028, AOTA_030, AOTA_035, AOTA_036, AOTA_038, AOTA_042, AOTA_048, AOTA_061, AOTA_073, AOTA_075, AOTA_079, AOTA_081, AOTA_087...
- **1 models** (27): AOTA_001, AOTA_007, AOTA_011, AOTA_018, AOTA_019, AOTA_025, AOTA_026, AOTA_029, AOTA_033, AOTA_040, AOTA_041, AOTA_044, AOTA_045, AOTA_047, AOTA_049...

### Hardest topics (all models wrong)

