#!/usr/bin/env python3
"""
Test script for OpenRouter API connection and functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.utils.llm_client import LLMClient

def test_openrouter_connection():
    """Test OpenRouter API connection"""
    print("Testing OpenRouter API connection...")
    print("=" * 50)
    
    client = LLMClient()
    
    # Test basic connection
    print("\n1. Testing basic API connection...")
    result = client.test_api_connection()
    
    if result['success']:
        print("✅ API connection successful!")
        print(f"Response: {result['content']}")
    else:
        print("❌ API connection failed!")
        print(f"Error: {result['error']}")
        return False
    
    # Test code refactoring
    print("\n2. Testing code refactoring...")
    test_code = """
def hello():
    print("hello world")
    return
"""
    
    refactor_result = client.refactor_code(
        code=test_code,
        language="python",
        file_path="test.py"
    )
    
    if refactor_result['success']:
        print("✅ Code refactoring successful!")
        print("Original code:")
        print(test_code)
        print("\nRefactored code:")
        print(refactor_result['refactored_code'])
        print(f"\nValidation - Original: {refactor_result['original_valid']}, Refactored: {refactor_result['refactored_valid']}")
        if refactor_result['validation_warnings']:
            print(f"Warnings: {refactor_result['validation_warnings']}")
    else:
        print("❌ Code refactoring failed!")
        print(f"Error: {refactor_result['error']}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! OpenRouter API is working correctly.")
    return True

if __name__ == "__main__":
    try:
        test_openrouter_connection()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)