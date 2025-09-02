#!/usr/bin/env python3
"""
RefactAI Batch CLI - Non-interactive mode for Git hooks and automation
Compatible with the interactive CLI but provides batch processing capabilities
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure Django settings for CLI usage
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY=os.getenv('DJANGO_SECRET_KEY', 'dev-only-key-change-in-production'),
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


def detect_language_from_file(file_path: str) -> str:
    """Detect programming language from file extension and content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return LanguageDetector.detect_language(file_path, content)
    except Exception:
        # Fallback to extension-based detection
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
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        return ext_map.get(ext, 'Unknown')


def is_supported_language(language: str) -> bool:
    """Check if the language is supported for refactoring"""
    supported = ['Python', 'JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'C#']
    return language in supported


def backup_file(file_path: str) -> str:
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup"
    with open(file_path, 'r', encoding='utf-8') as original:
        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(original.read())
    return backup_path


def validate_refactored_code(original_code: str, refactored_code: str, language: str) -> List[str]:
    """Validate the refactored code"""
    warnings = []
    
    # Basic checks
    if len(refactored_code.strip()) == 0:
        warnings.append("Refactored code is empty")
        return warnings
    
    if len(refactored_code) < len(original_code) * 0.5:
        warnings.append("Refactored code is significantly shorter than original")
    
    # Python-specific validation
    if language == 'Python':
        try:
            validator = ASTValidator()
            if not validator.validate_syntax(refactored_code):
                warnings.append("Python syntax validation failed")
        except Exception as e:
            warnings.append(f"Validation error: {str(e)}")
    
    return warnings


def refactor_file(file_path: str, model: str = "deepseek-coder:6.7b", 
                 create_backup: bool = True, dry_run: bool = False, 
                 processing_mode: str = "hybrid", quiet: bool = False) -> bool:
    """Refactor a single file"""
    if not os.path.exists(file_path):
        if not quiet:
            print(f"❌ Error: File not found: {file_path}")
        return False
    
    # Detect language
    language = detect_language_from_file(file_path)
    if not is_supported_language(language):
        if not quiet:
            print(f"⚠️  Skipping {file_path}: {language} is not supported")
        return True
    
    if not quiet:
        print(f"🔄 Refactoring {file_path} ({language})...")
    
    try:
        # Read original code
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Skip empty files
        if not original_code.strip():
            if not quiet:
                print(f"⚠️  Skipping {file_path}: File is empty")
            return True
        
        # Skip very large files (>100KB)
        if len(original_code) > 100000:
            if not quiet:
                print(f"⚠️  Skipping {file_path}: File too large (>100KB)")
            return True
        
        # Initialize LLM client based on processing mode
        if processing_mode == "hybrid":
            client = LLMClient(use_hybrid_approach=True, use_local_llm=True)
        elif processing_mode == "local":
            client = LocalLLMClient(model_name=model)
        elif processing_mode == "api":
            client = LLMClient(use_hybrid_approach=False, use_local_llm=False)
        else:
            # Default to hybrid
            client = LLMClient(use_hybrid_approach=True, use_local_llm=True)
        
        # Use appropriate method based on client type
        if processing_mode == "local":
            result = client.run_llm_refactor(original_code, language.lower())
        else:
            result = client.refactor_code(
                code=original_code,
                language=language.lower(),
                file_path=file_path,
                session_id=f'batch_cli_{os.path.basename(file_path)}'
            )
        
        if not result['success']:
            if not quiet:
                print(f"❌ Failed to refactor {file_path}: {result['error']}")
            return False
        
        refactored_code = result['refactored_code']
        
        # Validate refactored code
        warnings = validate_refactored_code(original_code, refactored_code, language)
        if warnings and not quiet:
            print(f"⚠️  Validation warnings for {file_path}:")
            for warning in warnings:
                print(f"   - {warning}")
        
        # Show diff in dry run mode
        if dry_run:
            if not quiet:
                print(f"\n📋 Dry run for {file_path}:")
                print("=" * 50)
                print(refactored_code[:500] + ("..." if len(refactored_code) > 500 else ""))
                print("=" * 50)
            return True
        
        # Create backup if requested
        if create_backup:
            backup_path = backup_file(file_path)
            if not quiet:
                print(f"💾 Backup created: {backup_path}")
        
        # Write refactored code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(refactored_code)
        
        if not quiet:
            print(f"✅ Successfully refactored {file_path}")
        return True
        
    except Exception as e:
        if not quiet:
            print(f"❌ Error refactoring {file_path}: {str(e)}")
        return False


def refactor_directory(directory: str, model: str = "deepseek-coder:6.7b", 
                      create_backup: bool = True, dry_run: bool = False, 
                      processing_mode: str = "hybrid", quiet: bool = False) -> bool:
    """Refactor all supported files in a directory"""
    if not os.path.isdir(directory):
        if not quiet:
            print(f"❌ Error: Directory not found: {directory}")
        return False
    
    # Find all code files
    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs']
    code_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common build/cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'build', 'dist']]
        
        for file in files:
            if any(file.endswith(ext) for ext in code_extensions):
                code_files.append(os.path.join(root, file))
    
    if not code_files:
        if not quiet:
            print(f"⚠️  No supported code files found in {directory}")
        return True
    
    if not quiet:
        print(f"🔍 Found {len(code_files)} code files to refactor")
    
    success_count = 0
    for file_path in code_files:
        if refactor_file(file_path, model, create_backup, dry_run, processing_mode, quiet):
            success_count += 1
    
    if not quiet:
        print(f"\n📊 Refactoring complete: {success_count}/{len(code_files)} files processed successfully")
    
    return success_count == len(code_files)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="RefactAI - Batch Mode Code Refactoring Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python cli_batch.py script.py                    # Refactor single file (hybrid mode)
  python cli_batch.py src/                         # Refactor directory (hybrid mode)
  python cli_batch.py script.py --dry-run          # Preview changes
  python cli_batch.py script.py --no-backup        # Don't create backup
  python cli_batch.py script.py --mode local       # Use local LLM only
  python cli_batch.py script.py --mode api         # Use API only
  python cli_batch.py script.py --model llama2:7b  # Use different model
  python cli_batch.py script.py --quiet            # Minimal output
"""
    )
    
    parser.add_argument('path', help='File or directory to refactor')
    parser.add_argument('--model', '-m', default='deepseek-coder:6.7b',
                       help='Local LLM model to use (default: deepseek-coder:6.7b)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not create backup files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without modifying files')
    parser.add_argument('--test', action='store_true',
                       help='Test local LLM connection')
    parser.add_argument('--mode', '-p', default='hybrid',
                       choices=['hybrid', 'local', 'api'],
                       help='Processing mode: hybrid (default), local, or api')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output (useful for scripts)')
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        if not args.quiet:
            print("🧪 Testing local LLM connection...")
        client = LocalLLMClient(model_name=args.model)
        test_result = client.test_connection()
        
        if test_result['available']:
            if not args.quiet:
                print(f"✅ Local LLM ({args.model}) is available and working!")
            return 0
        else:
            if not args.quiet:
                print(f"❌ Local LLM not available: {test_result['error']}")
                print("\nPlease install one of the following:")
                print("- Ollama: https://ollama.ai/")
                print("- LM Studio: https://lmstudio.ai/")
                print("- llama.cpp: https://github.com/ggerganov/llama.cpp")
            return 1
    
    # Validate path
    if not os.path.exists(args.path):
        if not args.quiet:
            print(f"❌ Error: Path not found: {args.path}")
        return 1
    
    if not args.quiet:
        print(f"🚀 RefactAI - Code Refactoring (Batch Mode)")
        print(f"📁 Target: {args.path}")
        print(f"🤖 Model: {args.model}")
        print(f"⚙️  Processing Mode: {args.mode.upper()}")
        print(f"💾 Backup: {'No' if args.no_backup else 'Yes'}")
        print(f"🔍 Mode: {'Dry Run' if args.dry_run else 'Live'}")
        print()
    
    # Refactor file or directory
    if os.path.isfile(args.path):
        success = refactor_file(args.path, args.model, not args.no_backup, args.dry_run, args.mode, args.quiet)
    else:
        success = refactor_directory(args.path, args.model, not args.no_backup, args.dry_run, args.mode, args.quiet)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
