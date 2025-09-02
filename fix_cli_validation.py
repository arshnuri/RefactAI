#!/usr/bin/env python3
"""
Fix for the CLI validation method issue
This script updates cli.py to fix the missing validate_refactored_code_with_ast method
"""

import os
import re

def fix_validation_method():
    """
    Fix the method name discrepancy in cli.py
    Replace validate_refactored_code_with_ast with validate_refactored_code
    """
    cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli.py')
    
    with open(cli_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the method call with the correct method name
    fixed_content = content.replace(
        'warnings = self.validate_refactored_code_with_ast(original_code, refactored_code, language)',
        'warnings = self.validate_refactored_code(original_code, refactored_code, language)'
    )
    
    if fixed_content == content:
        print("❌ No replacements made. Either the file has already been fixed or the pattern wasn't found.")
        return False
    
    with open(cli_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Successfully fixed the validation method name in cli.py")
    return True

if __name__ == "__main__":
    fix_validation_method()
