#!/usr/bin/env python3
"""
Test script for the new hybrid refactoring system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
import django
django.setup()

from refactai_app.utils.llm_client import LLMClient

def test_hybrid_refactor():
    """Test the hybrid refactoring system"""
    
    # Sample Python code with various improvement opportunities
    test_code = '''
def calc(x, y):
    temp = x + y
    if temp == True:
        return temp
    result = []
    for i in range(10):
        result.append(i * 2)
    return result

class MyClass:
    def __init__(self):
        self.data = []
        
    def process(self):
        if len(self.data) == 0:
            return None
        return self.data[0]
'''
    
    print("🔧 Testing Hybrid Refactoring System")
    print("=" * 50)
    
    # Initialize LLM client with hybrid approach
    client = LLMClient(use_hybrid_approach=True)
    
    print(f"✅ Hybrid approach enabled: {client.use_hybrid_approach}")
    print(f"✅ Hybrid refactor initialized: {hasattr(client, 'hybrid_refactor')}")
    
    print("\n📝 Original Code:")
    print("-" * 30)
    print(test_code)
    
    # Test refactoring
    print("\n🚀 Running hybrid refactoring...")
    result = client.refactor_code(
        code=test_code,
        language='python',
        file_path='test.py',
        session_id='test_session'
    )
    
    print("\n📊 Refactoring Results:")
    print("-" * 30)
    print(f"Success: {result['success']}")
    print(f"Original Valid: {result['original_valid']}")
    print(f"Refactored Valid: {result['refactored_valid']}")
    
    if result.get('validation_warnings'):
        print(f"Warnings: {result['validation_warnings']}")
    
    if result.get('llm_suggestions'):
        print(f"LLM Suggestions: {result['llm_suggestions']}")
    
    if result.get('ast_transformations'):
        print(f"AST Transformations: {result['ast_transformations']}")
    
    if result.get('improvements'):
        print(f"Improvements: {result['improvements']}")
    
    if result['success']:
        print("\n✨ Refactored Code:")
        print("-" * 30)
        print(result['refactored_code'])
    else:
        print(f"\n❌ Error: {result['error']}")
    
    print("\n" + "=" * 50)
    print("🎯 Hybrid Refactoring Test Complete!")
    
    return result

def test_ast_only():
    """Test AST-only transformations when LLM is not available"""
    
    print("\n🔧 Testing AST-Only Mode")
    print("=" * 50)
    
    # Initialize without LLM client
    from refactai_app.utils.hybrid_refactor import HybridRefactor
    hybrid = HybridRefactor(llm_client=None)
    
    test_code = '''
def test_func():
    if x == True:
        return True
    return False
'''
    
    result = hybrid.refactor_code(test_code, 'python', 'test.py')
    
    print(f"Success: {result['success']}")
    print(f"Refactored Code:\n{result['refactored_code']}")
    
    return result

if __name__ == '__main__':
    try:
        # Test hybrid refactoring
        hybrid_result = test_hybrid_refactor()
        
        # Test AST-only mode
        ast_result = test_ast_only()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()