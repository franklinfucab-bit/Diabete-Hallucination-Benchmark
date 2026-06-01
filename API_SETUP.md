# API Configuration Setup

## DeepSeek API Key Configuration

To use the DeepSeek API, you need to configure your API key using environment variables.

### Setup Instructions

**Option 1: Using .env file (Recommended)**

Create a `.env` file in the project root directory:
```
DEEPSEEK_API_KEY=your-api-key-here
```

Install python-dotenv if not already installed:
```bash
pip install python-dotenv
```

**Option 2: Set as environment variable**

**PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="your-api-key-here"
```

**CMD:**
```cmd
set DEEPSEEK_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

### How Scripts Access the API Key

Scripts will automatically use the API key from:
1. CLI argument (`--api-key YOUR_KEY`)
2. Environment variable (`DEEPSEEK_API_KEY`)
3. `.env` file (if python-dotenv is loaded)

### Security Guidelines

⚠️ **IMPORTANT SECURITY NOTES:**
- **NEVER** commit API keys to version control
- **NEVER** hardcode API keys in source files
- Always use environment variables or `.env` files
- Add `.env` to `.gitignore` (already configured)
- Keep your API key confidential and rotate it if exposed
- Use separate keys for development, testing, and production environments

### Testing Configuration

To verify the API key is loaded correctly:

```bash
# Test environment variable
python -c "import os; print('API Key loaded:', bool(os.getenv('DEEPSEEK_API_KEY')))"

# Run test script
python scripts/2026-01-28/Deepseek_generating_FQT_v2.py --dry-run
```

### If Your API Key Was Exposed

If you believe your API key has been compromised:
1. Regenerate a new API key in your DeepSeek account
2. Update your `.env` file with the new key
3. Delete the old key from DeepSeek console
4. The old key will no longer be valid
