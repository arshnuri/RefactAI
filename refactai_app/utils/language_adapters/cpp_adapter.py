#!/usr/bin/env python3
"""
C/C++ Language Adapter

Provides C and C++-specific parsing, transformation, and code generation.
Uses tree-sitter for parsing and gcc/clang for syntax validation.
"""

import subprocess
import tempfile
import re
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
class CppSymbol:
    """C/C++ symbol information"""
    name: str
    type: str  # function, class, struct, enum, variable, macro, namespace
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    is_static: bool = False
    is_const: bool = False
    is_inline: bool = False
    is_virtual: bool = False
    is_template: bool = False
    visibility: str = "public"  # public, private, protected (for C++ classes)
    parent: Optional[str] = None
    namespace: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    template_params: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.template_params is None:
            self.template_params = []


class CppTreeSitterParser:
    """Tree-sitter based C/C++ parser"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.c_parser = None
        self.cpp_parser = None
        self.c_language = None
        self.cpp_language = None
        
        if not TREE_SITTER_AVAILABLE:
            if logger:
                logger.log(
                    LogLevel.WARNING, OperationType.VALIDATION,
                    "tree-sitter not available - C/C++ parsing limited"
                )
            return
        
        try:
            # Try to load C and C++ languages
            self._setup_parsers()
        except Exception as e:
            if logger:
                logger.log_error(OperationType.VALIDATION, e, 
                                context={'component': 'tree-sitter-c-cpp'})
    
    def _setup_parsers(self):
        """Setup tree-sitter parsers for C and C++"""
        if TREE_SITTER_AVAILABLE:
            # C parser
            self.c_parser = Parser()
            # self.c_language = Language('path/to/tree-sitter-c.so', 'c')
            # self.c_parser.set_language(self.c_language)
            
            # C++ parser
            self.cpp_parser = Parser()
            # self.cpp_language = Language('path/to/tree-sitter-cpp.so', 'cpp')
            # self.cpp_parser.set_language(self.cpp_language)
    
    def parse(self, code: str, is_cpp: bool = True) -> Optional[Node]:
        """Parse C/C++ code"""
        parser = self.cpp_parser if is_cpp else self.c_parser
        if not parser:
            return None
        
        try:
            tree = parser.parse(bytes(code, 'utf8'))
            return tree.root_node
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return None
    
    def extract_symbols(self, root_node: Node, code: str, is_cpp: bool = True) -> List[CppSymbol]:
        """Extract symbols from tree-sitter AST"""
        symbols = []
        current_namespace = None
        current_class = None
        
        def get_modifiers(node: Node) -> Dict[str, Any]:
            """Extract modifiers from a node"""
            modifiers = {
                'is_static': False,
                'is_const': False,
                'is_inline': False,
                'is_virtual': False,
                'visibility': 'public'
            }
            
            # Look for modifier keywords in the node text
            node_text = code[node.start_byte:node.end_byte]
            modifiers['is_static'] = 'static' in node_text
            modifiers['is_const'] = 'const' in node_text
            modifiers['is_inline'] = 'inline' in node_text
            modifiers['is_virtual'] = 'virtual' in node_text
            
            if 'private:' in node_text or 'private ' in node_text:
                modifiers['visibility'] = 'private'
            elif 'protected:' in node_text or 'protected ' in node_text:
                modifiers['visibility'] = 'protected'
            
            return modifiers
        
        def traverse_node(node: Node, parent_name: str = None):
            nonlocal current_namespace, current_class
            
            if node.type == 'namespace_definition' and is_cpp:
                name_node = node.child_by_field_name('name')
                if name_node:
                    namespace_name = code[name_node.start_byte:name_node.end_byte]
                    old_namespace = current_namespace
                    current_namespace = namespace_name
                    
                    symbol = CppSymbol(
                        name=namespace_name,
                        type='namespace',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        namespace=old_namespace
                    )
                    symbols.append(symbol)
                    
                    # Traverse namespace body
                    for child in node.children:
                        traverse_node(child, namespace_name)
                    
                    current_namespace = old_namespace
                    return
            
            elif node.type in ['class_specifier', 'struct_specifier'] and is_cpp:
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = code[name_node.start_byte:name_node.end_byte]
                    modifiers = get_modifiers(node)
                    
                    symbol = CppSymbol(
                        name=class_name,
                        type='class' if node.type == 'class_specifier' else 'struct',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        namespace=current_namespace,
                        parent=parent_name,
                        **modifiers
                    )
                    symbols.append(symbol)
                    
                    old_class = current_class
                    current_class = class_name
                    
                    # Traverse class body
                    for child in node.children:
                        traverse_node(child, class_name)
                    
                    current_class = old_class
                    return
            
            elif node.type == 'function_definition':
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    # Extract function name
                    func_name = self._extract_function_name(declarator, code)
                    if func_name:
                        modifiers = get_modifiers(node)
                        
                        # Extract return type
                        return_type = None
                        type_node = node.child_by_field_name('type')
                        if type_node:
                            return_type = code[type_node.start_byte:type_node.end_byte].strip()
                        
                        # Extract parameters
                        parameters = self._extract_parameters(declarator, code)
                        
                        symbol = CppSymbol(
                            name=func_name,
                            type='function',
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            column_start=node.start_point[1],
                            column_end=node.end_point[1],
                            namespace=current_namespace,
                            parent=current_class,
                            return_type=return_type,
                            parameters=parameters,
                            **modifiers
                        )
                        symbols.append(symbol)
            
            elif node.type == 'declaration':
                # Handle variable declarations, function declarations, etc.
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    var_name = self._extract_variable_name(declarator, code)
                    if var_name:
                        modifiers = get_modifiers(node)
                        
                        # Extract type
                        var_type = None
                        type_node = node.child_by_field_name('type')
                        if type_node:
                            var_type = code[type_node.start_byte:type_node.end_byte].strip()
                        
                        symbol = CppSymbol(
                            name=var_name,
                            type='variable',
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            column_start=node.start_point[1],
                            column_end=node.end_point[1],
                            namespace=current_namespace,
                            parent=current_class,
                            return_type=var_type,
                            **modifiers
                        )
                        symbols.append(symbol)
            
            elif node.type == 'preproc_def':
                # Handle #define macros
                name_node = node.child_by_field_name('name')
                if name_node:
                    macro_name = code[name_node.start_byte:name_node.end_byte]
                    
                    symbol = CppSymbol(
                        name=macro_name,
                        type='macro',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1]
                    )
                    symbols.append(symbol)
            
            # Traverse children
            for child in node.children:
                traverse_node(child, parent_name)
        
        traverse_node(root_node)
        return symbols
    
    def _extract_function_name(self, declarator: Node, code: str) -> Optional[str]:
        """Extract function name from declarator"""
        if declarator.type == 'function_declarator':
            declarator = declarator.child_by_field_name('declarator')
        
        if declarator and declarator.type == 'identifier':
            return code[declarator.start_byte:declarator.end_byte]
        
        return None
    
    def _extract_variable_name(self, declarator: Node, code: str) -> Optional[str]:
        """Extract variable name from declarator"""
        if declarator.type == 'identifier':
            return code[declarator.start_byte:declarator.end_byte]
        elif declarator.type == 'init_declarator':
            name_node = declarator.child_by_field_name('declarator')
            if name_node and name_node.type == 'identifier':
                return code[name_node.start_byte:name_node.end_byte]
        
        return None
    
    def _extract_parameters(self, declarator: Node, code: str) -> List[str]:
        """Extract function parameters"""
        parameters = []
        
        if declarator.type == 'function_declarator':
            params_node = declarator.child_by_field_name('parameters')
            if params_node:
                for child in params_node.children:
                    if child.type == 'parameter_declaration':
                        declarator = child.child_by_field_name('declarator')
                        if declarator and declarator.type == 'identifier':
                            param_name = code[declarator.start_byte:declarator.end_byte]
                            parameters.append(param_name)
        
        return parameters


class CppTransformer:
    """C/C++ code transformer"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.changes_made = []
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """Log message if logger available"""
        if self.logger:
            self.logger.log(level, OperationType.TRANSFORMATION, message, **kwargs)
    
    def rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Rename variable in C/C++ code"""
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(old_name) + r'\b'
        new_code = re.sub(pattern, new_name, code)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'rename_variable',
                'old_name': old_name,
                'new_name': new_name
            })
            self.log(LogLevel.INFO, f"Renamed variable '{old_name}' to '{new_name}'")
        
        return new_code
    
    def add_doxygen_comment(self, code: str, function_name: str, comment: str) -> str:
        """Add Doxygen comment to function"""
        # Pattern to find function definition
        patterns = [
            rf'(\s*)(\w+\s+)*{re.escape(function_name)}\s*\(',
            rf'(\s*)(static\s+|inline\s+|virtual\s+)*\w+\s+{re.escape(function_name)}\s*\(',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code, re.MULTILINE)
            if match:
                indent = match.group(1)
                doxygen_comment = f"{indent}/**\n{indent} * {comment}\n{indent} */\n"
                new_code = code[:match.start()] + doxygen_comment + code[match.start():]
                
                self.changes_made.append({
                    'type': 'add_doxygen',
                    'function_name': function_name,
                    'comment': comment
                })
                self.log(LogLevel.INFO, f"Added Doxygen comment to function '{function_name}'")
                
                return new_code
        
        self.log(LogLevel.WARNING, f"Function '{function_name}' not found for Doxygen addition")
        return code
    
    def modernize_cpp(self, code: str) -> str:
        """Modernize C++ code with C++11/14/17 features"""
        # Replace NULL with nullptr
        code = re.sub(r'\bNULL\b', 'nullptr', code)
        
        # Replace typedef with using (simplified)
        code = re.sub(
            r'typedef\s+(.+)\s+(\w+);',
            r'using \2 = \1;',
            code
        )
        
        # Convert C-style casts to static_cast (very basic)
        code = re.sub(
            r'\((\w+)\*?\)\s*(\w+)',
            r'static_cast<\1>(\2)',
            code
        )
        
        if code != code:  # If any changes were made
            self.changes_made.append({
                'type': 'modernize_cpp',
                'description': 'Applied modern C++ features'
            })
            self.log(LogLevel.INFO, "Applied modern C++ transformations")
        
        return code
    
    def add_const_correctness(self, code: str) -> str:
        """Add const correctness to member functions"""
        # Find member functions that don't modify state and add const
        # This is a simplified heuristic
        pattern = r'(\w+\s+\w+\s*\([^)]*\))\s*{([^}]+)}'
        
        def add_const_if_needed(match):
            func_signature = match.group(1)
            func_body = match.group(2)
            
            # Simple heuristic: if function doesn't assign to members, make it const
            if ('this->' not in func_body and 
                '=' not in func_body and 
                'const' not in func_signature):
                return func_signature + ' const {' + func_body + '}'
            
            return match.group(0)
        
        new_code = re.sub(pattern, add_const_if_needed, code, flags=re.DOTALL)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'add_const_correctness',
                'description': 'Added const correctness to member functions'
            })
            self.log(LogLevel.INFO, "Added const correctness")
        
        return new_code
    
    def add_smart_pointers(self, code: str) -> str:
        """Convert raw pointers to smart pointers where appropriate"""
        # Convert new/delete patterns to unique_ptr (simplified)
        # This is a very basic transformation
        
        # Pattern: Type* var = new Type(...)
        pattern = r'(\w+)\*\s+(\w+)\s*=\s*new\s+\w+\s*\([^)]*\)'
        replacement = r'std::unique_ptr<\1> \2 = std::make_unique<\1>()'
        
        new_code = re.sub(pattern, replacement, code)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'add_smart_pointers',
                'description': 'Converted raw pointers to smart pointers'
            })
            self.log(LogLevel.INFO, "Converted raw pointers to smart pointers")
        
        return new_code
    
    def add_range_based_for(self, code: str) -> str:
        """Convert traditional for loops to range-based for loops"""
        # Pattern: for(int i = 0; i < container.size(); ++i)
        pattern = r'for\s*\(\s*\w+\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*(\w+)\.size\(\)\s*;\s*\+\+\w+\s*\)'
        
        def replace_with_range_for(match):
            container = match.group(1)
            return f'for(const auto& item : {container})'
        
        new_code = re.sub(pattern, replace_with_range_for, code)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'add_range_based_for',
                'description': 'Converted to range-based for loops'
            })
            self.log(LogLevel.INFO, "Converted to range-based for loops")
        
        return new_code


class CppAdapter:
    """Main C/C++ language adapter"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.parser = CppTreeSitterParser(logger)
        self.transformer = CppTransformer(logger)
        self.gcc_path = self._find_compiler('gcc')
        self.clang_path = self._find_compiler('clang')
        
        if not (self.gcc_path or self.clang_path) and logger:
            logger.log(
                LogLevel.WARNING, OperationType.VALIDATION,
                "No C/C++ compiler found - syntax validation disabled"
            )
    
    def _find_compiler(self, compiler_name: str) -> Optional[str]:
        """Find C/C++ compiler executable"""
        try:
            result = subprocess.run([compiler_name, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return compiler_name
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try with .exe extension on Windows
        try:
            exe_name = f"{compiler_name}.exe"
            result = subprocess.run([exe_name, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return exe_name
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def parse_code(self, code: str, file_path: str = None) -> Optional[Node]:
        """Parse C/C++ code"""
        is_cpp = self._is_cpp_file(file_path) if file_path else True
        return self.parser.parse(code, is_cpp)
    
    def _is_cpp_file(self, file_path: str) -> bool:
        """Check if file is C++ (vs C)"""
        cpp_extensions = ['.cpp', '.cxx', '.cc', '.hpp', '.hxx', '.hh']
        return Path(file_path).suffix.lower() in cpp_extensions
    
    def extract_symbols(self, code: str, file_path: str = None) -> List[CppSymbol]:
        """Extract symbols from C/C++ code"""
        try:
            is_cpp = self._is_cpp_file(file_path) if file_path else True
            root_node = self.parse_code(code, file_path)
            
            if root_node:
                symbols = self.parser.extract_symbols(root_node, code, is_cpp)
            else:
                # Fallback to regex-based extraction
                symbols = self._extract_symbols_regex(code, is_cpp)
            
            if self.logger:
                self.logger.log(
                    LogLevel.DEBUG, OperationType.TRANSFORMATION,
                    f"Extracted {len(symbols)} symbols from C/C++ code"
                )
            
            return symbols
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return []
    
    def _extract_symbols_regex(self, code: str, is_cpp: bool = True) -> List[CppSymbol]:
        """Fallback regex-based symbol extraction"""
        symbols = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function definitions
            func_match = re.search(r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{', line)
            if func_match and not re.search(r'\b(if|while|for|switch)\b', line):
                symbols.append(CppSymbol(
                    name=func_match.group(2),
                    type='function',
                    line_start=i,
                    line_end=i,
                    column_start=func_match.start(2),
                    column_end=func_match.end(2),
                    return_type=func_match.group(1)
                ))
            
            # Class/struct declarations (C++ only)
            if is_cpp:
                class_match = re.search(r'(class|struct)\s+(\w+)', line)
                if class_match:
                    symbols.append(CppSymbol(
                        name=class_match.group(2),
                        type=class_match.group(1),
                        line_start=i,
                        line_end=i,
                        column_start=class_match.start(2),
                        column_end=class_match.end(2)
                    ))
            
            # Macro definitions
            macro_match = re.search(r'#define\s+(\w+)', line)
            if macro_match:
                symbols.append(CppSymbol(
                    name=macro_match.group(1),
                    type='macro',
                    line_start=i,
                    line_end=i,
                    column_start=macro_match.start(1),
                    column_end=macro_match.end(1)
                ))
        
        return symbols
    
    def apply_transformations(self, code: str, suggestions: Dict[str, Any], 
                            file_path: str = None) -> str:
        """Apply transformations based on LLM suggestions"""
        try:
            refactored_code = code
            is_cpp = self._is_cpp_file(file_path) if file_path else True
            
            # Apply rename transformations
            if 'rename' in suggestions:
                for old_name, new_name in suggestions['rename'].items():
                    refactored_code = self.transformer.rename_variable(
                        refactored_code, old_name, new_name
                    )
            
            # Apply Doxygen comments
            if 'docstring' in suggestions:
                for func_info in suggestions['docstring']:
                    if isinstance(func_info, dict):
                        func_name = func_info.get('function')
                        doc = func_info.get('doc')
                        if func_name and doc:
                            refactored_code = self.transformer.add_doxygen_comment(
                                refactored_code, func_name, doc
                            )
            
            # Apply specific transformations
            if 'transformations' in suggestions:
                for transform in suggestions['transformations']:
                    transform_type = transform.get('type')
                    
                    if transform_type == 'modernize_cpp' and is_cpp:
                        refactored_code = self.transformer.modernize_cpp(refactored_code)
                    
                    elif transform_type == 'add_const_correctness' and is_cpp:
                        refactored_code = self.transformer.add_const_correctness(refactored_code)
                    
                    elif transform_type == 'add_smart_pointers' and is_cpp:
                        refactored_code = self.transformer.add_smart_pointers(refactored_code)
                    
                    elif transform_type == 'add_range_based_for' and is_cpp:
                        refactored_code = self.transformer.add_range_based_for(refactored_code)
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Applied {len(self.transformer.changes_made)} C/C++ transformations"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def validate_syntax(self, code: str, file_path: str = None) -> Tuple[bool, Optional[str]]:
        """Validate C/C++ syntax using gcc or clang"""
        compiler = self.gcc_path or self.clang_path
        if not compiler:
            return self._basic_syntax_check(code)
        
        try:
            is_cpp = self._is_cpp_file(file_path) if file_path else True
            
            # Create temporary file
            suffix = '.cpp' if is_cpp else '.c'
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Use compiler to check syntax
                cmd = [compiler, '-fsyntax-only', '-std=c++17' if is_cpp else '-std=c11', temp_file]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=15
                )
                
                if result.returncode == 0:
                    return True, None
                else:
                    error_msg = result.stderr.strip()
                    if self.logger:
                        self.logger.log(
                            LogLevel.ERROR, OperationType.VALIDATION,
                            f"C/C++ syntax error: {error_msg}"
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
        """Basic syntax check without compiler"""
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
    
    def format_code(self, code: str, file_path: str = None) -> str:
        """Format C/C++ code"""
        try:
            # Try to use clang-format if available
            try:
                result = subprocess.run(
                    ['clang-format', '-'],
                    input=code, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return result.stdout
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
            formatted_line = '    ' * indent_level + stripped
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
            lines_of_code = len([line for line in lines 
                               if line.strip() and not line.strip().startswith('//')
                               and not line.strip().startswith('/*')])
            
            function_count = len(re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*{', code))
            class_count = len(re.findall(r'\b(class|struct)\s+\w+', code))
            
            # Cyclomatic complexity
            complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', '&&', '||']
            cyclomatic_complexity = 1  # Base complexity
            
            for keyword in complexity_keywords:
                cyclomatic_complexity += len(re.findall(rf'\b{keyword}\b', code))
            
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
        return "cpp"
    
    def get_file_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return [".c", ".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx", ".hh"]
    
    def supports_file(self, file_path: str) -> bool:
        """Check if file is supported"""
        return Path(file_path).suffix.lower() in self.get_file_extensions()