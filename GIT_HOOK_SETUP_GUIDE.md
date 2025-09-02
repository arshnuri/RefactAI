# RefactAI Enhanced Git Hook Setup Guide

## 🎯 Overview

RefactAI now supports **two modes** for Git pre-push hooks:

1. **🎨 Interactive Mode**: Beautiful, menu-driven interface with progress bars and real-time feedback
2. **📝 Batch Mode**: Non-interactive mode for automation and CI/CD pipelines

## 🚀 Quick Setup

### Step 1: Install Dependencies

For **Interactive Mode** (recommended):
```bash
pip install rich inquirer colorama
```

For **Batch Mode** only:
```bash
# No additional dependencies needed beyond the base RefactAI requirements
```

### Step 2: Install the Git Hook

```bash
# Copy the enhanced pre-push hook
cp pre-push-enhanced .git/hooks/pre-push

# Make it executable (Unix/macOS/WSL)
chmod +x .git/hooks/pre-push

# Windows (if using Git Bash)
# The file should already be executable, but you can verify with:
# ls -la .git/hooks/pre-push
```

### Step 3: Test the Setup

```bash
# Test LLM connection
python cli_batch.py --test

# Or with the interactive CLI
python cli.py
# Then select "🧪 Test LLM connection"
```

## 🎨 Interactive Mode Features

When you push code, you'll see a beautiful interface like this:

```
╭─────────────────────────────────────────────────────────────────╮
│                     RefactAI Git Hook                          │
│              Pre-Push Code Refactoring                         │
╰─────────────────────────────────────────────────────────────────╯

🧪 Testing LLM connection...
✅ LLM connection successful

🔍 Found 3 code files in staged changes

┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ File                  ┃ Language   ┃ Size      ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ src/main.py          │ Python     │ 2.3KB     │ Ready     │
│ utils/helper.js      │ JavaScript │ 1.8KB     │ Ready     │
│ models/user.py       │ Python     │ 4.1KB     │ Ready     │
└───────────────────────┴────────────┴───────────┴───────────┘

Configuration Options:
? Use hybrid mode (local + API fallback)? Yes
? Preview changes only (dry run mode)? No
? Proceed with refactoring 3 files? Yes

⠋ Refactoring files... ████████████████████ 100% Processing helper.js...
✅ Refactored: src/main.py
✅ Refactored: utils/helper.js  
✅ Refactored: models/user.py

─────────────────────── Summary ───────────────────────
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric               ┃ Count                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✅ Processed:        │ 3                         │
│ ⏭️  Skipped:          │ 0                         │
│ ❌ Failed:            │ 0                         │
└──────────────────────┴───────────────────────────┘

📦 Refactored files have been staged
🎉 Code refactoring complete! Proceeding with push...
```

### Interactive Mode Options

- **Model Selection**: Choose from different LLM models on the fly
- **Processing Mode**: Switch between hybrid, local, or API-only modes  
- **Dry Run**: Preview changes without modifying files
- **File Preview**: See exactly which files will be processed
- **Progress Tracking**: Real-time progress bars and status updates
- **Error Handling**: Detailed error messages with recovery options

## 📝 Batch Mode Features

For users who prefer automation or are in CI/CD environments:

```
[RefactAI] 🎨 Starting interactive mode...
[RefactAI] ⚠️  Interactive mode not available (missing rich/inquirer packages)
[RefactAI]    Install with: pip install rich inquirer colorama
[RefactAI] 📝 Using basic refactoring mode...
[RefactAI] Found 3 code file(s) to refactor:
  - src/main.py
  - utils/helper.js
  - models/user.py

Refactor these files before push? [Y/n]: y
[RefactAI] Proceeding with refactoring...
[RefactAI] 🔄 Refactoring src/main.py (Python)...
[RefactAI] ✅ Refactored and staged: src/main.py
[RefactAI] 🔄 Refactoring utils/helper.js (JavaScript)...
[RefactAI] ✅ Refactored and staged: utils/helper.js
[RefactAI] 🔄 Refactoring models/user.py (Python)...
[RefactAI] ✅ Refactored and staged: models/user.py

[RefactAI] 📊 Refactoring Summary:
[RefactAI]   ✅ Successfully refactored: 3 files
[RefactAI] 🎉 Code refactoring complete! Proceeding with push...
```

## ⚙️ Configuration Options

### Environment Variables

You can configure the Git hook behavior with environment variables:

```bash
# Set preferred model
export DEFAULT_MODEL="qwen2.5-coder:7b"

# Enable local LLM preference
export PREFER_LOCAL_LLM="true"

# Set API keys for fallback
export OPENROUTER_API_KEY="your-api-key-here"
```

### Git Configuration

You can also use Git configuration:

```bash
# Set default model for RefactAI
git config refactai.model "qwen2.5-coder:7b"

# Enable/disable the hook
git config refactai.enabled true

# Set processing mode
git config refactai.mode "hybrid"  # hybrid, local, or api
```

## 🛠️ Usage Examples

### Skip Refactoring for a Single Push

```bash
git push --no-refactor
```

### Force Interactive Mode

```bash
# Ensure you have the dependencies
pip install rich inquirer colorama

# Push normally - it will automatically use interactive mode
git push origin main
```

### Use Batch Mode Only

```bash
# Remove rich and inquirer to force batch mode
pip uninstall rich inquirer

# Or set environment variable
export REFACTAI_FORCE_BATCH_MODE="true"
git push origin main
```

### Test Different Models

Interactive mode:
```bash
python cli.py
# Select "⚙️  Configure settings" 
# Choose your preferred model
```

Batch mode:
```bash
python cli_batch.py --test --model qwen2.5-coder:1.5b
```

## 🔧 Advanced Configuration

### Custom Hook Location

If you want to use a different location for the hook files:

```bash
# Edit the enhanced pre-push hook
nano .git/hooks/pre-push

# Modify these lines:
REFACTAI_DIR="/path/to/your/refactai"
INTERACTIVE_HOOK="$REFACTAI_DIR/git-hook-interactive.py"
CLI_SCRIPT="$REFACTAI_DIR/cli_batch.py"
```

### Performance Tuning

For faster processing in large repositories:

```bash
# Use faster models
export DEFAULT_MODEL="qwen2.5-coder:1.5b"

# Use local-only mode to avoid API delays
export PREFER_LOCAL_LLM="true"

# Enable quiet mode for batch processing
export REFACTAI_QUIET_MODE="true"
```

### CI/CD Integration

For automated environments:

```bash
# Disable interactive prompts
export REFACTAI_AUTO_CONFIRM="true"

# Use batch mode with minimal output
export REFACTAI_FORCE_BATCH_MODE="true"
export REFACTAI_QUIET_MODE="true"

# Set timeout for LLM operations
export REFACTAI_TIMEOUT="300"  # 5 minutes
```

## 🚨 Troubleshooting

### Interactive Mode Not Working

**Problem**: Hook falls back to batch mode even with dependencies installed.

**Solution**:
```bash
# Verify dependencies
python -c "import rich, inquirer; print('Dependencies OK')"

# Check hook file permissions
ls -la .git/hooks/pre-push

# Reinstall dependencies
pip install --force-reinstall rich inquirer colorama
```

### LLM Connection Issues

**Problem**: "Local LLM not available" error.

**Solution**:
```bash
# Test LLM connection
python cli_batch.py --test

# Check if Ollama is running
ollama list

# Check model availability
ollama pull deepseek-coder:6.7b
```

### Large File Warnings

**Problem**: Files are being skipped due to size.

**Solution**:
```bash
# Files >100KB are automatically skipped for performance
# You can modify this limit in both hook files by changing:
# if len(original_code) > 100000:

# Or use --dry-run to preview without modifying
git commit -m "test"
REFACTAI_DRY_RUN=true git push origin main
```

### Permission Errors

**Problem**: Hook doesn't execute.

**Solution**:
```bash
# Make hook executable
chmod +x .git/hooks/pre-push

# Check hook permissions
ls -la .git/hooks/pre-push

# On Windows, ensure Git Bash is being used
```

## 🎯 Best Practices

### 1. **Start with Interactive Mode**
- Install `rich` and `inquirer` for the best experience
- Use dry run mode first to preview changes
- Configure your preferred model and settings

### 2. **Team Setup**
- Add dependencies to `requirements.txt`:
  ```
  rich>=13.0.0
  inquirer>=3.1.0
  colorama>=0.4.4
  ```
- Share hook setup instructions with your team
- Consider using the same model across the team

### 3. **Performance Optimization**
- Use faster models (`qwen2.5-coder:1.5b`) for quick iterations
- Enable local-only mode for offline work
- Set up model caching with Ollama

### 4. **Safety First**
- Always test hooks in a separate branch first
- Use dry run mode for important releases
- Keep backups enabled when working outside Git hooks

### 5. **CI/CD Integration**
- Use batch mode in automated environments
- Set appropriate timeouts for LLM operations
- Consider model availability in your CI environment

## 🔄 Migration from Old Hook

If you're upgrading from the old bash-only hook:

1. **Backup your current hook**:
   ```bash
   cp .git/hooks/pre-push .git/hooks/pre-push.backup
   ```

2. **Install the new enhanced hook**:
   ```bash
   cp pre-push-enhanced .git/hooks/pre-push
   chmod +x .git/hooks/pre-push
   ```

3. **Install dependencies for interactive mode**:
   ```bash
   pip install rich inquirer colorama
   ```

4. **Test the new setup**:
   ```bash
   git add .
   git commit -m "test new hook"
   git push origin main
   ```

The new hook will automatically detect if you have the interactive dependencies and provide the best available experience!

## 🆚 Comparison: Interactive vs Batch Mode

| Feature | Interactive Mode | Batch Mode |
|---------|-----------------|------------|
| **UI** | Rich, colorful interface | Simple text output |
| **Configuration** | On-the-fly settings | Command-line arguments |
| **Progress** | Real-time progress bars | Text status updates |
| **File Preview** | Detailed table with metadata | Simple file list |
| **Error Handling** | Interactive recovery options | Continue/abort prompts |
| **Dependencies** | `rich`, `inquirer`, `colorama` | Base RefactAI only |
| **Automation** | Interactive prompts | Scriptable |
| **Performance** | Slightly slower (UI rendering) | Faster (minimal output) |
| **Use Case** | Development workflow | CI/CD, automation |

Choose the mode that best fits your workflow! 🚀
