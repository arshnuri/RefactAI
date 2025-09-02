#!/usr/bin/env python3
"""
RefactAI Interactive Git Pre-Push Hook
Provides an interactive, user-friendly experience for pre-push code refactoring
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Rich for beautiful terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule

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


class InteractiveGitHook:
    """Interactive Git Pre-Push Hook with rich UI"""
    
    def __init__(self):
        self.console = Console()
        # Force OpenRouter API + AST validation mode
        self.config = {
            'model': 'anthropic/claude-3.5-sonnet',  # Default OpenRouter model
            'processing_mode': 'hybrid_openrouter',  # Force hybrid with OpenRouter
            'create_backup': False,  # Don't create backups in git hooks
            'dry_run': False,
            'use_ast_validation': True,  # Always use AST validation
            'refactor_full_repo': True  # New option for full repo refactoring
        }
        
    def show_banner(self):
        """Display the RefactAI Git Hook banner"""
        banner_text = Text("RefactAI Git Hook", style="bold cyan")
        banner_text.append(" - Pre-Push Code Refactoring", style="bold white")
        
        banner = Panel(
            Align.center(banner_text),
            style="cyan",
            padding=(1, 2)
        )
        self.console.print(banner)
        self.console.print("")
    
    def get_git_changed_files(self) -> List[str]:
        """Get list of changed files from Git"""
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
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
            self.console.print(f"[red]❌ Error getting Git changes: {e}[/red]")
            return []
    
    def get_all_repo_files(self) -> List[str]:
        """Get all code files in the repository"""
        try:
            # Get all tracked files in the repository
            result = subprocess.run(
                ['git', 'ls-files'],
                capture_output=True,
                text=True,
                check=True
            )
            
            all_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Filter for supported code files
            supported_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs']
            code_files = []
            
            for file in all_files:
                if any(file.endswith(ext) for ext in supported_extensions) and os.path.exists(file):
                    code_files.append(file)
            
            return code_files
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error getting repository files: {e}[/red]")
            return []
    
    def detect_language_from_file(self, file_path: str) -> str:
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
                '.cs': 'C#'
            }
            return ext_map.get(ext, 'Unknown')
    
    def test_openrouter_connection(self) -> bool:
        """Test OpenRouter API connection"""
        try:
            # Force OpenRouter API client
            client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
            
            # Simple test call
            result = client.refactor_code(
                code="print('test')",
                language='python',
                file_path='test.py',
                session_id='git_hook_test'
            )
            
            return result.get('success', False)
        except Exception as e:
            self.console.print(f"[red]❌ OpenRouter API test failed: {e}[/red]")
            return False
    
    def refactor_file(self, file_path: str) -> Dict[str, Any]:
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
            
            language = self.detect_language_from_file(file_path)
            
            # Force OpenRouter API client with AST validation
            client = LLMClient(use_hybrid_approach=True, use_local_llm=False)
            
            # Refactor code using OpenRouter API
            result = client.refactor_code(
                code=original_code,
                language=language.lower(),
                file_path=file_path,
                session_id=f'git_hook_{os.path.basename(file_path)}',
                model_override=self.config['model']  # Use selected OpenRouter model
            )
            
            if not result['success']:
                return {'success': False, 'error': result['error']}
            
            refactored_code = result['refactored_code']
            
            # AST validation for Python files
            if language.lower() == 'python' and self.config['use_ast_validation']:
                ast_validator = ASTValidator()
                validation_result = ast_validator.validate_syntax(refactored_code)
                
                if not validation_result['valid']:
                    return {
                        'success': False, 
                        'error': f'AST validation failed: {validation_result["error"]}'
                    }
            
            # Write refactored code if not dry run
            if not self.config.get('dry_run', False):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(refactored_code)
            
            return {'success': True, 'refactored': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def show_file_preview(self, files: List[str]):
        """Show preview of files to be processed"""
        if not files:
            return
        
        files_table = Table(title="Files to Refactor", show_header=True, header_style="bold magenta")
        files_table.add_column("File", style="cyan", justify="left")
        files_table.add_column("Language", style="green", justify="center")
        files_table.add_column("Size", style="yellow", justify="right")
        files_table.add_column("Status", style="blue", justify="center")
        
        for file_path in files:
            language = self.detect_language_from_file(file_path)
            size = os.path.getsize(file_path)
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f}KB"
            
            # Determine status
            if size > 100000:
                status = "Skip (Large)"
                status_style = "yellow"
            elif size == 0:
                status = "Skip (Empty)"
                status_style = "yellow"
            else:
                status = "Ready"
                status_style = "green"
            
            files_table.add_row(
                file_path, 
                language, 
                size_str, 
                f"[{status_style}]{status}[/{status_style}]"
            )
        
        self.console.print(files_table)
        self.console.print("")
    
    def process_files_interactively(self, files: List[str], scope_msg: str = "files") -> Dict[str, Any]:
        """Process files with interactive options"""
        if not files:
            return {'success': True, 'processed': 0, 'skipped': 0, 'failed': 0}
        
        self.console.print(f"[cyan]🔍 Found {len(files)} code files in {scope_msg}[/cyan]\n")
        
        # Show file preview
        self.show_file_preview(files)
        
        # Configuration options
        self.console.print("[bold]Configuration Options:[/bold]")
        self.console.print("[green]✅ Using OpenRouter API + AST Validation (Forced)[/green]")
        
        # Ask for dry run
        dry_run = Confirm.ask("Preview changes only (dry run mode)?", default=False)
        self.config['dry_run'] = dry_run
        
        self.console.print("")
        
        # Confirm processing
        if not Confirm.ask(f"Proceed with refactoring {len(files)} files?", default=True):
            self.console.print("[yellow]⚠️  Refactoring cancelled by user[/yellow]")
            return {'success': False, 'cancelled': True}
        
        # Process files with progress
        processed = 0
        skipped = 0
        failed = 0
        failed_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Refactoring files...", total=len(files))
            
            for file_path in files:
                progress.update(task, description=f"Processing {os.path.basename(file_path)}...")
                
                if self.config['dry_run']:
                    # Simulate processing in dry run
                    time.sleep(0.1)
                    processed += 1
                    self.console.print(f"[blue]🔍 [Dry Run] Would refactor: {file_path}[/blue]")
                else:
                    result = self.refactor_file(file_path)
                    
                    if result['success']:
                        if result.get('skipped'):
                            skipped += 1
                            self.console.print(f"[yellow]⏭️  Skipped {file_path}: {result['reason']}[/yellow]")
                        else:
                            processed += 1
                            self.console.print(f"[green]✅ Refactored: {file_path}[/green]")
                    else:
                        failed += 1
                        failed_files.append(file_path)
                        self.console.print(f"[red]❌ Failed: {file_path} - {result['error']}[/red]")
                
                progress.advance(task)
        
        return {
            'success': True,
            'processed': processed,
            'skipped': skipped,
            'failed': failed,
            'failed_files': failed_files,
            'dry_run': self.config['dry_run']
        }
    
    def stage_refactored_files(self, files: List[str]):
        """Stage refactored files for commit"""
        try:
            for file in files:
                subprocess.run(['git', 'add', file], check=True)
            self.console.print("[green]📦 Refactored files have been staged[/green]")
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error staging files: {e}[/red]")
    
    def show_summary(self, results: Dict[str, Any]):
        """Show processing summary"""
        self.console.print(Rule("[bold]Summary[/bold]"))
        
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Metric", style="cyan", justify="right")
        summary_table.add_column("Count", style="green")
        
        if results.get('dry_run'):
            summary_table.add_row("🔍 Preview Mode:", "Enabled")
        
        summary_table.add_row("✅ Processed:", str(results.get('processed', 0)))
        summary_table.add_row("⏭️  Skipped:", str(results.get('skipped', 0)))
        summary_table.add_row("❌ Failed:", str(results.get('failed', 0)))
        
        summary_panel = Panel(
            summary_table,
            title="[bold]Refactoring Results[/bold]",
            border_style="blue"
        )
        self.console.print(summary_panel)
        
        # Show failed files if any
        if results.get('failed_files'):
            self.console.print("\n[red]Failed files:[/red]")
            for file in results['failed_files']:
                self.console.print(f"  [red]• {file}[/red]")
    
    def check_git_status(self):
        """Check Git repository status and user authentication"""
        try:
            # Check if we're in a Git repository
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                         capture_output=True, check=True)
            
            # Check if user is configured
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  capture_output=True, text=True)
            user_name = result.stdout.strip() if result.returncode == 0 else None
            
            result = subprocess.run(['git', 'config', 'user.email'], 
                                  capture_output=True, text=True)
            user_email = result.stdout.strip() if result.returncode == 0 else None
            
            # Check remote repository
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            remote_url = result.stdout.strip() if result.returncode == 0 else None
            
            return {
                'is_git_repo': True,
                'user_name': user_name,
                'user_email': user_email,
                'remote_url': remote_url,
                'can_push': bool(user_name and user_email and remote_url)
            }
            
        except subprocess.CalledProcessError:
            return {
                'is_git_repo': False,
                'user_name': None,
                'user_email': None,
                'remote_url': None,
                'can_push': False
            }

    def auto_push_changes(self, scope_msg="repository"):
        """Automatically push refactored changes to remote repository"""
        try:
            # Check Git status first
            git_status = self.check_git_status()
            
            if not git_status['can_push']:
                self.console.print("[yellow]⚠️  Cannot auto-push: Git user not configured or no remote[/yellow]")
                if not git_status['user_name']:
                    self.console.print("Configure with: git config user.name 'Your Name'")
                if not git_status['user_email']:
                    self.console.print("Configure with: git config user.email 'your.email@example.com'")
                if not git_status['remote_url']:
                    self.console.print("Add remote with: git remote add origin <url>")
                return False
            
            self.console.print(f"\n[cyan]🚀 Auto-pushing refactored {scope_msg}...[/cyan]")
            self.console.print(f"[dim]👤 User: {git_status['user_name']} <{git_status['user_email']}>[/dim]")
            self.console.print(f"[dim]📡 Remote: {git_status['remote_url']}[/dim]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                # Stage all changes
                task = progress.add_task("Staging changes...", total=None)
                subprocess.run(['git', 'add', '.'], check=True)
                
                # Create commit with detailed message
                progress.update(task, description="Creating commit...")
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"""refactor: Auto-refactored {scope_msg} using RefactAI

- Processed with OpenRouter API + AST validation
- Model: {self.config['model']}
- Timestamp: {timestamp}
- Scope: {scope_msg}

Generated by RefactAI Interactive Git Hook"""
                
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                
                # Push to remote
                progress.update(task, description="Pushing to remote...")
                subprocess.run(['git', 'push'], check=True)
            
            self.console.print("[green]✅ Successfully pushed refactored changes![/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Auto-push failed: {e}[/red]")
            self.console.print("[yellow]💡 You can manually push with: git push[/yellow]")
            return False
    
    def run(self):
        """Main hook execution"""
        try:
            self.show_banner()
            
            # Check for skip flag in git push arguments
            if '--no-refactor' in ' '.join(sys.argv):
                self.console.print("[yellow]⚠️  Skipping refactoring (--no-refactor flag detected)[/yellow]")
                return 0
            
            # Test OpenRouter API connection
            self.console.print("[cyan]🧪 Testing OpenRouter API connection...[/cyan]")
            
            if not self.test_openrouter_connection():
                error_panel = Panel(
                    "❌ OpenRouter API not available\n\n"
                    "Please ensure you have configured:\n"
                    "• OPENROUTER_API_KEY environment variable\n"
                    "• Valid API key from https://openrouter.ai\n\n"
                    "To skip refactoring: git push --no-refactor",
                    title="[red]OpenRouter API Connection Failed[/red]",
                    border_style="red"
                )
                self.console.print(error_panel)
                
                if not Confirm.ask("Continue push without refactoring?", default=False):
                    return 1
                return 0
            
            self.console.print("[green]✅ OpenRouter API connection successful[/green]\n")
            
            # Ask user about refactoring scope
            refactor_scope = Prompt.ask(
                "Refactoring scope",
                choices=["changed", "full-repo"],
                default="changed"
            )
            
            if refactor_scope == "full-repo":
                files = self.get_all_repo_files()
                scope_msg = "entire repository"
            else:
                files = self.get_git_changed_files()
                scope_msg = "staged changes"
            
            if not files:
                self.console.print(f"[yellow]ℹ️  No supported code files found in {scope_msg}[/yellow]")
                self.console.print("[green]✅ Proceeding with push (no refactoring needed)[/green]")
                return 0
            
            # Process files interactively
            results = self.process_files_interactively(files, scope_msg)
            
            if results.get('cancelled'):
                return 1
            
            # Show summary
            self.show_summary(results)
            
            # Auto-push if successful and user confirms
            if results.get('success') and results.get('processed') > 0:
                # Show Git status before asking
                git_status = self.check_git_status()
                
                if git_status['can_push']:
                    self.console.print(f"\n[cyan]📡 Git Status:[/cyan]")
                    self.console.print(f"  👤 User: {git_status['user_name']} <{git_status['user_email']}>")
                    self.console.print(f"  🌐 Remote: {git_status['remote_url']}")
                    
                    if Confirm.ask("Auto-push changes to remote repository?", default=True):
                        success = self.auto_push_changes(scope_msg)
                        if success:
                            self.console.print("\n[green]🎉 Refactoring and push completed successfully![/green]")
                        else:
                            self.console.print("\n[yellow]⚠️  Refactoring completed, but push failed[/yellow]")
                else:
                    self.console.print("\n[yellow]⚠️  Cannot auto-push: Git configuration incomplete[/yellow]")
                    if not git_status['user_name'] or not git_status['user_email']:
                        self.console.print("Please configure Git user:")
                        self.console.print("  git config user.name 'Your Name'")
                        self.console.print("  git config user.email 'your.email@example.com'")
                    if not git_status['remote_url']:
                        self.console.print("Please add a remote repository:")
                        self.console.print("  git remote add origin <repository-url>")
            
            # Handle failures
            if results.get('failed') > 0 and not results.get('dry_run'):
                self.console.print("\n[yellow]⚠️  Some files failed to refactor[/yellow]")
                
                continue_push = Confirm.ask("Continue with push despite failures?", default=False)
                if not continue_push:
                    self.console.print("[red]❌ Push cancelled by user[/red]")
                    return 1
            
            # Stage refactored files (if not dry run)
            if not results.get('dry_run') and results.get('processed', 0) > 0:
                processed_files = [f for f in files if os.path.exists(f)]  # Files that were actually processed
                self.stage_refactored_files(processed_files)
            
            if results.get('dry_run'):
                self.console.print("\n[blue]🔍 Dry run complete - no files were modified[/blue]")
            else:
                self.console.print("\n[green]🎉 Code refactoring complete! Proceeding with push...[/green]")
            
            return 0
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            return 1
        except Exception as e:
            self.console.print(f"\n[red]❌ Fatal error: {str(e)}[/red]")
            return 1


def main():
    """Main entry point"""
    hook = InteractiveGitHook()
    return hook.run()


if __name__ == "__main__":
    sys.exit(main())
