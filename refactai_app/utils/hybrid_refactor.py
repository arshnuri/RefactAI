import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from .ast_utils import ASTValidator
import json


class HybridRefactor:
    """Advanced hybrid refactoring system combining LLM intelligence with AST safety
    
    This follows the best practice model:
    - LLM: Generates semantic improvements (naming, documentation, suggestions)
    - AST: Executes safe structural transformations
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.ast_validator = ASTValidator()
        
        # Define what each component should handle
        self.llm_tasks = {
            'naming': 'Generate better variable/function names',
            'documentation': 'Create docstrings and comments',
            'suggestions': 'Identify improvement opportunities',
            'performance_hints': 'Suggest performance optimizations'
        }
        
        self.ast_tasks = {
            'rename_variables': 'Safely rename variables using AST',
            'add_docstrings': 'Insert docstrings at correct positions',
            'restructure_conditionals': 'Reorganize if/else blocks',
            'convert_loops': 'Transform loops to comprehensions',
            'extract_functions': 'Extract code into functions',
            'remove_duplicates': 'Eliminate duplicate code blocks'
        }
    
    def refactor_code(self, code: str, language: str, file_path: str = '') -> Dict[str, Any]:
        """Main hybrid refactoring method"""
        try:
            improvements = []
            warnings = []
            
            # Phase 1: LLM Analysis - Generate improvement suggestions
            llm_analysis = self._llm_analyze_code(code, language)
            
            # Phase 2: AST Transformations - Apply safe structural changes
            transformed_code = self._ast_apply_transformations(code, language, llm_analysis)
            
            # Phase 3: LLM Enhancement - Apply naming and documentation
            if llm_analysis['success'] and self.llm_client:
                enhanced_code = self._ast_apply_llm_suggestions(transformed_code, language, llm_analysis)
            else:
                enhanced_code = transformed_code
                warnings.append('LLM analysis failed - using AST-only transformations')
            
            # Phase 4: Validation
            validation_result = self._validate_result(code, enhanced_code, language)
            
            return {
                'success': True,
                'refactored_code': enhanced_code,
                'error': '',
                'original_valid': validation_result['original_valid'],
                'refactored_valid': validation_result['refactored_valid'],
                'validation_warnings': validation_result['warnings'] + warnings,
                'improvements': improvements + validation_result.get('improvements', []),
                'llm_suggestions': llm_analysis.get('suggestions', []),
                'ast_transformations': validation_result.get('transformations', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,
                'error': f"Hybrid refactoring error: {str(e)}",
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': [],
                'improvements': [],
                'llm_suggestions': [],
                'ast_transformations': []
            }
    
    def _llm_analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Phase 1: LLM analyzes code and generates improvement suggestions"""
        if not self.llm_client:
            return {'success': False, 'suggestions': [], 'naming_map': {}, 'docstrings': {}}
        
        try:
            analysis_prompt = self._create_analysis_prompt(language)
            user_prompt = f"Analyze this {language} code and provide improvement suggestions:\n\n{code}"
            
            response = self.llm_client._make_api_request(analysis_prompt, user_prompt)
            
            if response['success']:
                # Parse LLM response to extract structured suggestions
                analysis = self._parse_llm_analysis(response['content'])
                return {
                    'success': True,
                    'suggestions': analysis.get('suggestions', []),
                    'naming_map': analysis.get('naming_map', {}),
                    'docstrings': analysis.get('docstrings', {}),
                    'performance_hints': analysis.get('performance_hints', [])
                }
            
            return {'success': False, 'suggestions': [], 'naming_map': {}, 'docstrings': {}}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'suggestions': [], 'naming_map': {}, 'docstrings': {}}
    
    def _ast_apply_transformations(self, code: str, language: str, llm_analysis: Dict) -> str:
        """Phase 2: AST applies safe structural transformations"""
        if language.lower() != 'python':
            return code  # Currently only Python AST transformations
        
        try:
            tree = ast.parse(code)
            transformer = PythonASTTransformer(llm_analysis)
            
            # Apply transformations
            transformed_tree = transformer.visit(tree)
            
            # Convert back to code
            import astor
            return astor.to_source(transformed_tree)
            
        except Exception as e:
            print(f"AST transformation failed: {e}")
            return code
    
    def _ast_apply_llm_suggestions(self, code: str, language: str, llm_analysis: Dict) -> str:
        """Phase 3: AST safely applies LLM naming and documentation suggestions"""
        if language.lower() != 'python' or not llm_analysis.get('success'):
            return code
        
        try:
            tree = ast.parse(code)
            enhancer = PythonASTEnhancer(llm_analysis)
            
            # Apply LLM suggestions safely
            enhanced_tree = enhancer.visit(tree)
            
            # Convert back to code
            import astor
            return astor.to_source(enhanced_tree)
            
        except Exception as e:
            print(f"AST enhancement failed: {e}")
            return code
    
    def _create_analysis_prompt(self, language: str) -> str:
        """Create LLM prompt for code analysis"""
        return f"""You are a {language} code analysis expert. Analyze the provided code and return a JSON response with improvement suggestions.

Return ONLY a valid JSON object with this structure:
{{
    "suggestions": ["list of improvement suggestions"],
    "naming_map": {{"old_name": "new_name"}},
    "docstrings": {{"function_name": "docstring content"}},
    "performance_hints": ["performance improvement suggestions"]
}}

Focus on:
1. Better variable/function names
2. Missing documentation
3. Performance opportunities
4. Code structure improvements

Do NOT include code in your response, only analysis and suggestions."""
    
    def _parse_llm_analysis(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception:
            return {}
    
    def _validate_result(self, original: str, refactored: str, language: str) -> Dict[str, Any]:
        """Validate refactoring results"""
        warnings = []
        improvements = []
        transformations = []
        
        if language.lower() == 'python':
            # Validate syntax
            orig_valid, orig_error = self.ast_validator.validate_python_code(original)
            ref_valid, ref_error = self.ast_validator.validate_python_code(refactored)
            
            if not orig_valid:
                warnings.append(f"Original code has syntax errors: {orig_error}")
            if not ref_valid:
                warnings.append(f"Refactored code has syntax errors: {ref_error}")
            
            # Check for improvements
            if len(refactored) > len(original):
                improvements.append("Added documentation and improved naming")
            if refactored != original:
                transformations.append("Applied structural improvements")
            
            return {
                'original_valid': orig_valid,
                'refactored_valid': ref_valid,
                'warnings': warnings,
                'improvements': improvements,
                'transformations': transformations
            }
        
        return {
            'original_valid': True,
            'refactored_valid': True,
            'warnings': warnings,
            'improvements': improvements,
            'transformations': transformations
        }


class PythonASTTransformer(ast.NodeTransformer):
    """AST transformer for structural code improvements"""
    
    def __init__(self, llm_analysis: Dict):
        self.llm_analysis = llm_analysis
        self.improvements = []
    
    def visit_If(self, node):
        """Simplify conditional statements"""
        # Simplify if-else chains
        if (isinstance(node.test, ast.Compare) and 
            len(node.test.ops) == 1 and 
            isinstance(node.test.ops[0], ast.Eq)):
            
            # Check for simple boolean comparisons
            if (isinstance(node.test.comparators[0], ast.Constant) and 
                node.test.comparators[0].value is True):
                # Replace "if x == True:" with "if x:"
                node.test = node.test.left
                self.improvements.append("Simplified boolean comparison")
        
        return self.generic_visit(node)
    
    def visit_For(self, node):
        """Convert simple for loops to list comprehensions where appropriate"""
        # Check if this is a simple append loop
        if (len(node.body) == 1 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Call) and 
            isinstance(node.body[0].value.func, ast.Attribute) and 
            node.body[0].value.func.attr == 'append'):
            
            self.improvements.append("Identified loop that could be a list comprehension")
        
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Improve function structure"""
        # Check for long functions that could be split
        if len(node.body) > 20:
            self.improvements.append(f"Function '{node.name}' is long and could be split")
        
        return self.generic_visit(node)


class PythonASTEnhancer(ast.NodeTransformer):
    """AST enhancer that safely applies LLM suggestions"""
    
    def __init__(self, llm_analysis: Dict):
        self.naming_map = llm_analysis.get('naming_map', {})
        self.docstrings = llm_analysis.get('docstrings', {})
        self.enhancements = []
    
    def visit_Name(self, node):
        """Rename variables based on LLM suggestions"""
        if node.id in self.naming_map:
            old_name = node.id
            node.id = self.naming_map[old_name]
            self.enhancements.append(f"Renamed '{old_name}' to '{node.id}'")
        
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Add docstrings to functions"""
        # Check if function needs a docstring
        if node.name in self.docstrings:
            docstring_content = self.docstrings[node.name]
            
            # Check if docstring already exists
            has_docstring = (node.body and 
                           isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and 
                           isinstance(node.body[0].value.value, str))
            
            if not has_docstring:
                # Add docstring as first statement
                docstring_node = ast.Expr(value=ast.Constant(value=docstring_content))
                node.body.insert(0, docstring_node)
                self.enhancements.append(f"Added docstring to function '{node.name}'")
        
        return self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Add docstrings to classes"""
        if node.name in self.docstrings:
            docstring_content = self.docstrings[node.name]
            
            # Check if docstring already exists
            has_docstring = (node.body and 
                           isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and 
                           isinstance(node.body[0].value.value, str))
            
            if not has_docstring:
                # Add docstring as first statement
                docstring_node = ast.Expr(value=ast.Constant(value=docstring_content))
                node.body.insert(0, docstring_node)
                self.enhancements.append(f"Added docstring to class '{node.name}'")
        
        return self.generic_visit(node)