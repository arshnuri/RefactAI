# RefactAI Setup Guide for New Users

## 🚀 Quick Start for Cloned Repository

When you clone this repository to use RefactAI's "Refactor and Push to Git" feature, follow these steps:

### 1. **Clone the Repository**
```bash
git clone https://github.com/arshnuri/RefactAI.git
cd RefactAI
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set Up Environment Variables**
Create a `.env` file in the root directory:
```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
PREFER_LOCAL_LLM=false
```

**Get your OpenRouter API key from:** https://openrouter.ai/

### 4. **Configure Git for Your Repository**
```bash
# Set up your own remote repository
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Or configure existing remote
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 5. **Test the Setup**
```bash
python cli.py
```

---

## 🎯 Using "Refactor and Push to Git" Feature

### **For Your Own Codebase:**

1. **Navigate to your project directory** (or use absolute paths)
2. **Run RefactAI CLI:**
   ```bash
   python D:\RefactAI\cli.py
   ```
3. **Select:** "🚀 Refactor and Push to Git"
4. **Choose file selection method:**
   - **📁 All modified files** - Auto-detects from `git status`
   - **🎯 Specific files by pattern** - Use patterns like `*.py`, `src/**/*.js`
   - **📝 Manual file selection** - Specify exact paths

### **Example Workflows:**

#### **Scenario 1: Refactor files in current project**
```
Enter file paths (comma separated): src/main.py, utils/helper.js, models/user.java
```

#### **Scenario 2: Refactor files from different projects**
```
Enter file paths (comma separated): C:\MyProject\app.py, D:\WebApp\script.js, E:\Backend\api.java
```

#### **Scenario 3: Use patterns for bulk refactoring**
```
Pattern: src/**/*.py
```

---

## ⚙️ **Configuration Options**

### **Remote Repository Setup:**
When prompted during Git operations:
- **Remote name:** `origin` (or your custom remote)
- **Branch name:** `main` or `master` (your default branch)

### **Commit Messages:**
- Use descriptive messages like: `"Refactor authentication module using RefactAI"`
- Or use the default: `"Refactor X file(s) using RefactAI"`

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **1. "ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

#### **2. "OpenRouter API Key not found"**
- Check your `.env` file exists
- Verify the API key is correct
- Test with: `python test_openrouter_api.py`

#### **3. "Git remote not configured"**
```bash
git remote -v  # Check current remotes
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

#### **4. "Permission denied (publickey)"**
Set up SSH keys or use HTTPS with personal access token

#### **5. "Error refactoring file: 'InteractiveRefactorCLI' object has no attribute..." or "ASTValidator' object has no attribute 'validate_syntax'"**
If you encounter these validation errors:
```bash
# Run the fix scripts
python D:\RefactAI\fix_cli_validation.py
python D:\RefactAI\fix_ast_validator.py
```
*For more detailed troubleshooting, see the TROUBLESHOOTING.md file.*

---

## 🎯 **Best Practices**

### **For Team Usage:**
1. **Each team member** should have their own OpenRouter API key
2. **Configure separate Git remotes** for individual repositories
3. **Use descriptive commit messages** for refactored code
4. **Test locally first** before pushing to shared repositories

### **For Personal Projects:**
1. **Create backups** before large refactoring sessions
2. **Use dry-run mode** to preview changes
3. **Refactor incrementally** rather than entire codebases at once
4. **Review AI suggestions** before committing

---

## 📂 **Directory Structure After Setup**
```
RefactAI/
├── cli.py                    # Main CLI interface
├── requirements.txt          # Python dependencies
├── .env                     # Your API keys (create this)
├── refactai_app/           # Core refactoring logic
├── README.md               # This guide
└── examples/               # Sample code for testing
```

---

## 🚀 **Ready to Use!**

After setup, you can refactor and push code from anywhere on your system by running:
```bash
python D:\RefactAI\cli.py
```

The CLI will:
✅ Refactor your code using AI
✅ Stage the changes with Git
✅ Commit with your message
✅ Push to your repository

**Happy refactoring!** 🎉
