#!/usr/bin/env python3
"""
Test Python syntax error fixing with real problematic code
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.utils.llm_client import LLMClient
from refactai_app.utils.ast_utils import ASTValidator

def test_python_syntax_fixing():
    print("🧪 Testing Python Syntax Error Fixing...\n")
    
    # Test cases with common Python syntax errors
    test_cases = [
        {
            "name": "Missing closing parenthesis in function call",
            "code": "def calculate_sum(a, b):\n    result = max(a, b\n    return result"
        },
        {
            "name": "Unterminated string literal",
            "code": "def greet(name):\n    message = 'Hello, \n    print(message + name)\n    return message"
        },
        {
            "name": "Missing colon in if statement",
            "code": "def check_positive(num):\n    if num > 0\n        return True\n    return False"
        },
        {
            "name": "Incorrect indentation",
            "code": "def process_list(items):\nresult = []\n    for item in items:\n        result.append(item * 2)\n    return result"
        },
        {
            "name": "Missing import statement",
            "code": "def get_current_time():\n    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')"
        }
    ]
    
    # Initialize LLM client
    llm_client = LLMClient(mode='local')  # Use local mode for testing
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("=" * 50)
        
        code = test_case['code']
        
        # Validate original code (should fail)
        is_valid, error_msg = ASTValidator.validate_python_code(code)
        if is_valid:
            print("❌ Test case error: Code is actually valid!")
            continue
            
        print(f"✅ Confirmed syntax error: {error_msg}")
        
        # Try to refactor the code (which should trigger auto-fix)
        try:
            result = llm_client.refactor_code(
                code=code,
                language='python',
                file_path='test.py'
            )
            
            if result['success']:
                # Check if the refactored code is valid
                refactored_code = result['refactored_code']
                is_valid_after, _ = ASTValidator.validate_python_code(refactored_code)
                
                if is_valid_after:
                    print("✅ Successfully fixed and refactored!")
                    success_count += 1
                    print("Fixed code:")
                    print("-" * 30)
                    print(refactored_code)
                    print("-" * 30)
                else:
                    print("❌ Refactoring succeeded but code still has syntax errors")
                    print(f"Validation warnings: {result.get('validation_warnings', [])}")
            else:
                print(f"❌ Refactoring failed: {result['error']}")
                print(f"Validation warnings: {result.get('validation_warnings', [])}")
                
        except Exception as e:
            print(f"❌ Exception during refactoring: {e}")
        
        print("\n")
    
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Successful fixes: {success_count}")
    print(f"Failed fixes: {total_tests - success_count}")
    print(f"Success rate: {(success_count / total_tests) * 100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 All Python syntax errors were successfully fixed!")
        return True
    else:
        print(f"\n⚠️ {total_tests - success_count} out of {total_tests} syntax errors could not be fixed.")
        return False

if __name__ == "__main__":
    success = test_python_syntax_fixing()
    sys.exit(0 if success else 1)