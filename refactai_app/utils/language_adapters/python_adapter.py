#!/usr/bin/env python3
"""
Python Language Adapter

Provides Python-specific AST parsing, transformation, and code generation.
Uses both `ast` and `libcst` for maximum safety and flexibility.
"""

import ast
import astor
import inspect
import textwrap
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import libcst as cst
    from libcst import metadata
    LIBCST_AVAILABLE = True
except ImportError:
    cst = None
    LIBCST_AVAILABLE = False

from ..logger import RefactorLogger, LogLevel, OperationType


@dataclass
class PythonSymbol:
    """Python symbol information"""
    name: str
    type: str  # function, class, variable, import
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    docstring: Optional[str] = None
    parent: Optional[str] = None
    decorators: List[str] = None
    arguments: List[str] = None
    return_type: Optional[str] = None
    
    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []
        if self.arguments is None:
            self.arguments = []


class PythonASTTransformer(ast.NodeTransformer):
    """AST transformer for Python code refactoring"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.changes_made = []
        self.symbol_table = {}
        self.imports = set()
        self.current_class = None
        self.current_function = None
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """Log message if logger available"""
        if self.logger:
            self.logger.log(level, OperationType.TRANSFORMATION, message, **kwargs)
    
    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Track imports"""
        for alias in node.names:
            self.imports.add(alias.name)
        return node
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """Track from imports"""
        module = node.module or ''
        for alias in node.names:
            self.imports.add(f"{module}.{alias.name}")
        return node
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definition"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Process class
        node = self.generic_visit(node)
        
        self.current_class = old_class
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition"""
        old_function = self.current_function
        self.current_function = node.name
        
        # Process function
        node = self.generic_visit(node)
        
        self.current_function = old_function
        return node
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Visit async function definition"""
        old_function = self.current_function
        self.current_function = node.name
        
        # Process function
        node = self.generic_visit(node)
        
        self.current_function = old_function
        return node
    
    def rename_variable(self, old_name: str, new_name: str) -> None:
        """Add variable rename transformation"""
        self.changes_made.append({
            'type': 'rename_variable',
            'old_name': old_name,
            'new_name': new_name,
            'context': {
                'class': self.current_class,
                'function': self.current_function
            }
        })
    
    def add_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef], 
                     docstring: str) -> None:
        """Add docstring to function or class"""
        # Check if docstring already exists
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
            # Replace existing docstring
            node.body[0].value.s = docstring
        else:
            # Add new docstring
            docstring_node = ast.Expr(value=ast.Str(s=docstring))
            node.body.insert(0, docstring_node)
        
        self.changes_made.append({
            'type': 'add_docstring',
            'target': node.name,
            'docstring': docstring,
            'context': {
                'class': self.current_class,
                'function': self.current_function
            }
        })
    
    def optimize_imports(self, tree: ast.AST) -> ast.AST:
        """Optimize import statements"""
        # This is a placeholder for import optimization logic
        # Could remove unused imports, sort imports, etc.
        return tree
    
    def convert_for_to_comprehension(self, node: ast.For) -> Optional[ast.Assign]:
        """Convert simple for loops to list comprehensions"""
        # Check if this is a simple append pattern
        if (len(node.body) == 1 and 
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Call) and
            isinstance(node.body[0].value.func, ast.Attribute) and
            node.body[0].value.func.attr == 'append'):
            
            # Extract components
            target_list = node.body[0].value.func.value
            append_value = node.body[0].value.args[0]
            
            # Create list comprehension
            comprehension = ast.ListComp(
                elt=append_value,
                generators=[ast.comprehension(
                    target=node.target,
                    iter=node.iter,
                    ifs=node.orelse if node.orelse else [],
                    is_async=0
                )]
            )
            
            # Create assignment
            assignment = ast.Assign(
                targets=[target_list],
                value=comprehension
            )
            
            self.changes_made.append({
                'type': 'for_to_comprehension',
                'line': node.lineno,
                'context': {
                    'class': self.current_class,
                    'function': self.current_function
                }
            })
            
            return assignment
        
        return None
    
    def merge_nested_ifs(self, node: ast.If) -> Optional[ast.If]:
        """Merge nested if statements"""
        # Check for nested if pattern
        if (len(node.body) == 1 and 
            isinstance(node.body[0], ast.If) and
            not node.body[0].orelse and
            not node.orelse):
            
            inner_if = node.body[0]
            
            # Create combined condition
            combined_condition = ast.BoolOp(
                op=ast.And(),
                values=[node.test, inner_if.test]
            )
            
            # Create new if statement
            new_if = ast.If(
                test=combined_condition,
                body=inner_if.body,
                orelse=inner_if.orelse
            )
            
            self.changes_made.append({
                'type': 'merge_nested_ifs',
                'line': node.lineno,
                'context': {
                    'class': self.current_class,
                    'function': self.current_function
                }
            })
            
            return new_if
        
        return None


if LIBCST_AVAILABLE:
    class PythonLibCSTTransformer:
        """LibCST-based transformer for more complex refactoring"""
else:
    class PythonLibCSTTransformer:
        """Fallback transformer when libcst is not available"""
        
        def __init__(self, logger: RefactorLogger = None):
            self.logger = logger
        
        def rename_symbol(self, tree: Any, old_name: str, new_name: str) -> Any:
            return tree
        
        def add_type_annotations(self, tree: Any, annotations: Dict[str, str]) -> Any:
            return tree

if LIBCST_AVAILABLE:
    # Continue with the actual implementation
    
        def __init__(self, logger: RefactorLogger = None):
            self.logger = logger
            self.changes_made = []
            
            if not LIBCST_AVAILABLE:
                raise ImportError("libcst is required for advanced Python transformations")
        
        def log(self, level: LogLevel, message: str, **kwargs):
            """Log message if logger available"""
            if self.logger:
                self.logger.log(level, OperationType.TRANSFORMATION, message, **kwargs)
        
        def rename_symbol(self, tree: Any, old_name: str, new_name: str) -> Any:
            """Rename a symbol throughout the code"""
            
            class NameReplacer(cst.CSTTransformer):
                def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
                    if updated_node.value == old_name:
                        return updated_node.with_changes(value=new_name)
                    return updated_node
            
            transformer = NameReplacer()
            new_tree = tree.visit(transformer)
            
            self.changes_made.append({
                'type': 'rename_symbol',
                'old_name': old_name,
                'new_name': new_name
            })
            
            return new_tree
        
        def add_type_annotations(self, tree: Any, annotations: Dict[str, str]) -> Any:
            """Add type annotations to functions"""
            
            class TypeAnnotator(cst.CSTTransformer):
                def leave_FunctionDef(self, original_node: cst.FunctionDef, 
                                    updated_node: cst.FunctionDef) -> cst.FunctionDef:
                    func_name = updated_node.name.value
                    if func_name in annotations:
                        # Parse annotation
                        annotation_str = annotations[func_name]
                        try:
                            annotation = cst.parse_expression(annotation_str)
                            return updated_node.with_changes(returns=cst.Annotation(annotation=annotation))
                        except Exception as e:
                            if self.logger:
                                self.logger.log_error(
                                    OperationType.TRANSFORMATION, e,
                                    context={'function': func_name, 'annotation': annotation_str}
                                )
                    return updated_node
            
            transformer = TypeAnnotator()
            new_tree = tree.visit(transformer)
            
            self.changes_made.append({
                'type': 'add_type_annotations',
                'annotations': annotations
            })
            
            return new_tree


class PythonAdapter:
    """Main Python language adapter"""
    
    def __init__(self, logger: RefactorLogger = None):
        self.logger = logger
        self.ast_transformer = PythonASTTransformer(logger)
        
        if LIBCST_AVAILABLE:
            self.cst_transformer = PythonLibCSTTransformer(logger)
        else:
            self.cst_transformer = None
            if logger:
                logger.log(
                    LogLevel.WARNING, OperationType.VALIDATION,
                    "libcst not available - some advanced transformations disabled"
                )
    
    def parse_code(self, code: str) -> Tuple[ast.AST, Optional[Any]]:
        """Parse Python code into AST and CST"""
        try:
            # Parse with ast
            ast_tree = ast.parse(code)
            
            # Parse with libcst if available
            cst_tree = None
            if LIBCST_AVAILABLE:
                try:
                    cst_tree = cst.parse_module(code)
                except Exception as e:
                    if self.logger:
                        self.logger.log_error(
                            OperationType.TRANSFORMATION, e,
                            context={'parser': 'libcst'}
                        )
            
            return ast_tree, cst_tree
        
        except SyntaxError as e:
            if self.logger:
                self.logger.log_error(
                    OperationType.VALIDATION, e,
                    context={'parser': 'ast', 'line': e.lineno}
                )
            raise
    
    def extract_symbols(self, code: str) -> List[PythonSymbol]:
        """Extract symbols from Python code"""
        try:
            tree = ast.parse(code)
            symbols = []
            
            class SymbolExtractor(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.symbols = []
                
                def visit_ClassDef(self, node):
                    old_class = self.current_class
                    self.current_class = node.name
                    
                    # Extract class info
                    docstring = ast.get_docstring(node)
                    decorators = [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    
                    symbol = PythonSymbol(
                        name=node.name,
                        type='class',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset or node.col_offset,
                        docstring=docstring,
                        decorators=decorators
                    )
                    self.symbols.append(symbol)
                    
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    self._visit_function(node)
                
                def visit_AsyncFunctionDef(self, node):
                    self._visit_function(node)
                
                def _visit_function(self, node):
                    docstring = ast.get_docstring(node)
                    decorators = [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    arguments = [arg.arg for arg in node.args.args]
                    
                    return_type = None
                    if node.returns and hasattr(ast, 'unparse'):
                        return_type = ast.unparse(node.returns)
                    
                    symbol = PythonSymbol(
                        name=node.name,
                        type='function',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset or node.col_offset,
                        docstring=docstring,
                        parent=self.current_class,
                        decorators=decorators,
                        arguments=arguments,
                        return_type=return_type
                    )
                    self.symbols.append(symbol)
                    
                    self.generic_visit(node)
            
            extractor = SymbolExtractor()
            extractor.visit(tree)
            symbols = extractor.symbols
            
            if self.logger:
                self.logger.log(
                    LogLevel.DEBUG, OperationType.TRANSFORMATION,
                    f"Extracted {len(symbols)} symbols from Python code"
                )
            
            return symbols
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return []
    
    def apply_transformations(self, code: str, suggestions: Dict[str, Any]) -> str:
        """Apply transformations based on LLM suggestions"""
        try:
            ast_tree, cst_tree = self.parse_code(code)
            
            # Apply AST transformations
            if 'rename' in suggestions:
                for old_name, new_name in suggestions['rename'].items():
                    self.ast_transformer.rename_variable(old_name, new_name)
            
            if 'docstring' in suggestions:
                # This would require more complex logic to match functions
                pass
            
            if 'transformations' in suggestions:
                for transform in suggestions['transformations']:
                    transform_type = transform.get('type')
                    
                    if transform_type == 'for_to_comprehension':
                        # Apply for loop to comprehension transformation
                        class ForLoopTransformer(ast.NodeTransformer):
                            def visit_For(self, node):
                                result = self.ast_transformer.convert_for_to_comprehension(node)
                                return result if result else node
                        
                        transformer = ForLoopTransformer()
                        ast_tree = transformer.visit(ast_tree)
                    
                    elif transform_type == 'merge_nested_ifs':
                        # Apply nested if merging
                        class IfMerger(ast.NodeTransformer):
                            def visit_If(self, node):
                                result = self.ast_transformer.merge_nested_ifs(node)
                                return result if result else node
                        
                        transformer = IfMerger()
                        ast_tree = transformer.visit(ast_tree)
            
            # Convert back to code
            if hasattr(ast, 'unparse'):
                # Python 3.9+
                refactored_code = ast.unparse(ast_tree)
            else:
                # Use astor for older Python versions
                refactored_code = astor.to_source(ast_tree)
            
            # Apply libcst transformations if available and needed
            if self.cst_transformer and cst_tree:
                if 'rename' in suggestions:
                    for old_name, new_name in suggestions['rename'].items():
                        cst_tree = self.cst_transformer.rename_symbol(cst_tree, old_name, new_name)
                
                if 'type_annotations' in suggestions:
                    cst_tree = self.cst_transformer.add_type_annotations(
                        cst_tree, suggestions['type_annotations']
                    )
                
                # Convert back to code
                refactored_code = cst_tree.code
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Applied {len(self.ast_transformer.changes_made)} AST transformations"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax with comprehensive checks"""
        try:
            # Check for empty or whitespace-only code
            if not code or not code.strip():
                error_msg = "Code is empty or contains only whitespace"
                if self.logger:
                    self.logger.log(
                        LogLevel.ERROR, OperationType.VALIDATION,
                        error_msg
                    )
                return False, error_msg
            
            # Check for comments-only code (which is technically valid but not useful)
            stripped_lines = [line.strip() for line in code.split('\n') if line.strip()]
            non_comment_lines = [line for line in stripped_lines if not line.startswith('#')]
            
            if not non_comment_lines:
                # Only comments - this is valid Python but might not be useful for refactoring
                # We'll allow it but could add a warning
                pass
            
            # Parse the code to check for syntax errors
            parsed_ast = ast.parse(code)
            
            # Additional validation: check if the AST contains any actual statements
            # Empty modules or modules with only docstrings might be valid but not useful
            if not parsed_ast.body:
                # Empty AST body - valid Python but no executable code
                pass
            
            return True, None
            
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            if self.logger:
                self.logger.log(
                    LogLevel.ERROR, OperationType.VALIDATION,
                    error_msg
                )
            return False, error_msg
        except Exception as e:
            error_msg = f"Parse error: {str(e)}"
            if self.logger:
                self.logger.log_error(OperationType.VALIDATION, e)
            return False, error_msg
    
    def format_code(self, code: str) -> str:
        """Format Python code"""
        try:
            # Try to use black if available
            try:
                import black
                return black.format_str(code, mode=black.FileMode())
            except ImportError:
                pass
            
            # Fallback to basic formatting
            tree = ast.parse(code)
            if hasattr(ast, 'unparse'):
                return ast.unparse(tree)
            else:
                return astor.to_source(tree)
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code
    
    def get_complexity_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        try:
            tree = ast.parse(code)
            
            class ComplexityCalculator(ast.NodeVisitor):
                def __init__(self):
                    self.cyclomatic_complexity = 1  # Base complexity
                    self.lines_of_code = 0
                    self.function_count = 0
                    self.class_count = 0
                    self.max_nesting_depth = 0
                    self.current_depth = 0
                
                def visit(self, node):
                    # Count decision points for cyclomatic complexity
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                        ast.ExceptHandler, ast.With, ast.AsyncWith)):
                        self.cyclomatic_complexity += 1
                    elif isinstance(node, ast.BoolOp):
                        self.cyclomatic_complexity += len(node.values) - 1
                    
                    # Track nesting depth
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        self.current_depth += 1
                        self.max_nesting_depth = max(self.max_nesting_depth, self.current_depth)
                        self.generic_visit(node)
                        self.current_depth -= 1
                    else:
                        self.generic_visit(node)
                
                def visit_FunctionDef(self, node):
                    self.function_count += 1
                    self.current_depth += 1
                    self.max_nesting_depth = max(self.max_nesting_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
                
                def visit_AsyncFunctionDef(self, node):
                    self.function_count += 1
                    self.current_depth += 1
                    self.max_nesting_depth = max(self.max_nesting_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
                
                def visit_ClassDef(self, node):
                    self.class_count += 1
                    self.current_depth += 1
                    self.max_nesting_depth = max(self.max_nesting_depth, self.current_depth)
                    self.generic_visit(node)
                    self.current_depth -= 1
            
            calculator = ComplexityCalculator()
            calculator.visit(tree)
            calculator.lines_of_code = len(code.split('\n'))
            
            return {
                'cyclomatic_complexity': calculator.cyclomatic_complexity,
                'lines_of_code': calculator.lines_of_code,
                'function_count': calculator.function_count,
                'class_count': calculator.class_count,
                'max_nesting_depth': calculator.max_nesting_depth
            }
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return {}
    
    def apply_rename(self, code: str, old_name: str, new_name: str) -> str:
        """Apply variable/symbol rename to code"""
        try:
            ast_tree, cst_tree = self.parse_code(code)
            
            # Use CST transformer if available for better precision
            if self.cst_transformer and cst_tree:
                cst_tree = self.cst_transformer.rename_symbol(cst_tree, old_name, new_name)
                refactored_code = cst_tree.code
            else:
                # Fallback to AST transformation
                self.ast_transformer.rename_variable(old_name, new_name)
                
                class RenameTransformer(ast.NodeTransformer):
                    def visit_Name(self, node):
                        if node.id == old_name:
                            node.id = new_name
                        return node
                
                transformer = RenameTransformer()
                ast_tree = transformer.visit(ast_tree)
                
                if hasattr(ast, 'unparse'):
                    refactored_code = ast.unparse(ast_tree)
                else:
                    refactored_code = astor.to_source(ast_tree)
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Applied rename: {old_name} -> {new_name}"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def add_docstring(self, code: str, target_name: str, docstring: str, target_type: str = None) -> str:
        """Add docstring to a function or class"""
        try:
            ast_tree, _ = self.parse_code(code)
            
            class DocstringAdder(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    if node.name == target_name and (target_type is None or target_type in ['function', 'method']):
                        self._add_docstring_to_node(node, docstring)
                    return self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    if node.name == target_name and (target_type is None or target_type in ['function', 'method']):
                        self._add_docstring_to_node(node, docstring)
                    return self.generic_visit(node)
                
                def visit_ClassDef(self, node):
                    if node.name == target_name and (target_type is None or target_type == 'class'):
                        self._add_docstring_to_node(node, docstring)
                    return self.generic_visit(node)
                
                def _add_docstring_to_node(self, node, docstring_text):
                    # Check if docstring already exists
                    if (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                        # Replace existing docstring
                        if isinstance(node.body[0].value, ast.Str):
                            node.body[0].value.s = docstring_text
                        else:  # ast.Constant (Python 3.8+)
                            node.body[0].value.value = docstring_text
                    else:
                        # Add new docstring
                        if hasattr(ast, 'Constant'):  # Python 3.8+
                            docstring_node = ast.Expr(value=ast.Constant(value=docstring_text))
                        else:
                            docstring_node = ast.Expr(value=ast.Str(s=docstring_text))
                        node.body.insert(0, docstring_node)
            
            transformer = DocstringAdder()
            ast_tree = transformer.visit(ast_tree)
            
            if hasattr(ast, 'unparse'):
                refactored_code = ast.unparse(ast_tree)
            else:
                refactored_code = astor.to_source(ast_tree)
            
            if self.logger:
                self.logger.log(
                    LogLevel.INFO, OperationType.TRANSFORMATION,
                    f"Added docstring to {target_name}"
                )
            
            return refactored_code
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(OperationType.TRANSFORMATION, e)
            return code  # Return original code on error
    
    def get_language(self) -> str:
        """Get language identifier"""
        return "python"
    
    def get_file_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return [".py", ".pyw", ".pyi"]
    
    def supports_file(self, file_path: str) -> bool:
        """Check if file is supported"""
        return Path(file_path).suffix.lower() in self.get_file_extensions()