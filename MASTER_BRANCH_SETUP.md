# RefactAI Git Hook - Master Branch Setup

## 🎯 Your Branch: `master`

Since you mentioned your default branch is `master`, here are the correct commands for your setup:

## 🚀 RefactAI Workflow (Master Branch)

### Step 1: Install Git & Setup
```bash
# After installing Git, run:
python complete_git_setup.py
```

### Step 2: Use RefactAI with Master Branch
```bash
# Make your changes
git add .
git commit -m "Add new feature"

# This triggers RefactAI (note: master, not main):
git push origin master
```

## 🔄 What Happens When You Push to Master

```bash
$ git push origin master

# RefactAI Git Hook activates:
┌─────────────────────────────────────┐
│ RefactAI Git Hook - Pre-Push        │
│ 🧪 Testing OpenRouter API... ✅    │
│ 📂 Refactoring scope:               │
│   ❯ changed files                   │
│     full repository                 │
│ 🔄 Processing files...              │
│ ✅ Auto-push to origin/master? [Y]  │
└─────────────────────────────────────┘
```

## 🎯 Terminal Compatibility (Master Branch)

✅ **All of these will trigger RefactAI on master:**

- **Git Bash**: `$ git push origin master`
- **PowerShell**: `PS> git push origin master`  
- **Command Prompt**: `C:\> git push origin master`
- **VS Code Terminal**: `git push origin master`
- **Any Git client**: Same trigger, same result

## 📋 Master Branch Git History

After RefactAI runs, your Git history will look like:

```
abc123 refactor: Auto-refactored repository using RefactAI
def456 Add new feature (your original commit)
ghi789 Previous commits...
```

Both commits are pushed to `origin/master` automatically.

## 🔧 Master Branch Specific Commands

```bash
# Skip refactoring for this push:
git push origin master --no-refactor

# Check your master branch status:
git status
git log --oneline -5

# Test the hook setup:
echo "# Test" >> README.md
git add .
git commit -m "Test RefactAI on master"
git push origin master
```

## 🧪 Troubleshooting Master Branch Issues

If `git push origin master` doesn't trigger RefactAI:

1. **Check Git installation:**
   ```bash
   git --version
   ```

2. **Verify repository setup:**
   ```bash
   git branch  # Should show * master
   git remote -v  # Should show origin
   ```

3. **Check hook installation:**
   ```bash
   ls -la .git/hooks/pre-push
   # Should exist and be executable
   ```

4. **Test hook manually:**
   ```bash
   python .git/hooks/pre-push
   # Should show RefactAI interface
   ```

5. **Verify branch configuration:**
   ```bash
   git branch -a  # Should show master branch
   ```

## 💡 Key Points for Master Branch

- ✅ RefactAI hook works identically with `master` branch
- ✅ All terminals (Git Bash, PowerShell, CMD) supported
- ✅ Auto-refactoring triggers on `git push origin master`
- ✅ Auto-push sends refactored code back to `origin/master`
- ✅ No differences from `main` branch functionality

## 🎉 Ready to Use

Once Git is installed and you run `python complete_git_setup.py`, your RefactAI will be ready to automatically refactor and push code every time you run:

```bash
git push origin master
```

The hook is **branch-agnostic** - it works the same way whether you use `master`, `main`, or any other branch name! 🚀
