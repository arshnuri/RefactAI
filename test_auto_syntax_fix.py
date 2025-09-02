#!/usr/bin/env python3
"""
Test script for automatic syntax error fixing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')

import django
from django.conf import settings

try:
    django.setup()
except Exception as e:
    print(f"Warning: Django setup failed: {e}")
    # Configure minimal settings for testing
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            OPENROUTER_API_KEY='test-key-for-syntax-fixing',
            AUTO_FIX_SYNTAX_ERRORS=True,
            MAX_SYNTAX_FIX_ATTEMPTS=3
        )

from refactai_app.utils.llm_client import LLMClient
from refactai_app.utils.ast_utils import ASTValidator

def test_syntax_error_fixing():
    """Test the automatic syntax error fixing functionality"""
    print("🧪 Testing Automatic Syntax Error Fixing...\n")
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Test cases with intentional syntax errors
    test_cases = [
        {
            "name": "Missing closing parenthesis",
            "broken_code": "def hello_world():\n    print('Hello, World!'\n    return True",
            "original_code": "def hello_world():\n    print('Hello, World!')\n    return True"
        },
        {
            "name": "Unterminated string literal",
            "broken_code": "def greet(name):\n    message = 'Hello, \n    print(message + name)\n    return message",
            "original_code": "def greet(name):\n    message = 'Hello, '\n    print(message + name)\n    return message"
        },
        {
            "name": "Missing colon in function definition",
            "broken_code": "def calculate_sum(a, b)\n    result = a + b\n    return result",
            "original_code": "def calculate_sum(a, b):\n    result = a + b\n    return result"
        },
        {
            "name": "Incorrect indentation",
            "broken_code": "def process_data(data):\nresult = []\nfor item in data:\n    result.append(item * 2)\nreturn result",
            "original_code": "def process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result"
        },
        {
            "name": "Missing except block",
            "broken_code": "def safe_divide(a, b):\n    try:\n        return a / b\n    finally:\n        print('Division completed')",
            "original_code": "def safe_divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None\n    finally:\n        print('Division completed')"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("=" * 50)
        
        # Validate that the broken code is indeed broken
        is_valid, error_msg = ASTValidator.validate_python_code(test_case['broken_code'])
        
        if is_valid:
            print("❌ Test case error: 'Broken' code is actually valid!")
            results.append(False)
            continue
        
        print(f"✅ Confirmed syntax error: {error_msg}")
        
        # Test the automatic fixing
        try:
            fixed_code = llm_client._auto_fix_syntax_errors(
                test_case['broken_code'], 
                error_msg, 
                test_case['original_code'], 
                'python'
            )
            
            # Validate the fixed code
            is_fixed_valid, fixed_error = ASTValidator.validate_python_code(fixed_code)
            
            if is_fixed_valid:
                print("✅ Successfully fixed syntax error!")
                print("Fixed code:")
                print("-" * 30)
                print(fixed_code)
                print("-" * 30)
                results.append(True)
            else:
                print(f"❌ Fix attempt failed: {fixed_error}")
                print("Attempted fix:")
                print("-" * 30)
                print(fixed_code)
                print("-" * 30)
                results.append(False)
                
        except Exception as e:
            print(f"❌ Error during fixing: {str(e)}")
            results.append(False)
        
        print("\n")
    
    # Summary
    successful_fixes = sum(results)
    total_tests = len(test_cases)
    
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Successful fixes: {successful_fixes}")
    print(f"Failed fixes: {total_tests - successful_fixes}")
    print(f"Success rate: {(successful_fixes / total_tests) * 100:.1f}%")
    
    if successful_fixes == total_tests:
        print("\n🎉 All syntax errors were automatically fixed!")
    elif successful_fixes > 0:
        print(f"\n⚠️  {successful_fixes} out of {total_tests} syntax errors were fixed.")
    else:
        print("\n❌ No syntax errors were automatically fixed.")
    
    return successful_fixes == total_tests

def test_integration_with_refactor():
    """Test integration with the main refactor_code method"""
    print("\n🔧 Testing Integration with Main Refactor Method...\n")
    
    llm_client = LLMClient()
    
    # Test code that will likely produce a syntax error during refactoring
    test_code = """
def simple_function():
    x = 1
    y = 2
    return x + y

print(simple_function())
"""
    
    print("Original code:")
    print("-" * 30)
    print(test_code)
    print("-" * 30)
    
    # Attempt refactoring (this might introduce syntax errors that should be auto-fixed)
    result = llm_client.refactor_code(test_code, 'python', 'test.py')
    
    print(f"Refactoring success: {result['success']}")
    print(f"Original valid: {result['original_valid']}")
    print(f"Refactored valid: {result['refactored_valid']}")
    
    if result['validation_warnings']:
        print("Validation warnings:")
        for warning in result['validation_warnings']:
            print(f"  - {warning}")
    
    if result['success'] and result['refactored_valid']:
        print("\n✅ Integration test passed - refactored code is syntactically valid")
        print("\nRefactored code:")
        print("-" * 30)
        print(result['refactored_code'])
        print("-" * 30)
        return True
    else:
        print(f"\n❌ Integration test failed: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    print("🚀 RefactAI Automatic Syntax Error Fixing Test Suite\n")
    
    # Test 1: Direct syntax error fixing
    test1_passed = test_syntax_error_fixing()
    
    # Test 2: Integration with refactoring
    test2_passed = test_integration_with_refactor()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    print(f"Direct syntax fixing test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Integration test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Automatic syntax error fixing is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)