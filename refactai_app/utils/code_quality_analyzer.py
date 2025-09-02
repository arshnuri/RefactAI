import ast
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class CodeQualityAnalyzer:
    """Analyzes code quality metrics for various programming languages"""
    
    def __init__(self):
        self.language_analyzers = {
            'python': self._analyze_python,
            'javascript': self._analyze_javascript,
            'java': self._analyze_java,
            'cpp': self._analyze_cpp,
            'c': self._analyze_cpp,
        }
    
    def analyze_code(self, code: str, language: str) -> Dict[str, int]:
        """Analyze code and return quality metrics"""
        language = language.lower()
        
        if language in self.language_analyzers:
            return self.language_analyzers[language](code)
        else:
            return self._analyze_generic(code)
    
    def _analyze_python(self, code: str) -> Dict[str, int]:
        """Analyze Python code quality"""
        try:
            tree = ast.parse(code)
            
            # Calculate complexity
            complexity = self._calculate_python_complexity(tree)
            
            # Calculate readability
            readability = self._calculate_python_readability(code, tree)
            
            # Calculate maintainability
            maintainability = self._calculate_python_maintainability(code, tree)
            
            return {
                'complexity': min(100, max(65, 100 - complexity * 2)),
                'readability': readability,
                'maintainability': maintainability
            }
        except SyntaxError:
            # If code has syntax errors, return low scores
            return {'complexity': 65, 'readability': 20, 'maintainability': 25}
    
    def _calculate_python_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python code"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_python_readability(self, code: str, tree: ast.AST) -> int:
        """Calculate readability score for Python code"""
        score = 100
        lines = code.split('\n')
        
        # Check line length
        long_lines = sum(1 for line in lines if len(line) > 100)
        score -= long_lines * 2
        
        # Check for comments
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio < 0.1:
                score -= 15
            elif comment_ratio > 0.3:
                score += 10
        
        # Check function/class naming
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.islower() or '__' in node.name:
                    score -= 3
            elif isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    score -= 3
        
        return max(0, min(100, score))
    
    def _calculate_python_maintainability(self, code: str, tree: ast.AST) -> int:
        """Calculate maintainability score for Python code"""
        score = 100
        
        # Check function length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                if func_lines > 50:
                    score -= 10
                elif func_lines > 30:
                    score -= 5
        
        # Check for docstrings
        functions_with_docstrings = 0
        total_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    functions_with_docstrings += 1
        
        if total_functions > 0:
            docstring_ratio = functions_with_docstrings / total_functions
            if docstring_ratio < 0.5:
                score -= 15
            elif docstring_ratio > 0.8:
                score += 10
        
        return max(0, min(100, score))
    
    def _analyze_javascript(self, code: str) -> Dict[str, int]:
        """Analyze JavaScript code quality"""
        lines = code.split('\n')
        
        # Basic complexity analysis
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch']
        complexity = sum(line.count(keyword) for line in lines for keyword in complexity_keywords)
        complexity_score = min(100, max(65, 100 - complexity * 3))
        
        # Readability analysis
        readability = 100
        long_lines = sum(1 for line in lines if len(line) > 120)
        readability -= long_lines * 3
        
        # Check for comments
        comment_lines = sum(1 for line in lines if '//' in line or '/*' in line)
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0 and comment_lines / total_lines < 0.1:
            readability -= 20
        
        # Maintainability analysis
        maintainability = 100
        function_count = code.count('function') + code.count('=>')
        if function_count == 0:
            maintainability -= 20
        
        # Check for var usage (prefer let/const)
        var_count = len(re.findall(r'\bvar\s+', code))
        maintainability -= var_count * 5
        
        return {
            'complexity': max(65, min(100, complexity_score)),
            'readability': max(0, min(100, readability)),
            'maintainability': max(0, min(100, maintainability))
        }
    
    def _analyze_java(self, code: str) -> Dict[str, int]:
        """Analyze Java code quality"""
        lines = code.split('\n')
        
        # Complexity analysis
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch']
        complexity = sum(line.count(keyword) for line in lines for keyword in complexity_keywords)
        complexity_score = min(100, max(65, 100 - complexity * 2))
        
        # Readability analysis
        readability = 100
        long_lines = sum(1 for line in lines if len(line) > 100)
        readability -= long_lines * 2
        
        # Check for comments
        comment_lines = sum(1 for line in lines if '//' in line or '/*' in line or '*' in line.strip())
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0 and comment_lines / total_lines < 0.15:
            readability -= 15
        
        # Maintainability analysis
        maintainability = 100
        
        # Check for proper naming conventions
        class_pattern = re.findall(r'class\s+([A-Z][a-zA-Z0-9]*)', code)
        method_pattern = re.findall(r'(public|private|protected)\s+\w+\s+([a-z][a-zA-Z0-9]*)', code)
        
        if len(class_pattern) > 0:
            maintainability += 10
        if len(method_pattern) > 0:
            maintainability += 5
        
        return {
            'complexity': max(65, min(100, complexity_score)),
            'readability': max(0, min(100, readability)),
            'maintainability': max(0, min(100, maintainability))
        }
    
    def _analyze_cpp(self, code: str) -> Dict[str, int]:
        """Analyze C/C++ code quality"""
        lines = code.split('\n')
        
        # Complexity analysis
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case']
        complexity = sum(line.count(keyword) for line in lines for keyword in complexity_keywords)
        complexity_score = min(100, max(65, 100 - complexity * 2))
        
        # Readability analysis
        readability = 100
        long_lines = sum(1 for line in lines if len(line) > 100)
        readability -= long_lines * 2
        
        # Check for comments
        comment_lines = sum(1 for line in lines if '//' in line or '/*' in line)
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0 and comment_lines / total_lines < 0.1:
            readability -= 20
        
        # Maintainability analysis
        maintainability = 100
        
        # Check for includes
        include_count = sum(1 for line in lines if line.strip().startswith('#include'))
        if include_count > 10:
            maintainability -= 10
        
        # Check for proper function definitions
        function_count = len(re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*{', code))
        if function_count > 0:
            maintainability += 10
        
        return {
            'complexity': max(65, min(100, complexity_score)),
            'readability': max(0, min(100, readability)),
            'maintainability': max(0, min(100, maintainability))
        }
    
    def _analyze_generic(self, code: str) -> Dict[str, int]:
        """Generic analysis for unsupported languages"""
        lines = code.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        # Basic metrics
        complexity = min(100, max(65, 100 - total_lines // 10))
        readability = min(100, max(40, 90 - len([line for line in lines if len(line) > 120]) * 5))
        maintainability = min(100, max(45, 85 - total_lines // 20))
        
        return {
            'complexity': complexity,
            'readability': readability,
            'maintainability': maintainability
        }
    
    def calculate_overall_score(self, metrics: Dict[str, int]) -> int:
        """Calculate overall quality score from individual metrics"""
        weights = {
            'complexity': 0.4,
            'readability': 0.3,
            'maintainability': 0.3
        }
        
        overall = sum(metrics[key] * weights[key] for key in weights if key in metrics)
        return int(round(overall))
    
    def detect_nested_if_statements(self, code: str, language: str) -> List[Dict[str, any]]:
        """Detect deeply nested if statements that need refactoring"""
        language = language.lower()
        
        if language == 'python':
            return self._detect_python_nested_ifs(code)
        elif language == 'java':
            return self._detect_java_nested_ifs(code)
        elif language == 'javascript':
            return self._detect_javascript_nested_ifs(code)
        else:
            return self._detect_generic_nested_ifs(code)
    
    def _detect_python_nested_ifs(self, code: str) -> List[Dict[str, any]]:
        """Detect nested if statements in Python code using AST"""
        try:
            tree = ast.parse(code)
            nested_ifs = []
            
            def analyze_node(node, depth=0, parent_info=None):
                if isinstance(node, ast.If):
                    # Count nested depth
                    nested_depth = self._count_nested_depth(node)
                    
                    if nested_depth >= 3:  # 3 or more levels of nesting
                        line_start = getattr(node, 'lineno', 0)
                        line_end = getattr(node, 'end_lineno', line_start)
                        
                        nested_ifs.append({
                            'type': 'deeply_nested_if',
                            'line_start': line_start,
                            'line_end': line_end,
                            'depth': nested_depth,
                            'suggestion': 'Extract nested conditions into separate functions or use guard clauses',
                            'severity': 'high' if nested_depth >= 4 else 'medium',
                            'pattern': 'nested_conditionals'
                        })
                
                # Recursively analyze child nodes
                for child in ast.iter_child_nodes(node):
                    analyze_node(child, depth + 1, node)
            
            analyze_node(tree)
            return nested_ifs
            
        except SyntaxError:
            return []
    
    def _count_nested_depth(self, if_node: ast.If) -> int:
        """Count the maximum nesting depth of if statements"""
        max_depth = 1
        
        def count_depth(node, current_depth=1):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.If):
                    count_depth(child, current_depth + 1)
                else:
                    count_depth(child, current_depth)
        
        count_depth(if_node)
        return max_depth
    
    def _detect_java_nested_ifs(self, code: str) -> List[Dict[str, any]]:
        """Detect nested if statements in Java code using regex patterns"""
        lines = code.split('\n')
        nested_ifs = []
        
        # Track brace depth and if statements
        brace_depth = 0
        if_stack = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Count braces
            brace_depth += stripped.count('{') - stripped.count('}')
            
            # Detect if statements
            if re.search(r'\bif\s*\(', stripped):
                if_stack.append({'line': i, 'depth': brace_depth})
            
            # Check for deeply nested if statements
            if len(if_stack) >= 3:
                nested_ifs.append({
                    'type': 'deeply_nested_if',
                    'line_start': if_stack[0]['line'],
                    'line_end': i,
                    'depth': len(if_stack),
                    'suggestion': 'Extract nested conditions into separate methods or use early returns',
                    'severity': 'high' if len(if_stack) >= 4 else 'medium',
                    'pattern': 'nested_conditionals'
                })
            
            # Clean up stack when braces close
            if '}' in stripped:
                if_stack = [item for item in if_stack if item['depth'] <= brace_depth]
        
        return nested_ifs
    
    def _detect_javascript_nested_ifs(self, code: str) -> List[Dict[str, any]]:
        """Detect nested if statements in JavaScript code"""
        lines = code.split('\n')
        nested_ifs = []
        
        # Track brace depth and if statements
        brace_depth = 0
        if_stack = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Count braces
            brace_depth += stripped.count('{') - stripped.count('}')
            
            # Detect if statements
            if re.search(r'\bif\s*\(', stripped):
                if_stack.append({'line': i, 'depth': brace_depth})
            
            # Check for deeply nested if statements
            if len(if_stack) >= 3:
                nested_ifs.append({
                    'type': 'deeply_nested_if',
                    'line_start': if_stack[0]['line'],
                    'line_end': i,
                    'depth': len(if_stack),
                    'suggestion': 'Extract nested conditions into separate functions or use early returns',
                    'severity': 'high' if len(if_stack) >= 4 else 'medium',
                    'pattern': 'nested_conditionals'
                })
            
            # Clean up stack when braces close
            if '}' in stripped:
                if_stack = [item for item in if_stack if item['depth'] <= brace_depth]
        
        return nested_ifs
    
    def _detect_generic_nested_ifs(self, code: str) -> List[Dict[str, any]]:
        """Generic detection for unsupported languages"""
        lines = code.split('\n')
        nested_ifs = []
        
        # Simple pattern matching for if statements
        if_pattern = re.compile(r'\bif\b')
        indent_stack = []
        
        for i, line in enumerate(lines, 1):
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            
            if if_pattern.search(line):
                # Clean stack based on indentation
                indent_stack = [item for item in indent_stack if item['indent'] < indent]
                indent_stack.append({'line': i, 'indent': indent})
                
                # Check for deep nesting
                if len(indent_stack) >= 3:
                    nested_ifs.append({
                        'type': 'deeply_nested_if',
                        'line_start': indent_stack[0]['line'],
                        'line_end': i,
                        'depth': len(indent_stack),
                        'suggestion': 'Consider refactoring nested conditions',
                        'severity': 'medium',
                        'pattern': 'nested_conditionals'
                    })
        
        return nested_ifs
    
    def suggest_refactoring_for_nested_ifs(self, code: str, language: str, nested_ifs: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Generate specific refactoring suggestions for nested if statements"""
        suggestions = []
        
        for nested_if in nested_ifs:
            if language.lower() == 'python':
                suggestions.append(self._generate_python_refactor_suggestion(code, nested_if))
            elif language.lower() == 'java':
                suggestions.append(self._generate_java_refactor_suggestion(code, nested_if))
            elif language.lower() == 'javascript':
                suggestions.append(self._generate_javascript_refactor_suggestion(code, nested_if))
            else:
                suggestions.append(self._generate_generic_refactor_suggestion(code, nested_if))
        
        return suggestions
    
    def _generate_python_refactor_suggestion(self, code: str, nested_if: Dict[str, any]) -> Dict[str, any]:
        """Generate Python-specific refactoring suggestion"""
        lines = code.split('\n')
        start_line = nested_if['line_start'] - 1
        end_line = min(nested_if['line_end'], len(lines))
        
        problematic_code = '\n'.join(lines[start_line:end_line])
        
        return {
            'type': 'extract_method',
            'original_code': problematic_code,
            'suggestion': 'Extract nested conditions into separate functions with descriptive names',
            'example': '''# Instead of:
if condition1:
    if condition2:
        if condition3:
            do_something()

# Use:
def is_valid_scenario(data):
    return condition1 and condition2 and condition3

if is_valid_scenario(data):
    do_something()''',
            'benefits': ['Improved readability', 'Better testability', 'Reduced complexity'],
            'line_range': (nested_if['line_start'], nested_if['line_end'])
        }
    
    def _generate_java_refactor_suggestion(self, code: str, nested_if: Dict[str, any]) -> Dict[str, any]:
        """Generate Java-specific refactoring suggestion"""
        return {
            'type': 'extract_method',
            'suggestion': 'Extract nested conditions into private methods with meaningful names',
            'example': '''// Instead of:
if (condition1) {
    if (condition2) {
        if (condition3) {
            doSomething();
        }
    }
}

// Use:
private boolean isValidScenario() {
    return condition1 && condition2 && condition3;
}

if (isValidScenario()) {
    doSomething();
}''',
            'benefits': ['Improved readability', 'Better testability', 'Reduced cyclomatic complexity'],
            'line_range': (nested_if['line_start'], nested_if['line_end'])
        }
    
    def _generate_javascript_refactor_suggestion(self, code: str, nested_if: Dict[str, any]) -> Dict[str, any]:
        """Generate JavaScript-specific refactoring suggestion"""
        return {
            'type': 'extract_function',
            'suggestion': 'Extract nested conditions into separate functions or use early returns',
            'example': '''// Instead of:
if (condition1) {
    if (condition2) {
        if (condition3) {
            doSomething();
        }
    }
}

// Use:
function isValidScenario() {
    return condition1 && condition2 && condition3;
}

if (isValidScenario()) {
    doSomething();
}''',
            'benefits': ['Improved readability', 'Better maintainability', 'Easier debugging'],
            'line_range': (nested_if['line_start'], nested_if['line_end'])
        }
    
    def _generate_generic_refactor_suggestion(self, code: str, nested_if: Dict[str, any]) -> Dict[str, any]:
        """Generate generic refactoring suggestion"""
        return {
            'type': 'simplify_conditionals',
            'suggestion': 'Consider simplifying nested conditional logic',
            'benefits': ['Improved readability', 'Reduced complexity'],
            'line_range': (nested_if['line_start'], nested_if['line_end'])
        }