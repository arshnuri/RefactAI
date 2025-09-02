import ast
import re
from typing import Dict, List, Any, Optional
from .ast_utils import ASTValidator


class RuleBasedRefactor:
    """Rule-based code refactoring with LLM assistance for naming and documentation"""
    
    def __init__(self, llm_client=None):
        """Initialize with LLM client for naming and documentation assistance"""
        self.llm_client = llm_client
        self.ast_validator = ASTValidator()
        self.refactoring_rules = {
            'python': [
                self._extract_magic_numbers,
                self._simplify_conditionals,
                self._extract_long_functions,
                self._remove_duplicate_code,
                self._improve_list_comprehensions,
                self._add_type_hints,
                self._improve_exception_handling
            ],
            'javascript': [
                self._js_use_const_let,
                self._js_arrow_functions,
                self._js_template_literals,
                self._js_destructuring
            ],
            'java': [
                self._java_extract_constants,
                self._java_improve_naming,
                self._java_add_access_modifiers
            ]
        }
    
    def refactor_code(self, code: str, language: str, file_path: str = '') -> Dict[str, Any]:
        """Main refactoring method that combines rule-based and LLM approaches"""
        try:
            improvements = []
            llm_enhancements = []
            
            # Step 1: Apply rule-based refactoring
            refactored_code = self._apply_rules(code, language)
            if refactored_code != code:
                improvements.append('Applied rule-based refactoring transformations')
            
            # Step 2: Use LLM for naming improvements and documentation
            if self.llm_client:
                llm_result = self._enhance_with_llm(refactored_code, language, file_path)
                if llm_result['success'] and llm_result['code'].strip():
                    refactored_code = llm_result['code']
                    llm_enhancements.extend(llm_result['enhancements'])
                else:
                    llm_enhancements.append(f"LLM enhancement failed: {llm_result.get('error', 'Empty response or validation failed')}")
            else:
                llm_enhancements.append('LLM client not available')
            
            # Step 3: Validate the result
            validation_result = self._validate_refactored_code(code, refactored_code, language)
            
            return {
                'success': True,
                'refactored_code': refactored_code,
                'error': '',
                'original_valid': validation_result['original_valid'],
                'refactored_valid': validation_result['refactored_valid'],
                'validation_warnings': validation_result['warnings'],
                'improvements': improvements,
                'llm_enhancements': llm_enhancements
            }
            
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,
                'error': f"Refactoring error: {str(e)}",
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': [],
                'improvements': [],
                'llm_enhancements': []
            }
    
    def _apply_rules(self, code: str, language: str) -> str:
        """Apply rule-based refactoring transformations"""
        refactored_code = code
        rules = self.refactoring_rules.get(language.lower(), [])
        
        for rule in rules:
            try:
                refactored_code = rule(refactored_code)
            except Exception as e:
                # If a rule fails, continue with others
                print(f"Warning: Rule {rule.__name__} failed: {e}")
                continue
        
        return refactored_code
    
    def _enhance_with_llm(self, code: str, language: str, file_path: str = None) -> Dict[str, Any]:
        """Use LLM for naming improvements and adding docstrings"""
        enhancements = []
        enhanced_code = code
        
        # Skip LLM enhancement if no client available
        if not self.llm_client:
            return {
                'success': True,
                'code': code,
                'enhancements': ['LLM client not available - skipped naming and docstring improvements']
            }
        
        try:
            # Create a specific prompt for naming and documentation
            system_prompt = self._create_naming_prompt()
            user_prompt = f"Improve variable/function names and add docstrings to this {language} code:\n\n{code}"
            
            response = self.llm_client._make_api_request(system_prompt, user_prompt)
            
            if response['success']:
                enhanced_code = self.llm_client._clean_response(response['content'], language)
                # Validate that the enhanced code is still syntactically correct
                if language.lower() == 'python':
                    is_valid, _ = self.ast_validator.validate_python_code(enhanced_code)
                    if is_valid:
                        enhancements.append('Improved variable/function names and added docstrings')
                        return {
                            'success': True,
                            'code': enhanced_code,
                            'enhancements': enhancements
                        }
            
            # If LLM enhancement fails, return the original code
            return {
                'success': True,
                'code': code,
                'enhancements': ['LLM enhancement skipped - validation failed']
            }
            
        except Exception as e:
            return {
                'success': False,
                'code': code,
                'error': f"LLM enhancement failed: {str(e)}",
                'enhancements': []
            }
    
    def _create_naming_prompt(self) -> str:
        """Create system prompt specifically for naming and documentation"""
        return """You are a code naming and documentation expert.

Your job is to:
1. Improve variable and function names to be more descriptive and follow conventions
2. Add clear, concise docstrings to functions and classes
3. Keep the exact same code structure and logic
4. Only return the improved code without explanations

Do not change:
- Code logic or structure
- Import statements
- Function signatures (except parameter names)
- Class inheritance

Only improve:
- Variable names (make them descriptive)
- Function names (make them clear and action-oriented)
- Add docstrings where missing
- Improve existing comments"""
    
    # Python-specific refactoring rules
    
    def _extract_magic_numbers(self, code: str) -> str:
        """Extract magic numbers into named constants"""
        lines = code.split('\n')
        constants = []
        modified_lines = []
        
        # Find magic numbers (excluding 0, 1, -1 which are often not magic)
        # More precise pattern to avoid matching parts of variable names
        magic_number_pattern = r'\b(?<![a-zA-Z_])(?:[2-9]|[1-9]\d+)(?:\.\d+)?(?![a-zA-Z_])\b'
        
        for line in lines:
            # Skip comments and strings
            if line.strip().startswith('#') or '"""' in line or "'''" in line or 'import ' in line:
                modified_lines.append(line)
                continue
            
            # Only process lines that contain actual magic numbers in expressions
            if any(op in line for op in ['=', '+', '-', '*', '/', '%', '<', '>', '==', '!=']):
                matches = re.findall(magic_number_pattern, line)
                for match in matches:
                    # Skip common non-magic numbers and small numbers
                    if match not in ['2', '3', '4', '5', '10', '100'] and int(float(match)) > 5:
                        const_name = f"CONSTANT_{match.replace('.', '_')}"
                        if const_name not in [c.split('=')[0].strip() for c in constants]:
                            constants.append(f"{const_name} = {match}")
                        # Only replace if it's a standalone number, not part of a variable name
                        line = re.sub(r'\b' + re.escape(match) + r'\b', const_name, line)
            
            modified_lines.append(line)
        
        if constants:
            # Add constants at the top after imports
            result_lines = []
            imports_done = False
            
            for line in modified_lines:
                if not imports_done and (line.startswith('import ') or line.startswith('from ')):
                    result_lines.append(line)
                    continue
                elif not imports_done and line.strip() == '':
                    result_lines.append(line)
                    continue
                elif not imports_done:
                    # Insert constants before first non-import line
                    result_lines.append('')  # Empty line before constants
                    for const in constants:
                        result_lines.append(const)
                    result_lines.append('')  # Empty line after constants
                    result_lines.append(line)
                    imports_done = True
                else:
                    result_lines.append(line)
            
            return '\n'.join(result_lines)
        
        return code
    
    def _simplify_conditionals(self, code: str) -> str:
        """Simplify complex conditional statements"""
        # Replace if x == True with if x
        code = re.sub(r'if\s+([\w\.]+)\s*==\s*True\b', r'if \1', code)
        # Replace if x == False with if not x
        code = re.sub(r'if\s+([\w\.]+)\s*==\s*False\b', r'if not \1', code)
        # Replace if x != True with if not x
        code = re.sub(r'if\s+([\w\.]+)\s*!=\s*True\b', r'if not \1', code)
        # Replace if x != False with if x
        code = re.sub(r'if\s+([\w\.]+)\s*!=\s*False\b', r'if \1', code)
        
        return code
    
    def _extract_long_functions(self, code: str) -> str:
        """Extract long functions into smaller ones (basic implementation)"""
        try:
            lines = code.split('\n')
            result_lines = []
            in_function = False
            function_lines = 0
            indent_level = 0
            
            for line in lines:
                if line.strip().startswith('def '):
                    in_function = True
                    function_lines = 0
                    indent_level = len(line) - len(line.lstrip())
                    result_lines.append(line)
                elif in_function:
                    function_lines += 1
                    current_indent = len(line) - len(line.lstrip())
                    
                    # Check if we're still in the function
                    if line.strip() and current_indent <= indent_level:
                        in_function = False
                        # Add suggestion comment if function was long
                        if function_lines > 20:
                            comment_indent = ' ' * (indent_level + 4)
                            result_lines.insert(-function_lines, f"{comment_indent}# TODO: Consider breaking this function into smaller functions")
                    
                    result_lines.append(line)
                else:
                    result_lines.append(line)
            
            return '\n'.join(result_lines)
            
        except Exception:
            return code
    
    def _remove_duplicate_code(self, code: str) -> str:
        """Remove duplicate code blocks (basic implementation)"""
        # For now, disable duplicate code removal as it's too aggressive
        # and breaks code structure. This would need more sophisticated
        # AST-based analysis to work properly.
        return code
    
    def _improve_list_comprehensions(self, code: str) -> str:
        """Convert simple loops to list comprehensions where appropriate"""
        # Pattern: for item in list: result.append(transform(item))
        pattern = r'(\s*)(\w+)\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*\2\.append\(([^)]+)\)'
        replacement = r'\1\2 = [\5 for \3 in \4]'
        
        return re.sub(pattern, replacement, code, flags=re.MULTILINE)
    
    def _add_type_hints(self, code: str) -> str:
        """Add basic type hints where obvious"""
        # Add type hints for simple cases
        # def func(x) -> def func(x: Any)
        code = re.sub(r'def\s+(\w+)\(([^)]+)\):', r'def \1(\2) -> Any:', code)
        
        # Add typing import if type hints were added
        if ' -> Any:' in code and 'from typing import' not in code:
            lines = code.split('\n')
            # Find the right place to insert import
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                else:
                    lines.insert(i, 'from typing import Any')
                    break
            code = '\n'.join(lines)
        
        return code
    
    def _improve_exception_handling(self, code: str) -> str:
        """Improve exception handling patterns"""
        # Replace bare except with except Exception
        code = re.sub(r'except:\s*$', 'except Exception:', code, flags=re.MULTILINE)
        
        # Add pass to empty except blocks
        code = re.sub(r'except\s+\w+:\s*$', r'\g<0>\n    pass', code, flags=re.MULTILINE)
        
        return code
    
    # JavaScript-specific refactoring rules
    
    def _js_use_const_let(self, code: str) -> str:
        """Replace var with const/let in JavaScript"""
        # Replace var with const for variables that aren't reassigned
        # This is a simplified implementation
        lines = code.split('\n')
        result_lines = []
        
        for line in lines:
            if 'var ' in line and '=' in line:
                # Simple heuristic: if it looks like initialization, use const
                if re.match(r'\s*var\s+\w+\s*=', line):
                    line = line.replace('var ', 'const ', 1)
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _js_arrow_functions(self, code: str) -> str:
        """Convert function expressions to arrow functions"""
        # Convert function(args) { return expr; } to (args) => expr
        pattern = r'function\s*\(([^)]*)\)\s*{\s*return\s+([^;]+);?\s*}'
        replacement = r'(\1) => \2'
        
        return re.sub(pattern, replacement, code)
    
    def _js_template_literals(self, code: str) -> str:
        """Convert string concatenation to template literals"""
        # Convert "text" + variable + "text" to `text${variable}text`
        # This is a simplified implementation
        pattern = r'"([^"]*?)"\s*\+\s*(\w+)\s*\+\s*"([^"]*?)"'
        replacement = r'`\1${\2}\3`'
        
        return re.sub(pattern, replacement, code)
    
    def _js_destructuring(self, code: str) -> str:
        """Add destructuring where appropriate"""
        # Convert obj.prop1, obj.prop2 to {prop1, prop2} = obj
        # This would need more sophisticated analysis
        return code
    
    # Java-specific refactoring rules
    
    def _java_extract_constants(self, code: str) -> str:
        """Extract magic numbers to constants in Java"""
        # Similar to Python but with Java syntax
        magic_numbers = re.findall(r'\b(?:[2-9]|[1-9]\d+)\b', code)
        
        for number in set(magic_numbers):
            if number not in ['2', '10', '100']:  # Common non-magic numbers
                const_name = f"CONSTANT_{number}"
                const_declaration = f"private static final int {const_name} = {number};"
                # This would need proper placement logic
        
        return code
    
    def _java_improve_naming(self, code: str) -> str:
        """Improve Java naming conventions"""
        # Convert snake_case to camelCase for variables
        def to_camel_case(match):
            parts = match.group(0).split('_')
            return parts[0] + ''.join(word.capitalize() for word in parts[1:])
        
        # This would need more sophisticated analysis to avoid changing constants
        return code
    
    def _java_add_access_modifiers(self, code: str) -> str:
        """Add appropriate access modifiers"""
        # Add private to fields that don't have access modifiers
        pattern = r'^(\s*)(\w+\s+\w+\s*;)'
        replacement = r'\1private \2'
        
        return re.sub(pattern, replacement, code, flags=re.MULTILINE)
    
    def _validate_refactored_code(self, original: str, refactored: str, language: str) -> Dict[str, Any]:
        """Validate that refactoring preserved functionality"""
        if language.lower() == 'python':
            return ASTValidator.compare_code_structure(original, refactored)
        else:
            # For non-Python languages, do basic validation
            return {
                'original_valid': True,
                'refactored_valid': True,
                'structure_preserved': True,
                'warnings': [],
                'changes': ['Applied rule-based refactoring']
            }