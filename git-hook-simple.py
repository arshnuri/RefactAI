#!/usr/bin/env python
"""
RefactAI Simple Git Pre-Push Hook - Non-interactive version for testing
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add the repository root to Python path
repo_root = Path(__file__).parent.parent.parent.absolute()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Change working directory to repo root
os.chdir(repo_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Django settings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='cli-secret-key-for-refactai',
        OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY', ''),
        OPENROUTER_API_URL=os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions'),
        DEFAULT_MODEL=os.getenv('DEFAULT_MODEL', 'anthropic/claude-3.5-sonnet'),
        PREFER_LOCAL_LLM=os.getenv('PREFER_LOCAL_LLM', 'false').lower() == 'true',
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

from refactor import LocalLLMClient
from refactai_app.utils.language_detect import LanguageDetector
from refactai_app.utils.ast_utils import ASTValidator
from refactai_app.utils.llm_client import LLMClient


def get_git_changed_files():
    """Get list of changed files from Git"""
    try:
        # Get files changed in the commits being pushed
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'origin/master...HEAD', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # If no remote comparison available, get recent changes
        if not result.stdout.strip():
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', '--diff-filter=ACM'],
                capture_output=True,
                text=True,
                check=True
            )
        
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        # Filter for supported code files
        supported_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs']
        code_files = []
        
        for file in changed_files:
            if any(file.endswith(ext) for ext in supported_extensions) and os.path.exists(file):
                code_files.append(file)
        
        return code_files
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting Git changes: {e}")
        return []


def detect_language_from_file(file_path):
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    ext_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C',
        '.hpp': 'C++',
        '.cs': 'C#'
    }
    return ext_map.get(ext, 'Unknown')


def test_openrouter_connection():
    """Test OpenRouter API connection"""
    try:
        client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
        result = client.refactor_code(
            code="print('test')",
            language='python',
            file_path='test.py',
            session_id='git_hook_test'
        )
        return result.get('success', False)
    except Exception as e:
        print(f"❌ OpenRouter API test failed: {e}")
        return False


def refactor_file(file_path):
    """Refactor a single file using OpenRouter API + AST validation"""
    try:
        # Read original code
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Skip empty files
        if not original_code.strip():
            return {'success': True, 'skipped': True, 'reason': 'Empty file'}
        
        # Skip very large files
        if len(original_code) > 100000:
            return {'success': True, 'skipped': True, 'reason': 'File too large (>100KB)'}
        
        language = detect_language_from_file(file_path)
        
        print(f"🔄 Refactoring {file_path} ({language})...")
        
        # Force OpenRouter API client with AST validation
        client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
        
        # Refactor code using OpenRouter API
        result = client.refactor_code(
            code=original_code,
            language=language.lower(),
            file_path=file_path,
            session_id=f'git_hook_{os.path.basename(file_path)}'
        )
        
        if not result['success']:
            return {'success': False, 'error': result['error']}
        
        refactored_code = result['refactored_code']
        
        # AST validation for Python files
        if language.lower() == 'python':
            ast_validator = ASTValidator()
            is_valid, error_msg = ast_validator.validate_python_code(refactored_code)
            
            if not is_valid:
                return {
                    'success': False, 
                    'error': f'AST validation failed: {error_msg}'
                }
        
        # Write refactored code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(refactored_code)
            f.flush()  # Ensure content is written to disk
        
        # Force filesystem sync
        os.sync() if hasattr(os, 'sync') else None
        
        return {'success': True, 'refactored': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    """Main hook execution - non-interactive version"""
    print("🚀 RefactAI Git Hook - Simple Test Mode")
    print("=" * 50)
    
    # Check for skip flag
    if '--no-refactor' in ' '.join(sys.argv):
        print("⚠️  Skipping refactoring (--no-refactor flag detected)")
        return 0
    
    # Test OpenRouter API connection
    print("🧪 Testing OpenRouter API connection...")
    if not test_openrouter_connection():
        print("❌ OpenRouter API not available")
        print("   Please check your OPENROUTER_API_KEY environment variable")
        return 1
    
    print("✅ OpenRouter API connection successful")
    
    # Get changed files only (non-interactive)
    files = get_git_changed_files()
    
    if not files:
        print("ℹ️  No supported code files found in staged changes")
        print("✅ Proceeding with push (no refactoring needed)")
        return 0
    
    print(f"🔍 Found {len(files)} code file(s) to refactor:")
    for file in files:
        language = detect_language_from_file(file)
        size = os.path.getsize(file)
        print(f"   • {file} ({language}, {size} bytes)")
    
    print("\n🔄 Starting refactoring process...")
    
    # Process files
    processed = 0
    skipped = 0
    failed = 0
    successfully_refactored_files = []
    
    for file_path in files:
        result = refactor_file(file_path)
        
        if result['success']:
            if result.get('skipped'):
                skipped += 1
                print(f"⏭️  Skipped {file_path}: {result['reason']}")
            else:
                processed += 1
                successfully_refactored_files.append(file_path)
                print(f"✅ Refactored: {file_path}")
        else:
            failed += 1
            print(f"❌ Failed: {file_path} - {result['error']}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Processed: {processed}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Failed: {failed}")
    
    if processed > 0:
        print("\n📦 Staging refactored files...")
        for file in successfully_refactored_files:
            subprocess.run(['git', 'add', file], check=True)
        print("✅ Files staged successfully")
    
    if failed > 0:
        print("\n⚠️  Some files failed to refactor")
        print("❌ Stopping push due to failures")
        return 1
    
    print("\n🎉 Refactoring complete! Proceeding with push...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
