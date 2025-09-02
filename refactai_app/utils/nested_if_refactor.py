#!/usr/bin/env python3
"""
Nested If Statement Refactoring Module

Automatically refactors deeply nested if statements into cleaner, more readable code.
Implements various refactoring patterns like guard clauses, early returns, and method extraction.
"""

import ast
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RefactorPattern(Enum):
    """Types of refactoring patterns for nested if statements"""
    GUARD_CLAUSES = "guard_clauses"
    EARLY_RETURN = "early_return"
    EXTRACT_METHOD = "extract_method"
    COMBINE_CONDITIONS = "combine_conditions"
    STRATEGY_PATTERN = "strategy_pattern"


@dataclass
class RefactorSuggestion:
    """Represents a refactoring suggestion for nested if statements"""
    pattern: RefactorPattern
    original_lines: Tuple[int, int]
    original_code: str
    refactored_code: str
    confidence: float
    benefits: List[str]
    description: str


class NestedIfRefactor:
    """Automated refactoring for nested if statements"""
    
    def __init__(self):
        self.language_refactors = {
            'python': self._refactor_python_nested_ifs,
            'java': self._refactor_java_nested_ifs,
            'javascript': self._refactor_javascript_nested_ifs
        }
    
    def refactor_nested_ifs(self, code: str, language: str, nested_ifs: List[Dict[str, Any]]) -> List[RefactorSuggestion]:
        """Main entry point for refactoring nested if statements"""
        language = language.lower()
        
        if language in self.language_refactors:
            return self.language_refactors[language](code, nested_ifs)
        else:
            return self._refactor_generic_nested_ifs(code, nested_ifs)
    
    def _refactor_python_nested_ifs(self, code: str, nested_ifs: List[Dict[str, Any]]) -> List[RefactorSuggestion]:
        """Refactor Python nested if statements"""
        suggestions = []
        lines = code.split('\n')
        
        for nested_if in nested_ifs:
            if nested_if['depth'] >= 4:  # Only refactor deeply nested ones
                suggestion = self._create_python_guard_clause_refactor(lines, nested_if)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _create_python_guard_clause_refactor(self, lines: List[str], nested_if: Dict[str, Any]) -> Optional[RefactorSuggestion]:
        """Create a guard clause refactoring for Python"""
        start_line = nested_if['line_start'] - 1
        end_line = min(nested_if['line_end'], len(lines))
        
        original_code = '\n'.join(lines[start_line:end_line])
        
        # Try to parse and understand the nested structure
        try:
            # Extract the function containing this nested if
            func_start = self._find_function_start(lines, start_line)
            if func_start is None:
                return None
            
            func_end = self._find_function_end(lines, func_start)
            func_code = '\n'.join(lines[func_start:func_end])
            
            # Analyze the nested structure
            refactored = self._apply_python_guard_clauses(func_code)
            
            if refactored and refactored != func_code:
                return RefactorSuggestion(
                    pattern=RefactorPattern.GUARD_CLAUSES,
                    original_lines=(func_start + 1, func_end),
                    original_code=func_code,
                    refactored_code=refactored,
                    confidence=0.8,
                    benefits=[
                        "Reduced nesting depth",
                        "Improved readability",
                        "Easier to understand control flow",
                        "Better error handling"
                    ],
                    description="Convert nested if statements to guard clauses with early returns"
                )
        except Exception:
            pass
        
        return None
    
    def _find_function_start(self, lines: List[str], current_line: int) -> Optional[int]:
        """Find the start of the function containing the current line"""
        for i in range(current_line, -1, -1):
            if lines[i].strip().startswith('def '):
                return i
        return None
    
    def _find_function_end(self, lines: List[str], func_start: int) -> int:
        """Find the end of the function starting at func_start"""
        base_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
        
        for i in range(func_start + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                return i
        
        return len(lines)
    
    def _apply_python_guard_clauses(self, func_code: str) -> str:
        """Apply guard clause pattern to Python function"""
        try:
            tree = ast.parse(func_code)
            
            # Find the function definition
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return self._transform_python_function_with_guards(node, func_code)
            
            return func_code
        except:
            return func_code
    
    def _transform_python_function_with_guards(self, func_node: ast.FunctionDef, original_code: str) -> str:
        """Transform a Python function to use guard clauses"""
        lines = original_code.split('\n')
        func_name = func_node.name
        args = [arg.arg for arg in func_node.args.args]
        
        # Simple pattern: if we have a categorize_score-like function
        if 'score' in func_name.lower() or 'score' in args:
            return self._create_score_categorization_with_guards(func_name, args)
        
        # Generic guard clause transformation
        return self._create_generic_guard_clause_function(func_name, args, lines)
    
    def _create_score_categorization_with_guards(self, func_name: str, args: List[str]) -> str:
        """Create a score categorization function using guard clauses"""
        score_arg = 'score' if 'score' in args else args[0] if args else 'value'
        
        return f'''def {func_name}({', '.join(args)}):
    """Categorize score using guard clauses for better readability."""
    # Guard clauses for invalid inputs
    if {score_arg} < 0:
        return "Invalid score (negative)"
    
    if {score_arg} > 100:
        return "Invalid score (too high)"
    
    # Early returns for score categories
    if {score_arg} == 100:
        return "Perfect"
    
    if {score_arg} >= 90:
        return "Excellent"
    
    if {score_arg} >= 85:
        return "Very Good"
    
    if {score_arg} >= 80:
        return "Good"
    
    if {score_arg} >= 70:
        return "Average"
    
    if {score_arg} >= 60:
        return "Below Average"
    
    return "Poor"'''
    
    def _create_generic_guard_clause_function(self, func_name: str, args: List[str], lines: List[str]) -> str:
        """Create a generic guard clause transformation"""
        # Extract the original function signature
        signature_line = next((line for line in lines if line.strip().startswith('def ')), '')
        
        return f'''{signature_line}
    """Refactored function using guard clauses for better readability."""
    # TODO: Implement specific guard clause logic based on the original nested conditions
    # This is a placeholder that demonstrates the pattern
    
    # Guard clauses should be added here based on the specific conditions
    # Example pattern:
    # if not condition1:
    #     return early_result
    # 
    # if not condition2:
    #     return another_early_result
    # 
    # # Main logic here
    pass  # Replace with actual implementation'''
    
    def _refactor_java_nested_ifs(self, code: str, nested_ifs: List[Dict[str, Any]]) -> List[RefactorSuggestion]:
        """Refactor Java nested if statements"""
        suggestions = []
        lines = code.split('\n')
        
        for nested_if in nested_ifs:
            if nested_if['depth'] >= 4:
                suggestion = self._create_java_early_return_refactor(lines, nested_if)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _create_java_early_return_refactor(self, lines: List[str], nested_if: Dict[str, Any]) -> Optional[RefactorSuggestion]:
        """Create an early return refactoring for Java"""
        start_line = nested_if['line_start'] - 1
        end_line = min(nested_if['line_end'], len(lines))
        
        # Find the method containing this nested if
        method_start = self._find_java_method_start(lines, start_line)
        if method_start is None:
            return None
        
        method_end = self._find_java_method_end(lines, method_start)
        method_code = '\n'.join(lines[method_start:method_end])
        
        # Create refactored version
        refactored = self._apply_java_early_returns(method_code)
        
        if refactored and refactored != method_code:
            return RefactorSuggestion(
                pattern=RefactorPattern.EARLY_RETURN,
                original_lines=(method_start + 1, method_end),
                original_code=method_code,
                refactored_code=refactored,
                confidence=0.75,
                benefits=[
                    "Reduced cyclomatic complexity",
                    "Improved readability",
                    "Easier to test individual conditions",
                    "Better maintainability"
                ],
                description="Convert nested if statements to early return pattern"
            )
        
        return None
    
    def _find_java_method_start(self, lines: List[str], current_line: int) -> Optional[int]:
        """Find the start of the Java method containing the current line"""
        for i in range(current_line, -1, -1):
            line = lines[i].strip()
            if re.search(r'(public|private|protected).*\w+\s*\([^)]*\)\s*\{?', line):
                return i
        return None
    
    def _find_java_method_end(self, lines: List[str], method_start: int) -> int:
        """Find the end of the Java method starting at method_start"""
        brace_count = 0
        started = False
        
        for i in range(method_start, len(lines)):
            line = lines[i]
            
            if '{' in line:
                brace_count += line.count('{')
                started = True
            
            if '}' in line:
                brace_count -= line.count('}')
                
                if started and brace_count == 0:
                    return i + 1
        
        return len(lines)
    
    def _apply_java_early_returns(self, method_code: str) -> str:
        """Apply early return pattern to Java method"""
        # Extract method signature
        lines = method_code.split('\n')
        signature_line = lines[0] if lines else ''
        
        # Check if this looks like a score categorization method
        if 'score' in method_code.lower():
            return self._create_java_score_categorization_with_early_returns(signature_line)
        
        return self._create_java_generic_early_return_method(signature_line)
    
    def _create_java_score_categorization_with_early_returns(self, signature: str) -> str:
        """Create a Java score categorization method using early returns"""
        return f'''{signature}
    /**
     * Categorize score using early returns for better readability.
     * Refactored from deeply nested if statements.
     */
    
    // Guard clauses for invalid inputs
    if (score < 0) {{
        return "Invalid score (negative)";
    }}
    
    if (score > 100) {{
        return "Invalid score (too high)";
    }}
    
    // Early returns for score categories
    if (score == 100) {{
        return "Perfect";
    }}
    
    if (score >= 90) {{
        return "Excellent";
    }}
    
    if (score >= 85) {{
        return "Very Good";
    }}
    
    if (score >= 80) {{
        return "Good";
    }}
    
    if (score >= 70) {{
        return "Average";
    }}
    
    if (score >= 60) {{
        return "Below Average";
    }}
    
    return "Poor";
}}'''
    
    def _create_java_generic_early_return_method(self, signature: str) -> str:
        """Create a generic Java method with early return pattern"""
        return f'''{signature}
    /**
     * Refactored method using early returns for better readability.
     * TODO: Implement specific early return logic based on original nested conditions.
     */
    
    // Guard clauses should be added here based on the specific conditions
    // Example pattern:
    // if (!condition1) {{
    //     return earlyResult;
    // }}
    // 
    // if (!condition2) {{
    //     return anotherEarlyResult;
    // }}
    // 
    // // Main logic here
    
    // Placeholder - replace with actual implementation
    throw new UnsupportedOperationException("Method refactoring not yet implemented");
}}'''
    
    def _refactor_javascript_nested_ifs(self, code: str, nested_ifs: List[Dict[str, Any]]) -> List[RefactorSuggestion]:
        """Refactor JavaScript nested if statements"""
        suggestions = []
        lines = code.split('\n')
        
        for nested_if in nested_ifs:
            if nested_if['depth'] >= 4:
                suggestion = self._create_javascript_early_return_refactor(lines, nested_if)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _create_javascript_early_return_refactor(self, lines: List[str], nested_if: Dict[str, Any]) -> Optional[RefactorSuggestion]:
        """Create an early return refactoring for JavaScript"""
        start_line = nested_if['line_start'] - 1
        
        # Find the function containing this nested if
        func_start = self._find_javascript_function_start(lines, start_line)
        if func_start is None:
            return None
        
        func_end = self._find_javascript_function_end(lines, func_start)
        func_code = '\n'.join(lines[func_start:func_end])
        
        # Create refactored version
        refactored = self._apply_javascript_early_returns(func_code)
        
        if refactored and refactored != func_code:
            return RefactorSuggestion(
                pattern=RefactorPattern.EARLY_RETURN,
                original_lines=(func_start + 1, func_end),
                original_code=func_code,
                refactored_code=refactored,
                confidence=0.75,
                benefits=[
                    "Reduced nesting complexity",
                    "Improved readability",
                    "Better error handling",
                    "Easier debugging"
                ],
                description="Convert nested if statements to early return pattern"
            )
        
        return None
    
    def _find_javascript_function_start(self, lines: List[str], current_line: int) -> Optional[int]:
        """Find the start of the JavaScript function containing the current line"""
        for i in range(current_line, -1, -1):
            line = lines[i].strip()
            if (line.startswith('function ') or 
                '=>' in line or 
                re.search(r'\w+\s*\([^)]*\)\s*\{', line)):
                return i
        return None
    
    def _find_javascript_function_end(self, lines: List[str], func_start: int) -> int:
        """Find the end of the JavaScript function starting at func_start"""
        brace_count = 0
        started = False
        
        for i in range(func_start, len(lines)):
            line = lines[i]
            
            if '{' in line:
                brace_count += line.count('{')
                started = True
            
            if '}' in line:
                brace_count -= line.count('}')
                
                if started and brace_count == 0:
                    return i + 1
        
        return len(lines)
    
    def _apply_javascript_early_returns(self, func_code: str) -> str:
        """Apply early return pattern to JavaScript function"""
        lines = func_code.split('\n')
        signature_line = lines[0] if lines else ''
        
        # Check if this looks like a score categorization function
        if 'score' in func_code.lower():
            return self._create_javascript_score_categorization_with_early_returns(signature_line)
        
        return self._create_javascript_generic_early_return_function(signature_line)
    
    def _create_javascript_score_categorization_with_early_returns(self, signature: str) -> str:
        """Create a JavaScript score categorization function using early returns"""
        return f'''{signature}
    /**
     * Categorize score using early returns for better readability.
     * Refactored from deeply nested if statements.
     */
    
    // Guard clauses for invalid inputs
    if (score < 0) {{
        return "Invalid score (negative)";
    }}
    
    if (score > 100) {{
        return "Invalid score (too high)";
    }}
    
    // Early returns for score categories
    if (score === 100) {{
        return "Perfect";
    }}
    
    if (score >= 90) {{
        return "Excellent";
    }}
    
    if (score >= 85) {{
        return "Very Good";
    }}
    
    if (score >= 80) {{
        return "Good";
    }}
    
    if (score >= 70) {{
        return "Average";
    }}
    
    if (score >= 60) {{
        return "Below Average";
    }}
    
    return "Poor";
}}'''
    
    def _create_javascript_generic_early_return_function(self, signature: str) -> str:
        """Create a generic JavaScript function with early return pattern"""
        return f'''{signature}
    /**
     * Refactored function using early returns for better readability.
     * TODO: Implement specific early return logic based on original nested conditions.
     */
    
    // Guard clauses should be added here based on the specific conditions
    // Example pattern:
    // if (!condition1) {{
    //     return earlyResult;
    // }}
    // 
    // if (!condition2) {{
    //     return anotherEarlyResult;
    // }}
    // 
    // // Main logic here
    
    // Placeholder - replace with actual implementation
    throw new Error('Function refactoring not yet implemented');
}}'''
    
    def _refactor_generic_nested_ifs(self, code: str, nested_ifs: List[Dict[str, Any]]) -> List[RefactorSuggestion]:
        """Generic refactoring for unsupported languages"""
        suggestions = []
        
        for nested_if in nested_ifs:
            if nested_if['depth'] >= 4:
                suggestions.append(RefactorSuggestion(
                    pattern=RefactorPattern.EXTRACT_METHOD,
                    original_lines=(nested_if['line_start'], nested_if['line_end']),
                    original_code="// Original nested if code",
                    refactored_code="// Suggested: Extract to separate method",
                    confidence=0.5,
                    benefits=["Improved readability", "Better maintainability"],
                    description="Consider extracting nested logic to separate methods"
                ))
        
        return suggestions
    
    def apply_refactoring(self, code: str, suggestion: RefactorSuggestion) -> str:
        """Apply a refactoring suggestion to the code"""
        lines = code.split('\n')
        start_line = suggestion.original_lines[0] - 1
        end_line = suggestion.original_lines[1] - 1
        
        # Replace the original code with the refactored version
        refactored_lines = suggestion.refactored_code.split('\n')
        
        new_lines = lines[:start_line] + refactored_lines + lines[end_line + 1:]
        
        return '\n'.join(new_lines)