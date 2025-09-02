#!/usr/bin/env python3
"""
Refactor Engine Module

Main orchestrator for the multi-language hybrid refactoring system.
Combines LLM suggestions with AST-based safe transformations.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Import our modules
from .llm_suggestor import LLMSuggestor, LLMResponse, OpenAIProvider, AnthropicProvider, LocalLLMProvider
from .git_integrator import GitIntegrator, CodePattern
from .multilang_hybrid_refactor import MultilangHybridRefactor, LanguageAdapter
from .language_adapters import LANGUAGE_ADAPTERS, EXTENSION_MAP


class RefactorMode(Enum):
    """Refactoring modes"""
    CONSERVATIVE = "conservative"  # Only safe transformations
    BALANCED = "balanced"         # Safe + moderate risk transformations
    AGGRESSIVE = "aggressive"     # All transformations (with validation)
    LLM_ONLY = "llm_only"        # Only LLM suggestions, no AST transforms
    AST_ONLY = "ast_only"        # Only AST transforms, no LLM


@dataclass
class RefactorConfig:
    """Configuration for refactoring engine"""
    mode: RefactorMode = RefactorMode.BALANCED
    enable_git_context: bool = True
    enable_llm_suggestions: bool = True
    enable_ast_transforms: bool = True
    max_file_size: int = 50000  # Max file size in characters
    timeout_seconds: int = 60
    preserve_formatting: bool = True
    backup_original: bool = True
    validate_syntax: bool = True
    confidence_threshold: float = 0.7
    
    # LLM provider settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    local_llm_url: Optional[str] = None
    
    # Language-specific settings
    python_style: str = "google"  # docstring style
    javascript_style: str = "jsdoc"
    java_style: str = "javadoc"


@dataclass
class RefactorResult:
    """Result of refactoring operation"""
    success: bool
    original_code: str
    refactored_code: str
    language: str
    file_path: str
    
    # Applied changes
    renames_applied: List[Dict[str, Any]]
    docstrings_added: List[Dict[str, Any]]
    transformations_applied: List[Dict[str, Any]]
    
    # Suggestions not applied
    suggestions_skipped: List[Dict[str, Any]]
    
    # Metadata
    processing_time: float
    llm_suggestions: Optional[LLMResponse]
    git_context: Optional[Dict[str, Any]]
    validation_errors: List[str]
    warnings: List[str]
    
    # Statistics
    lines_changed: int = 0
    complexity_before: Optional[float] = None
    complexity_after: Optional[float] = None


class RefactorEngine:
    """Main refactoring engine that orchestrates the entire process"""
    
    def __init__(self, config: RefactorConfig = None):
        self.config = config or RefactorConfig()
        
        # Initialize components
        self.llm_suggestor = LLMSuggestor()
        self.git_integrator = GitIntegrator()
        self.multilang_refactor = MultilangHybridRefactor()
        
        # Setup LLM providers
        self._setup_llm_providers()
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'total_suggestions': 0,
            'applied_changes': 0,
            'errors': 0
        }
    
    def _setup_llm_providers(self):
        """Setup available LLM providers based on config"""
        if self.config.openai_api_key:
            try:
                provider = OpenAIProvider(self.config.openai_api_key)
                if provider.is_available():
                    self.llm_suggestor.add_provider(provider)
                    print("✓ OpenAI provider added")
            except Exception as e:
                print(f"Failed to setup OpenAI provider: {e}")
        
        if self.config.anthropic_api_key:
            try:
                provider = AnthropicProvider(self.config.anthropic_api_key)
                if provider.is_available():
                    self.llm_suggestor.add_provider(provider)
                    print("✓ Anthropic provider added")
            except Exception as e:
                print(f"Failed to setup Anthropic provider: {e}")
        
        if self.config.local_llm_url:
            try:
                provider = LocalLLMProvider(self.config.local_llm_url)
                if provider.is_available():
                    self.llm_suggestor.add_provider(provider)
                    print("✓ Local LLM provider added")
            except Exception as e:
                print(f"Failed to setup local LLM provider: {e}")
    
    def refactor_file(self, file_path: str) -> RefactorResult:
        """Refactor a single file"""
        start_time = time.time()
        file_path = Path(file_path).resolve()
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Check file size
            if len(original_code) > self.config.max_file_size:
                return RefactorResult(
                    success=False,
                    original_code=original_code,
                    refactored_code=original_code,
                    language="unknown",
                    file_path=str(file_path),
                    renames_applied=[],
                    docstrings_added=[],
                    transformations_applied=[],
                    suggestions_skipped=[],
                    processing_time=time.time() - start_time,
                    llm_suggestions=None,
                    git_context=None,
                    validation_errors=[f"File too large: {len(original_code)} > {self.config.max_file_size}"],
                    warnings=[]
                )
            
            # Detect language
            language = self._detect_language(file_path)
            if not language:
                return self._create_error_result(
                    original_code, str(file_path), "unknown", 
                    "Unsupported file type", start_time
                )
            
            # Refactor the code
            return self._refactor_code(original_code, language, str(file_path), start_time)
            
        except Exception as e:
            return self._create_error_result(
                "", str(file_path), "unknown", 
                f"Error reading file: {e}", start_time
            )
    
    def refactor_code(self, code: str, language: str, file_path: str = "<string>") -> RefactorResult:
        """Refactor code directly (without file I/O)"""
        start_time = time.time()
        return self._refactor_code(code, language, file_path, start_time)
    
    def _refactor_code(self, code: str, language: str, file_path: str, start_time: float) -> RefactorResult:
        """Core refactoring logic"""
        try:
            # Initialize result
            result = RefactorResult(
                success=False,
                original_code=code,
                refactored_code=code,
                language=language,
                file_path=file_path,
                renames_applied=[],
                docstrings_added=[],
                transformations_applied=[],
                suggestions_skipped=[],
                processing_time=0,
                llm_suggestions=None,
                git_context=None,
                validation_errors=[],
                warnings=[]
            )
            
            # Phase 0: Validate original code syntax FIRST
            if self.config.validate_syntax:
                original_syntax_errors = self._validate_syntax(code, language)
                if original_syntax_errors:
                    result.validation_errors = original_syntax_errors
                    result.success = False
                    result.processing_time = time.time() - start_time
                    result.warnings.append("Original code contains syntax errors - aborting refactoring")
                    return result
            
            # Phase 1: Gather context
            context = self._gather_context(code, language, file_path)
            result.git_context = context.get('git_context')
            
            # Phase 2: Get LLM suggestions (if enabled)
            llm_suggestions = None
            if self.config.enable_llm_suggestions and self.config.mode != RefactorMode.AST_ONLY:
                llm_suggestions = self._get_llm_suggestions(code, language, context)
                result.llm_suggestions = llm_suggestions
            
            # Phase 3: Apply AST transformations (if enabled)
            refactored_code = code
            if self.config.enable_ast_transforms and self.config.mode != RefactorMode.LLM_ONLY:
                refactored_code = self._apply_ast_transformations(
                    code, language, llm_suggestions, result
                )
            
            # Phase 4: Apply LLM suggestions (if enabled and not AST-only)
            if llm_suggestions and self.config.mode != RefactorMode.AST_ONLY:
                refactored_code = self._apply_llm_suggestions(
                    refactored_code, language, llm_suggestions, result
                )
            
            # Phase 5: Validate result
            if self.config.validate_syntax:
                validation_errors = self._validate_syntax(refactored_code, language)
                result.validation_errors = validation_errors
                
                if validation_errors:
                    # Phase 5.1: Retry with full folder context if syntax errors persist
                    retry_result = self._retry_with_folder_context(
                        code, language, file_path, result, validation_errors
                    )
                    
                    if retry_result.success and not retry_result.validation_errors:
                        # Retry succeeded
                        refactored_code = retry_result.refactored_code
                        result.validation_errors = []
                        result.warnings.append("Initial refactoring failed, succeeded with folder context")
                        # Merge retry results
                        result.renames_applied.extend(retry_result.renames_applied)
                        result.docstrings_added.extend(retry_result.docstrings_added)
                        result.transformations_applied.extend(retry_result.transformations_applied)
                    else:
                        # Retry also failed - provide clear error message
                        result.success = False
                        result.validation_errors = [
                            "Code contains syntax errors that cannot be automatically fixed.",
                            "Original errors: " + "; ".join(validation_errors),
                            "The code cannot be processed due to persistent syntax issues.",
                            "Please manually fix the syntax errors before attempting refactoring."
                        ]
                        result.warnings.append("Unable to process - syntax errors persist after retry with folder context")
                        refactored_code = code
                        return result
            
            # Update result - only set success=True if no validation errors
            result.refactored_code = refactored_code
            result.success = len(result.validation_errors) == 0
            result.processing_time = time.time() - start_time
            result.lines_changed = self._count_changed_lines(code, refactored_code)
            
            # Update statistics
            self.stats['files_processed'] += 1
            if llm_suggestions:
                self.stats['total_suggestions'] += (
                    len(llm_suggestions.renames) + 
                    len(llm_suggestions.docstrings) + 
                    len(llm_suggestions.transformations)
                )
            self.stats['applied_changes'] += len(result.renames_applied) + len(result.docstrings_added) + len(result.transformations_applied)
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            return self._create_error_result(
                code, file_path, language, 
                f"Refactoring error: {e}", start_time
            )
    
    def _gather_context(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """Gather context information for refactoring"""
        context = {
            'file_path': file_path,
            'language': language,
            'file_size': len(code),
            'line_count': len(code.split('\n'))
        }
        
        # Add Git context if enabled
        if self.config.enable_git_context:
            try:
                git_context = self.git_integrator.get_refactoring_context(file_path, language)
                context['git_context'] = git_context
            except Exception as e:
                context['git_context'] = {'error': str(e)}
        
        return context
    
    def _get_llm_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> Optional[LLMResponse]:
        """Get suggestions from LLM"""
        try:
            suggestions = self.llm_suggestor.get_suggestions(code, language, context)
            
            # Validate and filter suggestions
            validated_suggestions = self.llm_suggestor.validate_suggestions(suggestions, code, language)
            
            return validated_suggestions
            
        except Exception as e:
            print(f"Error getting LLM suggestions: {e}")
            return None
    
    def _apply_ast_transformations(self, code: str, language: str, 
                                 llm_suggestions: Optional[LLMResponse], 
                                 result: RefactorResult) -> str:
        """Apply AST-based transformations"""
        try:
            # Get language adapter
            adapter_class = LANGUAGE_ADAPTERS.get(language)
            if not adapter_class:
                result.warnings.append(f"No AST adapter available for {language}")
                return code
            
            adapter = adapter_class()
            
            # Apply transformations based on mode
            if self.config.mode == RefactorMode.CONSERVATIVE:
                # Only apply safe transformations
                transformed_code = adapter.apply_safe_transformations(code)
            elif self.config.mode == RefactorMode.BALANCED:
                # Apply safe and moderate transformations
                transformed_code = adapter.apply_transformations(code, risk_level="moderate")
            elif self.config.mode == RefactorMode.AGGRESSIVE:
                # Apply all transformations
                transformed_code = adapter.apply_transformations(code, risk_level="all")
            else:
                transformed_code = code
            
            # Track applied transformations
            if transformed_code != code:
                result.transformations_applied.append({
                    'type': 'ast_transformation',
                    'description': f'Applied {language} AST transformations',
                    'mode': self.config.mode.value
                })
            
            return transformed_code
            
        except Exception as e:
            result.warnings.append(f"AST transformation failed: {e}")
            return code
    
    def _apply_llm_suggestions(self, code: str, language: str, 
                             suggestions: LLMResponse, 
                             result: RefactorResult) -> str:
        """Apply LLM suggestions to code"""
        try:
            # Get language adapter for safe application
            adapter_class = LANGUAGE_ADAPTERS.get(language)
            if not adapter_class:
                result.warnings.append(f"No adapter available for applying {language} suggestions")
                return code
            
            adapter = adapter_class()
            current_code = code
            
            # Apply renames
            for rename in suggestions.renames:
                if rename.confidence >= self.config.confidence_threshold:
                    try:
                        new_code = adapter.apply_rename(current_code, rename.old_name, rename.new_name)
                        if new_code != current_code:
                            current_code = new_code
                            result.renames_applied.append({
                                'old_name': rename.old_name,
                                'new_name': rename.new_name,
                                'reason': rename.reason,
                                'confidence': rename.confidence
                            })
                    except Exception as e:
                        result.suggestions_skipped.append({
                            'type': 'rename',
                            'suggestion': asdict(rename),
                            'reason': f"Application failed: {e}"
                        })
                else:
                    result.suggestions_skipped.append({
                        'type': 'rename',
                        'suggestion': asdict(rename),
                        'reason': f"Low confidence: {rename.confidence}"
                    })
            
            # Apply docstrings
            for docstring in suggestions.docstrings:
                try:
                    new_code = adapter.add_docstring(
                        current_code, 
                        docstring.target_name, 
                        docstring.docstring,
                        docstring.target_type
                    )
                    if new_code != current_code:
                        current_code = new_code
                        result.docstrings_added.append({
                            'target_type': docstring.target_type,
                            'target_name': docstring.target_name,
                            'style': docstring.style
                        })
                except Exception as e:
                    result.suggestions_skipped.append({
                        'type': 'docstring',
                        'suggestion': asdict(docstring),
                        'reason': f"Application failed: {e}"
                    })
            
            # Apply safe transformations suggested by LLM
            for transform in suggestions.transformations:
                if (transform.confidence >= self.config.confidence_threshold and 
                    transform.safety_level in ['safe', 'moderate']):
                    try:
                        new_code = adapter.apply_transformation(
                            current_code, 
                            transform.transformation_type,
                            transform.location
                        )
                        if new_code != current_code:
                            current_code = new_code
                            result.transformations_applied.append({
                                'type': transform.transformation_type,
                                'description': transform.description,
                                'location': transform.location,
                                'confidence': transform.confidence
                            })
                    except Exception as e:
                        result.suggestions_skipped.append({
                            'type': 'transformation',
                            'suggestion': asdict(transform),
                            'reason': f"Application failed: {e}"
                        })
                else:
                    result.suggestions_skipped.append({
                        'type': 'transformation',
                        'suggestion': asdict(transform),
                        'reason': f"Safety/confidence check failed"
                    })
            
            return current_code
            
        except Exception as e:
            result.warnings.append(f"LLM suggestion application failed: {e}")
            return code
    
    def _retry_with_folder_context(self, code: str, language: str, file_path: str, 
                                  original_result: 'RefactorResult', 
                                  validation_errors: List[str]) -> 'RefactorResult':
        """Retry refactoring with full folder context when syntax errors persist"""
        import time
        from .file_scanner import FileScanner
        
        start_time = time.time()
        
        try:
            # Create a new result for the retry attempt
            retry_result = RefactorResult(
                success=False,
                original_code=code,
                refactored_code=code,
                language=language,
                file_path=file_path,
                renames_applied=[],
                docstrings_added=[],
                transformations_applied=[],
                suggestions_skipped=[],
                processing_time=0,
                llm_suggestions=None,
                git_context=None,
                validation_errors=[],
                warnings=[]
            )
            
            # Get folder context
            folder_context = self._gather_folder_context(file_path, language)
            
            if not folder_context:
                retry_result.warnings.append("Could not gather folder context for retry")
                return retry_result
            
            # Enhanced context with folder information
            enhanced_context = {
                'file_path': file_path,
                'language': language,
                'file_size': len(code),
                'line_count': len(code.split('\n')),
                'folder_context': folder_context,
                'syntax_errors': validation_errors,
                'retry_attempt': True
            }
            
            # Get LLM suggestions with enhanced context for syntax fixing
            if self.config.enable_llm_suggestions:
                llm_suggestions = self._get_llm_suggestions_for_syntax_fix(
                    code, language, enhanced_context, validation_errors
                )
                retry_result.llm_suggestions = llm_suggestions
                
                if llm_suggestions:
                    # Apply syntax-focused transformations
                    refactored_code = self._apply_syntax_focused_suggestions(
                        code, language, llm_suggestions, retry_result
                    )
                    
                    # Validate the retry result
                    retry_validation_errors = self._validate_syntax(refactored_code, language)
                    retry_result.validation_errors = retry_validation_errors
                    
                    if not retry_validation_errors:
                        retry_result.success = True
                        retry_result.refactored_code = refactored_code
                        retry_result.warnings.append("Syntax errors fixed using folder context")
                    else:
                        retry_result.warnings.append("Retry with folder context still has syntax errors")
                        retry_result.refactored_code = code
                else:
                    retry_result.warnings.append("No LLM suggestions available for syntax fixing")
            else:
                retry_result.warnings.append("LLM suggestions disabled - cannot retry with folder context")
            
            retry_result.processing_time = time.time() - start_time
            return retry_result
            
        except Exception as e:
            retry_result.warnings.append(f"Error during folder context retry: {e}")
            retry_result.processing_time = time.time() - start_time
            return retry_result
    
    def _gather_folder_context(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """Gather context from the entire folder structure"""
        try:
            from .file_scanner import FileScanner
            from pathlib import Path
            
            file_path_obj = Path(file_path)
            folder_path = file_path_obj.parent
            
            # Scan the folder for related files
            scanner = FileScanner(max_file_size=512*1024)  # 512KB limit for context
            scan_result = scanner.scan_directory(str(folder_path), recursive=True)
            
            # Filter files by language and proximity
            related_files = []
            for file_info in scan_result.supported_files:
                if file_info.language == language and file_info.path != file_path_obj:
                    # Read file content for context (limit size)
                    try:
                        with open(file_info.path, 'r', encoding='utf-8') as f:
                            content = f.read()[:2048]  # First 2KB only
                        related_files.append({
                            'path': str(file_info.relative_path),
                            'content_preview': content,
                            'size': file_info.size_bytes
                        })
                    except Exception:
                        continue
            
            # Limit to most relevant files (max 5)
            related_files = sorted(related_files, key=lambda x: x['size'])[:5]
            
            return {
                'folder_path': str(folder_path),
                'total_files': len(scan_result.supported_files),
                'related_files': related_files,
                'language_stats': scan_result.language_stats.get(language, {})
            }
            
        except Exception as e:
            print(f"Error gathering folder context: {e}")
            return None
    
    def _get_llm_suggestions_for_syntax_fix(self, code: str, language: str, 
                                           context: Dict[str, Any], 
                                           validation_errors: List[str]) -> Optional['LLMResponse']:
        """Get LLM suggestions specifically focused on fixing syntax errors"""
        try:
            # Enhanced prompt for syntax fixing
            syntax_fix_context = {
                **context,
                'task_type': 'syntax_fix',
                'specific_errors': validation_errors,
                'instruction': (
                    "Focus on fixing syntax errors only. "
                    "Use the folder context to understand imports, dependencies, and patterns. "
                    "Preserve the original logic and functionality."
                )
            }
            
            suggestions = self.llm_suggestor.get_suggestions(code, language, syntax_fix_context)
            
            # Validate suggestions with focus on syntax correctness
            if suggestions:
                validated_suggestions = self.llm_suggestor.validate_suggestions(
                    suggestions, code, language
                )
                return validated_suggestions
            
            return None
            
        except Exception as e:
            print(f"Error getting syntax fix suggestions: {e}")
            return None
    
    def _apply_syntax_focused_suggestions(self, code: str, language: str, 
                                        suggestions: 'LLMResponse', 
                                        result: 'RefactorResult') -> str:
        """Apply LLM suggestions with focus on syntax fixing"""
        try:
            adapter_class = LANGUAGE_ADAPTERS.get(language)
            if not adapter_class:
                result.warnings.append(f"No adapter available for {language} syntax fixing")
                return code
            
            adapter = adapter_class()
            current_code = code
            
            # Apply transformations that might fix syntax issues
            for transform in suggestions.transformations:
                if transform.safety_level in ['safe', 'moderate']:
                    try:
                        new_code = adapter.apply_transformation(
                            current_code, 
                            transform.transformation_type,
                            transform.location
                        )
                        if new_code != current_code:
                            # Validate each step
                            step_errors = self._validate_syntax(new_code, language)
                            if not step_errors:  # Only keep changes that don't introduce errors
                                current_code = new_code
                                result.transformations_applied.append({
                                    'type': transform.transformation_type,
                                    'description': f'Syntax fix: {transform.description}',
                                    'location': transform.location,
                                    'confidence': transform.confidence
                                })
                    except Exception as e:
                        result.suggestions_skipped.append({
                            'type': 'syntax_fix_transformation',
                            'suggestion': transform.transformation_type,
                            'reason': f"Application failed: {e}"
                        })
            
            # Apply safe renames that might resolve undefined variables
            for rename in suggestions.renames:
                if rename.confidence >= 0.8:  # Higher threshold for syntax fixes
                    try:
                        new_code = adapter.apply_rename(current_code, rename.old_name, rename.new_name)
                        if new_code != current_code:
                            step_errors = self._validate_syntax(new_code, language)
                            if not step_errors:
                                current_code = new_code
                                result.renames_applied.append({
                                    'old_name': rename.old_name,
                                    'new_name': rename.new_name,
                                    'reason': f'Syntax fix: {rename.reason}',
                                    'confidence': rename.confidence
                                })
                    except Exception as e:
                        result.suggestions_skipped.append({
                            'type': 'syntax_fix_rename',
                            'suggestion': f'{rename.old_name} -> {rename.new_name}',
                            'reason': f"Application failed: {e}"
                        })
            
            return current_code
            
        except Exception as e:
            result.warnings.append(f"Syntax-focused suggestion application failed: {e}")
            return code
    
    def _validate_syntax(self, code: str, language: str) -> List[str]:
        """Validate syntax of refactored code"""
        errors = []
        
        try:
            adapter_class = LANGUAGE_ADAPTERS.get(language)
            if adapter_class:
                adapter = adapter_class()
                if hasattr(adapter, 'validate_syntax'):
                    is_valid, error_msg = adapter.validate_syntax(code)
                    if not is_valid:
                        errors.append(error_msg)
            else:
                errors.append(f"No syntax validator available for {language}")
                
        except Exception as e:
            errors.append(f"Syntax validation error: {e}")
        
        return errors
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension"""
        extension = file_path.suffix.lower()
        return EXTENSION_MAP.get(extension)
    
    def _count_changed_lines(self, original: str, refactored: str) -> int:
        """Count number of changed lines"""
        original_lines = original.split('\n')
        refactored_lines = refactored.split('\n')
        
        changes = 0
        max_len = max(len(original_lines), len(refactored_lines))
        
        for i in range(max_len):
            orig_line = original_lines[i] if i < len(original_lines) else ""
            refact_line = refactored_lines[i] if i < len(refactored_lines) else ""
            
            if orig_line != refact_line:
                changes += 1
        
        return changes
    
    def _create_error_result(self, code: str, file_path: str, language: str, 
                           error_msg: str, start_time: float) -> RefactorResult:
        """Create error result"""
        return RefactorResult(
            success=False,
            original_code=code,
            refactored_code=code,
            language=language,
            file_path=file_path,
            renames_applied=[],
            docstrings_added=[],
            transformations_applied=[],
            suggestions_skipped=[],
            processing_time=time.time() - start_time,
            llm_suggestions=None,
            git_context=None,
            validation_errors=[error_msg],
            warnings=[]
        )
    
    def refactor_directory(self, directory_path: str, 
                          file_patterns: List[str] = None) -> List[RefactorResult]:
        """Refactor all supported files in a directory"""
        directory_path = Path(directory_path)
        results = []
        
        # Default patterns for supported languages
        if not file_patterns:
            file_patterns = ['*.py', '*.js', '*.jsx', '*.java', '*.cpp', '*.c', '*.h']
        
        # Find all matching files
        files_to_process = []
        for pattern in file_patterns:
            files_to_process.extend(directory_path.rglob(pattern))
        
        print(f"Found {len(files_to_process)} files to process")
        
        # Process each file
        for file_path in files_to_process:
            print(f"Processing: {file_path}")
            result = self.refactor_file(str(file_path))
            results.append(result)
            
            if result.success:
                print(f"  ✓ Success: {len(result.renames_applied)} renames, "
                      f"{len(result.docstrings_added)} docstrings, "
                      f"{len(result.transformations_applied)} transformations")
            else:
                print(f"  ✗ Failed: {result.validation_errors}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            'success_rate': (self.stats['files_processed'] - self.stats['errors']) / max(1, self.stats['files_processed']),
            'avg_suggestions_per_file': self.stats['total_suggestions'] / max(1, self.stats['files_processed']),
            'avg_applied_per_file': self.stats['applied_changes'] / max(1, self.stats['files_processed'])
        }
    
    def export_results(self, results: List[RefactorResult], output_file: str):
        """Export refactoring results to JSON file"""
        export_data = {
            'timestamp': time.time(),
            'config': asdict(self.config),
            'statistics': self.get_statistics(),
            'results': []
        }
        
        for result in results:
            result_data = asdict(result)
            # Convert LLMResponse to dict if present
            if result.llm_suggestions:
                result_data['llm_suggestions'] = asdict(result.llm_suggestions)
            export_data['results'].append(result_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Results exported to: {output_file}")