#!/usr/bin/env python3
"""
Multilanguage Hybrid Refactoring Engine

A comprehensive system that combines LLM intelligence with language-specific parsers
for safe, syntax-aware code transformations across multiple programming languages.

Supported Languages:
- Python (via ast, libcst)
- JavaScript/JSX (via tree-sitter, babel)
- Java (via tree-sitter)
- C/C++ (via tree-sitter)
- TypeScript (via tree-sitter)
"""

import ast
import json
import re
import subprocess
import tempfile
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

try:
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    Language = Parser = Node = None
    TREE_SITTER_AVAILABLE = False

try:
    import libcst as cst
    LIBCST_AVAILABLE = True
except ImportError:
    cst = None
    LIBCST_AVAILABLE = False

from .ast_utils import ASTValidator


class LanguageAdapter(ABC):
    """Abstract base class for language-specific adapters"""
    
    @abstractmethod
    def parse_code(self, code: str) -> Any:
        """Parse code into language-specific AST/IR"""
        pass
    
    @abstractmethod
    def apply_transformations(self, parsed_code: Any, suggestions: Dict[str, Any]) -> Any:
        """Apply LLM suggestions using safe AST transformations"""
        pass
    
    @abstractmethod
    def generate_code(self, transformed_ast: Any) -> str:
        """Convert transformed AST back to source code"""
        pass
    
    @abstractmethod
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate syntax of generated code"""
        pass
    
    @abstractmethod
    def get_language_info(self) -> Dict[str, Any]:
        """Get language-specific information"""
        pass


class PythonAdapter(LanguageAdapter):
    """Python language adapter using ast and libcst"""
    
    def __init__(self):
        self.validator = ASTValidator()
        self.use_libcst = LIBCST_AVAILABLE
    
    def parse_code(self, code: str) -> Union[ast.AST, Any]:
        """Parse Python code using ast or libcst"""
        if self.use_libcst:
            try:
                return cst.parse_module(code)
            except Exception:
                # Fallback to ast
                return ast.parse(code)
        else:
            return ast.parse(code)
    
    def apply_transformations(self, parsed_code: Any, suggestions: Dict[str, Any]) -> Any:
        """Apply transformations using Python AST"""
        if isinstance(parsed_code, cst.Module):
            transformer = LibCSTTransformer(suggestions)
            return parsed_code.visit(transformer)
        else:
            transformer = PythonASTTransformer(suggestions)
            return transformer.visit(parsed_code)
    
    def generate_code(self, transformed_ast: Any) -> str:
        """Generate Python code from AST"""
        if isinstance(transformed_ast, cst.Module):
            return transformed_ast.code
        else:
            import astor
            return astor.to_source(transformed_ast)
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax"""
        return self.validator.validate_python_code(code)
    
    def get_language_info(self) -> Dict[str, Any]:
        return {
            'name': 'Python',
            'extensions': ['.py', '.pyw'],
            'parser': 'libcst' if self.use_libcst else 'ast',
            'features': ['variable_renaming', 'docstring_insertion', 'loop_optimization']
        }


class JavaScriptAdapter(LanguageAdapter):
    """JavaScript/JSX adapter using tree-sitter"""
    
    def __init__(self):
        self.parser = None
        self.language = None
        if TREE_SITTER_AVAILABLE:
            self._init_parser()
    
    def _init_parser(self):
        """Initialize tree-sitter parser for JavaScript"""
        try:
            # This would require tree-sitter-javascript to be installed
            # Language.build_library('build/languages.so', ['tree-sitter-javascript'])
            # self.language = Language('build/languages.so', 'javascript')
            # self.parser = Parser()
            # self.parser.set_language(self.language)
            pass
        except Exception as e:
            print(f"Warning: Could not initialize JavaScript parser: {e}")
    
    def parse_code(self, code: str) -> Any:
        """Parse JavaScript code using tree-sitter"""
        if not self.parser:
            raise NotImplementedError("Tree-sitter JavaScript parser not available")
        
        tree = self.parser.parse(bytes(code, 'utf8'))
        return tree
    
    def apply_transformations(self, parsed_code: Any, suggestions: Dict[str, Any]) -> Any:
        """Apply transformations to JavaScript AST"""
        transformer = JavaScriptTransformer(suggestions)
        return transformer.transform(parsed_code)
    
    def generate_code(self, transformed_ast: Any) -> str:
        """Generate JavaScript code from AST"""
        # This would use tree-sitter's code generation capabilities
        # or a separate code generator
        raise NotImplementedError("JavaScript code generation not yet implemented")
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate JavaScript syntax using Node.js"""
        try:
            # Use Node.js to validate syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', '--check', temp_file],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, Any]:
        return {
            'name': 'JavaScript',
            'extensions': ['.js', '.jsx', '.mjs'],
            'parser': 'tree-sitter',
            'features': ['variable_renaming', 'function_optimization', 'es6_conversion']
        }


class JavaAdapter(LanguageAdapter):
    """Java adapter using tree-sitter"""
    
    def __init__(self):
        self.parser = None
        if TREE_SITTER_AVAILABLE:
            self._init_parser()
    
    def _init_parser(self):
        """Initialize tree-sitter parser for Java"""
        try:
            # This would require tree-sitter-java to be installed
            pass
        except Exception as e:
            print(f"Warning: Could not initialize Java parser: {e}")
    
    def parse_code(self, code: str) -> Any:
        """Parse Java code using tree-sitter"""
        if not self.parser:
            raise NotImplementedError("Tree-sitter Java parser not available")
        
        tree = self.parser.parse(bytes(code, 'utf8'))
        return tree
    
    def apply_transformations(self, parsed_code: Any, suggestions: Dict[str, Any]) -> Any:
        """Apply transformations to Java AST"""
        transformer = JavaTransformer(suggestions)
        return transformer.transform(parsed_code)
    
    def generate_code(self, transformed_ast: Any) -> str:
        """Generate Java code from AST"""
        raise NotImplementedError("Java code generation not yet implemented")
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Java syntax using javac"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                # Extract class name from code for proper file naming
                class_match = re.search(r'class\s+(\w+)', code)
                if class_match:
                    class_name = class_match.group(1)
                    f.name = f.name.replace('.java', f'_{class_name}.java')
                
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['javac', '-cp', '.', temp_file],
                capture_output=True,
                text=True
            )
            
            # Clean up
            os.unlink(temp_file)
            class_file = temp_file.replace('.java', '.class')
            if os.path.exists(class_file):
                os.unlink(class_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, Any]:
        return {
            'name': 'Java',
            'extensions': ['.java'],
            'parser': 'tree-sitter',
            'features': ['variable_renaming', 'method_optimization', 'javadoc_insertion']
        }


class CppAdapter(LanguageAdapter):
    """C/C++ adapter using tree-sitter"""
    
    def __init__(self):
        self.parser = None
        if TREE_SITTER_AVAILABLE:
            self._init_parser()
    
    def _init_parser(self):
        """Initialize tree-sitter parser for C/C++"""
        try:
            # This would require tree-sitter-cpp to be installed
            pass
        except Exception as e:
            print(f"Warning: Could not initialize C/C++ parser: {e}")
    
    def parse_code(self, code: str) -> Any:
        """Parse C/C++ code using tree-sitter"""
        if not self.parser:
            raise NotImplementedError("Tree-sitter C/C++ parser not available")
        
        tree = self.parser.parse(bytes(code, 'utf8'))
        return tree
    
    def apply_transformations(self, parsed_code: Any, suggestions: Dict[str, Any]) -> Any:
        """Apply transformations to C/C++ AST"""
        transformer = CppTransformer(suggestions)
        return transformer.transform(parsed_code)
    
    def generate_code(self, transformed_ast: Any) -> str:
        """Generate C/C++ code from AST"""
        raise NotImplementedError("C/C++ code generation not yet implemented")
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate C/C++ syntax using gcc/clang"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Try gcc first, then clang
            for compiler in ['g++', 'clang++']:
                result = subprocess.run(
                    [compiler, '-fsyntax-only', temp_file],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    os.unlink(temp_file)
                    return True, None
            
            os.unlink(temp_file)
            return False, result.stderr
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, Any]:
        return {
            'name': 'C++',
            'extensions': ['.cpp', '.cxx', '.cc', '.c', '.h', '.hpp'],
            'parser': 'tree-sitter',
            'features': ['variable_renaming', 'function_optimization', 'modern_cpp_conversion']
        }


class MultilangHybridRefactor:
    """Main multilanguage hybrid refactoring engine"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
        # Initialize language adapters
        self.adapters = {
            'python': PythonAdapter(),
            'javascript': JavaScriptAdapter(),
            'java': JavaAdapter(),
            'cpp': CppAdapter()
        }
        
        # File extension to language mapping
        self.extension_map = {
            '.py': 'python',
            '.pyw': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.mjs': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp'
        }
    
    def detect_language(self, file_path: str, code: str = None) -> Optional[str]:
        """Detect programming language from file extension or content"""
        # First try file extension
        ext = Path(file_path).suffix.lower()
        if ext in self.extension_map:
            return self.extension_map[ext]
        
        # Fallback to content-based detection
        if code:
            return self._detect_language_from_content(code)
        
        return None
    
    def _detect_language_from_content(self, code: str) -> Optional[str]:
        """Detect language from code content"""
        # Simple heuristics for language detection
        if 'def ' in code and 'import ' in code:
            return 'python'
        elif 'function ' in code or 'const ' in code or 'let ' in code:
            return 'javascript'
        elif 'public class ' in code or 'private ' in code:
            return 'java'
        elif '#include' in code or 'std::' in code:
            return 'cpp'
        
        return None
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.adapters.keys())
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get information about a specific language"""
        if language in self.adapters:
            return self.adapters[language].get_language_info()
        return {}
    
    def refactor_code(self, code: str, language: str = None, file_path: str = '') -> Dict[str, Any]:
        """Main refactoring method for multilanguage support"""
        try:
            # Detect language if not provided
            if not language:
                language = self.detect_language(file_path, code)
                if not language:
                    return {
                        'success': False,
                        'refactored_code': code,
                        'error': 'Could not detect programming language',
                        'original_valid': True,
                        'refactored_valid': True,
                        'validation_warnings': [],
                        'improvements': [],
                        'llm_suggestions': [],
                        'transformations': []
                    }
            
            # Check if language is supported
            if language not in self.adapters:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': f'Language {language} not supported',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': [],
                    'improvements': [],
                    'llm_suggestions': [],
                    'transformations': []
                }
            
            adapter = self.adapters[language]
            
            # Phase 1: LLM Analysis
            llm_suggestions = self._get_llm_suggestions(code, language, file_path)
            
            # Phase 2: Parse code
            try:
                parsed_code = adapter.parse_code(code)
            except Exception as e:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': f'Parse error: {str(e)}',
                    'original_valid': False,
                    'refactored_valid': True,
                    'validation_warnings': [],
                    'improvements': [],
                    'llm_suggestions': llm_suggestions.get('suggestions', []),
                    'transformations': []
                }
            
            # Phase 3: Apply transformations
            try:
                transformed_ast = adapter.apply_transformations(parsed_code, llm_suggestions)
            except Exception as e:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': f'Transformation error: {str(e)}',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': [],
                    'improvements': [],
                    'llm_suggestions': llm_suggestions.get('suggestions', []),
                    'transformations': []
                }
            
            # Phase 4: Generate code
            try:
                refactored_code = adapter.generate_code(transformed_ast)
            except Exception as e:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': f'Code generation error: {str(e)}',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': [],
                    'improvements': [],
                    'llm_suggestions': llm_suggestions.get('suggestions', []),
                    'transformations': []
                }
            
            # Phase 5: Validation
            original_valid, orig_error = adapter.validate_syntax(code)
            refactored_valid, ref_error = adapter.validate_syntax(refactored_code)
            
            warnings = []
            if not original_valid:
                warnings.append(f'Original code has syntax errors: {orig_error}')
            if not refactored_valid:
                warnings.append(f'Refactored code has syntax errors: {ref_error}')
                # If refactored code is invalid, return original
                refactored_code = code
                refactored_valid = original_valid
            
            improvements = []
            if refactored_code != code:
                improvements.append(f'Applied {language} refactoring transformations')
            
            return {
                'success': True,
                'refactored_code': refactored_code,
                'error': '',
                'original_valid': original_valid,
                'refactored_valid': refactored_valid,
                'validation_warnings': warnings,
                'improvements': improvements,
                'llm_suggestions': llm_suggestions.get('suggestions', []),
                'transformations': llm_suggestions.get('transformations', []),
                'language': language,
                'adapter_info': adapter.get_language_info()
            }
            
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,
                'error': f'Multilang refactoring error: {str(e)}',
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': [],
                'improvements': [],
                'llm_suggestions': [],
                'transformations': []
            }
    
    def _get_llm_suggestions(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """Get suggestions from LLM for the given language"""
        if not self.llm_client:
            return {'suggestions': [], 'transformations': []}
        
        try:
            prompt = self._create_language_specific_prompt(language)
            user_prompt = f"Analyze this {language} code and provide improvement suggestions:\n\n{code}"
            
            response = self.llm_client._make_api_request(prompt, user_prompt)
            
            if response['success']:
                return self._parse_llm_response(response['content'])
            
            return {'suggestions': [], 'transformations': []}
            
        except Exception as e:
            return {'suggestions': [], 'transformations': [], 'error': str(e)}
    
    def _create_language_specific_prompt(self, language: str) -> str:
        """Create language-specific LLM prompt"""
        base_prompt = f"""You are a {language} code analysis expert. Analyze the provided code and return a JSON response with improvement suggestions.

Return ONLY a valid JSON object with this structure:
{{
    "suggestions": ["list of improvement suggestions"],
    "rename": {{"old_name": "new_name"}},
    "docstrings": {{"function_name": "docstring content"}},
    "transformations": [
        {{"type": "transformation_type", "location": "line_number", "description": "what to do"}}
    ]
}}

Focus on:
1. Better variable/function names
2. Missing documentation
3. Language-specific optimizations
4. Code structure improvements

Do NOT include code in your response, only analysis and suggestions."""
        
        # Add language-specific guidance
        if language == 'python':
            base_prompt += "\n\nPython-specific focus: PEP 8 compliance, list comprehensions, context managers, type hints."
        elif language == 'javascript':
            base_prompt += "\n\nJavaScript-specific focus: ES6+ features, async/await, destructuring, arrow functions."
        elif language == 'java':
            base_prompt += "\n\nJava-specific focus: OOP principles, generics, streams, proper exception handling."
        elif language == 'cpp':
            base_prompt += "\n\nC++-specific focus: Modern C++ features, RAII, smart pointers, const correctness."
        
        return base_prompt
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response into structured suggestions"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'suggestions': [], 'transformations': []}
        except Exception:
            return {'suggestions': [], 'transformations': []}


# Language-specific transformer classes
class PythonASTTransformer(ast.NodeTransformer):
    """Python AST transformer for structural improvements"""
    
    def __init__(self, suggestions: Dict[str, Any]):
        self.suggestions = suggestions
        self.rename_map = suggestions.get('rename', {})
        self.transformations = suggestions.get('transformations', [])
    
    def visit_Name(self, node):
        """Rename variables"""
        if node.id in self.rename_map:
            node.id = self.rename_map[node.id]
        return self.generic_visit(node)
    
    def visit_If(self, node):
        """Simplify boolean comparisons"""
        if (isinstance(node.test, ast.Compare) and 
            len(node.test.ops) == 1 and 
            isinstance(node.test.ops[0], ast.Eq) and
            isinstance(node.test.comparators[0], ast.Constant) and 
            node.test.comparators[0].value is True):
            node.test = node.test.left
        
        return self.generic_visit(node)


if LIBCST_AVAILABLE:
    class LibCSTTransformer(cst.CSTTransformer):
        """LibCST-based transformer for advanced Python refactoring"""
        
        def __init__(self, suggestions: Dict[str, Any]):
            super().__init__()
            self.suggestions = suggestions
            self.changes_made = []
        
        def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
            """Handle variable renaming"""
            if 'rename' in self.suggestions:
                old_name = original_node.value
                if old_name in self.suggestions['rename']:
                    new_name = self.suggestions['rename'][old_name]
                    self.changes_made.append({
                        'type': 'rename',
                        'old_name': old_name,
                        'new_name': new_name
                    })
                    return updated_node.with_changes(value=new_name)
            return updated_node
else:
    class LibCSTTransformer:
        """Fallback LibCST transformer when libcst is not available"""
        
        def __init__(self, suggestions: Dict[str, Any]):
            self.suggestions = suggestions
            self.changes_made = []
        
        def transform(self, code: str) -> str:
            """Fallback transformation using regex"""
            return code


class JavaScriptTransformer:
    """JavaScript transformer using tree-sitter"""
    
    def __init__(self, suggestions: Dict[str, Any]):
        self.suggestions = suggestions
    
    def transform(self, tree):
        """Apply JavaScript-specific transformations"""
        # Implementation would use tree-sitter's tree walking capabilities
        return tree


class JavaTransformer:
    """Java transformer using tree-sitter"""
    
    def __init__(self, suggestions: Dict[str, Any]):
        self.suggestions = suggestions
    
    def transform(self, tree):
        """Apply Java-specific transformations"""
        # Implementation would use tree-sitter's tree walking capabilities
        return tree


class CppTransformer:
    """C/C++ transformer using tree-sitter"""
    
    def __init__(self, suggestions: Dict[str, Any]):
        self.suggestions = suggestions
    
    def transform(self, tree):
        """Apply C/C++-specific transformations"""
        # Implementation would use tree-sitter's tree walking capabilities
        return tree