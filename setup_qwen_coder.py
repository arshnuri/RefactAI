#!/usr/bin/env python3
"""
RefactAI Qwen Coder Setup Script

Simplified setup script specifically for Qwen Coder model.
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
    """Check if Ollama is installed"""
    print("🦙 Checking Ollama installation...")
    
    success, _, _ = run_command("ollama --version")
    if success:
        print("✅ Ollama is already installed")
        return True
    
    print("❌ Ollama not found. Please install Ollama:")
    print("   Windows: Download from https://ollama.ai/download")
    print("   macOS: brew install ollama")
    print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
    
    return False

def pull_qwen_coder():
    """Pull Qwen Coder model"""
    print("🧠 Pulling Qwen Coder model...")
    
    # Try different Qwen Coder variants
    qwen_models = [
        "qwen2.5-coder:7b",
        "qwen2.5-coder:1.5b",
        "qwen2.5-coder:3b",
        "qwen2-coder:7b",
        "qwen-coder:7b"
    ]
    
    for model in qwen_models:
        print(f"   Trying to pull {model}...")
        success, stdout, stderr = run_command(f"ollama pull {model}")
        
        if success:
            print(f"✅ Successfully pulled {model}")
            return model
        else:
            error_msg = stderr.strip() if stderr else "Unknown error"
            print(f"   ⚠️  Failed to pull {model}: {error_msg}")
    
    print("❌ Failed to pull any Qwen Coder models")
    print("   Available models: https://ollama.ai/library/qwen2.5-coder")
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

def create_env_file(model_name):
    """Create a .env file with Qwen Coder configuration"""
    print("📝 Creating .env configuration...")
    
    env_content = f'''# RefactAI Configuration for Qwen Coder

# Set to true to use local LLM
PREFER_LOCAL_LLM=true

# Qwen Coder model name
LOCAL_LLM_MODEL={model_name}

# OpenRouter API key (optional, for fallback)
# OPENROUTER_API_KEY=your_api_key_here
'''
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created with Qwen Coder configuration")
    else:
        print("   ⚠️  .env file already exists. Please update it manually if needed.")
        print(f"   Add: LOCAL_LLM_MODEL={model_name}")

def test_qwen_coder(model_name):
    """Test Qwen Coder model"""
    print("🧪 Testing Qwen Coder model...")
    
    try:
        # Test if model is available
        success, stdout, stderr = run_command(f"ollama list | findstr {model_name.split(':')[0]}" if os.name == 'nt' else f"ollama list | grep {model_name.split(':')[0]}")
        
        if success and model_name.split(':')[0] in stdout:
            print("✅ Qwen Coder model is available")
            
            # Test a simple generation
            test_prompt = "def hello_world():"
            success, stdout, stderr = run_command(f'ollama run {model_name} "{test_prompt}"')
            
            if success:
                print("✅ Qwen Coder model test successful")
                return True
            else:
                print(f"⚠️  Model test failed: {stderr}")
                return False
        else:
            print("❌ Qwen Coder model not found in Ollama")
            return False
    except Exception as e:
        print(f"❌ Error testing Qwen Coder: {e}")
        return False

def main():
    """Main setup function for Qwen Coder"""
    print("🚀 RefactAI Qwen Coder Setup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Install dependencies
    if install_dependencies():
        success_count += 1
    
    # Step 2: Check Ollama
    if not install_ollama():
        print("\n❌ Setup failed: Ollama is required")
        print("Please install Ollama and run this script again.")
        return
    success_count += 1
    
    # Step 3: Pull Qwen Coder model
    model = pull_qwen_coder()
    if model:
        success_count += 1
    else:
        print("\n❌ Setup failed: Could not pull Qwen Coder model")
        print("Please check your internet connection and try again.")
        return
    
    # Step 4: Setup Git hook
    if setup_git_hook():
        success_count += 1
    
    # Step 5: Create .env file
    create_env_file(model)
    success_count += 1
    
    # Test the model
    print("\n🧪 Testing Qwen Coder setup...")
    if test_qwen_coder(model):
        print("\n" + "=" * 40)
        print(f"🎉 Qwen Coder setup completed successfully!")
        print(f"Model: {model}")
        print("\nNext steps:")
        print("1. Start the Django server: python manage.py runserver")
        print("2. Use the CLI: python cli.py <file.py>")
        print("3. Git integration will work automatically on push")
        print("\n💡 Your code will be refactored using Qwen Coder locally!")
    else:
        print("\n⚠️  Setup completed but model test failed.")
        print("You can still try using RefactAI - the model might work in practice.")

if __name__ == "__main__":
    main()