#!/usr/bin/env python3
"""
RefactAI Local LLM Setup Script

This script helps set up RefactAI with local LLM capabilities.
It installs dependencies, configures the Git hook, and tests the local LLM connection.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout or "", e.stderr or ""
    except Exception as e:
        return False, "", str(e)

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], shell=False)
    
    if success:
        print("✅ Dependencies installed successfully")
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False
    return True

def install_ollama():
    """Install Ollama (if not already installed)"""
    print("🦙 Checking Ollama installation...")
    
    # Check if Ollama is already installed
    success, _, _ = run_command("ollama --version")
    if success:
        print("✅ Ollama is already installed")
        return True
    
    print("📥 Ollama not found. Please install Ollama manually:")
    print("   Windows: Download from https://ollama.ai/download")
    print("   macOS: brew install ollama")
    print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
    
    return False

def pull_recommended_model():
    """Pull a recommended coding model"""
    print("🧠 Pulling recommended coding model...")
    
    models_to_try = [
        "deepseek-coder:6.7b",
        "codellama:7b",
        "mistral:7b"
    ]
    
    for model in models_to_try:
        print(f"   Trying to pull {model}...")
        success, stdout, stderr = run_command(f"ollama pull {model}")
        
        if success:
            print(f"✅ Successfully pulled {model}")
            return model
        else:
            error_msg = stderr.strip() if stderr else "Unknown error"
            print(f"   ⚠️  Failed to pull {model}: {error_msg}")
    
    print("❌ Failed to pull any recommended models")
    print("   You can manually pull a model later with: ollama pull <model-name>")
    return None

def setup_git_hook():
    """Set up the Git pre-push hook"""
    print("🔗 Setting up Git pre-push hook...")
    
    git_dir = Path(".git")
    if not git_dir.exists():
        print("   ⚠️  Not a Git repository. Skipping Git hook setup.")
        return False
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    hook_source = Path("pre-push")
    hook_target = hooks_dir / "pre-push"
    
    if hook_source.exists():
        shutil.copy2(hook_source, hook_target)
        
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(hook_target, 0o755)
        
        print("✅ Git pre-push hook installed")
        return True
    else:
        print("   ⚠️  pre-push script not found. Skipping Git hook setup.")
        return False

def test_local_llm():
    """Test the local LLM connection"""
    print("🧪 Testing local LLM connection...")
    
    try:
        from refactor import LocalLLMClient
        
        client = LocalLLMClient()
        if client.test_connection():
            print("✅ Local LLM connection successful")
            return True
        else:
            print("❌ Local LLM connection failed")
            return False
    except ImportError:
        print("❌ Failed to import LocalLLMClient")
        return False
    except Exception as e:
        print(f"❌ Error testing local LLM: {e}")
        return False

def create_env_file():
    """Create a .env file with local LLM configuration"""
    print("📝 Creating .env configuration...")
    
    env_content = '''# RefactAI Configuration

# Set to true to prefer local LLM over API
PREFER_LOCAL_LLM=true

# Local LLM model name (Ollama model)
LOCAL_LLM_MODEL=deepseek-coder:6.7b

# OpenRouter API key (optional, for fallback)
# OPENROUTER_API_KEY=your_api_key_here
'''
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
    else:
        print("   ⚠️  .env file already exists. Please update it manually if needed.")

def main():
    """Main setup function"""
    print("🚀 RefactAI Local LLM Setup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success_count = 0
    total_steps = 6
    
    # Step 1: Install dependencies
    if install_dependencies():
        success_count += 1
    
    # Step 2: Check/Install Ollama
    if install_ollama():
        success_count += 1
    
    # Step 3: Pull recommended model
    model = pull_recommended_model()
    if model:
        success_count += 1
    
    # Step 4: Setup Git hook
    if setup_git_hook():
        success_count += 1
    
    # Step 5: Create .env file
    create_env_file()
    success_count += 1
    
    # Step 6: Test local LLM
    if test_local_llm():
        success_count += 1
    
    print("\n" + "=" * 40)
    print(f"Setup completed: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 RefactAI is ready to use with local LLM!")
        print("\nNext steps:")
        print("1. Start the Django server: python manage.py runserver")
        print("2. Use the CLI: python cli.py <file.py>")
        print("3. Git integration will work automatically on push")
    else:
        print("⚠️  Some setup steps failed. Please check the errors above.")
        print("\nYou can still use RefactAI with API keys if local LLM setup failed.")

if __name__ == "__main__":
    main()