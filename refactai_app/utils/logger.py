#!/usr/bin/env python3
"""
Logger Module

Provides comprehensive logging for the refactoring engine.
Tracks before/after diffs, operations, performance metrics, and errors.
"""

import os
import json
import time
import logging
import difflib
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib


class LogLevel(Enum):
    """Log levels for refactoring operations"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OperationType(Enum):
    """Types of refactoring operations"""
    RENAME = "rename"
    DOCSTRING = "docstring"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    SUGGESTION = "suggestion"
    FILE_SCAN = "file_scan"
    GIT_ANALYSIS = "git_analysis"
    LLM_REQUEST = "llm_request"


@dataclass
class LogEntry:
    """Single log entry"""
    timestamp: float
    level: LogLevel
    operation_type: OperationType
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'level': self.level.value,
            'operation_type': self.operation_type.value,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'function_name': self.function_name,
            'metadata': self.metadata or {}
        }


@dataclass
class DiffEntry:
    """Code diff entry"""
    file_path: str
    original_code: str
    refactored_code: str
    language: str
    timestamp: float
    operation_id: str
    changes_summary: Dict[str, Any]
    
    def __post_init__(self):
        """Calculate diff statistics"""
        self.original_lines = self.original_code.split('\n')
        self.refactored_lines = self.refactored_code.split('\n')
        self.lines_added = len(self.refactored_lines) - len(self.original_lines)
        self.lines_changed = self._count_changed_lines()
        self.similarity_ratio = difflib.SequenceMatcher(
            None, self.original_code, self.refactored_code
        ).ratio()
    
    def _count_changed_lines(self) -> int:
        """Count number of changed lines"""
        differ = difflib.unified_diff(
            self.original_lines, self.refactored_lines, lineterm=''
        )
        changes = 0
        for line in differ:
            if line.startswith('+') or line.startswith('-'):
                if not line.startswith('+++') and not line.startswith('---'):
                    changes += 1
        return changes
    
    def get_unified_diff(self, context_lines: int = 3) -> str:
        """Get unified diff format"""
        return '\n'.join(difflib.unified_diff(
            self.original_lines,
            self.refactored_lines,
            fromfile=f"{self.file_path} (original)",
            tofile=f"{self.file_path} (refactored)",
            lineterm='',
            n=context_lines
        ))
    
    def get_html_diff(self) -> str:
        """Get HTML diff format"""
        differ = difflib.HtmlDiff()
        return differ.make_file(
            self.original_lines,
            self.refactored_lines,
            fromdesc=f"{self.file_path} (original)",
            todesc=f"{self.file_path} (refactored)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'operation_id': self.operation_id,
            'changes_summary': self.changes_summary,
            'statistics': {
                'original_lines': len(self.original_lines),
                'refactored_lines': len(self.refactored_lines),
                'lines_added': self.lines_added,
                'lines_changed': self.lines_changed,
                'similarity_ratio': self.similarity_ratio
            },
            'original_hash': hashlib.md5(self.original_code.encode()).hexdigest(),
            'refactored_hash': hashlib.md5(self.refactored_code.encode()).hexdigest()
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_id: str
    operation_type: OperationType
    start_time: float
    end_time: float
    duration: float
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    line_count: Optional[int] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'start_datetime': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_datetime': datetime.fromtimestamp(self.end_time).isoformat(),
            'file_path': self.file_path,
            'file_size': self.file_size,
            'line_count': self.line_count,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage
        }


class RefactorLogger:
    """Main logger for refactoring operations"""
    
    def __init__(self, log_dir: str = "logs", 
                 enable_file_logging: bool = True,
                 enable_console_logging: bool = True,
                 log_level: LogLevel = LogLevel.INFO,
                 max_log_files: int = 10,
                 max_file_size: int = 10 * 1024 * 1024):  # 10MB
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.log_level = log_level
        self.max_log_files = max_log_files
        self.max_file_size = max_file_size
        
        # Storage for different types of logs
        self.log_entries: List[LogEntry] = []
        self.diff_entries: List[DiffEntry] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # Active operations tracking
        self.active_operations: Dict[str, float] = {}
        
        # Setup file logging
        self._setup_file_logging()
        
        # Setup console logging
        self._setup_console_logging()
        
        # Session info
        self.session_id = self._generate_session_id()
        self.session_start = time.time()
        
        self.log(LogLevel.INFO, OperationType.FILE_SCAN, 
                f"RefactorLogger initialized - Session: {self.session_id}")
    
    def _setup_file_logging(self):
        """Setup file logging"""
        if not self.enable_file_logging:
            return
        
        # Create log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.main_log_file = self.log_dir / f"refactor_{timestamp}.log"
        self.diff_log_file = self.log_dir / f"diffs_{timestamp}.json"
        self.performance_log_file = self.log_dir / f"performance_{timestamp}.json"
        
        # Setup Python logging
        self.logger = logging.getLogger('refactor_engine')
        self.logger.setLevel(getattr(logging, self.log_level.value.upper()))
        
        # File handler
        file_handler = logging.FileHandler(self.main_log_file)
        file_handler.setLevel(getattr(logging, self.log_level.value.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_console_logging(self):
        """Setup console logging"""
        if not self.enable_console_logging:
            return
        
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('refactor_engine')
            self.logger.setLevel(getattr(logging, self.log_level.value.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level.value.upper()))
        
        # Formatter for console (more compact)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{int(time.time())}_{os.getpid()}"
    
    def log(self, level: LogLevel, operation_type: OperationType, 
            message: str, file_path: str = None, line_number: int = None,
            function_name: str = None, metadata: Dict[str, Any] = None):
        """Log a message"""
        
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            operation_type=operation_type,
            message=message,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            metadata=metadata
        )
        
        self.log_entries.append(entry)
        
        # Log to Python logger if available
        if hasattr(self, 'logger'):
            log_msg = message
            if file_path:
                log_msg += f" [{file_path}"
                if line_number:
                    log_msg += f":{line_number}"
                log_msg += "]"
            
            getattr(self.logger, level.value)(log_msg)
    
    def log_diff(self, file_path: str, original_code: str, refactored_code: str,
                language: str, operation_id: str, changes_summary: Dict[str, Any]):
        """Log code diff"""
        
        diff_entry = DiffEntry(
            file_path=file_path,
            original_code=original_code,
            refactored_code=refactored_code,
            language=language,
            timestamp=time.time(),
            operation_id=operation_id,
            changes_summary=changes_summary
        )
        
        self.diff_entries.append(diff_entry)
        
        # Log summary
        self.log(
            LogLevel.INFO, OperationType.TRANSFORMATION,
            f"Code diff recorded: {diff_entry.lines_changed} lines changed, "
            f"similarity: {diff_entry.similarity_ratio:.2%}",
            file_path=file_path,
            metadata={
                'operation_id': operation_id,
                'lines_added': diff_entry.lines_added,
                'lines_changed': diff_entry.lines_changed,
                'similarity_ratio': diff_entry.similarity_ratio
            }
        )
    
    def start_operation(self, operation_type: OperationType, 
                       operation_id: str = None, file_path: str = None) -> str:
        """Start tracking an operation"""
        if operation_id is None:
            operation_id = f"{operation_type.value}_{int(time.time() * 1000)}"
        
        self.active_operations[operation_id] = time.time()
        
        self.log(
            LogLevel.DEBUG, operation_type,
            f"Started operation: {operation_id}",
            file_path=file_path,
            metadata={'operation_id': operation_id}
        )
        
        return operation_id
    
    def end_operation(self, operation_id: str, operation_type: OperationType = None,
                     file_path: str = None, file_size: int = None, 
                     line_count: int = None, success: bool = True):
        """End tracking an operation"""
        
        if operation_id not in self.active_operations:
            self.log(
                LogLevel.WARNING, OperationType.VALIDATION,
                f"Attempted to end unknown operation: {operation_id}"
            )
            return
        
        start_time = self.active_operations.pop(operation_id)
        end_time = time.time()
        duration = end_time - start_time
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            operation_id=operation_id,
            operation_type=operation_type or OperationType.TRANSFORMATION,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            file_path=file_path,
            file_size=file_size,
            line_count=line_count
        )
        
        self.performance_metrics.append(metrics)
        
        # Log completion
        status = "completed" if success else "failed"
        self.log(
            LogLevel.INFO if success else LogLevel.ERROR,
            operation_type or OperationType.TRANSFORMATION,
            f"Operation {status}: {operation_id} ({duration:.3f}s)",
            file_path=file_path,
            metadata={
                'operation_id': operation_id,
                'duration': duration,
                'success': success
            }
        )
    
    def log_error(self, operation_type: OperationType, error: Exception,
                 file_path: str = None, context: Dict[str, Any] = None):
        """Log an error"""
        
        self.log(
            LogLevel.ERROR, operation_type,
            f"Error: {type(error).__name__}: {str(error)}",
            file_path=file_path,
            metadata={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {}
            }
        )
    
    def log_llm_request(self, provider: str, model: str, tokens_used: int = None,
                       response_time: float = None, success: bool = True,
                       error_message: str = None):
        """Log LLM API request"""
        
        metadata = {
            'provider': provider,
            'model': model,
            'tokens_used': tokens_used,
            'response_time': response_time,
            'success': success
        }
        
        if error_message:
            metadata['error_message'] = error_message
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"LLM request to {provider}/{model}"
        if success:
            message += f" completed ({response_time:.2f}s, {tokens_used} tokens)"
        else:
            message += f" failed: {error_message}"
        
        self.log(level, OperationType.LLM_REQUEST, message, metadata=metadata)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        current_time = time.time()
        session_duration = current_time - self.session_start
        
        # Count operations by type
        operation_counts = {}
        for entry in self.log_entries:
            op_type = entry.operation_type.value
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        # Count log levels
        level_counts = {}
        for entry in self.log_entries:
            level = entry.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Performance statistics
        if self.performance_metrics:
            durations = [m.duration for m in self.performance_metrics]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0
        
        return {
            'session_id': self.session_id,
            'session_start': self.session_start,
            'session_duration': session_duration,
            'total_log_entries': len(self.log_entries),
            'total_diffs': len(self.diff_entries),
            'total_operations': len(self.performance_metrics),
            'active_operations': len(self.active_operations),
            'operation_counts': operation_counts,
            'level_counts': level_counts,
            'performance': {
                'avg_operation_duration': avg_duration,
                'max_operation_duration': max_duration,
                'min_operation_duration': min_duration
            }
        }
    
    def export_logs(self, output_dir: str = None) -> Dict[str, str]:
        """Export all logs to files"""
        if output_dir is None:
            output_dir = self.log_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_created = {}
        
        # Export main logs
        main_log_file = output_dir / f"refactor_logs_{timestamp}.json"
        with open(main_log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_summary': self.get_session_summary(),
                'log_entries': [entry.to_dict() for entry in self.log_entries]
            }, f, indent=2, default=str)
        files_created['main_logs'] = str(main_log_file)
        
        # Export diffs
        if self.diff_entries:
            diff_log_file = output_dir / f"code_diffs_{timestamp}.json"
            with open(diff_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'diffs': [diff.to_dict() for diff in self.diff_entries]
                }, f, indent=2, default=str)
            files_created['diffs'] = str(diff_log_file)
        
        # Export performance metrics
        if self.performance_metrics:
            perf_log_file = output_dir / f"performance_{timestamp}.json"
            with open(perf_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'metrics': [metric.to_dict() for metric in self.performance_metrics]
                }, f, indent=2, default=str)
            files_created['performance'] = str(perf_log_file)
        
        # Export unified diff files
        if self.diff_entries:
            diff_text_file = output_dir / f"unified_diffs_{timestamp}.txt"
            with open(diff_text_file, 'w', encoding='utf-8') as f:
                f.write(f"Unified Diffs - Session: {self.session_id}\n")
                f.write("=" * 80 + "\n\n")
                
                for diff in self.diff_entries:
                    f.write(f"File: {diff.file_path}\n")
                    f.write(f"Operation: {diff.operation_id}\n")
                    f.write(f"Language: {diff.language}\n")
                    f.write(f"Timestamp: {datetime.fromtimestamp(diff.timestamp)}\n")
                    f.write("-" * 40 + "\n")
                    f.write(diff.get_unified_diff())
                    f.write("\n" + "=" * 80 + "\n\n")
            
            files_created['unified_diffs'] = str(diff_text_file)
        
        self.log(
            LogLevel.INFO, OperationType.FILE_SCAN,
            f"Logs exported to {len(files_created)} files",
            metadata={'files_created': files_created}
        )
        
        return files_created
    
    def cleanup_old_logs(self):
        """Clean up old log files"""
        if not self.enable_file_logging:
            return
        
        try:
            # Find all log files
            log_files = list(self.log_dir.glob("*.log")) + list(self.log_dir.glob("*.json"))
            
            # Sort by modification time (oldest first)
            log_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove excess files
            while len(log_files) > self.max_log_files:
                old_file = log_files.pop(0)
                old_file.unlink()
                self.log(
                    LogLevel.DEBUG, OperationType.FILE_SCAN,
                    f"Removed old log file: {old_file}"
                )
        
        except Exception as e:
            self.log_error(OperationType.FILE_SCAN, e, context={'action': 'cleanup_old_logs'})
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.log_error(
                OperationType.VALIDATION,
                Exception(f"{exc_type.__name__}: {exc_val}"),
                context={'traceback': str(exc_tb)}
            )
        
        # Export logs on exit
        self.export_logs()
        
        # Cleanup old logs
        self.cleanup_old_logs()
        
        self.log(
            LogLevel.INFO, OperationType.FILE_SCAN,
            f"Session ended - Duration: {time.time() - self.session_start:.2f}s"
        )