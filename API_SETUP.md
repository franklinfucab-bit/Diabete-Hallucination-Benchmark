# API Configuration Setup

## DeepSeek API Key Configuration

Your DeepSeek API key has been configured in `config.py` for automatic use by all scripts.

### Current Setup

- **Location**: `config.py`
- **Variable**: `DEEPSEEK_API_KEY`
- **Status**: ✓ Configured

### Usage

Scripts will automatically use the API key from `config.py`. No need to:
- Set environment variables
- Pass `--api-key` argument
- Re-enter the key each time

### Priority Order

If multiple API keys are available, scripts use this priority:
1. CLI argument (`--api-key YOUR_KEY`)
2. `config.py` (`DEEPSEEK_API_KEY`)
3. Environment variable (`DEEPSEEK_API_KEY`)

### Security Note

⚠️ **Important**: The `config.py` file contains your API key. 
- Do NOT commit this file to public repositories
- Consider using environment variables for shared/production environments
- Keep backups of your API key in a secure location

### Testing

To verify the configuration works:

```bash
# Test API key loading
python -c "import config; print('API Key loaded:', config.DEEPSEEK_API_KEY[:10] + '...')"

# Run FQT v2 generation (dry run)
python scripts/2026-01-28/Deepseek_generating_FQT_v2.py --dry-run
```

### Alternative: Environment Variable

If you prefer to use environment variables instead:

**PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="sk-c48d90ddbd4d46ad91f527582066e8ea"
```

**CMD:**
```cmd
set DEEPSEEK_API_KEY=sk-c48d90ddbd4d46ad91f527582066e8ea
```

**Linux/Mac:**
```bash
export DEEPSEEK_API_KEY="sk-c48d90ddbd4d46ad91f527582066e8ea"
```

Then remove the `DEEPSEEK_API_KEY` line from `config.py`.
