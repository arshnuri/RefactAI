#!/usr/bin/env python3
"""
Java Language Adapter

Provides Java-specific parsing, transformation, and code generation.
Uses tree-sitter for parsing and javac for syntax validation.
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
class JavaSymbol:
    """Java symbol information"""
    name: str
    type: str  # class, interface, method, field, enum, annotation
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    visibility: str = "package"  # public, private, protected, package
    is_static: bool = False
    is_final: bool = False
    is_abstract: bool = False
    parent: Optional[str] = None
    package: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    annotations: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.annotations is None:
            self.annotations = []


class JavaTreeSitterParser:
    """Tree-sitter based Java parser"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.parser = None
        self.language = None
        
        if not TREE_SITTER_AVAILABLE:
            if logger:
                logger.log(
                    LogLevel.WARNING, OperationType.VALIDATION,
                    "tree-sitter not available - Java parsing limited"
                )
            return
        
        try:
            # Try to load Java language
            # Note: In practice, you'd need to build the tree-sitter Java grammar
            self._setup_parser()
        except Exception as e:
            if logger:
                logger.log_error(OperationType.VALIDATION, e, 
                                context={'component': 'tree-sitter-java'})
    
    def _setup_parser(self):
        """Setup tree-sitter parser for Java"""
        if TREE_SITTER_AVAILABLE:
            self.parser = Parser()
            # self.language = Language('path/to/tree-sitter-java.so', 'java')
            # self.parser.set_language(self.language)
    
    def parse(self, code: str) -> Optional[Node]:
        """Parse Java code"""
        if not self.parser:
            return None
        
        try:
            tree = self.parser.parse(bytes(code, 'utf8'))
            return tree.root_node
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return None
    
    def extract_symbols(self, root_node: Node, code: str) -> List[JavaSymbol]:
        """Extract symbols from tree-sitter AST"""
        symbols = []
        current_package = None
        current_class = None
        
        def get_modifiers(node: Node) -> Dict[str, Any]:
            """Extract modifiers from a node"""
            modifiers = {
                'visibility': 'package',
                'is_static': False,
                'is_final': False,
                'is_abstract': False
            }
            
            for child in node.children:
                if child.type == 'modifiers':
                    modifier_text = code[child.start_byte:child.end_byte]
                    if 'public' in modifier_text:
                        modifiers['visibility'] = 'public'
                    elif 'private' in modifier_text:
                        modifiers['visibility'] = 'private'
                    elif 'protected' in modifier_text:
                        modifiers['visibility'] = 'protected'
                    
                    modifiers['is_static'] = 'static' in modifier_text
                    modifiers['is_final'] = 'final' in modifier_text
                    modifiers['is_abstract'] = 'abstract' in modifier_text
            
            return modifiers
        
        def traverse_node(node: Node, parent_name: str = None):
            nonlocal current_package, current_class
            
            if node.type == 'package_declaration':
                package_node = node.child_by_field_name('name')
                if package_node:
                    current_package = code[package_node.start_byte:package_node.end_byte]
            
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = code[name_node.start_byte:name_node.end_byte]
                    modifiers = get_modifiers(node)
                    
                    symbol = JavaSymbol(
                        name=class_name,
                        type='class',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        package=current_package,
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
            
            elif node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    interface_name = code[name_node.start_byte:name_node.end_byte]
                    modifiers = get_modifiers(node)
                    
                    symbol = JavaSymbol(
                        name=interface_name,
                        type='interface',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        package=current_package,
                        parent=parent_name,
                        **modifiers
                    )
                    symbols.append(symbol)
            
            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    method_name = code[name_node.start_byte:name_node.end_byte]
                    modifiers = get_modifiers(node)
                    
                    # Extract return type
                    return_type = None
                    type_node = node.child_by_field_name('type')
                    if type_node:
                        return_type = code[type_node.start_byte:type_node.end_byte]
                    
                    # Extract parameters
                    parameters = []
                    params_node = node.child_by_field_name('parameters')
                    if params_node:
                        for param in params_node.children:
                            if param.type == 'formal_parameter':
                                param_name_node = param.child_by_field_name('name')
                                if param_name_node:
                                    parameters.append(
                                        code[param_name_node.start_byte:param_name_node.end_byte]
                                    )
                    
                    symbol = JavaSymbol(
                        name=method_name,
                        type='method',
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        package=current_package,
                        parent=current_class,
                        return_type=return_type,
                        parameters=parameters,
                        **modifiers
                    )
                    symbols.append(symbol)
            
            elif node.type == 'field_declaration':
                # Extract field declarations
                for child in node.children:
                    if child.type == 'variable_declarator':
                        name_node = child.child_by_field_name('name')
                        if name_node:
                            field_name = code[name_node.start_byte:name_node.end_byte]
                            modifiers = get_modifiers(node)
                            
                            # Extract field type
                            field_type = None
                            type_node = node.child_by_field_name('type')
                            if type_node:
                                field_type = code[type_node.start_byte:type_node.end_byte]
                            
                            symbol = JavaSymbol(
                                name=field_name,
                                type='field',
                                line_start=node.start_point[0] + 1,
                                line_end=node.end_point[0] + 1,
                                column_start=node.start_point[1],
                                column_end=node.end_point[1],
                                package=current_package,
                                parent=current_class,
                                return_type=field_type,
                                **modifiers
                            )
                            symbols.append(symbol)
            
            # Traverse children
            for child in node.children:
                traverse_node(child, parent_name)
        
        traverse_node(root_node)
        return symbols


class JavaTransformer:
    """Java code transformer"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.changes_made = []
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """Log message if logger available"""
        if self.logger:
            self.logger.log(level, OperationType.TRANSFORMATION, message, **kwargs)
    
    def rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Rename variable in Java code"""
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
    
    def add_javadoc(self, code: str, method_name: str, javadoc: str) -> str:
        """Add Javadoc comment to method"""
        # Pattern to find method declaration
        patterns = [
            rf'(\s*)(public|private|protected|static|final|abstract|\s)*\s*\w+\s+{re.escape(method_name)}\s*\(',
            rf'(\s*){re.escape(method_name)}\s*\(',  # Constructor
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code, re.MULTILINE)
            if match:
                indent = match.group(1)
                javadoc_comment = f"{indent}/**\n{indent} * {javadoc}\n{indent} */\n"
                new_code = code[:match.start()] + javadoc_comment + code[match.start():]
                
                self.changes_made.append({
                    'type': 'add_javadoc',
                    'method_name': method_name,
                    'javadoc': javadoc
                })
                self.log(LogLevel.INFO, f"Added Javadoc to method '{method_name}'")
                
                return new_code
        
        self.log(LogLevel.WARNING, f"Method '{method_name}' not found for Javadoc addition")
        return code
    
    def add_annotations(self, code: str, method_name: str, annotations: List[str]) -> str:
        """Add annotations to method"""
        pattern = rf'(\s*)(public|private|protected|static|final|abstract|\s)*\s*\w+\s+{re.escape(method_name)}\s*\('
        match = re.search(pattern, code, re.MULTILINE)
        
        if match:
            indent = match.group(1)
            annotation_lines = [f"{indent}@{ann}" for ann in annotations]
            annotation_text = '\n'.join(annotation_lines) + '\n'
            
            new_code = code[:match.start()] + annotation_text + code[match.start():]
            
            self.changes_made.append({
                'type': 'add_annotations',
                'method_name': method_name,
                'annotations': annotations
            })
            self.log(LogLevel.INFO, f"Added annotations to method '{method_name}': {annotations}")
            
            return new_code
        
        self.log(LogLevel.WARNING, f"Method '{method_name}' not found for annotation addition")
        return code
    
    def convert_for_to_stream(self, code: str) -> str:
        """Convert traditional for loops to Java 8 streams where applicable"""
        # This is a simplified example - real implementation would be more complex
        # Pattern for simple for-each loops that could be streams
        pattern = r'for\s*\(\s*(\w+)\s+(\w+)\s*:\s*(\w+)\s*\)\s*\{([^}]+)\}'
        
        def replace_with_stream(match):
            type_name = match.group(1)
            var_name = match.group(2)
            collection = match.group(3)
            body = match.group(4).strip()
            
            # Simple case: just processing each element
            if 'System.out.println' in body:
                return f"{collection}.forEach(System.out::println);"
            
            # Return original if we can't convert
            return match.group(0)
        
        new_code = re.sub(pattern, replace_with_stream, code, flags=re.DOTALL)
        
        if new_code != code:
            self.changes_made.append({
                'type': 'for_to_stream',
                'description': 'Converted for loop to stream operation'
            })
            self.log(LogLevel.INFO, "Converted for loop to stream operation")
        
        return new_code
    
    def add_null_checks(self, code: str, variable_names: List[str]) -> str:
        """Add null checks for specified variables"""
        for var_name in variable_names:
            # Look for method calls on the variable
            pattern = rf'({re.escape(var_name)}\.\w+\([^)]*\))'
            
            def add_null_check(match):
                method_call = match.group(1)
                return f"if ({var_name} != null) {{ {method_call}; }}"
            
            new_code = re.sub(pattern, add_null_check, code)
            
            if new_code != code:
                self.changes_made.append({
                    'type': 'add_null_check',
                    'variable': var_name
                })
                self.log(LogLevel.INFO, f"Added null check for variable '{var_name}'")
                code = new_code
        
        return code
    
    def modernize_syntax(self, code: str) -> str:
        """Modernize Java syntax"""
        # Convert diamond operator
        code = re.sub(
            r'(\w+)<([^>]+)>\s+(\w+)\s*=\s*new\s+\w+<[^>]+>\(',
            r'\1<\2> \3 = new \1<>(',
            code
        )
        
        # Convert to try-with-resources (simplified)
        # This would need more sophisticated parsing in practice
        
        return code


class JavaAdapter:
    """Main Java language adapter"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.parser = JavaTreeSitterParser(logger)
        self.transformer = JavaTransformer(logger)
        self.javac_path = self._find_javac_executable()
        
        if not self.javac_path and logger:
            logger.log(
                LogLevel.WARNING, OperationType.VALIDATION,
                "javac not found - Java syntax validation disabled"
            )
    
    def _find_javac_executable(self) -> Optional[str]:
        """Find javac executable"""
        try:
            result = subprocess.run(['javac', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'javac'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try common paths
        common_paths = [
            'javac.exe',
            'C:\\Program Files\\Java\\jdk*\\bin\\javac.exe',
            '/usr/bin/javac',
            '/usr/local/bin/javac'
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # Try to find via JAVA_HOME
        import os
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            javac_path = Path(java_home) / 'bin' / 'javac'
            if javac_path.exists():
                return str(javac_path)
            
            javac_exe_path = Path(java_home) / 'bin' / 'javac.exe'
            if javac_exe_path.exists():
                return str(javac_exe_path)
        
        return None
    
    def parse_code(self, code: str) -> Optional[Node]:
        """Parse Java code"""
        return self.parser.parse(code)
    
    def extract_symbols(self, code: str) -> List[JavaSymbol]:
        """Extract symbols from Java code"""
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
                    f"Extracted {len(symbols)} symbols from Java code"
                )
            
            return symbols
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return []
    
    def _extract_symbols_regex(self, code: str) -> List[JavaSymbol]:
        """Fallback regex-based symbol extraction"""
        symbols = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Class declarations
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                symbols.append(JavaSymbol(
                    name=class_match.group(1),
                    type='class',
                    line_start=i,
                    line_end=i,
                    column_start=class_match.start(1),
                    column_end=class_match.end(1)
                ))
            
            # Method declarations
            method_match = re.search(
                r'(public|private|protected)?\s*(static)?\s*(\w+)\s+(\w+)\s*\(',
                line
            )
            if method_match and not re.search(r'\b(class|interface)\b', line):
                symbols.append(JavaSymbol(
                    name=method_match.group(4),
                    type='method',
                    line_start=i,
                    line_end=i,
                    column_start=method_match.start(4),
                    column_end=method_match.end(4),
                    visibility=method_match.group(1) or 'package',
                    is_static=bool(method_match.group(2)),
                    return_type=method_match.group(3)
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
            
            # Apply Javadoc additions
            if 'docstring' in suggestions:
                for method_info in suggestions['docstring']:
                    if isinstance(method_info, dict):
                        method_name = method_info.get('method')
                        doc = method_info.get('doc')
                        if method_name and doc:
                            refactored_code = self.transformer.add_javadoc(
                                refactored_code, method_name, doc
                            )
            
            # Apply specific transformations
            if 'transformations' in suggestions:
                for transform in suggestions['transformations']:
                    transform_type = transform.get('type')
                    
                    if transform_type == 'modernize_syntax':
                        refactored_code = self.transformer.modernize_syntax(refactored_code)
                    
                    elif transform_type == 'for_to_stream':
                        refactored_code = self.transformer.convert_for_to_stream(refactored_code)
                    
                    elif transform_type == 'add_null_checks':
                        variables = transform.get('variables', [])
                        refactored_code = self.transformer.add_null_checks(
                            refactored_code, variables
                        )
                    
                    elif transform_type == 'add_annotations':
                        method_name = transform.get('method_name')
                        annotations = transform.get('annotations', [])
                        if method_name and annotations:
                            refactored_code = self.transformer.add_annotations(
                                refactored_code, method_name, annotations
                            )
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Applied {len(self.transformer.changes_made)} Java transformations"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Java syntax using javac"""
        if not self.javac_path:
            return self._basic_syntax_check(code)
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                # Extract class name for proper file naming
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                if class_match:
                    class_name = class_match.group(1)
                    f.close()
                    temp_file = f.name.replace('.java', f'_{class_name}.java')
                    with open(temp_file, 'w') as cf:
                        cf.write(code)
                else:
                    f.write(code)
                    temp_file = f.name
            
            try:
                # Use javac to check syntax
                result = subprocess.run(
                    [self.javac_path, '-Xlint:none', temp_file],
                    capture_output=True, text=True, timeout=15
                )
                
                if result.returncode == 0:
                    return True, None
                else:
                    error_msg = result.stderr.strip()
                    if self.logger:
                        self.logger.log(
                            LogLevel.ERROR, OperationType.VALIDATION,
                            f"Java syntax error: {error_msg}"
                        )
                    return False, error_msg
            
            finally:
                # Clean up temp files
                Path(temp_file).unlink(missing_ok=True)
                # Also clean up .class files
                class_file = temp_file.replace('.java', '.class')
                Path(class_file).unlink(missing_ok=True)
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.VALIDATION, e)
            return False, str(e)
    
    def _basic_syntax_check(self, code: str) -> Tuple[bool, Optional[str]]:
        """Basic syntax check without javac"""
        try:
            # Check for balanced braces
            brace_count = code.count('{') - code.count('}')
            if brace_count != 0:
                return False, f"Unbalanced braces: {brace_count}"
            
            # Check for balanced parentheses
            paren_count = code.count('(') - code.count(')')
            if paren_count != 0:
                return False, f"Unbalanced parentheses: {paren_count}"
            
            # Check for semicolons after statements (basic check)
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if (stripped and not stripped.startswith('//') and 
                    not stripped.startswith('/*') and not stripped.endswith('*/') and
                    not stripped.endswith('{') and not stripped.endswith('}') and
                    not stripped.startswith('@') and not stripped.startswith('package') and
                    not stripped.startswith('import') and not stripped.startswith('public class') and
                    not stripped.startswith('private class') and not stripped.startswith('class') and
                    not stripped.endswith(';')):
                    return False, f"Missing semicolon at line {i}: {stripped}"
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    def format_code(self, code: str) -> str:
        """Format Java code"""
        try:
            # Try to use google-java-format if available
            try:
                result = subprocess.run(
                    ['java', '-jar', 'google-java-format.jar', '-'],
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
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
            method_count = len(re.findall(r'\b(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(', code))
            class_count = len(re.findall(r'\bclass\s+\w+', code))
            
            # Cyclomatic complexity
            complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', '&&', '||', 'catch']
            cyclomatic_complexity = 1  # Base complexity
            
            for keyword in complexity_keywords:
                cyclomatic_complexity += len(re.findall(rf'\b{keyword}\b', code))
            
            return {
                'cyclomatic_complexity': cyclomatic_complexity,
                'lines_of_code': lines_of_code,
                'method_count': method_count,
                'class_count': class_count
            }
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return {}
    
    def get_language(self) -> str:
        """Get language identifier"""
        return "java"
    
    def get_file_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return [".java"]
    
    def supports_file(self, file_path: str) -> bool:
        """Check if file is supported"""
        return Path(file_path).suffix.lower() in self.get_file_extensions()