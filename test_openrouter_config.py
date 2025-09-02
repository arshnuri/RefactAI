#!/usr/bin/env python3
"""
Test script to verify OpenRouter API + AST forced mode implementations
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cli_config():
    """Test CLI configuration forcing OpenRouter + AST"""
    print("🧪 Testing CLI Configuration...")
    
    try:
        from cli import InteractiveRefactorCLI
        cli = InteractiveRefactorCLI()
        
        # Check forced configuration
        assert cli.config['processing_mode'] == 'hybrid_openrouter', "Processing mode should be hybrid_openrouter"
        assert cli.config['model'] == 'anthropic/claude-3.5-sonnet', "Default model should be Claude 3.5 Sonnet"
        assert cli.config['use_ast_validation'] == True, "AST validation should be enabled"
        
        print("✅ CLI configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ CLI configuration test failed: {e}")
        return False

def test_git_hook_config():
    """Test Git hook configuration forcing OpenRouter + AST"""
    print("🧪 Testing Git Hook Configuration...")
    
    try:
        # Import git hook module directly from file
        import importlib.util
        spec = importlib.util.spec_from_file_location("git_hook_interactive", "git-hook-interactive.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        hook = module.InteractiveGitHook()
        
        # Check forced configuration
        assert hook.config['processing_mode'] == 'hybrid_openrouter', "Processing mode should be hybrid_openrouter"
        assert hook.config['model'] == 'anthropic/claude-3.5-sonnet', "Default model should be Claude 3.5 Sonnet"
        assert hook.config['use_ast_validation'] == True, "AST validation should be enabled"
        assert hook.config['refactor_full_repo'] == True, "Full repo refactoring should be enabled"
        
        print("✅ Git hook configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Git hook configuration test failed: {e}")
        return False

def test_api_dependencies():
    """Test required API dependencies"""
    print("🧪 Testing API Dependencies...")
    
    try:
        # Test OpenRouter API key
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("⚠️  Warning: OPENROUTER_API_KEY not set")
        else:
            print("✅ OpenRouter API key found")
        
        # Test imports
        from refactai_app.utils.llm_client import LLMClient
        from refactai_app.utils.ast_utils import ASTValidator
        
        print("✅ API dependencies test passed!")
        return True
        
    except Exception as e:
        print(f"❌ API dependencies test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RefactAI OpenRouter + AST Configuration Tests\n")
    
    tests = [
        test_cli_config,
        test_git_hook_config,
        test_api_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RefactAI is configured for OpenRouter API + AST validation")
        return 0
    else:
        print("❌ Some tests failed. Please review the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
