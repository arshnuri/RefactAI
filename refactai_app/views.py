import os
import tempfile
import zipfile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import models

from .forms import ZipUploadForm
from .models import RefactorSession, ProcessedFile
from .utils.zip_handler import ZipHandler
from .utils.language_detect import LanguageDetector
from .utils.llm_client import LLMClient
from .utils.ast_utils import ASTValidator
from .utils.error_monitor import error_monitor
from .utils.code_quality_analyzer import CodeQualityAnalyzer
from .utils.enhanced_rule_based_refactor import EnhancedRuleBasedRefactor


def home(request):
    """Home page with upload form"""
    form = ZipUploadForm()
    return render(request, 'refactai_app/home.html', {'form': form})


@require_http_methods(["POST"])
def upload_zip(request):
    """Handle ZIP file upload and processing"""
    form = ZipUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'refactai_app/home.html', {'form': form})
    
    zip_file = form.cleaned_data['zip_file']
    processing_mode = form.cleaned_data.get('processing_mode', 'local')
    refactor_type = form.cleaned_data.get('refactor_type', 'comprehensive')
    preserve_comments = form.cleaned_data.get('preserve_comments', True)
    add_documentation = form.cleaned_data.get('add_documentation', True)
    follow_conventions = form.cleaned_data.get('follow_conventions', False)
    
    try:
        # Create refactor session with options
        session = RefactorSession.objects.create(
            original_filename=zip_file.name,
            status='processing',
            processing_mode=processing_mode,
            refactor_type=refactor_type,
            preserve_comments=preserve_comments,
            add_documentation=add_documentation,
            follow_conventions=follow_conventions
        )
        
        # Save uploaded file to temporary location
        import tempfile
        os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
        temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, f"upload_{session.id}.zip")
        
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in zip_file.chunks():
                temp_file.write(chunk)
        
        # Start background processing with file path and options
        import threading
        processing_options = {
            'processing_mode': processing_mode,
            'refactor_type': refactor_type,
            'preserve_comments': preserve_comments,
            'add_documentation': add_documentation,
            'follow_conventions': follow_conventions
        }
        thread = threading.Thread(
            target=process_zip_file_async,
            args=(temp_file_path, session, processing_options)
        )
        thread.daemon = True
        thread.start()
        
        # Return immediately to processing page
        return redirect('refactai_app:results', session_id=session.id)
            
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'refactai_app/home.html', {'form': ZipUploadForm()})


def process_zip_file_async(temp_file_path, session, processing_options=None):
    """Asynchronous version of ZIP file processing"""
    try:
        success = process_zip_file(temp_file_path, session, processing_options)
        if not success:
            session.status = 'failed'
            session.save()
    except Exception as e:
        # Comprehensive session-level error handling
        error_msg = str(e)
        
        # Sanitize error message for user display
        if 'timeout' in error_msg.lower():
            user_error = 'Processing timed out. Please try with a smaller ZIP file.'
        elif 'memory' in error_msg.lower() or 'out of memory' in error_msg.lower():
            user_error = 'File too large to process. Please try with a smaller ZIP file.'
        elif 'permission' in error_msg.lower() or 'access' in error_msg.lower():
            user_error = 'File access error. Please check file permissions and try again.'
        elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
            user_error = 'Network connection issue. Please check your internet and try again.'
        elif 'api' in error_msg.lower() or 'rate limit' in error_msg.lower():
            user_error = 'Refactoring service temporarily busy. Please try again in a few minutes.'
        elif 'zip' in error_msg.lower() or 'extract' in error_msg.lower():
            user_error = 'Invalid or corrupted ZIP file. Please check your file and try again.'
        else:
            user_error = 'An unexpected error occurred during processing. Please try again.'
        
        session.status = 'failed'
        session.error_message = user_error
        session.save()
        
        # Log detailed error for debugging (not shown to user)
        print(f"Detailed error processing ZIP file: {error_msg}")
        
    finally:
        # Clean up temporary file with error handling
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temp file {temp_file_path}: {cleanup_error}")


def process_zip_file(temp_file_path, session, processing_options=None):
    """Process uploaded ZIP file and refactor code"""
    if processing_options is None:
        processing_options = {
            'processing_mode': 'local',
            'refactor_type': 'comprehensive',
            'preserve_comments': True,
            'add_documentation': True,
            'follow_conventions': False
        }
    
    try:
        # Ensure temp directory exists
        os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
        
        with ZipHandler(temp_file_path) as zip_handler:
            # Extract ZIP file
            temp_dir = zip_handler.extract_zip()
            
            # Get all code files
            code_files = zip_handler.extracted_files
            session.total_files = len(code_files)
            session.save()
            
            if not code_files:
                return False
            
            # Initialize LLM client with processing mode
            llm_client = LLMClient(mode=processing_options.get('processing_mode', 'local'))
            
            # Process each file with comprehensive error handling
            for file_path, relative_path in code_files:
                processed_file = None
                content = ''
                try:
                    # Read file content with error handling
                    try:
                        content = zip_handler.get_file_content(file_path)
                    except Exception as read_error:
                        # Create failed record for unreadable files
                        ProcessedFile.objects.create(
                            session=session,
                            original_path=relative_path,
                            language='unknown',
                            original_content='',
                            refactored_content='',
                            status='failed',
                            error_message=f'Could not read file: {str(read_error)[:200]}'
                        )
                        session.processed_files += 1
                        session.save()
                        continue
                    
                    # Detect language with error handling
                    try:
                        language = LanguageDetector.detect_language(relative_path, content)
                    except Exception:
                        language = 'unknown'
                    
                    # Only process specific languages: Python, JavaScript, Java, JSX, and C/C++
                    allowed_languages = ['Python', 'JavaScript', 'Java', 'C', 'C++', 'C/C++']
                    
                    # Check for JSX files (JavaScript files with JSX syntax)
                    if language == 'JavaScript' and ('.jsx' in relative_path.lower() or 'jsx' in content[:1000].lower()):
                        language = 'JSX'
                        allowed_languages.append('JSX')
                    
                    # Skip files that are not in the allowed languages
                    if language not in allowed_languages:
                        ProcessedFile.objects.create(
                            session=session,
                            original_path=relative_path,
                            language=language,
                            original_content=content,
                            refactored_content=content,
                            status='skipped',
                            error_message=f'Language "{language}" is not supported for refactoring'
                        )
                        session.processed_files += 1
                        session.save()
                        continue
                    
                    # Create ProcessedFile record
                    processed_file = ProcessedFile.objects.create(
                        session=session,
                        original_path=relative_path,
                        language=language,
                        original_content=content,
                        status='processing'
                    )
                    
                    # Skip very large files (>50KB) to avoid API limits
                    if len(content) > 50000:
                        processed_file.status = 'skipped'
                        processed_file.error_message = 'File is too large for processing (maximum 50KB allowed)'
                        processed_file.refactored_content = content  # Keep original
                        processed_file.save()
                        session.processed_files += 1
                        session.save()
                        continue
                    
                    # Skip empty files
                    if not content.strip():
                        processed_file.status = 'completed'
                        processed_file.refactored_content = content
                        processed_file.error_message = 'File is empty'
                        processed_file.save()
                        session.processed_files += 1
                        session.save()
                        continue
                    
                    # Refactor with LLM with comprehensive error handling
                    prefer_local = getattr(settings, 'PREFER_LOCAL_LLM', False)
                    
                    try:
                        # Always try to refactor (either with local LLM or remote API)
                        result = llm_client.refactor_code(
                            content, 
                            language, 
                            relative_path,
                            session_id=str(session.id),
                            processing_options=processing_options
                        )
                        
                        # Validate result structure
                        if not isinstance(result, dict):
                            result = {
                                'success': False,
                                'refactored_code': content,
                                'error': 'Invalid response from refactoring service'
                            }
                        
                        if result.get('success', False):
                            refactored_code = result.get('refactored_code', content)
                            validation_warnings = result.get('validation_warnings', [])
                            
                            # Check for syntax errors in validation warnings
                            has_syntax_errors = any(
                                any(keyword in warning.lower() for keyword in [
                                    'syntax', 'invalid syntax', 'syntaxerror', 'parse error',
                                    'unexpected token', 'unexpected indent', 'indentation error',
                                    'invalid character', 'unexpected eof', 'invalid decimal literal'
                                ])
                                for warning in validation_warnings
                            )
                            
                            # Ensure refactored code is not empty
                            if not refactored_code or not refactored_code.strip():
                                processed_file.refactored_content = content
                                processed_file.status = 'completed'
                                processed_file.error_message = 'Refactoring returned empty code, kept original'
                            elif has_syntax_errors:
                                # If there are syntax errors, mark as failed
                                processed_file.refactored_content = content  # Keep original
                                processed_file.status = 'failed'
                                processed_file.error_message = 'Refactored code has syntax errors: ' + '; '.join(validation_warnings[:3])
                            else:
                                processed_file.refactored_content = refactored_code
                                processed_file.status = 'completed'
                                
                                # Apply enhanced rule-based improvements to boost quality
                                try:
                                    enhanced_refactor = EnhancedRuleBasedRefactor()
                                    enhancement_result = enhanced_refactor.refactor_code(refactored_code, language, relative_path)
                                    
                                    if enhancement_result.get('success', False) and enhancement_result.get('refactored_code'):
                                        # Use enhanced code if improvements were made
                                        final_code = enhancement_result['refactored_code']
                                        improvements = enhancement_result.get('improvements', [])
                                        if improvements:
                                            print(f"Enhanced {relative_path}: {', '.join(improvements[:3])}")
                                    else:
                                        final_code = refactored_code
                                except Exception as enhancement_error:
                                    print(f"Enhancement failed for {relative_path}: {enhancement_error}")
                                    final_code = refactored_code
                                
                                # Update the refactored content with enhanced version
                                processed_file.refactored_content = final_code
                                
                                # Calculate and store quality metrics on the final enhanced code
                                try:
                                    analyzer = CodeQualityAnalyzer()
                                    final_metrics = analyzer.analyze_code(final_code, language)
                                    
                                    # Store quality metrics in the processed file
                                    processed_file.complexity_score = final_metrics.get('complexity', 0)
                                    processed_file.readability_score = final_metrics.get('readability', 0)
                                    processed_file.maintainability_score = final_metrics.get('maintainability', 0)
                                    processed_file.overall_quality_score = analyzer.calculate_overall_score(final_metrics)
                                except Exception as quality_error:
                                    # Don't fail the whole process if quality analysis fails
                                    print(f"Quality analysis failed for {relative_path}: {quality_error}")
                                
                                # Add validation warnings if any (non-syntax related)
                                if validation_warnings:
                                    processed_file.error_message = '; '.join(validation_warnings[:3])  # Limit warnings
                        else:
                            # LLM refactoring failed, try enhanced rule-based refactoring as fallback
                            try:
                                enhanced_refactor = EnhancedRuleBasedRefactor()
                                fallback_result = enhanced_refactor.refactor_code(content, language, relative_path)
                                
                                if fallback_result.get('success', False) and fallback_result.get('refactored_code'):
                                    processed_file.refactored_content = fallback_result['refactored_code']
                                    processed_file.status = 'completed'
                                    improvements = fallback_result.get('improvements', [])
                                    if improvements:
                                        processed_file.error_message = f"LLM failed, applied rule-based improvements: {', '.join(improvements[:2])}"
                                        print(f"Fallback enhanced {relative_path}: {', '.join(improvements[:3])}")
                                    else:
                                        processed_file.error_message = "LLM failed, no rule-based improvements available"
                                    
                                    # Calculate quality metrics for fallback result
                                    try:
                                        analyzer = CodeQualityAnalyzer()
                                        fallback_metrics = analyzer.analyze_code(processed_file.refactored_content, language)
                                        processed_file.complexity_score = fallback_metrics.get('complexity', 0)
                                        processed_file.readability_score = fallback_metrics.get('readability', 0)
                                        processed_file.maintainability_score = fallback_metrics.get('maintainability', 0)
                                        processed_file.overall_quality_score = analyzer.calculate_overall_score(fallback_metrics)
                                    except Exception:
                                        pass  # Quality analysis is optional for fallback
                                else:
                                    # Both LLM and rule-based failed
                                    processed_file.status = 'failed'
                                    error_msg = result.get('error', 'Unknown refactoring error')
                                    processed_file.error_message = error_monitor.record_error(
                                        'refactoring_failed',
                                        f"LLM and rule-based refactoring failed: {error_msg}",
                                        session_id=str(session.id),
                                        file_path=relative_path
                                    )
                                    processed_file.refactored_content = content  # Keep original
                            except Exception as fallback_error:
                                # Fallback also failed
                                processed_file.status = 'failed'
                                error_msg = result.get('error', 'Unknown refactoring error')
                                processed_file.error_message = error_monitor.record_error(
                                    'refactoring_failed',
                                    f"Both LLM and fallback failed: {error_msg}, {fallback_error}",
                                    session_id=str(session.id),
                                    file_path=relative_path
                                )
                                processed_file.refactored_content = content  # Keep original
                            
                    except Exception as llm_error:
                        processed_file.status = 'failed'
                        processed_file.error_message = error_monitor.record_error(
                            'llm_service_error',
                            f'Refactoring service error: {str(llm_error)}',
                            session_id=str(session.id),
                            file_path=relative_path
                        )
                        processed_file.refactored_content = content  # Keep original
                    
                    # Add delay between API calls to respect rate limits (only for API calls)
                    if not prefer_local:
                        import time
                        time.sleep(1)  # 1 second delay between files
                    
                    processed_file.save()
                    session.processed_files += 1
                    session.save()
                    
                except Exception as e:
                    # Handle individual file errors with detailed logging
                    error_msg = f'Processing error: {str(e)[:200]}'
                    
                    if processed_file:
                        processed_file.status = 'failed'
                        processed_file.error_message = error_msg
                        processed_file.refactored_content = content
                        try:
                            processed_file.save()
                        except Exception:
                            pass  # Ignore save errors in error handler
                    else:
                        # Create a failed record if processed_file wasn't created
                        try:
                            ProcessedFile.objects.create(
                                session=session,
                                original_path=relative_path,
                                language='unknown',
                                original_content=content,
                                refactored_content=content,
                                status='failed',
                                error_message=error_msg
                            )
                        except Exception:
                            pass  # Ignore creation errors in error handler
                    
                    session.processed_files += 1
                    session.save()
                    continue
            
            # Mark session as completed
            session.status = 'completed'
            session.save()
            
            return True
            
    except Exception as e:
        print(f"Error processing ZIP file: {e}")
        return False


def results(request, session_id):
    """Display processing results"""
    session = get_object_or_404(RefactorSession, id=session_id)
    files = session.files.all().order_by('original_path')
    
    # Calculate statistics
    total_files = files.count()
    completed_files = files.filter(status='completed').count()
    failed_files = files.filter(status='failed').count()
    processing_files = files.filter(status='processing').count()
    skipped_files = files.filter(status='skipped').count()
    
    # Update session totals if they don't match
    if session.total_files != total_files:
        session.total_files = total_files
        session.save()
    
    # Group files by language
    languages = {}
    for file in files:
        if file.language not in languages:
            languages[file.language] = []
        languages[file.language].append(file)
    
    # Calculate session-level quality metrics
    completed_files_with_metrics = files.filter(status='completed', overall_quality_score__gt=0)
    
    if completed_files_with_metrics.exists():
        avg_complexity = completed_files_with_metrics.aggregate(
            avg=models.Avg('complexity_score')
        )['avg'] or 0
        avg_readability = completed_files_with_metrics.aggregate(
            avg=models.Avg('readability_score')
        )['avg'] or 0
        avg_maintainability = completed_files_with_metrics.aggregate(
            avg=models.Avg('maintainability_score')
        )['avg'] or 0
        avg_overall = completed_files_with_metrics.aggregate(
            avg=models.Avg('overall_quality_score')
        )['avg'] or 0
    else:
        # Default values if no metrics available
        avg_complexity = avg_readability = avg_maintainability = avg_overall = 0
    
    context = {
        'session': session,
        'files': files,
        'languages': languages,
        'total_files': total_files,
        'completed_files': completed_files,
        'failed_files': failed_files,
        'processing_files': processing_files,
        'skipped_files': skipped_files,
        'success_rate': round((completed_files / total_files * 100) if total_files > 0 else 0, 1),
        # Quality metrics
        'avg_complexity': round(avg_complexity),
        'avg_readability': round(avg_readability),
        'avg_maintainability': round(avg_maintainability),
        'avg_overall_quality': round(avg_overall)
    }
    
    return render(request, 'refactai_app/results.html', context)


def view_file(request, session_id, file_id):
    """View individual file comparison"""
    session = get_object_or_404(RefactorSession, id=session_id)
    file = get_object_or_404(ProcessedFile, id=file_id, session=session)
    
    # Get validation info for Python files
    validation_info = None
    if file.language.lower() == 'python' and file.refactored_content:
        validation_info = ASTValidator.compare_code_structure(
            file.original_content,
            file.refactored_content
        )
    
    context = {
        'session': session,
        'file': file,
        'validation_info': validation_info
    }
    
    return render(request, 'refactai_app/file_detail.html', context)


@require_http_methods(["GET"])
def check_status(request, session_id):
    """AJAX endpoint to check processing status"""
    try:
        session = get_object_or_404(RefactorSession, id=session_id)
        
        # Get processing statistics
        total_files = session.files.count()
        completed_files = session.files.filter(status='completed').count()
        failed_files = session.files.filter(status='failed').count()
        processing_files = session.files.filter(status='processing').count()
        
        # Get recent error messages for failed sessions
        error_messages = []
        if session.status == 'failed':
            recent_errors = session.files.filter(
                status='failed'
            ).exclude(
                error_message__isnull=True
            ).exclude(
                error_message__exact=''
            ).values_list('error_message', flat=True)[:5]
            
            error_messages = list(recent_errors)
        
        # Get session-specific error info from monitor
        session_errors = error_monitor.get_session_errors(str(session_id))
        health_status = error_monitor.get_health_status()
        
        response_data = {
            'status': session.status,
            'total_files': session.total_files,
            'processed_files': session.processed_files,
            'progress': round((session.processed_files / session.total_files * 100) if session.total_files > 0 else 0, 1),
            'completed_files': completed_files,
            'failed_files': failed_files,
            'processing_files': processing_files,
            'progress_percentage': int((completed_files + failed_files) / total_files * 100) if total_files > 0 else 0,
            'error_messages': error_messages,
            'session_error_count': len(session_errors),
            'service_health': health_status['status']
        }
        
        if session.status == 'failed':
            response_data['error'] = getattr(session, 'error_message', 'Processing failed')
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_monitor.record_error(
            'status_check_error',
            f'Status check failed: {str(e)}',
            session_id=str(session_id)
        )
        return JsonResponse({'error': 'Status check temporarily unavailable'}, status=500)


def download_refactored(request, session_id):
    """Download refactored code as ZIP"""
    session = get_object_or_404(RefactorSession, id=session_id)
    
    if session.status != 'completed':
        messages.error(request, 'Session is not completed yet.')
        return redirect('refactai_app:results', session_id=session_id)
    
    try:
        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file in session.files.all():
                # Use refactored content if available, otherwise original
                content = file.refactored_content or file.original_content
                
                # Add file to ZIP
                zip_ref.writestr(file.original_path, content)
        
        # Read ZIP file content
        with open(temp_zip.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up temporary file
        os.unlink(temp_zip.name)
        
        # Create response
        response = HttpResponse(zip_content, content_type='application/zip')
        filename = f"refactored_{session.original_filename}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        error_monitor.record_error(
            'download_error',
            f'Download failed: {str(e)}',
            session_id=str(session_id)
        )
        messages.error(request, 'Download temporarily unavailable. Please try again.')
        return redirect('refactai_app:results', session_id=session_id)


def health_check(request):
    """Health check endpoint for monitoring system status"""
    try:
        health_status = error_monitor.get_health_status()
        error_stats = error_monitor.get_error_stats()
        
        # Check if service is degraded
        is_degraded = error_monitor.is_service_degraded()
        
        response_data = {
            'status': 'degraded' if is_degraded else 'healthy',
            'timestamp': timezone.now().timestamp(),
            'error_stats': error_stats,
            'health_details': health_status,
            'service_available': not is_degraded
        }
        
        status_code = 503 if is_degraded else 200
        return JsonResponse(response_data, status=status_code)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Health check failed',
            'timestamp': timezone.now().timestamp()
        }, status=500)


def documentation(request):
    """Documentation page with CLI and Git Hook setup instructions"""
    return render(request, 'refactai_app/documentation.html')


def setup_guide(request):
    """Serve the complete setup guide"""
    import os
    import markdown
    
    guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'SETUP_GUIDE_FOR_USERS.md')
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'toc'])
        
        return render(request, 'refactai_app/markdown_doc.html', {
            'title': 'Complete Setup Guide',
            'content': html_content,
            'file_name': 'SETUP_GUIDE_FOR_USERS.md'
        })
    except FileNotFoundError:
        return render(request, 'refactai_app/error.html', {
            'error_message': 'Setup guide not found'
        })


def new_user_setup(request):
    """Serve the new user setup guide"""
    import os
    import markdown
    
    guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'NEW_USER_SETUP.md')
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'toc'])
        
        return render(request, 'refactai_app/markdown_doc.html', {
            'title': 'Quick Start for Beginners',
            'content': html_content,
            'file_name': 'NEW_USER_SETUP.md'
        })
    except FileNotFoundError:
        return render(request, 'refactai_app/error.html', {
            'error_message': 'New user setup guide not found'
        })


def troubleshooting_guide(request):
    """Serve the troubleshooting guide"""
    import os
    import markdown
    
    guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TROUBLESHOOTING.md')
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'toc'])
        
        return render(request, 'refactai_app/markdown_doc.html', {
            'title': 'Detailed Troubleshooting',
            'content': html_content,
            'file_name': 'TROUBLESHOOTING.md'
        })
    except FileNotFoundError:
        return render(request, 'refactai_app/error.html', {
            'error_message': 'Troubleshooting guide not found'
        })


def setup_script_info(request):
    """Serve information about the setup script"""
    import os
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'setup.py')
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return render(request, 'refactai_app/script_doc.html', {
            'title': 'Automated Setup Script',
            'content': content,
            'file_name': 'setup.py',
            'description': 'Automated environment setup script that configures RefactAI with all dependencies and fixes.'
        })
    except FileNotFoundError:
        return render(request, 'refactai_app/error.html', {
            'error_message': 'Setup script not found'
        })


def compare_sessions(request):
    """Display all refactoring sessions for comparison"""
    # Get all sessions ordered by creation date (newest first)
    sessions = RefactorSession.objects.all().order_by('-created_at')
    
    # Add statistics for each session
    for session in sessions:
        files = session.files.all()
        session.total_files_count = files.count()
        session.completed_files_count = files.filter(status='completed').count()
        session.failed_files_count = files.filter(status='failed').count()
        session.success_rate = round((session.completed_files_count / session.total_files_count * 100) if session.total_files_count > 0 else 0, 1)
        
        # Get language breakdown
        languages = {}
        for file in files:
            if file.language not in languages:
                languages[file.language] = 0
            languages[file.language] += 1
        session.languages = languages
    
    context = {
        'sessions': sessions,
        'total_sessions': sessions.count()
    }
    
    return render(request, 'refactai_app/compare_sessions.html', context)