#!/usr/bin/env python3
"""
JavaScript/JSX Language Adapter

Provides JavaScript and JSX-specific parsing, transformation, and code generation.
Uses tree-sitter for parsing and Node.js for syntax validation.
"""

import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = Parser = Node = None

from ..logger import RefactorLogger, LogLevel, OperationType


@dataclass
class JavaScriptSymbol:
    """JavaScript symbol information"""
    name: str
    type: str  # function, class, variable, import, export
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    is_async: bool = False
    is_arrow: bool = False
    is_export: bool = False
    is_default_export: bool = False
    parent: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


class JavaScriptTreeSitterParser:
    """Tree-sitter based JavaScript parser"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.parser = None
        self.language = None
        
        if not TREE_SITTER_AVAILABLE:
            if logger:
                logger.log(
                    LogLevel.WARNING, OperationType.VALIDATION,
                    "tree-sitter not available - JavaScript parsing limited"
                )
            return
        
        try:
            # Try to load JavaScript language
            # Note: In practice, you'd need to build the tree-sitter JavaScript grammar
            # This is a placeholder for the actual implementation
            self._setup_parser()
        except Exception as e:
            if logger:
                logger.log_error(OperationType.VALIDATION, e, 
                                context={'component': 'tree-sitter-javascript'})
    
    def _setup_parser(self):
        """Setup tree-sitter parser for JavaScript"""
        # This would require building tree-sitter-javascript
        # For now, we'll use a placeholder
        if TREE_SITTER_AVAILABLE:
            self.parser = Parser()
            # self.language = Language('path/to/tree-sitter-javascript.so', 'javascript')
            # self.parser.set_language(self.language)
    
    def parse(self, code: str) -> Optional[Node]:
        """Parse JavaScript code"""
        if not self.parser:
            return None
        
        try:
            tree = self.parser.parse(bytes(code, 'utf8'))
            return tree.root_node
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return None
    
    def extract_symbols(self, root_node: Node, code: str) -> List[JavaScriptSymbol]:
        """Extract symbols from tree-sitter AST"""
        symbols = []
        
        def traverse_node(node: Node, parent_name: str = None):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbol = JavaScriptSymbol(
                        name=code[name_node.start_byte:name_node.end_byte],
                        type='function',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        parent=parent_name
                    )
                    symbols.append(symbol)
            
            elif node.type == 'arrow_function':
                # Handle arrow functions
                symbol = JavaScriptSymbol(
                    name='<anonymous>',
                    type='function',
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    column_start=node.start_point[1],
                    column_end=node.end_point[1],
                    is_arrow=True,
                    parent=parent_name
                )
                symbols.append(symbol)
            
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = code[name_node.start_byte:name_node.end_byte]
                    symbol = JavaScriptSymbol(
                        name=class_name,
                        type='class',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        parent=parent_name
                    )
                    symbols.append(symbol)
                    
                    # Traverse class body with class name as parent
                    for child in node.children:
                        traverse_node(child, class_name)
                    return
            
            elif node.type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbol = JavaScriptSymbol(
                        name=code[name_node.start_byte:name_node.end_byte],
                        type='variable',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        parent=parent_name
                    )
                    symbols.append(symbol)
            
            # Traverse children
            for child in node.children:
                traverse_node(child, parent_name)
        
        traverse_node(root_node)
        return symbols


class JavaScriptTransformer:
    """JavaScript code transformer"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.changes_made = []
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """Log message if logger available"""
        if self.logger:
            self.logger.log(level, OperationType.TRANSFORMATION, message, **kwargs)
    
    def rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Rename variable in JavaScript code"""
        # Simple regex-based replacement (in practice, use AST)
        import re
        
        # Pattern to match variable names (word boundaries)
        pattern = r'\b' + re.escape(old_name) + r'\b'
        
        # Replace with new name
        new_code = re.sub(pattern, new_name, code)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'rename_variable',
                'old_name': old_name,
                'new_name': new_name
            })
            self.log(LogLevel.INFO, f"Renamed variable '{old_name}' to '{new_name}'")
        
        return new_code
    
    def add_jsdoc(self, code: str, function_name: str, jsdoc: str) -> str:
        """Add JSDoc comment to function"""
        import re
        
        # Pattern to find function declaration
        patterns = [
            rf'(function\s+{re.escape(function_name)}\s*\([^)]*\)\s*{{)',
            rf'(const\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*{{)',
            rf'(let\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*{{)',
            rf'(var\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*{{)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                # Insert JSDoc before function
                jsdoc_comment = f"/**\n * {jsdoc}\n */\n"
                new_code = code[:match.start()] + jsdoc_comment + code[match.start():]
                
                self.changes_made.append({
                    'type': 'add_jsdoc',
                    'function_name': function_name,
                    'jsdoc': jsdoc
                })
                self.log(LogLevel.INFO, f"Added JSDoc to function '{function_name}'")
                
                return new_code
        
        self.log(LogLevel.WARNING, f"Function '{function_name}' not found for JSDoc addition")
        return code
    
    def convert_var_to_const_let(self, code: str) -> str:
        """Convert var declarations to const/let"""
        import re
        
        # Simple heuristic: if variable is reassigned, use let; otherwise const
        # This is a simplified implementation
        
        lines = code.split('\n')
        new_lines = []
        
        for line in lines:
            # Replace var with let (simplified)
            if re.match(r'^\s*var\s+', line):
                new_line = re.sub(r'^(\s*)var\s+', r'\1let ', line)
                new_lines.append(new_line)
                
                self.changes_made.append({
                    'type': 'var_to_let',
                    'line': line.strip()
                })
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def add_async_await(self, code: str, function_name: str) -> str:
        """Convert function to async/await pattern"""
        import re
        
        # Pattern to find function and make it async
        pattern = rf'(function\s+{re.escape(function_name)}\s*\([^)]*\))'
        replacement = rf'async \1'
        
        new_code = re.sub(pattern, replacement, code)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'add_async',
                'function_name': function_name
            })
            self.log(LogLevel.INFO, f"Made function '{function_name}' async")
        
        return new_code
    
    def modernize_syntax(self, code: str) -> str:
        """Modernize JavaScript syntax"""
        # Apply multiple modernization transformations
        code = self.convert_var_to_const_let(code)
        
        # Add more modernization rules here
        # - Convert function expressions to arrow functions
        # - Use template literals instead of string concatenation
        # - Use destructuring assignments
        # etc.
        
        return code


class JavaScriptAdapter:
    """Main JavaScript language adapter"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.parser = JavaScriptTreeSitterParser(logger)
        self.transformer = JavaScriptTransformer(logger)
        self.node_path = self._find_node_executable()
        
        if not self.node_path and logger:
            logger.log(
                LogLevel.WARNING, OperationType.VALIDATION,
                "Node.js not found - JavaScript syntax validation disabled"
            )
    
    def _find_node_executable(self) -> Optional[str]:
        """Find Node.js executable"""
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'node'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try common paths
        common_paths = [
            'node.exe',
            'C:\\Program Files\\nodejs\\node.exe',
            '/usr/bin/node',
            '/usr/local/bin/node'
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
    
    def parse_code(self, code: str) -> Optional[Node]:
        """Parse JavaScript code"""
        return self.parser.parse(code)
    
    def extract_symbols(self, code: str) -> List[JavaScriptSymbol]:
        """Extract symbols from JavaScript code"""
        try:
            root_node = self.parse_code(code)
            if root_node:
                symbols = self.parser.extract_symbols(root_node, code)
            else:
                # Fallback to regex-based extraction
                symbols = self._extract_symbols_regex(code)
            
            if self.logger:
                self.logger.log(
                    LogLevel.DEBUG, OperationType.TRANSFORMATION,
                    f"Extracted {len(symbols)} symbols from JavaScript code"
                )
            
            return symbols
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return []
    
    def _extract_symbols_regex(self, code: str) -> List[JavaScriptSymbol]:
        """Fallback regex-based symbol extraction"""
        import re
        symbols = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function declarations
            func_match = re.search(r'function\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append(JavaScriptSymbol(
                    name=func_match.group(1),
                    type='function',
                    line_start=i,
                    line_end=i,
                    column_start=func_match.start(1),
                    column_end=func_match.end(1)
                ))
            
            # Arrow functions with names
            arrow_match = re.search(r'(const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>', line)
            if arrow_match:
                symbols.append(JavaScriptSymbol(
                    name=arrow_match.group(2),
                    type='function',
                    line_start=i,
                    line_end=i,
                    column_start=arrow_match.start(2),
                    column_end=arrow_match.end(2),
                    is_arrow=True
                ))
            
            # Class declarations
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                symbols.append(JavaScriptSymbol(
                    name=class_match.group(1),
                    type='class',
                    line_start=i,
                    line_end=i,
                    column_start=class_match.start(1),
                    column_end=class_match.end(1)
                ))
        
        return symbols
    
    def apply_transformations(self, code: str, suggestions: Dict[str, Any]) -> str:
        """Apply transformations based on LLM suggestions"""
        try:
            refactored_code = code
            
            # Apply rename transformations
            if 'rename' in suggestions:
                for old_name, new_name in suggestions['rename'].items():
                    refactored_code = self.transformer.rename_variable(
                        refactored_code, old_name, new_name
                    )
            
            # Apply JSDoc additions
            if 'docstring' in suggestions:
                for func_info in suggestions['docstring']:
                    if isinstance(func_info, dict):
                        func_name = func_info.get('function')
                        doc = func_info.get('doc')
                        if func_name and doc:
                            refactored_code = self.transformer.add_jsdoc(
                                refactored_code, func_name, doc
                            )
            
            # Apply specific transformations
            if 'transformations' in suggestions:
                for transform in suggestions['transformations']:
                    transform_type = transform.get('type')
                    
                    if transform_type == 'modernize_syntax':
                        refactored_code = self.transformer.modernize_syntax(refactored_code)
                    
                    elif transform_type == 'add_async':
                        func_name = transform.get('function_name')
                        if func_name:
                            refactored_code = self.transformer.add_async_await(
                                refactored_code, func_name
                            )
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Applied {len(self.transformer.changes_made)} JavaScript transformations"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate JavaScript syntax using Node.js"""
        if not self.node_path:
            # Fallback to basic validation
            return self._basic_syntax_check(code)
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Use Node.js to check syntax
                result = subprocess.run(
                    [self.node_path, '--check', temp_file],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    return True, None
                else:
                    error_msg = result.stderr.strip()
                    if self.logger:
                        self.logger.log(
                            LogLevel.ERROR, OperationType.VALIDATION,
                            f"JavaScript syntax error: {error_msg}"
                        )
                    return False, error_msg
            
            finally:
                # Clean up temp file
                Path(temp_file).unlink(missing_ok=True)
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.VALIDATION, e)
            return False, str(e)
    
    def _basic_syntax_check(self, code: str) -> Tuple[bool, Optional[str]]:
        """Basic syntax check without Node.js"""
        # Very basic checks
        try:
            # Check for balanced braces
            brace_count = code.count('{') - code.count('}')
            if brace_count != 0:
                return False, f"Unbalanced braces: {brace_count}"
            
            # Check for balanced parentheses
            paren_count = code.count('(') - code.count(')')
            if paren_count != 0:
                return False, f"Unbalanced parentheses: {paren_count}"
            
            # Check for balanced brackets
            bracket_count = code.count('[') - code.count(']')
            if bracket_count != 0:
                return False, f"Unbalanced brackets: {bracket_count}"
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    def format_code(self, code: str) -> str:
        """Format JavaScript code"""
        try:
            # Try to use prettier if available
            if self.node_path:
                try:
                    # Check if prettier is available
                    result = subprocess.run(
                        [self.node_path, '-e', 'require("prettier")'],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if result.returncode == 0:
                        # Use prettier to format
                        format_script = f'''
                        const prettier = require("prettier");
                        const code = {json.dumps(code)};
                        console.log(prettier.format(code, {{ parser: "babel" }}));
                        '''
                        
                        result = subprocess.run(
                            [self.node_path, '-e', format_script],
                            capture_output=True, text=True, timeout=10
                        )
                        
                        if result.returncode == 0:
                            return result.stdout.strip()
                
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Fallback to basic formatting
            return self._basic_format(code)
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code
    
    def _basic_format(self, code: str) -> str:
        """Basic code formatting"""
        # Very basic formatting
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
            
            # Add indentation
            formatted_line = '  ' * indent_level + stripped
            formatted_lines.append(formatted_line)
            
            # Increase indent for opening braces
            if stripped.endswith('{'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def get_complexity_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        try:
            lines = code.split('\n')
            
            # Basic metrics
            lines_of_code = len([line for line in lines if line.strip()])
            function_count = code.count('function ') + code.count('=>')
            class_count = code.count('class ')
            
            # Cyclomatic complexity (simplified)
            complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', '&&', '||']
            cyclomatic_complexity = 1  # Base complexity
            
            for keyword in complexity_keywords:
                cyclomatic_complexity += code.count(keyword)
            
            return {
                'cyclomatic_complexity': cyclomatic_complexity,
                'lines_of_code': lines_of_code,
                'function_count': function_count,
                'class_count': class_count
            }
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return {}
    
    def get_language(self) -> str:
        """Get language identifier"""
        return "javascript"
    
    def get_file_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return [".js", ".jsx", ".mjs", ".ts", ".tsx"]
    
    def supports_file(self, file_path: str) -> bool:
        """Check if file is supported"""
        return Path(file_path).suffix.lower() in self.get_file_extensions()
    
    def is_jsx_file(self, file_path: str) -> bool:
        """Check if file is JSX"""
        return Path(file_path).suffix.lower() in [".jsx", ".tsx"]
    
    def is_typescript_file(self, file_path: str) -> bool:
        """Check if file is TypeScript"""
        return Path(file_path).suffix.lower() in [".ts", ".tsx"]