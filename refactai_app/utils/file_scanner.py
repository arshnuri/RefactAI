#!/usr/bin/env python3
"""
File Scanner Module

Recursively scans directories to detect supported file types for refactoring.
Provides filtering, categorization, and analysis capabilities.
"""

import os
import re
import mimetypes
from typing import Dict, List, Set, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import fnmatch
import hashlib


@dataclass
class FileInfo:
    """Information about a scanned file"""
    path: Path
    relative_path: Path
    language: str
    size_bytes: int
    line_count: int
    extension: str
    encoding: str
    is_binary: bool
    last_modified: float
    file_hash: str
    complexity_estimate: Optional[float] = None
    
    def __post_init__(self):
        """Calculate additional properties"""
        if self.size_bytes > 0 and self.line_count > 0:
            self.avg_line_length = self.size_bytes / self.line_count
        else:
            self.avg_line_length = 0


@dataclass
class ScanResult:
    """Result of directory scanning"""
    root_path: Path
    total_files: int
    supported_files: List[FileInfo]
    unsupported_files: List[Path]
    binary_files: List[Path]
    large_files: List[Path]
    empty_files: List[Path]
    
    # Statistics by language
    language_stats: Dict[str, Dict[str, Any]]
    
    # Scan metadata
    scan_time: float
    filters_applied: List[str]
    errors: List[str]


class FileScanner:
    """Scanner for detecting and analyzing code files"""
    
    # Supported languages and their extensions
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyw', '.pyi'],
        'javascript': ['.js', '.mjs', '.cjs'],
        'jsx': ['.jsx'],
        'typescript': ['.ts'],
        'tsx': ['.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.cxx', '.cc', '.c++'],
        'c': ['.c'],
        'header': ['.h', '.hpp', '.hxx', '.h++'],
        'csharp': ['.cs'],
        'go': ['.go'],
        'rust': ['.rs'],
        'php': ['.php'],
        'ruby': ['.rb'],
        'swift': ['.swift'],
        'kotlin': ['.kt', '.kts'],
        'scala': ['.scala'],
        'r': ['.r', '.R'],
        'matlab': ['.m'],
        'shell': ['.sh', '.bash', '.zsh', '.fish'],
        'powershell': ['.ps1'],
        'sql': ['.sql'],
        'html': ['.html', '.htm'],
        'css': ['.css', '.scss', '.sass', '.less'],
        'xml': ['.xml'],
        'json': ['.json'],
        'yaml': ['.yaml', '.yml'],
        'toml': ['.toml'],
        'markdown': ['.md', '.markdown']
    }
    
    # Currently supported for refactoring
    REFACTORABLE_LANGUAGES = {
        'python', 'javascript', 'jsx', 'typescript', 'tsx', 'java', 'cpp', 'c'
    }
    
    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.obj', '.o',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.ttf', '.otf', '.woff', '.woff2',
        '.pyc', '.pyo', '.class', '.jar'
    }
    
    # Directories to skip by default
    SKIP_DIRECTORIES = {
        '.git', '.svn', '.hg', '.bzr',
        'node_modules', '__pycache__', '.pytest_cache',
        'build', 'dist', 'target', 'bin', 'obj',
        '.vscode', '.idea', '.vs',
        'venv', 'env', '.env', 'virtualenv',
        'coverage', '.coverage', '.nyc_output',
        'logs', 'log', 'tmp', 'temp'
    }
    
    def __init__(self, max_file_size: int = 1024 * 1024,  # 1MB default
                 max_line_count: int = 10000,
                 include_patterns: List[str] = None,
                 exclude_patterns: List[str] = None,
                 skip_directories: Set[str] = None):
        
        self.max_file_size = max_file_size
        self.max_line_count = max_line_count
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.skip_directories = skip_directories or self.SKIP_DIRECTORIES.copy()
        
        # Build extension to language mapping
        self.ext_to_language = {}
        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            for ext in extensions:
                self.ext_to_language[ext.lower()] = language
    
    def scan_directory(self, root_path: str, 
                      recursive: bool = True,
                      follow_symlinks: bool = False) -> ScanResult:
        """Scan directory for code files"""
        import time
        start_time = time.time()
        
        root_path = Path(root_path).resolve()
        if not root_path.exists():
            raise ValueError(f"Directory does not exist: {root_path}")
        
        supported_files = []
        unsupported_files = []
        binary_files = []
        large_files = []
        empty_files = []
        errors = []
        total_files = 0
        
        # Scan files
        try:
            if recursive:
                file_iterator = root_path.rglob('*')
            else:
                file_iterator = root_path.iterdir()
            
            for file_path in file_iterator:
                if not file_path.is_file():
                    continue
                
                # Skip if in excluded directory
                if self._should_skip_file(file_path, root_path):
                    continue
                
                total_files += 1
                
                try:
                    file_info = self._analyze_file(file_path, root_path)
                    
                    if file_info.is_binary:
                        binary_files.append(file_path)
                    elif file_info.size_bytes == 0:
                        empty_files.append(file_path)
                    elif file_info.size_bytes > self.max_file_size:
                        large_files.append(file_path)
                    elif file_info.language in self.REFACTORABLE_LANGUAGES:
                        supported_files.append(file_info)
                    else:
                        unsupported_files.append(file_path)
                        
                except Exception as e:
                    errors.append(f"Error analyzing {file_path}: {e}")
                    
        except Exception as e:
            errors.append(f"Error scanning directory: {e}")
        
        # Calculate language statistics
        language_stats = self._calculate_language_stats(supported_files)
        
        # Create result
        scan_time = time.time() - start_time
        filters_applied = self._get_applied_filters()
        
        return ScanResult(
            root_path=root_path,
            total_files=total_files,
            supported_files=supported_files,
            unsupported_files=unsupported_files,
            binary_files=binary_files,
            large_files=large_files,
            empty_files=empty_files,
            language_stats=language_stats,
            scan_time=scan_time,
            filters_applied=filters_applied,
            errors=errors
        )
    
    def _should_skip_file(self, file_path: Path, root_path: Path) -> bool:
        """Check if file should be skipped"""
        # Check if file is in a skipped directory
        relative_path = file_path.relative_to(root_path)
        for part in relative_path.parts[:-1]:  # Exclude filename
            if part in self.skip_directories:
                return True
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(str(relative_path), pattern):
                return True
        
        # Check include patterns (if specified)
        if self.include_patterns:
            included = False
            for pattern in self.include_patterns:
                if fnmatch.fnmatch(str(relative_path), pattern):
                    included = True
                    break
            if not included:
                return True
        
        return False
    
    def _analyze_file(self, file_path: Path, root_path: Path) -> FileInfo:
        """Analyze a single file"""
        # Get basic file info
        stat = file_path.stat()
        size_bytes = stat.st_size
        last_modified = stat.st_mtime
        extension = file_path.suffix.lower()
        relative_path = file_path.relative_to(root_path)
        
        # Detect if binary
        is_binary = self._is_binary_file(file_path)
        
        # Initialize defaults
        line_count = 0
        encoding = 'utf-8'
        file_hash = ''
        
        if not is_binary and size_bytes > 0:
            try:
                # Detect encoding and read file
                encoding = self._detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Count lines
                line_count = len(content.split('\n'))
                
                # Calculate hash
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
            except Exception as e:
                # If we can't read it, treat as binary
                is_binary = True
                encoding = 'unknown'
        
        # Detect language
        language = self._detect_language(file_path, is_binary)
        
        return FileInfo(
            path=file_path,
            relative_path=relative_path,
            language=language,
            size_bytes=size_bytes,
            line_count=line_count,
            extension=extension,
            encoding=encoding,
            is_binary=is_binary,
            last_modified=last_modified,
            file_hash=file_hash
        )
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary"""
        # Check extension first
        if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and not mime_type.startswith('text/'):
            return True
        
        # Check file content (sample first 1024 bytes)
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Null bytes indicate binary
                    return True
                
                # Check for high ratio of non-printable characters
                if len(chunk) > 0:
                    printable_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in [9, 10, 13])
                    ratio = printable_chars / len(chunk)
                    if ratio < 0.7:  # Less than 70% printable
                        return True
        except Exception:
            return True
        
        return False
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Sample first 10KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8') or 'utf-8'
        except ImportError:
            # Fallback without chardet
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Try to read a chunk
                    return encoding
                except UnicodeDecodeError:
                    continue
            return 'utf-8'  # Default fallback
    
    def _detect_language(self, file_path: Path, is_binary: bool) -> str:
        """Detect programming language"""
        if is_binary:
            return 'binary'
        
        extension = file_path.suffix.lower()
        
        # Check extension mapping
        if extension in self.ext_to_language:
            return self.ext_to_language[extension]
        
        # Special cases based on filename
        filename = file_path.name.lower()
        
        # Makefiles
        if filename in ['makefile', 'gnumakefile'] or filename.startswith('makefile.'):
            return 'makefile'
        
        # Docker files
        if filename in ['dockerfile'] or filename.startswith('dockerfile.'):
            return 'dockerfile'
        
        # Configuration files
        if filename in ['.gitignore', '.dockerignore']:
            return 'gitignore'
        
        # Try to detect from shebang
        if extension == '' or extension == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#!'):
                        if 'python' in first_line:
                            return 'python'
                        elif 'node' in first_line or 'javascript' in first_line:
                            return 'javascript'
                        elif 'bash' in first_line or 'sh' in first_line:
                            return 'shell'
            except Exception:
                pass
        
        return 'unknown'
    
    def _calculate_language_stats(self, files: List[FileInfo]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics by language"""
        stats = defaultdict(lambda: {
            'file_count': 0,
            'total_size': 0,
            'total_lines': 0,
            'avg_file_size': 0,
            'avg_lines_per_file': 0,
            'largest_file': None,
            'smallest_file': None
        })
        
        for file_info in files:
            lang = file_info.language
            lang_stats = stats[lang]
            
            lang_stats['file_count'] += 1
            lang_stats['total_size'] += file_info.size_bytes
            lang_stats['total_lines'] += file_info.line_count
            
            # Track largest and smallest files
            if (lang_stats['largest_file'] is None or 
                file_info.size_bytes > lang_stats['largest_file']['size']):
                lang_stats['largest_file'] = {
                    'path': str(file_info.relative_path),
                    'size': file_info.size_bytes,
                    'lines': file_info.line_count
                }
            
            if (lang_stats['smallest_file'] is None or 
                file_info.size_bytes < lang_stats['smallest_file']['size']):
                lang_stats['smallest_file'] = {
                    'path': str(file_info.relative_path),
                    'size': file_info.size_bytes,
                    'lines': file_info.line_count
                }
        
        # Calculate averages
        for lang, lang_stats in stats.items():
            if lang_stats['file_count'] > 0:
                lang_stats['avg_file_size'] = lang_stats['total_size'] / lang_stats['file_count']
                lang_stats['avg_lines_per_file'] = lang_stats['total_lines'] / lang_stats['file_count']
        
        return dict(stats)
    
    def _get_applied_filters(self) -> List[str]:
        """Get list of applied filters"""
        filters = []
        
        if self.max_file_size < float('inf'):
            filters.append(f"max_file_size: {self.max_file_size} bytes")
        
        if self.max_line_count < float('inf'):
            filters.append(f"max_line_count: {self.max_line_count}")
        
        if self.include_patterns:
            filters.append(f"include_patterns: {self.include_patterns}")
        
        if self.exclude_patterns:
            filters.append(f"exclude_patterns: {self.exclude_patterns}")
        
        if self.skip_directories != self.SKIP_DIRECTORIES:
            filters.append(f"custom_skip_directories: {self.skip_directories}")
        
        return filters
    
    def filter_by_language(self, files: List[FileInfo], languages: List[str]) -> List[FileInfo]:
        """Filter files by programming language"""
        return [f for f in files if f.language in languages]
    
    def filter_by_size(self, files: List[FileInfo], 
                      min_size: int = 0, max_size: int = None) -> List[FileInfo]:
        """Filter files by size"""
        if max_size is None:
            max_size = float('inf')
        
        return [f for f in files if min_size <= f.size_bytes <= max_size]
    
    def filter_by_complexity(self, files: List[FileInfo], 
                           min_complexity: float = 0, 
                           max_complexity: float = None) -> List[FileInfo]:
        """Filter files by estimated complexity"""
        if max_complexity is None:
            max_complexity = float('inf')
        
        return [f for f in files 
                if f.complexity_estimate is not None and 
                min_complexity <= f.complexity_estimate <= max_complexity]
    
    def get_refactorable_files(self, scan_result: ScanResult) -> List[FileInfo]:
        """Get only files that can be refactored"""
        return [f for f in scan_result.supported_files 
                if f.language in self.REFACTORABLE_LANGUAGES]
    
    def estimate_processing_time(self, files: List[FileInfo]) -> Dict[str, float]:
        """Estimate processing time for files"""
        # Rough estimates based on file size and complexity
        total_time = 0
        by_language = defaultdict(float)
        
        for file_info in files:
            # Base time: 0.1 seconds per 1000 lines
            base_time = (file_info.line_count / 1000) * 0.1
            
            # Language complexity multiplier
            multipliers = {
                'python': 1.0,
                'javascript': 1.2,
                'jsx': 1.3,
                'typescript': 1.4,
                'java': 1.5,
                'cpp': 2.0,
                'c': 1.8
            }
            
            multiplier = multipliers.get(file_info.language, 1.0)
            estimated_time = base_time * multiplier
            
            total_time += estimated_time
            by_language[file_info.language] += estimated_time
        
        return {
            'total_seconds': total_time,
            'total_minutes': total_time / 60,
            'by_language': dict(by_language)
        }
    
    def generate_report(self, scan_result: ScanResult) -> str:
        """Generate a human-readable scan report"""
        report = []
        report.append(f"📁 Directory Scan Report")
        report.append(f"{'=' * 50}")
        report.append(f"Root Path: {scan_result.root_path}")
        report.append(f"Scan Time: {scan_result.scan_time:.2f} seconds")
        report.append(f"Total Files Found: {scan_result.total_files}")
        report.append("")
        
        # File categories
        report.append(f"📊 File Categories:")
        report.append(f"  ✅ Supported for refactoring: {len(scan_result.supported_files)}")
        report.append(f"  ❌ Unsupported: {len(scan_result.unsupported_files)}")
        report.append(f"  📦 Binary files: {len(scan_result.binary_files)}")
        report.append(f"  📏 Large files (skipped): {len(scan_result.large_files)}")
        report.append(f"  📄 Empty files: {len(scan_result.empty_files)}")
        report.append("")
        
        # Language statistics
        if scan_result.language_stats:
            report.append(f"🔤 Language Statistics:")
            for lang, stats in sorted(scan_result.language_stats.items()):
                report.append(f"  {lang.title()}:")
                report.append(f"    Files: {stats['file_count']}")
                report.append(f"    Total Size: {stats['total_size']:,} bytes")
                report.append(f"    Total Lines: {stats['total_lines']:,}")
                report.append(f"    Avg File Size: {stats['avg_file_size']:.0f} bytes")
                report.append(f"    Avg Lines/File: {stats['avg_lines_per_file']:.0f}")
            report.append("")
        
        # Processing estimates
        refactorable = self.get_refactorable_files(scan_result)
        if refactorable:
            estimates = self.estimate_processing_time(refactorable)
            report.append(f"⏱️  Processing Estimates:")
            report.append(f"  Refactorable Files: {len(refactorable)}")
            report.append(f"  Estimated Time: {estimates['total_minutes']:.1f} minutes")
            report.append("")
        
        # Filters applied
        if scan_result.filters_applied:
            report.append(f"🔍 Filters Applied:")
            for filter_desc in scan_result.filters_applied:
                report.append(f"  - {filter_desc}")
            report.append("")
        
        # Errors
        if scan_result.errors:
            report.append(f"⚠️  Errors ({len(scan_result.errors)}):")
            for error in scan_result.errors[:10]:  # Show first 10 errors
                report.append(f"  - {error}")
            if len(scan_result.errors) > 10:
                report.append(f"  ... and {len(scan_result.errors) - 10} more")
        
        return "\n".join(report)