import logging
import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from django.conf import settings


class ErrorMonitor:
    """Monitor and track errors for better debugging and user experience"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.recent_errors = deque(maxlen=100)  # Keep last 100 errors
        self.error_patterns = defaultdict(int)
        self.session_errors = defaultdict(list)
        
        # Setup logging
        self.logger = logging.getLogger('refactai.errors')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def record_error(self, error_type: str, error_message: str, 
                    session_id: Optional[str] = None, 
                    file_path: Optional[str] = None,
                    additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Record an error and return a user-friendly message"""
        
        timestamp = time.time()
        
        # Create error record
        error_record = {
            'timestamp': timestamp,
            'type': error_type,
            'message': error_message,
            'session_id': session_id,
            'file_path': file_path,
            'context': additional_context or {}
        }
        
        # Store error
        self.recent_errors.append(error_record)
        self.error_counts[error_type] += 1
        
        # Extract error pattern
        pattern = self._extract_error_pattern(error_message)
        self.error_patterns[pattern] += 1
        
        # Store session-specific errors
        if session_id:
            self.session_errors[session_id].append(error_record)
        
        # Log error for debugging
        self.logger.error(
            f"Error recorded - Type: {error_type}, Message: {error_message[:200]}, "
            f"Session: {session_id}, File: {file_path}"
        )
        
        # Return user-friendly message
        return self._get_user_friendly_message(error_type, error_message)
    
    def _extract_error_pattern(self, error_message: str) -> str:
        """Extract a pattern from error message for categorization"""
        message_lower = error_message.lower()
        
        # Common error patterns
        patterns = {
            'timeout': ['timeout', 'timed out'],
            'network': ['network', 'connection', 'dns', 'unreachable'],
            'rate_limit': ['rate limit', 'quota', 'too many requests'],
            'auth': ['unauthorized', 'authentication', 'api key', 'forbidden'],
            'syntax': ['syntax error', 'invalid syntax', 'parsing'],
            'memory': ['memory', 'out of memory', 'allocation'],
            'file_size': ['too large', 'file size', 'exceeds limit'],
            'api_error': ['api error', 'server error', '500', '502', '503'],
            'json_error': ['json', 'invalid json', 'decode'],
            'llm_error': ['llm', 'model', 'generation']
        }
        
        for pattern, keywords in patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return pattern
        
        return 'unknown'
    
    def _get_user_friendly_message(self, error_type: str, error_message: str) -> str:
        """Convert technical error to user-friendly message"""
        pattern = self._extract_error_pattern(error_message)
        
        friendly_messages = {
            'timeout': 'Request timed out. Please try again with a smaller file.',
            'network': 'Network connection issue. Please check your internet and try again.',
            'rate_limit': 'Service temporarily busy. Please try again in a few minutes.',
            'auth': 'Service configuration issue. Please contact support.',
            'syntax': 'Code contains syntax errors that prevent refactoring.',
            'memory': 'File too large to process. Please try with a smaller file.',
            'file_size': 'File is too large for processing. Please try with a smaller file.',
            'api_error': 'Refactoring service temporarily unavailable. Please try again later.',
            'json_error': 'Service response error. Please try again.',
            'llm_error': 'Refactoring model encountered an issue. Please try again.',
            'unknown': 'An unexpected error occurred. Please try again.'
        }
        
        return friendly_messages.get(pattern, friendly_messages['unknown'])
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts),
            'error_patterns': dict(self.error_patterns),
            'recent_error_count': len(self.recent_errors)
        }
    
    def get_session_errors(self, session_id: str) -> list:
        """Get errors for a specific session"""
        return self.session_errors.get(session_id, [])
    
    def is_service_degraded(self) -> bool:
        """Check if service is experiencing high error rates"""
        recent_errors = [e for e in self.recent_errors 
                        if time.time() - e['timestamp'] < 300]  # Last 5 minutes
        
        # Consider service degraded if more than 50% of recent requests failed
        if len(recent_errors) > 10:
            return len(recent_errors) > 20
        
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        recent_errors = [e for e in self.recent_errors 
                        if time.time() - e['timestamp'] < 300]
        
        return {
            'status': 'degraded' if self.is_service_degraded() else 'healthy',
            'recent_errors': len(recent_errors),
            'total_errors': sum(self.error_counts.values()),
            'most_common_pattern': max(self.error_patterns.items(), 
                                     key=lambda x: x[1], default=('none', 0))[0]
        }
    
    def clear_old_errors(self, max_age_hours: int = 24):
        """Clear errors older than specified hours"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clear old session errors
        for session_id in list(self.session_errors.keys()):
            self.session_errors[session_id] = [
                error for error in self.session_errors[session_id]
                if error['timestamp'] > cutoff_time
            ]
            if not self.session_errors[session_id]:
                del self.session_errors[session_id]


# Global error monitor instance
error_monitor = ErrorMonitor()