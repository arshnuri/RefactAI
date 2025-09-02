# RefactAI - AI-Powered Code Refactoring Tool

🔧 **RefactAI** is a powerful code refactoring tool that supports both web-based and local LLM processing. It can automatically refactor code using AI, with support for Django web interface, CLI usage, and Git integration for seamless development workflows.

## ✨ Features

### 🌐 Web Interface
- **📦 ZIP Processing**: Upload ZIP files and get refactored codebases
- **🌐 Clean UI**: Responsive web interface built with HTML/CSS
- **📊 Detailed Results**: Side-by-side comparison of original vs refactored code
- **⬇️ Easy Download**: Download refactored codebase as ZIP file

### 🖥️ Local LLM & CLI
- **🏠 Fully Offline**: Run completely locally without API dependencies
- **⚡ CLI Support**: Command-line interface for single files and directories
- **🔗 Git Integration**: Automatic refactoring via Git pre-push hooks
- **🧠 Multiple LLM Backends**: Support for Ollama, LM Studio, llama.cpp, and more

### 🔍 Smart Analysis
- **🔍 Smart Language Detection**: Automatically detects programming languages
- **✅ AST Validation**: Validates Python code syntax before and after refactoring
- **🛡️ Safe Refactoring**: Preserves functionality while improving code quality

## 🛠️ Tech Stack

- **Backend**: Django 4.2+ (Python)
- **Frontend**: HTML + CSS (no JavaScript frameworks)
- **AI Options**: 
  - **Local LLM**: Ollama, LM Studio, llama.cpp (recommended)
  - **API Fallback**: OpenRouter (Mistral AI)
- **Database**: SQLite (default)
- **File Processing**: Python zipfile, AST parsing
- **CLI**: Standalone Python scripts for local processing

## 📋 Supported Languages

- Python 🐍
- JavaScript 📜
- TypeScript 🔷
- Java ☕
- C/C++ ⚡
- C# 🔷
- PHP 🐘
- Ruby 💎
- Go 🐹
- Rust 🦀
- HTML/CSS 🌐
- And many more!

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- **For Local LLM (Recommended)**:
  - Ollama, LM Studio, or llama.cpp installed
  - At least 8GB RAM for 7B models
- **For API Fallback (Optional)**:
  - OpenRouter API key (get one at [OpenRouter](https://openrouter.ai/keys))

### 🏠 Local LLM Installation (Recommended)

1. **Clone or download the project**:
   ```bash
   cd RefactAI
   ```

2. **Run the automated setup**:
   ```bash
   python setup_local_llm.py
   ```
   This will:
   - Install Python dependencies
   - Check/install Ollama
   - Pull a recommended coding model
   - Set up Git pre-push hook
   - Configure environment variables
   - Test the local LLM connection

3. **Manual setup (if automated setup fails)**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install Ollama (if not already installed)
   # Windows: Download from https://ollama.ai/download
   # macOS: brew install ollama
   # Linux: curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a coding model
   ollama pull deepseek-coder:6.7b
   
   # Set environment variables
   echo "PREFER_LOCAL_LLM=true" > .env
   echo "LOCAL_LLM_MODEL=deepseek-coder:6.7b" >> .env
   ```

### 🌐 Web Interface Setup

1. **Run database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

3. **Open your browser** and go to `http://127.0.0.1:8000`

### 🔑 API Fallback Setup (Optional)

If you want to use API as fallback:
```bash
# Windows
set OPENROUTER_API_KEY=your_api_key_here

# macOS/Linux
export OPENROUTER_API_KEY=your_api_key_here
```

## 📖 Usage Guide

### 🖥️ CLI Usage (Local LLM)

#### Single File Refactoring
```bash
# Refactor a single file
python cli.py path/to/your/file.py

# Dry run (preview changes without applying)
python cli.py --dry-run path/to/your/file.py

# Use specific model
python cli.py --model codellama:7b path/to/your/file.py

# Create backup before refactoring
python cli.py --backup path/to/your/file.py
```

#### Directory Refactoring
```bash
# Refactor all supported files in a directory
python cli.py --recursive src/

# Test connection to local LLM
python cli.py --test-connection
```

### 🔗 Git Integration

The Git pre-push hook automatically refactors code before pushing:

1. **Install the hook** (done automatically by setup script):
   ```bash
   cp pre-push .git/hooks/pre-push
   chmod +x .git/hooks/pre-push  # Unix/macOS only
   ```

2. **Use normally**:
   ```bash
   git add .
   git commit -m "Your changes"
   git push  # Automatic refactoring happens here
   ```

3. **Skip refactoring** (if needed):
   ```bash
   SKIP_REFACTOR=1 git push
   ```

### 🌐 Web Interface Usage

#### 1. Upload Code
- Navigate to the home page
- Click "Choose File" and select a ZIP file (max 25MB)
- Click "Start Refactoring"

#### 2. View Results
- Wait for processing to complete
- Review the statistics and file list
- Click on individual files to see before/after comparison

#### 3. Download Refactored Code
- Click "Download Refactored Code" button
- Extract the ZIP file to get your improved codebase

#### 4. Review Changes
- Always test the refactored code thoroughly
- Check the validation warnings for Python files
- Compare original vs refactored versions

## ⚙️ Configuration

### Environment Variables

#### Local LLM Configuration
- `PREFER_LOCAL_LLM`: Set to `true` to use local LLM (default: `false`)
- `LOCAL_LLM_MODEL`: Model name for local LLM (default: `deepseek-coder:6.7b`)

#### API Fallback Configuration
- `OPENROUTER_API_KEY`: Your OpenRouter API key (optional)
- `DJANGO_SECRET_KEY`: Django secret key (optional, auto-generated)
- `DEBUG`: Set to `False` for production

### Settings (refactai_project/settings.py)

```python
# Local LLM Configuration
PREFER_LOCAL_LLM = os.environ.get('PREFER_LOCAL_LLM', 'false').lower() == 'true'
LOCAL_LLM_MODEL = os.environ.get('LOCAL_LLM_MODEL', 'deepseek-coder:6.7b')

# OpenRouter API Configuration (Fallback)
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_MODEL = 'mistralai/mistral-7b-instruct'

# File Upload Limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # 25MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024   # 25MB

# Supported File Extensions
ALLOWED_CODE_EXTENSIONS = [
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift',
    '.html', '.css', '.json', '.yaml', '.xml'
]
```

### 🧠 Recommended Local Models

#### For Code Refactoring:
- **deepseek-coder:6.7b** (recommended, best for code)
- **codellama:7b** (good alternative)
- **mistral:7b** (general purpose)
- **yi-coder:9b** (larger, more capable)

#### Model Installation:
```bash
# Install via Ollama
ollama pull deepseek-coder:6.7b
ollama pull codellama:7b
ollama pull mistral:7b

# List installed models
ollama list
```

## 📁 Project Structure

```
RefactAI/
├── refactai_project/          # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Main configuration
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI application
├── refactai_app/             # Main Django app
│   ├── models.py             # Database models
│   ├── views.py              # View logic
│   ├── forms.py              # Form definitions
│   ├── urls.py               # App URL patterns
│   ├── admin.py              # Admin interface
│   ├── utils/                # Utility modules
│   │   ├── zip_handler.py    # ZIP file processing
│   │   ├── language_detect.py # Language detection
│   │   ├── ast_utils.py      # Python AST validation
│   │   └── llm_client.py     # LLM client (local + API)
│   └── templates/            # HTML templates
│       └── refactai_app/
│           ├── base.html     # Base template
│           ├── home.html     # Upload page
│           ├── results.html  # Results page
│           └── file_detail.html # File comparison
├── refactor.py               # Local LLM interface
├── cli.py                    # CLI entry point
├── prompt.txt                # System prompt for LLM
├── pre-push                  # Git pre-push hook
├── setup_local_llm.py        # Automated setup script
├── .git/hooks/pre-push       # Installed Git hook
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔒 Security Features

- **File Validation**: Validates ZIP files and prevents directory traversal
- **Size Limits**: 25MB upload limit to prevent abuse
- **Extension Filtering**: Only processes known code file types
- **AST Validation**: Ensures Python code syntax correctness
- **CSRF Protection**: Django CSRF middleware enabled
- **Input Sanitization**: Sanitizes file paths and content

## 🐛 Troubleshooting

### Local LLM Issues

1. **"Local LLM client not initialized" error**:
   - Ensure Ollama is installed and running: `ollama --version`
   - Check if the model is available: `ollama list`
   - Pull the model if missing: `ollama pull deepseek-coder:6.7b`
   - Set `PREFER_LOCAL_LLM=true` in environment

2. **"Connection failed" error**:
   - Start Ollama service: `ollama serve` (if not running as service)
   - Check if port 11434 is available
   - Try alternative LLM backends (LM Studio, llama.cpp)

3. **"Model not found" error**:
   - List available models: `ollama list`
   - Pull the required model: `ollama pull <model-name>`
   - Update `LOCAL_LLM_MODEL` environment variable

4. **Performance issues**:
   - Use smaller models (6.7B instead of 13B+)
   - Enable GPU acceleration if available
   - Increase system RAM allocation

### CLI Issues

1. **"File not found" error**:
   - Ensure the file path is correct
   - Use absolute paths if relative paths fail
   - Check file permissions

2. **Git hook not working**:
   - Ensure hook is executable: `chmod +x .git/hooks/pre-push`
   - Check if Python is in PATH
   - Verify RefactAI directory structure

### Web Interface Issues

1. **"No API key configured and local LLM not enabled" error**:
   - Set `PREFER_LOCAL_LLM=true` environment variable
   - Or set `OPENROUTER_API_KEY` for API fallback
   - Restart the Django server

2. **"File too large" error**:
   - Ensure ZIP file is under 25MB
   - Remove unnecessary files from your codebase

3. **"Invalid ZIP file" error**:
   - Ensure the file is a valid ZIP archive
   - Try creating a new ZIP file

### Debug Mode

To enable debug mode for development:

```python
# In settings.py
DEBUG = True
```

### Logs

Check Django logs for detailed error information:
```bash
python manage.py runserver --verbosity=2
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Ollama** for making local LLM deployment simple
- **DeepSeek** for excellent coding models
- **OpenRouter** for providing AI API access
- **Django** for the excellent web framework
- **LM Studio** and **llama.cpp** for alternative LLM backends

## 📞 Support

If you encounter issues:

1. Check this README for common solutions
2. Review the Django error logs
3. Verify your API key and configuration
4. Create an issue with detailed error information

---

**Happy Refactoring! 🚀**