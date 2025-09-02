#!/usr/bin/env python3
"""
Fix for the AST validator syntax validation method issue
This script updates the ASTValidator class to include the validate_syntax method
"""

import os
import re

def fix_ast_validator():
    """
    Fix the missing validate_syntax method in the ASTValidator class
    """
    # Find the ast_utils.py file
    ast_utils_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'refactai_app', 'utils', 'ast_utils.py')
    
    if not os.path.exists(ast_utils_path):
        print(f"❌ Could not find AST utils file at {ast_utils_path}")
        return False
    
    with open(ast_utils_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the validate_syntax method already exists
    if 'def validate_syntax' in content:
        print("✅ The validate_syntax method already exists in ASTValidator")
        return True
    
    # Find the ASTValidator class definition
    class_match = re.search(r'class ASTValidator[^\{]*:', content)
    if not class_match:
        print("❌ Could not find ASTValidator class in ast_utils.py")
        return False
    
    # Add the validate_syntax method to the class
    # The validate_syntax method will check the Python syntax using ast.parse
    validate_syntax_method = '''
    def validate_syntax(self, code: str) -> bool:
        """
        Validate Python code syntax
        
        Args:
            code (str): Python code to validate
            
        Returns:
            bool: True if syntax is valid, False otherwise
        """
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    '''
    
    # Insert the method at the end of the class
    # Find the end of the class by looking for the next class or end of file
    class_start = class_match.start()
    next_class = re.search(r'class ', content[class_start+1:])
    if next_class:
        insert_pos = class_start + 1 + next_class.start()
    else:
        insert_pos = len(content)
    
    # Insert the method
    updated_content = content[:insert_pos] + validate_syntax_method + content[insert_pos:]
    
    with open(ast_utils_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Successfully added validate_syntax method to ASTValidator class")
    return True

if __name__ == "__main__":
    fix_ast_validator()
