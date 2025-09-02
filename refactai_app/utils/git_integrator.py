#!/usr/bin/env python3
"""
Git Integration Module

Provides Git-aware context tracking for the hybrid refactoring engine.
Tracks function reuse, naming patterns, and code evolution across commits.
"""

import os
import re
import subprocess
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FunctionInfo:
    """Information about a function across commits"""
    name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str
    body_hash: str
    commit_hash: str
    timestamp: datetime
    language: str


@dataclass
class CodePattern:
    """Represents a code pattern found across commits"""
    pattern_type: str  # 'function_reuse', 'naming_pattern', 'refactor_pattern'
    description: str
    occurrences: List[Dict[str, Any]]
    confidence: float
    suggested_action: str


class GitIntegrator:
    """Git integration for context-aware refactoring"""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.getcwd()
        self.git_available = self._check_git_availability()
        self.function_cache = {}
        self.pattern_cache = {}
        
    def _check_git_availability(self) -> bool:
        """Check if Git is available and repo is initialized"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_recent_commits(self, days: int = 30, max_commits: int = 100) -> List[Dict[str, Any]]:
        """Get recent commits for analysis"""
        if not self.git_available:
            return []
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            result = subprocess.run([
                'git', 'log',
                f'--since={since_date}',
                f'--max-count={max_commits}',
                '--pretty=format:%H|%an|%ad|%s',
                '--date=iso'
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return commits
            
        except Exception as e:
            print(f"Error getting recent commits: {e}")
            return []
    
    def get_file_history(self, file_path: str, max_commits: int = 20) -> List[Dict[str, Any]]:
        """Get commit history for a specific file"""
        if not self.git_available:
            return []
        
        try:
            result = subprocess.run([
                'git', 'log',
                f'--max-count={max_commits}',
                '--pretty=format:%H|%an|%ad|%s',
                '--date=iso',
                '--', file_path
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            history = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        history.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return history
            
        except Exception as e:
            print(f"Error getting file history: {e}")
            return []
    
    def get_file_content_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """Get file content at a specific commit"""
        if not self.git_available:
            return None
        
        try:
            result = subprocess.run([
                'git', 'show',
                f'{commit_hash}:{file_path}'
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            return None
            
        except Exception as e:
            print(f"Error getting file content at commit: {e}")
            return None
    
    def extract_functions_from_code(self, code: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract function definitions from code"""
        functions = []
        
        if language == 'python':
            functions.extend(self._extract_python_functions(code, file_path))
        elif language == 'javascript':
            functions.extend(self._extract_javascript_functions(code, file_path))
        elif language == 'java':
            functions.extend(self._extract_java_functions(code, file_path))
        elif language in ['cpp', 'c']:
            functions.extend(self._extract_cpp_functions(code, file_path))
        
        return functions
    
    def _extract_python_functions(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Python function definitions"""
        functions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Match function definitions
            func_match = re.match(r'^\s*(def|async def)\s+(\w+)\s*\(([^)]*)\)\s*:', line)
            if func_match:
                func_type = func_match.group(1)
                func_name = func_match.group(2)
                func_params = func_match.group(3)
                
                # Find function end (simplified)
                end_line = self._find_python_function_end(lines, i)
                
                functions.append({
                    'name': func_name,
                    'type': func_type,
                    'params': func_params,
                    'start_line': i + 1,
                    'end_line': end_line,
                    'signature': f"{func_type} {func_name}({func_params})",
                    'file_path': file_path,
                    'language': 'python'
                })
        
        return functions
    
    def _extract_javascript_functions(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract JavaScript function definitions"""
        functions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Match various JavaScript function patterns
            patterns = [
                r'^\s*function\s+(\w+)\s*\(([^)]*)\)',  # function name()
                r'^\s*const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>',  # const name = () =>
                r'^\s*(\w+)\s*:\s*function\s*\(([^)]*)\)',  # name: function()
                r'^\s*async\s+function\s+(\w+)\s*\(([^)]*)\)'  # async function name()
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(1)
                    func_params = match.group(2) if len(match.groups()) > 1 else ''
                    
                    functions.append({
                        'name': func_name,
                        'type': 'function',
                        'params': func_params,
                        'start_line': i + 1,
                        'end_line': i + 1,  # Simplified
                        'signature': f"function {func_name}({func_params})",
                        'file_path': file_path,
                        'language': 'javascript'
                    })
                    break
        
        return functions
    
    def _extract_java_functions(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Java method definitions"""
        functions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Match Java method definitions
            method_match = re.match(
                r'^\s*(public|private|protected)?\s*(static)?\s*(\w+)\s+(\w+)\s*\(([^)]*)\)',
                line
            )
            if method_match:
                visibility = method_match.group(1) or 'package'
                static = method_match.group(2) or ''
                return_type = method_match.group(3)
                method_name = method_match.group(4)
                params = method_match.group(5)
                
                functions.append({
                    'name': method_name,
                    'type': 'method',
                    'visibility': visibility,
                    'static': bool(static),
                    'return_type': return_type,
                    'params': params,
                    'start_line': i + 1,
                    'end_line': i + 1,  # Simplified
                    'signature': f"{visibility} {static} {return_type} {method_name}({params})".strip(),
                    'file_path': file_path,
                    'language': 'java'
                })
        
        return functions
    
    def _extract_cpp_functions(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract C/C++ function definitions"""
        functions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Match C/C++ function definitions (simplified)
            func_match = re.match(
                r'^\s*(\w+(?:\s*\*)?\s+)?(\w+)\s*\(([^)]*)\)\s*{?',
                line
            )
            if func_match and not line.strip().startswith('//'):
                return_type = func_match.group(1) or 'void'
                func_name = func_match.group(2)
                params = func_match.group(3)
                
                # Skip common keywords that aren't functions
                if func_name not in ['if', 'for', 'while', 'switch', 'return']:
                    functions.append({
                        'name': func_name,
                        'type': 'function',
                        'return_type': return_type.strip(),
                        'params': params,
                        'start_line': i + 1,
                        'end_line': i + 1,  # Simplified
                        'signature': f"{return_type}{func_name}({params})",
                        'file_path': file_path,
                        'language': 'cpp'
                    })
        
        return functions
    
    def _find_python_function_end(self, lines: List[str], start_line: int) -> int:
        """Find the end line of a Python function (simplified)"""
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level:
                    return i
        
        return len(lines)
    
    def analyze_function_reuse(self, file_path: str, language: str) -> List[CodePattern]:
        """Analyze function reuse patterns across commits"""
        patterns = []
        
        if not self.git_available:
            return patterns
        
        try:
            # Get file history
            history = self.get_file_history(file_path)
            
            # Track functions across commits
            function_evolution = defaultdict(list)
            
            for commit in history[:10]:  # Analyze last 10 commits
                content = self.get_file_content_at_commit(file_path, commit['hash'])
                if content:
                    functions = self.extract_functions_from_code(content, language, file_path)
                    
                    for func in functions:
                        func['commit'] = commit
                        function_evolution[func['name']].append(func)
            
            # Analyze patterns
            for func_name, versions in function_evolution.items():
                if len(versions) > 1:
                    # Check for function reuse/renaming patterns
                    signatures = [v['signature'] for v in versions]
                    if len(set(signatures)) > 1:
                        patterns.append(CodePattern(
                            pattern_type='function_evolution',
                            description=f"Function '{func_name}' has evolved across commits",
                            occurrences=[{
                                'function': func_name,
                                'versions': len(versions),
                                'signatures': signatures
                            }],
                            confidence=0.8,
                            suggested_action=f"Consider standardizing '{func_name}' signature"
                        ))
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing function reuse: {e}")
            return []
    
    def detect_naming_patterns(self, file_paths: List[str]) -> List[CodePattern]:
        """Detect naming patterns across the codebase"""
        patterns = []
        
        if not self.git_available:
            return patterns
        
        try:
            # Collect function names from recent commits
            all_functions = []
            
            for file_path in file_paths:
                history = self.get_file_history(file_path, max_commits=5)
                
                for commit in history:
                    content = self.get_file_content_at_commit(file_path, commit['hash'])
                    if content:
                        # Detect language
                        ext = Path(file_path).suffix
                        language = self._detect_language_from_extension(ext)
                        
                        if language:
                            functions = self.extract_functions_from_code(content, language, file_path)
                            all_functions.extend(functions)
            
            # Analyze naming patterns
            naming_patterns = self._analyze_naming_conventions(all_functions)
            
            for pattern in naming_patterns:
                patterns.append(CodePattern(
                    pattern_type='naming_pattern',
                    description=pattern['description'],
                    occurrences=pattern['examples'],
                    confidence=pattern['confidence'],
                    suggested_action=pattern['suggestion']
                ))
            
            return patterns
            
        except Exception as e:
            print(f"Error detecting naming patterns: {e}")
            return []
    
    def _detect_language_from_extension(self, extension: str) -> Optional[str]:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp'
        }
        return ext_map.get(extension.lower())
    
    def _analyze_naming_conventions(self, functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze naming conventions in function list"""
        patterns = []
        
        # Group by language
        by_language = defaultdict(list)
        for func in functions:
            by_language[func['language']].append(func)
        
        for language, funcs in by_language.items():
            names = [f['name'] for f in funcs]
            
            # Check for snake_case vs camelCase consistency
            snake_case = sum(1 for name in names if '_' in name and name.islower())
            camel_case = sum(1 for name in names if '_' not in name and any(c.isupper() for c in name[1:]))
            
            total = len(names)
            if total > 5:  # Only analyze if we have enough samples
                if snake_case > camel_case * 2:
                    patterns.append({
                        'description': f'{language} codebase prefers snake_case naming',
                        'examples': [name for name in names if '_' in name][:5],
                        'confidence': min(0.9, snake_case / total),
                        'suggestion': 'Use snake_case for consistency'
                    })
                elif camel_case > snake_case * 2:
                    patterns.append({
                        'description': f'{language} codebase prefers camelCase naming',
                        'examples': [name for name in names if '_' not in name][:5],
                        'confidence': min(0.9, camel_case / total),
                        'suggestion': 'Use camelCase for consistency'
                    })
        
        return patterns
    
    def get_refactoring_context(self, file_path: str, language: str) -> Dict[str, Any]:
        """Get comprehensive refactoring context for a file"""
        context = {
            'git_available': self.git_available,
            'file_history': [],
            'function_patterns': [],
            'naming_patterns': [],
            'recent_changes': [],
            'suggestions': []
        }
        
        if not self.git_available:
            return context
        
        try:
            # Get file history
            context['file_history'] = self.get_file_history(file_path, max_commits=10)
            
            # Analyze function reuse patterns
            context['function_patterns'] = self.analyze_function_reuse(file_path, language)
            
            # Get naming patterns from related files
            related_files = self._find_related_files(file_path, language)
            context['naming_patterns'] = self.detect_naming_patterns(related_files)
            
            # Get recent changes
            context['recent_changes'] = self._get_recent_file_changes(file_path)
            
            # Generate suggestions based on context
            context['suggestions'] = self._generate_context_suggestions(context)
            
            return context
            
        except Exception as e:
            print(f"Error getting refactoring context: {e}")
            return context
    
    def _find_related_files(self, file_path: str, language: str) -> List[str]:
        """Find files related to the current file"""
        try:
            ext = Path(file_path).suffix
            
            # Find files with same extension
            result = subprocess.run([
                'git', 'ls-files',
                f'*{ext}'
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return [f for f in files if f and f != file_path][:20]  # Limit to 20 files
            
            return []
            
        except Exception:
            return []
    
    def _get_recent_file_changes(self, file_path: str) -> List[Dict[str, Any]]:
        """Get recent changes to the file"""
        try:
            result = subprocess.run([
                'git', 'log',
                '--max-count=5',
                '--pretty=format:%H|%s|%ad',
                '--date=relative',
                '--', file_path
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 2)
                    if len(parts) == 3:
                        changes.append({
                            'commit': parts[0],
                            'message': parts[1],
                            'date': parts[2]
                        })
            
            return changes
            
        except Exception:
            return []
    
    def _generate_context_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """Generate refactoring suggestions based on Git context"""
        suggestions = []
        
        # Suggest based on function patterns
        for pattern in context['function_patterns']:
            if pattern.pattern_type == 'function_evolution':
                suggestions.append(f"Consider reviewing function evolution: {pattern.description}")
        
        # Suggest based on naming patterns
        for pattern in context['naming_patterns']:
            if pattern.confidence > 0.7:
                suggestions.append(f"Follow naming convention: {pattern.suggested_action}")
        
        # Suggest based on recent changes
        if len(context['recent_changes']) > 3:
            suggestions.append("File has been frequently modified - consider refactoring for stability")
        
        return suggestions