#!/usr/bin/env python
"""
RefactAI Simple Git Pre-Push Hook - ASCII only version
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Set environment variables to force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    pass

# Configure Django settings
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY=os.getenv('DJANGO_SECRET_KEY', 'git-hook-dev-key-change-in-production'),
        OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY', ''),
        OPENROUTER_API_URL=os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions'),
        DEFAULT_MODEL=os.getenv('DEFAULT_MODEL', 'anthropic/claude-3.5-sonnet'),
        PREFER_LOCAL_LLM=False,
        INSTALLED_APPS=[
            'refactai_app',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    )

django.setup()

def get_git_changed_files():
    """Get list of changed files from git diff"""
    try:
        # Get files that are different between local and remote
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD', 'origin/master'],
            capture_output=True, text=True, cwd=project_root, encoding='utf-8'
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return files
        else:
            # Fallback to staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, cwd=project_root, encoding='utf-8'
            )
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                return files
        return []
    except Exception as e:
        print(f"ERROR: Error getting Git changes: {e}")
        return []

def is_supported_file(file_path):
    """Check if file is supported for refactoring"""
    supported_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs'}
    return Path(file_path).suffix.lower() in supported_extensions

def detect_language(file_path):
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cs': 'csharp'
    }
    return language_map.get(ext, 'unknown')

def test_openrouter_api():
    """Test if OpenRouter API is available"""
    try:
        from refactai_app.utils.llm_client import LLMClient
        client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
        
        # Simple test with minimal code
        result = client.refactor_code(
            code="print('test')",
            language='python',
            file_path='test.py',
            session_id='hook_test'
        )
        return result.get('success', False)
    except Exception as e:
        print(f"ERROR: OpenRouter API test failed: {e}")
        return False

def refactor_file(file_path, language):
    """Refactor a single file"""
    try:
        from refactai_app.utils.llm_client import LLMClient
        
        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        if not original_code.strip():
            return {'success': True, 'skipped': True, 'reason': 'Empty file'}
        
        print(f"REFACTORING: {file_path} ({language})...")
        
        # Create LLM client
        client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
        
        # Refactor the code
        result = client.refactor_code(
            code=original_code,
            language=language,
            file_path=file_path,
            session_id=f'git_hook_{Path(file_path).stem}'
        )
        
        if result['success']:
            refactored_code = result['refactored_code']
            
            # Write refactored code back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
                f.flush()
            os.sync()
            
            return {'success': True, 'refactored': True}
        else:
            return {'success': False, 'error': result.get('error', 'Unknown error')}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """Main hook function"""
    print("=== RefactAI Git Hook - Simple Mode ===")
    print("==================================================")
    
    # Skip if --no-refactor flag is present
    if '--no-refactor' in sys.argv:
        print("WARNING: Skipping refactoring (--no-refactor flag detected)")
        return 0
    
    # Test OpenRouter API connection
    print("TESTING: OpenRouter API connection...")
    if not test_openrouter_api():
        print("ERROR: OpenRouter API not available")
        return 1
    
    print("SUCCESS: OpenRouter API connection successful")
    
    # Get changed files
    changed_files = get_git_changed_files()
    code_files = [f for f in changed_files if is_supported_file(f) and os.path.exists(f)]
    
    if not code_files:
        print("SUCCESS: Proceeding with push (no refactoring needed)")
        return 0
    
    print(f"FOUND: {len(code_files)} code file(s) to refactor:")
    for file_path in code_files:
        file_size = os.path.getsize(file_path)
        print(f"   • {file_path} ({detect_language(file_path).title()}, {file_size} bytes)")
    
    print("\nSTARTING: refactoring process...")
    
    successfully_refactored_files = []
    processed = 0
    skipped = 0
    failed = 0
    failed_files = []
    
    for file_path in code_files:
        language = detect_language(file_path)
        result = refactor_file(file_path, language)
        
        if result['success']:
            if result.get('refactored'):
                print(f"SUCCESS: Refactored: {file_path}")
                successfully_refactored_files.append(file_path)
                processed += 1
            elif result.get('skipped'):
                print(f"SKIPPED: {file_path} - {result.get('reason', 'Unknown reason')}")
                skipped += 1
        else:
            print(f"ERROR: Failed: {file_path} - {result['error']}")
            failed_files.append(file_path)
            failed += 1
    
    print(f"\nSUMMARY:")
    print(f"   SUCCESS: Processed: {processed}")
    print(f"   SKIPPED: Skipped: {skipped}")
    print(f"   ERROR: Failed: {failed}")
    
    # Stage only successfully refactored files
    if successfully_refactored_files:
        for file_path in successfully_refactored_files:
            subprocess.run(['git', 'add', file_path], cwd=project_root, check=False)
        print("SUCCESS: Files staged successfully")
        return 0
    elif failed_files:
        print("\nWARNING: Some files failed to refactor")
        print("ERROR: Stopping push due to failures")
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
