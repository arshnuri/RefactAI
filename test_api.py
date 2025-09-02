#!/usr/bin/env python
import os
import django
import sys

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.utils.llm_client import LLMClient

def test_api():
    print("Testing OpenRouter API connection...")
    
    client = LLMClient()
    print(f"API Key: {client.api_key[:20]}...")
    print(f"Model: {client.default_model}")
    print(f"API URL: {client.api_url}")
    
    # Test simple connection
    print("\n--- Testing API Connection ---")
    result = client.test_api_connection()
    print(f"Connection test result: {result}")
    
    # Test code refactoring
    print("\n--- Testing Code Refactoring ---")
    test_code = "def hello():\n    print('hello world')"
    
    try:
        refactor_result = client.refactor_code(test_code, "python", "test.py")
        print(f"Refactor result: {refactor_result}")
    except Exception as e:
        print(f"Refactor error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()