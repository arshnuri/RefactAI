#!/usr/bin/env python3
import ast
import sys

def check_syntax(file_path):
    """Check syntax of a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Try to parse with ast
        ast.parse(code)
        print(f"✓ {file_path}: No syntax errors found")
        return True
        
    except SyntaxError as e:
        print(f"✗ {file_path}: Syntax error at line {e.lineno}: {e.msg}")
        if e.text:
            print(f"   Problem line: {e.text.strip()}")
        return False
    except Exception as e:
        print(f"✗ {file_path}: Error reading file: {e}")
        return False

if __name__ == "__main__":
    files = [
        "d:\\RefactAI\\temp_uploads\\tmp0rysm705\\test2\\enhanced_app.py",
        "d:\\RefactAI\\temp_uploads\\tmp67zoyv9z\\tmpz5m7v4fo\\foresight chain\\enhanced_app.py",
        "d:\\RefactAI\\temp_uploads\\tmpz_ir35wy\\foresight chain\\enhanced_app.py"
    ]
    
    for file_path in files:
        print(f"\nChecking: {file_path}")
        check_syntax(file_path)