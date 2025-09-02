# RefactAI - Quick Setup Guide for New Users

When someone clones your RefactAI repository, here's how they can set it up to use the "Refactor and Push to Git" feature:

## 🚀 **Setup Steps**

### 1. **Clone and Install**
```bash
git clone https://github.com/arshnuri/RefactAI.git
cd RefactAI
pip install -r requirements.txt
```

### 2. **Get OpenRouter API Key**
- Go to https://openrouter.ai/
- Sign up and get your API key
- Create `.env` file:
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

### 3. **Configure Git Remote**
```bash
# Remove original remote and add your own
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 4. **Test the Setup**
```bash
python cli.py
```

## 🎯 **Using Multi-File Refactor & Push**

### **Select Multiple Files from Different Locations:**

When using "🚀 Refactor and Push to Git" → "📝 Manual file selection":

```
# Files from different drives/locations
Enter file paths (comma separated): C:\MyProject\main.py, D:\WebApp\script.js, E:\Backend\api.java

# Mix relative and absolute paths  
Enter file paths (comma separated): ./local_file.py, C:\OtherProject\utils.js

# Use patterns for bulk selection
Pattern: src/**/*.py
```

### **Example Workflow:**
1. Run: `python D:\RefactAI\cli.py` (from anywhere)
2. Select: "🚀 Refactor and Push to Git"  
3. Choose: "📝 Manual file selection"
4. Enter: `C:\MyCode\app.py, C:\MyCode\utils.js, C:\MyCode\models\user.java`
5. AI refactors all files with proper documentation, type hints, clean naming
6. Automatically commits and pushes to your repository

## ✅ **What They Get**

- **Multi-language refactoring** (Python, Java, JavaScript, C++, etc.)
- **Cross-drive file selection** (C:, D:, E:, network drives)
- **Professional code transformation** with documentation
- **Automated Git workflow** (add, commit, push)
- **No setup complexity** - works out of the box

Perfect for teams and individual developers who want AI-powered code refactoring with seamless Git integration! 🚀
