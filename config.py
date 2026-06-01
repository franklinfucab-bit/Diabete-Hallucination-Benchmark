"""
Configuration file for the Diabetes Hallucination Benchmark
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
RESULTS_DIR = BASE_DIR / "results"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Dataset configuration
EXCEL_FILE = DATA_DIR / "diabetes_QA_dataset.xlsx"  # User should place their Excel file here
BENCHMARK_OUTPUT = OUTPUT_DIR / "diabetes_hallucination_benchmark.jsonl"

# Hallucination injection strategies
HALLUCINATION_STRATEGIES = [
    "contradiction",      # Contradict correct information
    "fabrication",        # Add false information
    "omission",          # Omit critical information
    "exaggeration",      # Exaggerate claims
    "misattribution"     # Attribute information incorrectly
]

# Evaluation metrics
METRICS = [
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "hallucination_detection_rate"
]

# Model configurations (for testing)
SUPPORTED_MODELS = [
    "openai",
    "anthropic",
    "local"  # For local models
]

# API Keys - Load from environment variables
# IMPORTANT: Do not commit API keys to version control
# Set environment variables in your .env file or system configuration:
#   export DEEPSEEK_API_KEY="your-api-key-here"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
