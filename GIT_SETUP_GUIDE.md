# RefactAI Git Setup & Auto-Push Installation Guide

## 🚨 Current Status: Git Not Installed

The error you encountered indicates that Git is not installed or not in your system PATH. Here's how to set everything up:

## 📥 Step 1: Install Git

### Option A: Download Git for Windows
1. Go to: https://git-scm.com/download/win
2. Download and install Git for Windows
3. During installation, select "Git from the command line and also from 3rd-party software"
4. Restart your PowerShell/Command Prompt

### Option B: Install via Chocolatey (if you have it)
```powershell
choco install git
```

### Option C: Install via Winget
```powershell
winget install --id Git.Git -e --source winget
```

## 🔧 Step 2: Verify Git Installation

After installing Git, restart your terminal and run:
```powershell
git --version
```

You should see output like: `git version 2.x.x.windows.x`

## 🏗️ Step 3: Initialize Git Repository

Once Git is installed, set up your RefactAI project as a Git repository:

```powershell
# Navigate to your RefactAI directory
cd "D:\RefactAI"

# Initialize Git repository
git init

# Configure Git user (required for commits)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files to Git
git add .

# Create initial commit
git commit -m "Initial RefactAI setup with OpenRouter + AST configuration"
```

## 📡 Step 4: Add Remote Repository (Optional but Recommended)

If you want to push to GitHub/GitLab/etc:

```powershell
# Add remote repository
git remote add origin https://github.com/yourusername/your-repo.git

# Push to remote
git push -u origin main
```

## 🪝 Step 5: Install RefactAI Git Hook

Once Git is properly set up:

```powershell
# Copy the interactive Git hook
cp git-hook-interactive.py .git/hooks/pre-push

# Make it executable (on Windows with Git Bash)
# Or simply ensure the file has proper permissions
```

## 🎯 Alternative: Manual Git Hook Setup

If you prefer to set up the hook manually:

1. **Create the hooks directory** (if it doesn't exist):
   ```powershell
   mkdir .git/hooks -Force
   ```

2. **Copy the hook file**:
   ```powershell
   Copy-Item "git-hook-interactive.py" ".git/hooks/pre-push"
   ```

3. **Make sure Python can execute it** by adding a shebang line at the top of the hook file (already included).

## 🚀 Step 6: Test the Installation

After everything is set up:

```powershell
# Test the hook manually
python .git/hooks/pre-push

# Or test with a real push (after making changes)
git add .
git commit -m "Test RefactAI auto-refactoring"
git push origin main
```

## 🔄 Alternative Workflow (No Git Required)

If you don't want to use Git, you can still use RefactAI's auto-refactoring:

### Interactive CLI Mode
```powershell
python cli.py
```

### Batch Mode
```powershell
# Refactor single file
python cli_batch.py --file your_file.py --output overwrite

# Refactor entire directory
python cli_batch.py --directory . --language python --backup
```

## 🧪 Testing Your Setup

Run our test suite to verify everything works:

```powershell
# Test OpenRouter + AST configuration
python test_openrouter_config.py

# Test the complete setup (if Git is available)
python demo_git_autopush.py
```

## ⚡ Quick Setup Script

Here's a complete PowerShell script to set up everything:

```powershell
# Check if Git is installed
try {
    git --version
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Initialize Git repository if not already initialized
if (-not (Test-Path ".git")) {
    Write-Host "🏗️ Initializing Git repository..." -ForegroundColor Blue
    git init
    
    # Set up Git user if not configured
    $userName = git config user.name
    $userEmail = git config user.email
    
    if (-not $userName) {
        $name = Read-Host "Enter your Git user name"
        git config user.name "$name"
    }
    
    if (-not $userEmail) {
        $email = Read-Host "Enter your Git email"
        git config user.email "$email"
    }
    
    # Initial commit
    git add .
    git commit -m "Initial RefactAI setup with auto-refactoring"
}

# Install Git hook
Write-Host "🪝 Installing RefactAI Git hook..." -ForegroundColor Blue
if (-not (Test-Path ".git/hooks")) {
    New-Item -ItemType Directory -Path ".git/hooks" -Force
}

Copy-Item "git-hook-interactive.py" ".git/hooks/pre-push" -Force

Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host "Now you can use: git push origin main" -ForegroundColor Cyan
```

## 🔍 Troubleshooting

### Common Issues:

1. **"git: command not found"**
   - Solution: Install Git and restart your terminal

2. **"Could not find .git directory"**
   - Solution: Run `git init` in your project directory

3. **"Permission denied"**
   - Solution: Make sure you have write permissions in the directory

4. **"Hook not executing"**
   - Solution: Ensure the hook file has proper permissions and Python shebang

### Need Help?

Run the diagnostic script:
```powershell
python demo_git_autopush.py
```

This will show you exactly what's configured and what needs to be fixed.

## 🎯 Summary

Once Git is installed and configured:
1. Your RefactAI will automatically refactor code on every `git push`
2. You can choose between refactoring changed files or the entire repository
3. All refactoring uses OpenRouter API with AST validation
4. Changes are automatically committed and pushed
5. The workflow is completely automated after initial setup

The auto-push feature ensures your refactored code is always in sync with your remote repository!
