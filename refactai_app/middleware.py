import logging
import time
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .utils.error_monitor import error_monitor


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware to handle errors gracefully and provide user-friendly responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('refactai.middleware')
        super().__init__(get_response)
    
    def process_exception(self, request, exception):
        """Handle unhandled exceptions"""
        try:
            # Get session ID if available
            session_id = None
            if hasattr(request, 'resolver_match') and request.resolver_match:
                session_id = request.resolver_match.kwargs.get('session_id')
            
            # Record the error
            error_message = str(exception)
            user_friendly_message = error_monitor.record_error(
                error_type='unhandled_exception',
                error_message=error_message,
                session_id=str(session_id) if session_id else None,
                additional_context={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': self._get_client_ip(request)
                }
            )
            
            # Log the error for debugging
            self.logger.error(
                f"Unhandled exception in {request.path}: {error_message}",
                exc_info=True,
                extra={
                    'request_path': request.path,
                    'request_method': request.method,
                    'session_id': session_id,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': self._get_client_ip(request)
                }
            )
            
            # Return appropriate response based on request type
            if request.headers.get('Accept', '').startswith('application/json') or request.path.startswith('/api/'):
                # Return JSON response for AJAX/API requests
                return JsonResponse({
                    'error': user_friendly_message,
                    'status': 'error',
                    'timestamp': time.time()
                }, status=500)
            else:
                # Return HTML error page for regular requests
                context = {
                    'error_message': user_friendly_message,
                    'session_id': session_id,
                    'timestamp': time.time(),
                    'suggestions': self._get_error_suggestions(error_message)
                }
                
                return render(request, 'refactai_app/error.html', context, status=500)
        
        except Exception as middleware_error:
            # Fallback if middleware itself fails
            self.logger.critical(
                f"Error handling middleware failed: {str(middleware_error)}",
                exc_info=True
            )
            
            # Return basic error response
            if request.headers.get('Accept', '').startswith('application/json'):
                return JsonResponse({
                    'error': 'Service temporarily unavailable',
                    'status': 'error'
                }, status=500)
            else:
                return HttpResponseServerError(
                    "<h1>Service Temporarily Unavailable</h1>"
                    "<p>We're experiencing technical difficulties. Please try again later.</p>"
                )
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_error_suggestions(self, error_message):
        """Get contextual suggestions based on error type"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower:
            return [
                "Try with a smaller ZIP file (under 10MB)",
                "Ensure your internet connection is stable",
                "Wait a few minutes before trying again"
            ]
        elif 'memory' in error_lower or 'size' in error_lower:
            return [
                "Reduce the size of your ZIP file",
                "Remove large files or binaries from your ZIP",
                "Try processing files in smaller batches"
            ]
        elif 'network' in error_lower or 'connection' in error_lower:
            return [
                "Check your internet connection",
                "Try again in a few minutes",
                "Contact your network administrator if the problem persists"
            ]
        elif 'rate limit' in error_lower or 'quota' in error_lower:
            return [
                "Wait 5-10 minutes before trying again",
                "Try with fewer files at once",
                "The service may be experiencing high demand"
            ]
        elif 'zip' in error_lower or 'extract' in error_lower:
            return [
                "Ensure your ZIP file is not corrupted",
                "Try creating a new ZIP file",
                "Check that the ZIP file contains valid code files"
            ]
        else:
            return [
                "Wait a few minutes and try again",
                "Try with a smaller ZIP file",
                "Check your internet connection",
                "Contact support if the problem persists"
            ]


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log requests for monitoring and debugging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('refactai.requests')
        super().__init__(get_response)
    
    def __call__(self, request):
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log request details (only for non-static files)
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            self.logger.info(
                f"{request.method} {request.path} - {response.status_code} - {processing_time:.3f}s",
                extra={
                    'request_method': request.method,
                    'request_path': request.path,
                    'response_status': response.status_code,
                    'processing_time': processing_time,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': self._get_client_ip(request)
                }
            )
            
            # Record slow requests as potential issues
            if processing_time > 10:  # Requests taking more than 10 seconds
                error_monitor.record_error(
                    error_type='slow_request',
                    error_message=f'Slow request: {request.path} took {processing_time:.2f}s',
                    additional_context={
                        'path': request.path,
                        'method': request.method,
                        'processing_time': processing_time
                    }
                )
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip