import ast
import sys
from typing import Tuple, Optional


class ASTValidator:
    """Validates Python code using AST parsing"""
    
    @staticmethod
    def validate_python_code(code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python code using AST parsing
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not code.strip():
            return True, None  # Empty code is considered valid
        
        try:
            # Parse the code into an AST
            ast.parse(code)
            return True, None
            
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return False, error_msg
            
        except Exception as e:
            error_msg = f"AST parsing error: {str(e)}"
            return False, error_msg
    
    @staticmethod
    def get_code_structure_info(code: str) -> dict:
        """Extract structural information from Python code
        
        Returns:
            dict: Information about classes, functions, imports, etc.
        """
        info = {
            'classes': [],
            'functions': [],
            'imports': [],
            'has_main': False,
            'docstrings': [],
            'complexity_score': 0
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    info['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                
                elif isinstance(node, ast.FunctionDef):
                    info['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': len(node.args.args)
                    })
                    
                    # Check for main function
                    if node.name == 'main':
                        info['has_main'] = True
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        info['imports'].append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    # Check for docstrings
                    if isinstance(node.value.value, str):
                        info['docstrings'].append(node.value.value[:100])  # First 100 chars
            
            # Calculate complexity score (simple heuristic)
            info['complexity_score'] = ASTValidator._calculate_complexity(tree)
            
            # Check for if __name__ == '__main__' pattern
            for node in ast.walk(tree):
                if (isinstance(node, ast.If) and 
                    isinstance(node.test, ast.Compare) and
                    isinstance(node.test.left, ast.Name) and
                    node.test.left.id == '__name__'):
                    info['has_main'] = True
                    break
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    @staticmethod
    def _calculate_complexity(tree: ast.AST) -> int:
        """Calculate a simple complexity score for the code"""
        complexity = 0
        
        for node in ast.walk(tree):
            # Control flow statements add complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            
            # Nested functions/classes add complexity
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                complexity += 1
            
            # Exception handling adds complexity
            elif isinstance(node, (ast.ExceptHandler, ast.Raise)):
                complexity += 1
            
            # Comprehensions add complexity
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
        
        return complexity
    
    @staticmethod
    def compare_code_structure(original_code: str, refactored_code: str) -> dict:
        """Compare structural differences between original and refactored code
        
        Returns:
            dict: Comparison results
        """
        comparison = {
            'original_valid': False,
            'refactored_valid': False,
            'structure_preserved': False,
            'changes': [],
            'warnings': []
        }
        
        # Validate both versions
        orig_valid, orig_error = ASTValidator.validate_python_code(original_code)
        ref_valid, ref_error = ASTValidator.validate_python_code(refactored_code)
        
        comparison['original_valid'] = orig_valid
        comparison['refactored_valid'] = ref_valid
        
        if not orig_valid:
            comparison['warnings'].append(f"Original code has syntax errors: {orig_error}")
        
        if not ref_valid:
            comparison['warnings'].append(f"Refactored code has syntax errors: {ref_error}")
            return comparison
        
        # If both are valid, compare structures
        if orig_valid and ref_valid:
            orig_info = ASTValidator.get_code_structure_info(original_code)
            ref_info = ASTValidator.get_code_structure_info(refactored_code)
            
            # Compare key structural elements
            orig_classes = {cls['name'] for cls in orig_info['classes']}
            ref_classes = {cls['name'] for cls in ref_info['classes']}
            
            orig_functions = {func['name'] for func in orig_info['functions']}
            ref_functions = {func['name'] for func in ref_info['functions']}
            
            # Check for missing classes or functions
            missing_classes = orig_classes - ref_classes
            missing_functions = orig_functions - ref_functions
            
            added_classes = ref_classes - orig_classes
            added_functions = ref_functions - orig_functions
            
            if missing_classes:
                comparison['changes'].append(f"Removed classes: {', '.join(missing_classes)}")
            
            if missing_functions:
                comparison['changes'].append(f"Removed functions: {', '.join(missing_functions)}")
            
            if added_classes:
                comparison['changes'].append(f"Added classes: {', '.join(added_classes)}")
            
            if added_functions:
                comparison['changes'].append(f"Added functions: {', '.join(added_functions)}")
            
            # Check if main structure is preserved
            structure_preserved = (
                len(missing_classes) == 0 and 
                len(missing_functions) == 0 and
                orig_info['has_main'] == ref_info['has_main']
            )
            
            comparison['structure_preserved'] = structure_preserved
            
            # Compare complexity
            complexity_change = ref_info['complexity_score'] - orig_info['complexity_score']
            if complexity_change > 5:
                comparison['warnings'].append("Refactored code is significantly more complex")
            elif complexity_change < -5:
                comparison['warnings'].append("Refactored code is significantly simpler")
        
        return comparison
    
    @staticmethod
    def extract_safe_code_snippet(code: str, max_lines: int = 50) -> str:
        """Extract a safe snippet of code for display purposes
        
        Args:
            code: The code to extract from
            max_lines: Maximum number of lines to include
            
        Returns:
            str: Safe code snippet
        """
        lines = code.split('\n')
        
        if len(lines) <= max_lines:
            return code
        
        # Take first portion and add truncation notice
        snippet_lines = lines[:max_lines]
        snippet = '\n'.join(snippet_lines)
        snippet += f"\n\n# ... ({len(lines) - max_lines} more lines truncated)"
        
        return snippet
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
    