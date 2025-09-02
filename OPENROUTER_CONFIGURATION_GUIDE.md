# RefactAI OpenRouter + AST Configuration Guide

## 🎯 Overview

RefactAI has been successfully configured to **force OpenRouter API usage with AST validation**. This ensures reliable, cloud-based code refactoring with enhanced validation for maximum code quality.

## 🔧 Key Features Implemented

### 1. **Interactive CLI (`cli.py`)**
- **Forced OpenRouter Mode**: Always uses `hybrid_openrouter` processing mode
- **Default Model**: `anthropic/claude-3.5-sonnet` (OpenRouter API)
- **AST Validation**: Automatically enabled for Python files
- **Rich Terminal UI**: Beautiful interface with progress bars, tables, and panels
- **Configuration Lock**: Removes local LLM options, focuses on OpenRouter models only

#### Available Models:
- `anthropic/claude-3.5-sonnet` (Default)
- `openai/gpt-4-turbo`
- `openai/gpt-4o`
- `google/gemini-pro-1.5`
- `meta-llama/llama-3.1-405b-instruct`

### 2. **Interactive Git Hook (`git-hook-interactive.py`)**
- **OpenRouter API Only**: Forces hybrid mode with OpenRouter (no local LLM)
- **Full Repository Refactoring**: Option to refactor entire codebase, not just changed files
- **AST Validation**: Built-in Python syntax validation
- **Auto-Push Feature**: Automatically commits and pushes refactored code
- **Interactive Scope Selection**: Choose between "changed files" or "full repository"

### 3. **Batch CLI (`cli_batch.py`)**
- **Non-Interactive Mode**: For CI/CD and automation
- **Same OpenRouter Backend**: Consistent API usage across all modes
- **Full Argument Support**: Compatible with original command-line interface

## 🚀 Usage Examples

### Interactive CLI
```bash
# Start interactive refactoring interface
python cli.py

# Features available:
# - Refactor single files or directories
# - Configure OpenRouter models
# - Test API connection
# - View refactoring statistics
# - Built-in help system
```

### Git Hook (Interactive)
```bash
# Setup Git hook for automatic refactoring
cp git-hook-interactive.py .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Or use enhanced bash script
cp pre-push-enhanced .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# When you push, you'll get options:
# 1. Refactor only changed files
# 2. Refactor entire repository
# 3. Auto-push after successful refactoring
```

### Batch Processing
```bash
# Non-interactive batch processing
python cli_batch.py --file example.py --output overwrite
python cli_batch.py --directory src/ --language python --backup
```

## ⚙️ Configuration Details

### Forced Settings
- **Processing Mode**: `hybrid_openrouter` (locked)
- **API Service**: OpenRouter API (required)
- **AST Validation**: Enabled for Python files
- **Local LLM**: Disabled (cloud-only processing)

### Environment Variables Required
```bash
# OpenRouter API Key (required)
export OPENROUTER_API_KEY="your-api-key-here"

# Optional: Custom API URL
export OPENROUTER_API_URL="https://openrouter.ai/api/v1/chat/completions"

# Optional: Default model
export DEFAULT_MODEL="anthropic/claude-3.5-sonnet"
```

## 🔄 Git Workflow Integration

### Automatic Repository Refactoring
1. **Git Hook Activation**: Pre-push hook intercepts push commands
2. **Scope Selection**: Choose between changed files or full repository
3. **OpenRouter Processing**: All files processed using cloud API + AST validation
4. **Interactive Confirmation**: Preview changes before applying
5. **Auto-Push**: Automatically commit and push refactored code

### Workflow Example
```bash
# Make your changes
git add .
git commit -m "Initial changes"

# Push triggers interactive refactoring
git push origin main

# Interactive prompts:
# 1. "Refactoring scope: [changed/full-repo]"
# 2. "Preview changes only (dry run)?"
# 3. "Proceed with refactoring X files?"
# 4. "Auto-push changes to remote repository?"
```

## 🧪 Testing & Validation

### Configuration Test
```bash
# Verify OpenRouter + AST configuration
python test_openrouter_config.py

# Expected output:
# ✅ CLI configuration test passed!
# ✅ Git hook configuration test passed!
# ✅ API dependencies test passed!
# 🎉 All tests passed!
```

### API Connection Test
```bash
# Test OpenRouter API from CLI
python cli.py
# Select: "🧪 Test LLM connection"
```

## 📊 Benefits of OpenRouter + AST Mode

### 1. **Reliability**
- Cloud-based processing (no local dependencies)
- Multiple model options for different needs
- Consistent results across environments

### 2. **Quality Assurance**
- AST validation prevents syntax errors
- Enhanced error detection and reporting
- Code structure preservation

### 3. **Scalability**
- Full repository refactoring capability
- Batch processing for large codebases
- Automated Git integration

### 4. **User Experience**
- Interactive menus and progress bars
- Clear configuration display
- Helpful error messages and guidance

## 🔒 Security & Best Practices

### API Key Management
- Store API keys in environment variables
- Never commit API keys to version control
- Use `.env` files for local development

### Git Integration
- Automatic backup creation before refactoring
- Dry run mode for preview without changes
- User confirmation for all operations

### Error Handling
- Graceful fallback for API failures
- Clear error messages with suggestions
- Optional continuation on partial failures

## 🆘 Troubleshooting

### Common Issues

1. **Missing API Key**
   ```bash
   # Set OpenRouter API key
   export OPENROUTER_API_KEY="your-key"
   ```

2. **Git Hook Not Working**
   ```bash
   # Ensure executable permissions
   chmod +x .git/hooks/pre-push
   ```

3. **Import Errors**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

### Support Commands
```bash
# Check configuration
python test_openrouter_config.py

# Test CLI directly
python cli.py

# Manual batch processing
python cli_batch.py --help
```

## 🎉 Success!

RefactAI is now configured for optimal performance with:
- ✅ OpenRouter API integration
- ✅ AST validation enabled
- ✅ Interactive terminal UI
- ✅ Full repository refactoring
- ✅ Automated Git workflow
- ✅ Comprehensive error handling

Your code refactoring workflow is now enterprise-ready with cloud-based AI processing and intelligent validation!
