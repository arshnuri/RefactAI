# RefactAI Qwen Coder Setup Guide

## Quick Setup for Qwen Coder Only

This guide will help you set up RefactAI with **Qwen Coder** model specifically.

### Prerequisites

1. **Install Ollama** (if not already installed):
   - Windows: Download from [https://ollama.ai/download](https://ollama.ai/download)
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

### Automated Setup

**Run the Qwen Coder setup script:**
```bash
python setup_qwen_coder.py
```

This script will:
- ✅ Install Python dependencies
- ✅ Check Ollama installation
- ✅ Pull Qwen Coder model (tries multiple variants)
- ✅ Set up Git pre-push hook
- ✅ Create .env configuration
- ✅ Test the model

### Manual Setup (Alternative)

If you prefer manual setup:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Pull Qwen Coder model:**
   ```bash
   ollama pull qwen2.5-coder:7b
   ```
   
   Or try smaller variants if you have limited resources:
   ```bash
   ollama pull qwen2.5-coder:1.5b  # Smaller, faster
   ollama pull qwen2.5-coder:3b    # Medium size
   ```

3. **Create .env file:**
   ```bash
   echo "PREFER_LOCAL_LLM=true" > .env
   echo "LOCAL_LLM_MODEL=qwen2.5-coder:7b" >> .env
   ```

4. **Set up Git hook (optional):**
   ```bash
   cp pre-push .git/hooks/pre-push
   chmod +x .git/hooks/pre-push  # On Unix/macOS
   ```

### Usage

#### Web Interface
1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Open browser:** http://127.0.0.1:8000/

3. **Upload ZIP file** with your code and let Qwen Coder refactor it!

#### Command Line Interface
```bash
# Refactor a single file
python cli.py myfile.py

# Refactor with specific model
python cli.py myfile.py --model qwen2.5-coder:1.5b

# Dry run (preview changes)
python cli.py myfile.py --dry-run

# Refactor entire directory
python cli.py /path/to/code/directory
```

#### Git Integration
Once set up, the pre-push hook will automatically refactor your code before pushing:
```bash
git add .
git commit -m "My changes"
git push  # Automatic refactoring happens here!
```

### Available Qwen Coder Models

| Model | Size | Speed | Quality | Recommended For |
|-------|------|-------|---------|----------------|
| `qwen2.5-coder:1.5b` | ~1GB | Fast | Good | Quick refactoring, limited resources |
| `qwen2.5-coder:3b` | ~2GB | Medium | Better | Balanced performance |
| `qwen2.5-coder:7b` | ~4GB | Slower | Best | High-quality refactoring |

### Troubleshooting

**Model not found:**
```bash
# Check available models
ollama list

# Pull specific model
ollama pull qwen2.5-coder:7b
```

**Connection issues:**
```bash
# Test Ollama
ollama --version

# Test model
ollama run qwen2.5-coder:7b "def hello(): pass"
```

**Performance issues:**
- Use smaller model: `qwen2.5-coder:1.5b`
- Close other applications
- Ensure sufficient RAM (4GB+ recommended)

### Benefits of Qwen Coder

- 🚀 **Specialized for coding** - Built specifically for code understanding and generation
- 🏠 **Fully local** - Your code never leaves your machine
- ⚡ **Fast processing** - No network delays
- 🔒 **Private** - Complete privacy for your code
- 💰 **Free** - No API costs or rate limits

### Next Steps

After setup:
1. Test with a small code file first
2. Adjust model size based on your hardware
3. Explore CLI options for batch processing
4. Set up Git integration for automatic refactoring

Enjoy coding with Qwen Coder! 🎉