#!/usr/bin/env python3
"""
Configuration script to enable automatic syntax error fixing in RefactAI
"""

import os
import sys
from pathlib import Path

def update_django_settings():
    """Update Django settings to enable automatic syntax error fixing"""
    settings_path = Path(__file__).parent / "refactai_project" / "settings.py"
    
    if not settings_path.exists():
        print(f"❌ Django settings file not found at {settings_path}")
        return False
    
    # Read current settings
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Configuration to add
    auto_fix_config = """

# Automatic Syntax Error Fixing Configuration
# Enable automatic fixing of syntax errors introduced by LLM refactoring
AUTO_FIX_SYNTAX_ERRORS = True
MAX_SYNTAX_FIX_ATTEMPTS = 3
ENABLE_SYNTAX_FIX_LOGGING = True
"""
    
    # Check if configuration already exists
    if "AUTO_FIX_SYNTAX_ERRORS" in content:
        print("✅ Automatic syntax error fixing is already configured")
        return True
    
    # Add configuration to the end of the file
    updated_content = content + auto_fix_config
    
    # Write back to file
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("✅ Successfully enabled automatic syntax error fixing in Django settings")
        return True
    except Exception as e:
        print(f"❌ Failed to update Django settings: {str(e)}")
        return False

def create_syntax_fix_documentation():
    """Create documentation for the automatic syntax error fixing feature"""
    doc_content = """
# Automatic Syntax Error Fixing

RefactAI now includes automatic syntax error fixing to handle errors introduced during LLM refactoring.

## How It Works

1. **Detection**: When the LLM refactors code, the system validates the output using AST parsing
2. **Error Identification**: If syntax errors are detected, the specific error message is captured
3. **Automatic Correction**: The system sends the broken code back to the LLM with a specialized error correction prompt
4. **Validation**: The corrected code is validated again to ensure the fix was successful
5. **Retry Logic**: If the first attempt fails, the system can retry up to 3 times with updated error information

## Features

- **Intelligent Error Correction**: Uses specialized prompts designed specifically for syntax error fixing
- **Context Preservation**: Provides both the broken code and original code as context for better fixes
- **Multi-Attempt Logic**: Retries with updated error messages if initial fixes don't work
- **Fallback Mechanisms**: Falls back to simpler fix attempts if LLM-based fixing fails
- **Local and API Support**: Works with both local LLM and API-based refactoring

## Configuration

The following settings control automatic syntax error fixing:

```python
# Enable/disable automatic syntax error fixing
AUTO_FIX_SYNTAX_ERRORS = True

# Maximum number of fix attempts per syntax error
MAX_SYNTAX_FIX_ATTEMPTS = 3

# Enable detailed logging of syntax fix attempts
ENABLE_SYNTAX_FIX_LOGGING = True
```

## Error Types Handled

- Unterminated string literals
- Missing parentheses, brackets, or braces
- Incorrect indentation
- Missing colons in function/class definitions
- Missing except/finally blocks in try statements
- Invalid syntax in expressions

## Benefits

1. **Reduced Manual Intervention**: Automatically fixes common LLM-introduced syntax errors
2. **Improved Success Rate**: Higher percentage of successful refactoring operations
3. **Better User Experience**: Users get working code without manual debugging
4. **Consistent Quality**: Ensures refactored code is always syntactically valid

## Monitoring

The system logs all syntax error fixing attempts, including:
- Original error messages
- Fix attempts and results
- Success/failure rates
- Performance metrics

This allows for continuous improvement of the error fixing mechanisms.
"""
    
    doc_path = Path(__file__).parent / "SYNTAX_ERROR_FIXING.md"
    
    try:
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        print(f"✅ Created documentation at {doc_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create documentation: {str(e)}")
        return False

def main():
    """Main function to enable automatic syntax error fixing"""
    print("🔧 Enabling Automatic Syntax Error Fixing in RefactAI...\n")
    
    success_count = 0
    total_tasks = 2
    
    # Task 1: Update Django settings
    print("1. Updating Django settings...")
    if update_django_settings():
        success_count += 1
    
    print()
    
    # Task 2: Create documentation
    print("2. Creating documentation...")
    if create_syntax_fix_documentation():
        success_count += 1
    
    print()
    
    # Summary
    print("=" * 50)
    print("📊 CONFIGURATION SUMMARY")
    print("=" * 50)
    print(f"Tasks completed: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("\n🎉 Automatic syntax error fixing has been successfully enabled!")
        print("\n📋 What's been configured:")
        print("   ✅ Django settings updated with auto-fix configuration")
        print("   ✅ Documentation created for the feature")
        print("\n🚀 The system will now automatically fix syntax errors introduced by LLM refactoring.")
        print("\n💡 Next steps:")
        print("   1. Restart the Django server to apply settings")
        print("   2. Run test_auto_syntax_fix.py to verify functionality")
        print("   3. Monitor logs for syntax fix attempts and success rates")
        return True
    else:
        print(f"\n⚠️  {total_tasks - success_count} configuration task(s) failed.")
        print("Please check the error messages above and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)