#!/usr/bin/env python3
"""
Test script to directly test the refactor_file_internal method
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure Django for CLI testing
import django
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY=os.getenv('DJANGO_SECRET_KEY', 'test-only-key-not-for-production'),
        OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY', ''),
        OPENROUTER_API_URL=os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions'),
        DEFAULT_MODEL=os.getenv('DEFAULT_MODEL', 'anthropic/claude-3.5-sonnet'),
        PREFER_LOCAL_LLM=False,
        INSTALLED_APPS=[
            'refactai_app',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    )

django.setup()

# Import after Django setup
from cli import InteractiveRefactorCLI

def test_refactor_file():
    """Test the refactor_file_internal method directly"""
    print("🧪 Testing refactor_file_internal method...")
    
    # Create CLI instance
    cli = InteractiveRefactorCLI()
    
    # Test with t1.py
    file_path = "t1.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"📁 Testing refactoring of: {file_path}")
    
    # Read original content
    with open(file_path, 'r') as f:
        original_content = f.read()
    
    print("📝 Original content:")
    print(original_content)
    print("-" * 50)
    
    # Test refactoring
    result = cli.refactor_file_internal(file_path)
    
    if result['success']:
        print("✅ Refactoring successful!")
        
        # Read refactored content
        with open(file_path, 'r') as f:
            new_content = f.read()
        
        print("🔄 Refactored content:")
        print(new_content)
        print("-" * 50)
        
        # Restore original content for next test
        with open(file_path, 'w') as f:
            f.write(original_content)
        
        print("🔄 Original content restored for next test")
        return True
    else:
        print(f"❌ Refactoring failed: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = test_refactor_file()
    if success:
        print("\n🎉 Test completed successfully! The CLI refactor feature should work.")
    else:
        print("\n❌ Test failed. Check the error messages above.")
