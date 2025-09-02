#!/usr/bin/env python3
"""
Debug test for Local LLM Client integration
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

def test_local_llm_integration():
    print("🔍 Testing Local LLM Integration...\n")
    
    # Test 1: Check if local LLM client is available
    print("Test 1: Local LLM Client Availability")
    print("=" * 40)
    
    llm_client = LLMClient(mode='local')
    
    print(f"Use local LLM: {llm_client.use_local_llm}")
    print(f"Has local client: {hasattr(llm_client, 'local_client')}")
    
    if hasattr(llm_client, 'local_client'):
        print(f"Local client type: {type(llm_client.local_client)}")
        print(f"Has fix_syntax_errors method: {hasattr(llm_client.local_client, 'fix_syntax_errors')}")
        
        # Test local LLM connection
        try:
            test_result = llm_client.local_client.test_connection()
            print(f"Local LLM available: {test_result.get('available', False)}")
            if not test_result.get('available', False):
                print(f"Error: {test_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error testing local LLM: {e}")
    else:
        print("❌ Local client not initialized")
    
    print("\n")
    
    # Test 2: Simple syntax error fixing
    print("Test 2: Direct Syntax Error Fixing")
    print("=" * 40)
    
    broken_code = "def hello():\n    print('Hello'\n    return True"
    print(f"Broken code:\n{broken_code}\n")
    
    # Validate it's actually broken
    is_valid, error_msg = ASTValidator.validate_python_code(broken_code)
    print(f"Is valid: {is_valid}")
    print(f"Error: {error_msg}\n")
    
    if hasattr(llm_client, 'local_client') and hasattr(llm_client.local_client, 'fix_syntax_errors'):
        try:
            fixed_code = llm_client.local_client.fix_syntax_errors(broken_code, error_msg, broken_code)
            print(f"Fixed code:\n{fixed_code}\n")
            
            # Validate fixed code
            is_fixed_valid, _ = ASTValidator.validate_python_code(fixed_code)
            print(f"Fixed code is valid: {is_fixed_valid}")
            
            if is_fixed_valid:
                print("✅ Direct syntax fixing works!")
            else:
                print("❌ Direct syntax fixing failed")
        except Exception as e:
            print(f"❌ Error during direct fixing: {e}")
    else:
        print("❌ Cannot test direct fixing - method not available")
    
    print("\n")
    
    # Test 3: Refactor with syntax error fixing
    print("Test 3: Refactor with Auto-Fix")
    print("=" * 40)
    
    try:
        result = llm_client.refactor_code(
            code=broken_code,
            language='python',
            file_path='test.py'
        )
        
        print(f"Refactor success: {result['success']}")
        print(f"Original valid: {result['original_valid']}")
        print(f"Refactored valid: {result['refactored_valid']}")
        print(f"Validation warnings: {result['validation_warnings']}")
        
        if result['success'] and result['refactored_valid']:
            print("✅ Refactor with auto-fix works!")
        else:
            print("❌ Refactor with auto-fix failed")
            print(f"Error: {result.get('error', 'No error message')}")
            
    except Exception as e:
        print(f"❌ Error during refactor: {e}")

if __name__ == "__main__":
    test_local_llm_integration()