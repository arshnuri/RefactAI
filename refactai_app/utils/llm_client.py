import requests
import json
import time
import re
from typing import Optional, Dict, Any
import os
import sys
from pathlib import Path
from django.conf import settings
from .language_detect import LanguageDetector
from .ast_utils import ASTValidator
from .hybrid_refactor import HybridRefactor
from .error_monitor import error_monitor

# Add the project root to Python path for local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from refactor import LocalLLMClient
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False


class LLMClient:
    """Client for interacting with OpenRouter API or Local LLM with robust error handling and circuit breaker"""
    
    def __init__(self, use_local_llm: bool = None, use_hybrid_approach: bool = True, mode: str = 'local'):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL
        self.default_model = settings.DEFAULT_MODEL
        self.session = requests.Session()
        self.processing_mode = mode
        
        # Set processing behavior based on mode
        if mode == 'local':
            self.use_hybrid_approach = False
            self.use_local_llm = True
        elif mode == 'api':
            self.use_hybrid_approach = False
            self.use_local_llm = False
        elif mode == 'hybrid':
            self.use_hybrid_approach = True
            # For hybrid mode, determine local LLM usage based on settings
            self.use_local_llm = LOCAL_LLM_AVAILABLE and getattr(settings, 'PREFER_LOCAL_LLM', False)
        else:
            # Default to hybrid if unknown mode
            self.use_hybrid_approach = use_hybrid_approach
            self.use_local_llm = LOCAL_LLM_AVAILABLE and getattr(settings, 'PREFER_LOCAL_LLM', False)
        
        # Circuit breaker for API failures
        self.api_failure_count = 0
        self.api_failure_threshold = 5
        self.api_circuit_open_until = None
        self.api_circuit_timeout = 300  # 5 minutes
        
        # Circuit breaker for local LLM failures
        self.local_failure_count = 0
        self.local_failure_threshold = 3
        self.local_circuit_open_until = None
        self.local_circuit_timeout = 180  # 3 minutes
        
        # Set default headers
        headers = {
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:8000',
            'X-Title': 'RefactAI'
        }
        
        # Only add Authorization header if API key is provided
        if self.api_key and self.api_key.strip():
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session.headers.update(headers)
        
        # Override use_local_llm if explicitly provided (for backward compatibility)
        if use_local_llm is not None:
            self.use_local_llm = use_local_llm and LOCAL_LLM_AVAILABLE
        
        # Initialize local LLM client if needed
        if self.use_local_llm:
            try:
                local_model = getattr(settings, 'LOCAL_LLM_MODEL', 'deepseek-coder:6.7b')
                self.local_client = LocalLLMClient(model_name=local_model)
            except Exception as e:
                print(f"Warning: Failed to initialize local LLM client: {e}")
                self.use_local_llm = False
        
        # Initialize hybrid refactorer
        if self.use_hybrid_approach:
            self.hybrid_refactor = HybridRefactor(llm_client=self)
    
    def _is_api_circuit_open(self) -> bool:
        """Check if API circuit breaker is open"""
        if self.api_circuit_open_until is None:
            return False
        
        if time.time() < self.api_circuit_open_until:
            return True
        
        # Circuit timeout expired, reset
        self.api_circuit_open_until = None
        self.api_failure_count = 0
        return False
    
    def _is_local_circuit_open(self) -> bool:
        """Check if local LLM circuit breaker is open"""
        if self.local_circuit_open_until is None:
            return False
        
        if time.time() < self.local_circuit_open_until:
            return True
        
        # Circuit timeout expired, reset
        self.local_circuit_open_until = None
        self.local_failure_count = 0
        return False
    
    def _record_api_failure(self):
        """Record API failure and potentially open circuit"""
        self.api_failure_count += 1
        if self.api_failure_count >= self.api_failure_threshold:
            self.api_circuit_open_until = time.time() + self.api_circuit_timeout
    
    def _record_local_failure(self):
        """Record local LLM failure and potentially open circuit"""
        self.local_failure_count += 1
        if self.local_failure_count >= self.local_failure_threshold:
            self.local_circuit_open_until = time.time() + self.local_circuit_timeout
    
    def _record_api_success(self):
        """Record API success and reset failure count"""
        self.api_failure_count = 0
        self.api_circuit_open_until = None
    
    def _record_local_success(self):
        """Record local LLM success and reset failure count"""
        self.local_failure_count = 0
        self.local_circuit_open_until = None
    
    def _sanitize_error_message(self, error_msg: str, session_id: Optional[str] = None, file_path: Optional[str] = None) -> str:
        """Sanitize error messages to be user-friendly and record them"""
        if not error_msg:
            error_msg = "Refactoring service temporarily unavailable"
        
        # Record the error for monitoring
        user_friendly_message = error_monitor.record_error(
            error_type='llm_processing',
            error_message=error_msg,
            session_id=session_id,
            file_path=file_path
        )
        
        return user_friendly_message
    
    def refactor_code(self, code: str, language: str, file_path: str, session_id: Optional[str] = None, processing_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Refactor code using hybrid approach (rule-based + LLM) or pure LLM with robust error handling
        
        Args:
            code: The code content to refactor
            language: Programming language of the code
            file_path: Original file path for context
            session_id: Optional session ID for error tracking
            
        Returns:
            Dict containing refactored code and metadata
        """
        # Validate input parameters
        if not code or not code.strip():
            return {
                'success': True,
                'refactored_code': code,
                'error': '',
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': ['File is empty']
            }
        
        # Check file size limits
        if len(code) > 100000:  # 100KB limit
            return {
                'success': False,
                'refactored_code': code,
                'error': self._sanitize_error_message('File too large for processing', session_id, file_path),
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': []
            }
        
        try:
            # Use hybrid approach (rule-based + LLM for naming/docs) if enabled
            if self.use_hybrid_approach and hasattr(self, 'hybrid_refactor'):
                result = self.hybrid_refactor.refactor_code(code, language, file_path)
                if not result['success']:
                    result['error'] = self._sanitize_error_message(result['error'], session_id, file_path)
                return result
            
            # Use local LLM if configured
            elif self.use_local_llm:
                # Check local circuit breaker
                if self._is_local_circuit_open():
                    # Local LLM circuit is open, try API fallback
                    if self.api_key and self.api_key.strip() and not self._is_api_circuit_open():
                        result = self._refactor_with_api(code, language, file_path, processing_options)
                        if result['success']:
                            self._record_api_success()
                            result['validation_warnings'].append('Used API fallback (local LLM temporarily unavailable)')
                            return result
                        else:
                            self._record_api_failure()
                            result['error'] = self._sanitize_error_message(result['error'], session_id, file_path)
                    else:
                        result = {
                            'success': False,
                            'refactored_code': code,
                            'error': self._sanitize_error_message('Refactoring service temporarily unavailable', session_id, file_path),
                            'original_valid': True,
                            'refactored_valid': True,
                            'validation_warnings': []
                        }
                else:
                    result = self._refactor_with_local_llm(code, language, file_path)
                    if result['success']:
                        self._record_local_success()
                    else:
                        self._record_local_failure()
                        result['error'] = self._sanitize_error_message(result['error'], session_id, file_path)
                        # Try API fallback if local LLM fails and API circuit is closed
                        if self.api_key and self.api_key.strip() and not self._is_api_circuit_open():
                            fallback_result = self._refactor_with_api(code, language, file_path, processing_options)
                            if fallback_result['success']:
                                self._record_api_success()
                                fallback_result['validation_warnings'].append('Used API fallback after local LLM failure')
                                return fallback_result
                            else:
                                self._record_api_failure()
                                fallback_result['error'] = self._sanitize_error_message(fallback_result['error'], session_id, file_path)
                return result
            
            # Fallback to API-based refactoring
            else:
                # Check API circuit breaker
                if self._is_api_circuit_open():
                    return {
                        'success': False,
                        'refactored_code': code,
                        'error': self._sanitize_error_message('Refactoring service temporarily unavailable', session_id, file_path),
                        'original_valid': True,
                        'refactored_valid': True,
                        'validation_warnings': []
                    }
                
                result = self._refactor_with_api(code, language, file_path, processing_options)
                if result['success']:
                    self._record_api_success()
                else:
                    self._record_api_failure()
                    result['error'] = self._sanitize_error_message(result['error'], session_id, file_path)
                return result
                
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,  # Return original code on error
                'error': self._sanitize_error_message(f"Unexpected error: {str(e)}", session_id, file_path),
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': []
            }
    
    def _refactor_with_local_llm(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """Refactor code using local LLM with robust error handling"""
        try:
            if not hasattr(self, 'local_client'):
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': 'Local LLM client not initialized',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': []
                }
            
            # Validate input
            if not code or not code.strip():
                return {
                    'success': True,
                    'refactored_code': code,
                    'error': '',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': ['File is empty']
                }
            
            # Use the local LLM client with timeout
            try:
                result = self.local_client.run_llm_refactor(code, language.lower())
            except Exception as llm_error:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': f'Local LLM error: {str(llm_error)}',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': []
                }
            
            # Validate result structure
            if not isinstance(result, dict) or 'success' not in result:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': 'Invalid response from local LLM',
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': []
                }
            
            # Convert result format to match expected format
            if result['success']:
                # Validate that refactored_code exists
                if 'refactored_code' not in result or not result['refactored_code']:
                    return {
                        'success': False,
                        'refactored_code': code,
                        'error': 'Local LLM returned empty refactored code',
                        'original_valid': True,
                        'refactored_valid': True,
                        'validation_warnings': []
                    }
                
                # Validate original code if it's Python
                original_valid = True
                validation_warnings = []
                if language.lower() == 'python':
                    try:
                        is_valid, error_msg = ASTValidator.validate_python_code(code)
                        original_valid = is_valid
                        if not is_valid:
                            validation_warnings.append(f"Original code validation: {error_msg}")
                            # Try to auto-fix original code syntax errors before refactoring using API
                            fixed_code = self._auto_fix_syntax_errors(code, error_msg, code, language)
                            if fixed_code != code:
                                is_valid_fixed, _ = ASTValidator.validate_python_code(fixed_code)
                                if is_valid_fixed:
                                    code = fixed_code  # Use fixed code for refactoring
                                    original_valid = True
                                    validation_warnings.append("Auto-fixed original code syntax errors (API)")
                    except Exception:
                        validation_warnings.append("Could not validate original code syntax")
                
                # Validate refactored code if it's Python
                refactored_valid = True
                if language.lower() == 'python':
                    try:
                        is_valid, error_msg = ASTValidator.validate_python_code(result['refactored_code'])
                        refactored_valid = is_valid
                        if not is_valid:
                            validation_warnings.append(f"Refactored code validation: {error_msg}")
                            # Try to auto-fix syntax errors using API
                            fixed_code = self._auto_fix_syntax_errors(result['refactored_code'], error_msg, code, language)
                            if fixed_code != result['refactored_code']:
                                is_valid_fixed, _ = ASTValidator.validate_python_code(fixed_code)
                                if is_valid_fixed:
                                    result['refactored_code'] = fixed_code
                                    refactored_valid = True
                                    validation_warnings.append("Auto-fixed syntax errors (API)")
                    except Exception:
                        validation_warnings.append("Could not validate refactored code syntax")
                
                return {
                    'success': True,
                    'refactored_code': result['refactored_code'],
                    'error': '',
                    'original_valid': original_valid,
                    'refactored_valid': refactored_valid,
                    'validation_warnings': validation_warnings + result.get('validation_warnings', [])
                }
            else:
                return {
                    'success': False,
                    'refactored_code': code,
                    'error': result['error'],
                    'original_valid': True,
                    'refactored_valid': True,
                    'validation_warnings': []
                }
            
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,
                'error': f"Local LLM error: {str(e)}",
                'original_valid': True,
                'refactored_valid': True,
                'validation_warnings': []
            }
    
    def _refactor_with_api(self, code: str, language: str, file_path: str, processing_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Refactor code using API with robust error handling and retries"""
        result = {
            'success': False,
            'refactored_code': '',
            'error': '',
            'original_valid': True,
            'refactored_valid': True,
            'validation_warnings': []
        }
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Validate original code if it's Python
                if language.lower() == 'python':
                    is_valid, error_msg = ASTValidator.validate_python_code(code)
                    result['original_valid'] = is_valid
                    if not is_valid:
                        result['validation_warnings'].append(f"Original code validation: {error_msg}")
                        # Try to auto-fix original code syntax errors before refactoring using API
                        fixed_code = self._auto_fix_syntax_errors(code, error_msg, code, language)
                        if fixed_code != code:
                            is_valid_fixed, _ = ASTValidator.validate_python_code(fixed_code)
                            if is_valid_fixed:
                                code = fixed_code  # Use fixed code for refactoring
                                result['original_valid'] = True
                                result['validation_warnings'].append("Auto-fixed original code syntax errors (API)")
                
                # Prepare the prompt with processing options
                system_prompt = self._create_system_prompt(language, processing_options)
                user_prompt = self._create_user_prompt(code, language)
                
                # Make API request
                response = self._make_api_request(system_prompt, user_prompt)
                
                if response['success']:
                    refactored_code = response['content']
                    
                    # Clean up the response (remove markdown formatting if present)
                    refactored_code = self._clean_response(refactored_code, language)
                    
                    # Validate refactored code if it's Python
                    refactored_valid = True
                    if language.lower() == 'python':
                        is_valid, error_msg = ASTValidator.validate_python_code(refactored_code)
                        refactored_valid = is_valid
                        if not is_valid:
                            result['validation_warnings'].append(f"Refactored code validation: {error_msg}")
                            # Attempt automatic syntax error fixing using API
                            fixed_code = self._auto_fix_syntax_errors(refactored_code, error_msg, code, language)
                            if fixed_code != refactored_code:
                                is_valid, _ = ASTValidator.validate_python_code(fixed_code)
                                if is_valid:
                                    refactored_code = fixed_code
                                    refactored_valid = True
                                    result['validation_warnings'].append("Automatically fixed syntax errors (API)")
                    
                    result['refactored_valid'] = refactored_valid
                    result['refactored_code'] = refactored_code
                    result['success'] = True
                    return result
                    
                else:
                    # Check if error is retryable
                    error_msg = response['error'].lower()
                    if ('timeout' in error_msg or 'rate limit' in error_msg or 
                        'server error' in error_msg or 'network' in error_msg):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            continue
                    
                    result['error'] = response['error']
                    return result
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                result['error'] = "API request timed out after all retries"
                return result
                
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                result['error'] = "Connection error after all retries"
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                result['error'] = f"API error during refactoring: {str(e)}"
                return result
        
        # If we get here, all retries failed
        result['error'] = "All retry attempts failed"
        return result
    
    def _create_system_prompt(self, language: str, processing_options: Dict[str, Any] = None) -> str:
        """Create system prompt for refactoring based on processing options"""
        if not processing_options:
            processing_options = {
                'refactor_type': 'comprehensive',
                'preserve_comments': True,
                'add_documentation': True,
                'follow_conventions': False
            }
        
        refactor_type = processing_options.get('refactor_type', 'comprehensive')
        preserve_comments = processing_options.get('preserve_comments', True)
        add_documentation = processing_options.get('add_documentation', True)
        follow_conventions = processing_options.get('follow_conventions', False)
        
        base_prompt = "You are an expert code refactoring engine.\n\nYour job is to take code written in any language and return only the refactored version. Follow these rules strictly:\n\n1. Do not explain anything. Do not use any comments or markdown.\n2. Keep the original structure and language.\n"
        
        # Add refactor type specific instructions
        if refactor_type == 'performance':
            base_prompt += "3. Focus primarily on PERFORMANCE optimizations: optimize loops, reduce complexity, improve algorithms, eliminate redundant operations.\n"
        elif refactor_type == 'readability':
            base_prompt += "3. Focus primarily on READABILITY improvements: better naming, clearer logic flow, simplified expressions, consistent formatting.\n"
        elif refactor_type == 'security':
            base_prompt += "3. Focus primarily on SECURITY improvements: fix vulnerabilities, secure data handling, input validation, safe coding practices.\n"
        else:  # comprehensive
            base_prompt += "3. Provide COMPREHENSIVE refactoring: improve naming, simplify logic, remove duplication, add typing (if language supports it), and make code modern and clean.\n"
        
        # Add comment preservation instructions
        if preserve_comments:
            base_prompt += "4. PRESERVE all existing comments and maintain their placement.\n"
        else:
            base_prompt += "4. Remove unnecessary comments but keep essential ones.\n"
        
        # Add documentation instructions
        if add_documentation:
            base_prompt += "5. ADD clear docstrings/documentation for functions and classes where missing.\n"
        else:
            base_prompt += "5. Do not add new documentation unless absolutely necessary.\n"
        
        # Add convention following instructions
        if follow_conventions:
            base_prompt += f"6. STRICTLY follow {language} coding conventions and style guidelines.\n"
        else:
            base_prompt += "6. Maintain existing code style while making improvements.\n"
        
        base_prompt += "7. NEVER output text like 'Here is the refactored code:' — only output the code.\n\nYour output must be clean, minimal, and production-ready."
        
        return base_prompt
    
    def _create_user_prompt(self, code: str, language: str) -> str:
        """Create user prompt with the code to refactor"""
        return code
    
    def _make_api_request(self, system_prompt: str, user_prompt: str, max_retries: int = 1) -> Dict[str, Any]:
        """Make API request to DeepSeek API using chat completion format"""
        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        last_error = ""
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=180
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        choice = data['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            content = choice['message']['content']
                            return {
                                'success': True,
                                'content': content,
                                'usage': data.get('usage', {})
                            }
                    
                    last_error = f'No response content from API. Response: {data}'
                    return {
                        'success': False,
                        'error': last_error
                    }
                
                elif response.status_code == 429:  # Rate limit
                    # OpenRouter rate limiting
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', '')
                        if 'daily' in error_message.lower() or 'quota' in error_message.lower():
                            last_error = "Daily rate limit exceeded. Please wait until tomorrow or upgrade your plan."
                            return {
                                'success': False,
                                'error': last_error
                            }
                    except:
                        pass
                    
                    wait_time = 60 + (30 * attempt)  # Wait time for OpenRouter
                    last_error = f"Rate limited, waiting {wait_time}s"
                    time.sleep(wait_time)
                    continue
                
                else:
                    error_msg = f"API request failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
                    except:
                        error_msg += f": {response.text[:500]}"
                    
                    last_error = error_msg
                    
                    # Don't retry on certain errors
                    if response.status_code in [400, 401, 403]:
                        return {
                            'success': False,
                            'error': error_msg
                        }
                    
            except requests.exceptions.Timeout:
                last_error = f"API request timed out (attempt {attempt + 1})"
                if attempt < max_retries - 1:
                    time.sleep(15)  # Shorter timeout wait
                    continue
                return {
                    'success': False,
                    'error': 'API request timed out after all retries'
                }
            
            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(15)  # Shorter network error wait
                    continue
                return {
                    'success': False,
                    'error': last_error
                }
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                return {
                    'success': False,
                    'error': last_error
                }
        
        return {
            'success': False,
            'error': f'Failed after {max_retries} attempts. Last error: {last_error}'
        }
    
    def _clean_response(self, response: str, language: str) -> str:
        """Clean up LLM response to extract just the code"""
        
        # Handle completely corrupted responses that start with quotes and backticks
        if response.strip().startswith('"\n```'):
            # This is a corrupted response, try to extract any actual code
            # Look for patterns that might contain actual code
            code_pattern = re.search(r'def\s+\w+|class\s+\w+|function\s+\w+|public\s+class', response)
            if not code_pattern:
                # No actual code found, return empty
                return ""
        
        # Remove instruction tokens first
        cleaned = re.sub(r'\[INST\].*?\[/INST\]', '', response, flags=re.DOTALL)
        cleaned = re.sub(r'<<INST>>.*?<</INST>>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<<SYS>>.*?<</SYS>>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\[SYS\].*?\[/SYS\]', '', cleaned, flags=re.DOTALL)
        
        # Remove leading quotes and backticks that indicate corrupted response
        cleaned = re.sub(r'^"\s*\n```.*?-->', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^".*?-->', '', cleaned, flags=re.MULTILINE)
        
        # Remove repetitive explanatory text
        cleaned = re.sub(r'no refactoring performed.*?syntax itself', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'It\'s already as simple.*?language syntax', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Try to find code in markdown blocks first
        code_block_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', cleaned, re.DOTALL)
        if code_block_match:
            potential_code = code_block_match.group(1).strip()
            if self._is_valid_code(potential_code, language):
                return potential_code
        
        # If no markdown blocks, try to extract based on language patterns
        if language.lower() == 'python':
            return self._extract_python_code_simple(cleaned)
        elif language.lower() in ['javascript', 'jsx']:
            return self._extract_js_code_simple(cleaned)
        elif language.lower() == 'java':
            return self._extract_java_code_simple(cleaned)
        
        # Fallback: return cleaned response
        return cleaned.strip()
    
    def _is_valid_code(self, text: str, language: str) -> bool:
        """Check if text contains valid code patterns"""
        if not text.strip():
            return False
        
        if language.lower() == 'python':
            return bool(re.search(r'def\s+\w+|class\s+\w+|import\s+\w+|return\s+', text))
        elif language.lower() in ['javascript', 'jsx']:
            return bool(re.search(r'function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+', text))
        elif language.lower() == 'java':
            return bool(re.search(r'public\s+class|private\s+\w+|public\s+\w+', text))
        
        return True
    
    def _extract_python_code_simple(self, response: str) -> str:
        """Simple Python code extraction"""
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            # Skip obvious non-code lines
            if (line.strip().startswith('"') or
                'no refactoring performed' in line.lower() or
                'already as simple' in line.lower() or
                line.strip().startswith('-->')): 
                continue
            
            # Include lines that look like Python code
            if (line.startswith('def ') or
                line.startswith('class ') or
                line.startswith('import ') or
                line.startswith('from ') or
                line.startswith('    ') or  # indented
                line.startswith('return ') or
                line.startswith('print(') or
                '=' in line and not line.strip().startswith('#') or
                line.strip() == ''):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _extract_js_code_simple(self, response: str) -> str:
        """Simple JavaScript code extraction"""
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            if (line.strip().startswith('"') or
                'no refactoring performed' in line.lower()):
                continue
            
            if (line.startswith('function ') or
                line.startswith('const ') or
                line.startswith('let ') or
                line.startswith('var ') or
                line.startswith('    ') or
                '=' in line or
                line.strip() == ''):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _extract_java_code_simple(self, response: str) -> str:
        """Simple Java code extraction"""
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            if (line.strip().startswith('"') or
                'no refactoring performed' in line.lower()):
                continue
            
            if (line.startswith('public ') or
                line.startswith('private ') or
                line.startswith('class ') or
                line.startswith('    ') or
                '=' in line or
                line.strip() == ''):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _extract_python_code(self, response: str) -> str:
        """Extract actual Python code from verbose response"""
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip obvious explanatory lines
            if (stripped.startswith('The refactored code') or 
                stripped.startswith('<<SYS>>') or
                stripped.startswith('Here is the refactored') or
                stripped.startswith('This is the refactored') or
                'refactored code should be' in stripped.lower()):
                continue
            
            # Skip lines that are clearly explanations
            if ('refactoring task' in stripped.lower() and 
                'def ' not in stripped and 
                'class ' not in stripped):
                continue
            
            # If we find a function or class definition, we're definitely in code
            if (line.startswith('def ') or line.startswith('class ')):
                in_code_block = True
                code_lines.append(line)
                continue
            
            # If we're in a code block, include most lines
            if in_code_block:
                code_lines.append(line)
                continue
            
            # Include lines that look like Python code even if not in a block
            if (line.startswith('import ') or
                line.startswith('from ') or
                line.startswith('    ') or  # indented lines
                line.startswith('if ') or
                line.startswith('for ') or
                line.startswith('while ') or
                line.startswith('try:') or
                line.startswith('except') or
                line.startswith('return ') or
                line.startswith('print(') or
                stripped.endswith(':') or
                ('=' in line and not line.strip().startswith('#')) or
                line.strip() == ''):
                code_lines.append(line)
                in_code_block = True
        
        # If we didn't find any clear code structure, try to extract from the original response
        if not code_lines or not any('def ' in line or 'class ' in line or 'import ' in line for line in code_lines):
            # Look for code patterns in the original response
            
            # Try to find code blocks in markdown format
            code_block_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
            if code_block_match:
                return code_block_match.group(1).strip()
            
            # Try to find code after "Python Code" or similar markers
            code_after_marker = re.search(r'(?:Python Code|Refactored code|Improved code|refactoring version)\s*:?-?\s*(?:would be:?)?\s*\n(.*?)(?:\n\n|$)', response, re.DOTALL | re.IGNORECASE)
            if code_after_marker:
                potential_code = code_after_marker.group(1).strip()
                # Clean up the extracted code
                lines = potential_code.split('\n')
                clean_lines = []
                for line in lines:
                    # Skip lines that are clearly explanatory
                    if not (line.strip().startswith('Please note') or 
                           line.strip().startswith('This is') or
                           line.strip().startswith('The refactored') or
                           'for better understanding' in line.lower() or
                           'recommended using tools' in line.lower()):
                        clean_lines.append(line)
                if clean_lines:
                    return '\n'.join(clean_lines).strip()
            
            # Try to extract code that appears after instruction tokens
            code_after_inst = re.search(r'<<INST\]?>>(.+?)(?:<<|$)', response, re.DOTALL)
            if code_after_inst:
                potential_code = code_after_inst.group(1).strip()
                # Look for actual Python code patterns
                if re.search(r'def\s+\w+\s*\(', potential_code) or re.search(r'\breturn\b', potential_code):
                    return potential_code
            
            # Try to find lines that look like Python code
            potential_code_lines = []
            for line in lines:
                stripped = line.strip()
                # Skip obvious explanatory text
                if (stripped.startswith('The refactored code') or 
                   stripped.startswith('<<SYS>>') or
                   stripped.startswith('Here is the refactored') or
                   stripped.startswith('This is the refactored') or
                   stripped.startswith('This code is already') or
                   stripped.startswith('Please note') or
                   'does not need any changes' in stripped):
                    continue
                
                # Look for lines that contain code-like patterns
                if (re.search(r'def\s+\w+\s*\(', line) or
                    re.search(r'\s*return\s+', line) or
                    re.search(r'\s*print\s*\(', line) or
                    re.search(r'^\s*[a-zA-Z_]\w*\s*=', line) or
                    (line.strip() and not line.strip().startswith('#') and 
                     ('(' in line and ')' in line or '+' in line or '=' in line))):
                    potential_code_lines.append(line)
            
            if potential_code_lines:
                return '\n'.join(potential_code_lines).strip()
            
            # Last resort: return original code if no refactored version found
            return response.strip()
        
        return '\n'.join(code_lines).strip()
    
    def _extract_js_code(self, response: str) -> str:
        """Extract actual JavaScript code from verbose response"""
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip explanatory lines
            if (stripped.startswith('The refactored code') or 
                stripped.startswith('<<SYS>>') or
                stripped.startswith('Here is the refactored') or
                'refactored code should be' in stripped.lower()):
                continue
            
            # Include lines that look like JavaScript code
            if (line.startswith('function ') or 
                line.startswith('const ') or
                line.startswith('let ') or
                line.startswith('var ') or
                line.startswith('import ') or
                line.startswith('export ') or
                line.startswith('    ') or  # indented lines
                line.startswith('if ') or
                line.startswith('for ') or
                line.startswith('while ') or
                line.startswith('return ') or
                line.startswith('console.') or
                stripped.endswith('{') or
                stripped.endswith('}') or
                stripped.endswith(';') or
                '=' in line or
                line.strip() == ''):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _extract_java_code(self, response: str) -> str:
        """Extract actual Java code from verbose response"""
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip explanatory lines
            if (stripped.startswith('The refactored code') or 
                stripped.startswith('<<SYS>>') or
                stripped.startswith('Here is the refactored') or
                'refactored code should be' in stripped.lower()):
                continue
            
            # Include lines that look like Java code
            if (line.startswith('public ') or 
                line.startswith('private ') or
                line.startswith('protected ') or
                line.startswith('class ') or
                line.startswith('interface ') or
                line.startswith('import ') or
                line.startswith('package ') or
                line.startswith('    ') or  # indented lines
                line.startswith('if ') or
                line.startswith('for ') or
                line.startswith('while ') or
                line.startswith('return ') or
                line.startswith('System.') or
                stripped.endswith('{') or
                stripped.endswith('}') or
                stripped.endswith(';') or
                '=' in line or
                line.strip() == ''):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _auto_fix_syntax_errors(self, broken_code: str, error_msg: str, original_code: str, language: str, max_attempts: int = 3) -> str:
        """Automatically fix syntax errors using LLM with specific error correction prompts"""
        current_code = broken_code
        
        for attempt in range(max_attempts):
            try:
                # Create error-specific correction prompt
                system_prompt = self._create_error_correction_prompt(language)
                user_prompt = self._create_error_correction_user_prompt(current_code, error_msg, original_code)
                
                # Make API request for error correction
                response = self._make_api_request(system_prompt, user_prompt, max_retries=1)
                
                if response['success']:
                    corrected_code = self._clean_response(response['content'], language)
                    
                    # Validate the corrected code
                    if language.lower() == 'python':
                        is_valid, new_error = ASTValidator.validate_python_code(corrected_code)
                        if is_valid:
                            return corrected_code
                        else:
                            # Update error message for next attempt
                            error_msg = new_error
                            current_code = corrected_code
                    else:
                        # For non-Python languages, return the corrected code
                        return corrected_code
                else:
                    # If API call fails, break and return original
                    break
                    
            except Exception as e:
                # If any error occurs, break and return original
                break
        
        # If all attempts fail, return the original broken code
        return broken_code
    
    def _create_error_correction_prompt(self, language: str) -> str:
        """Create system prompt specifically for error correction"""
        return f"""You are a syntax error correction specialist for {language} code.

Your ONLY job is to fix syntax errors in the provided code while preserving all functionality and logic.

Rules:
1. Fix ONLY syntax errors - do not refactor or improve the code
2. Preserve all variable names, function names, and logic exactly as they are
3. Output ONLY the corrected code - no explanations, no markdown, no comments
4. Do not add or remove functionality
5. Ensure the output is valid {language} syntax

You will receive the broken code and the specific error message. Fix only what's broken."""
    
    def _create_error_correction_user_prompt(self, broken_code: str, error_msg: str, original_code: str) -> str:
        """Create user prompt for error correction with context"""
        return f"""BROKEN CODE:
```
{broken_code}
```

ERROR MESSAGE:
{error_msg}

ORIGINAL CODE (for reference):
```
{original_code}
```

Fix the syntax error in the broken code. Output only the corrected code."""
    
    def _attempt_code_fix(self, code: str) -> str:
        """Attempt to fix common syntax issues in refactored code"""
        # Remove any trailing explanatory text after the code
        lines = code.split('\n')
        
        # Find the last line that looks like code
        last_code_line = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('#') and not line.startswith('Note:') and not line.startswith('This'):
                last_code_line = i
                break
        
        # Keep only up to the last code line
        fixed_code = '\n'.join(lines[:last_code_line + 1])
        
        return fixed_code.strip()
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test the API connection"""
        try:
            test_prompt = "Hello, please respond with 'API connection successful'"
            response = self._make_api_request(
                "You are a helpful assistant.",
                test_prompt
            )
            return response
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection test failed: {str(e)}"
            }