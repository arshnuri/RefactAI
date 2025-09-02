#!/usr/bin/env python3
"""
RefactAI Setup Script for New Users
Automates the setup process after cloning the repository
"""

import os
import sys
import subprocess
from pathlib import Path

def create_env_file():
    """Create .env file with user input"""
    env_path = Path('.env')
    
    if env_path.exists():
        response = input("⚠️  .env file already exists. Overwrite? [y/N]: ")
        if response.lower() != 'y':
            print("✅ Using existing .env file")
            return
    
    print("\n🔧 Setting up environment variables...")
    print("\n📋 You'll need an OpenRouter API key from: https://openrouter.ai/")
    
    api_key = input("🔑 Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("❌ API key is required. Setup cancelled.")
        return False
    
    env_content = f"""# RefactAI Environment Configuration
OPENROUTER_API_KEY={api_key}
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
PREFER_LOCAL_LLM=false
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run manually: pip install -r requirements.txt")
        return False

def setup_git_remote():
    """Help user configure Git remote"""
    print("\n🔧 Git Remote Configuration")
    print("Current remotes:")
    
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("No remotes configured")
    except:
        print("Git not available or not in a Git repository")
        return
    
    response = input("\n🤔 Do you want to configure a new remote repository? [y/N]: ")
    if response.lower() == 'y':
        repo_url = input("🔗 Enter your repository URL (e.g., https://github.com/username/repo.git): ").strip()
        
        if repo_url:
            try:
                # Remove existing origin if it exists
                subprocess.run(['git', 'remote', 'remove', 'origin'], 
                             capture_output=True, text=True)
                
                # Add new origin
                subprocess.run(['git', 'remote', 'add', 'origin', repo_url], 
                             check=True, capture_output=True, text=True)
                print("✅ Git remote configured successfully!")
            except subprocess.CalledProcessError:
                print("❌ Failed to configure Git remote. Please set it up manually.")

def test_setup():
    """Test if setup is working"""
    print("\n🧪 Testing setup...")
    
    # Test environment file
    if not Path('.env').exists():
        print("❌ .env file not found")
        return False
    
    # Test API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OpenRouter API key not found in .env file")
        return False
    
    print("✅ Environment configuration looks good!")
    
    # Test CLI import
    try:
        from cli import InteractiveRefactorCLI
        print("✅ CLI modules loaded successfully!")
    except ImportError as e:
        print(f"❌ Failed to import CLI modules: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 RefactAI Setup Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('cli.py').exists():
        print("❌ Error: cli.py not found. Please run this script from the RefactAI directory.")
        sys.exit(1)
    
    print("📂 Setting up RefactAI in:", os.getcwd())
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("⚠️  Dependency installation failed. Please install manually and re-run.")
        return
    
    # Step 2: Create .env file
    if not create_env_file():
        print("⚠️  Environment setup failed. Please create .env file manually.")
        return
    
    # Step 3: Git remote setup
    setup_git_remote()
    
    # Step 4: Test setup
    if test_setup():
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 You can now run the CLI with:")
        print("   python cli.py")
        print("\n📖 See SETUP_GUIDE_FOR_USERS.md for detailed usage instructions.")
    else:
        print("\n⚠️  Setup completed with warnings. Please check the issues above.")
    
    print("\n✨ Ready to refactor and push code with AI! ✨")

if __name__ == "__main__":
    main()
