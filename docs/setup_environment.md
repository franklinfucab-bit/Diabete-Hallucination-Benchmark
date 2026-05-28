# Environment Setup Guide

## About the Global Installation Warning

If you see warnings about global Python installation, it's recommended to use a virtual environment or conda environment to avoid conflicts.

## Option 1: Using Conda (Recommended if you have Anaconda/Miniconda)

Since you're already in a conda base environment, you can create a dedicated environment:

```bash
# Create a new conda environment
conda create -n diabetes_benchmark python=3.11

# Activate the environment
conda activate diabetes_benchmark

# Install dependencies
pip install -r requirements.txt
```

## Option 2: Using Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## Option 3: Continue with Current Setup

If you prefer to continue with your current conda base environment, the packages are already installed and you can proceed directly to using the benchmark.

## Verify Installation

Run this to verify everything is set up:
```bash
python inspect_excel.py
```

You should see your dataset information printed successfully.
