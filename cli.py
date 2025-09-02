#!/usr/bin/env python3
"""
Interactive CLI interface for RefactAI local refactoring
Provides a user-friendly menu-driven interface for code refactoring
"""

import sys
import os
import time
import subprocess
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any

# Rich for beautiful terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.align import Align

# Inquirer for interactive prompts
import inquirer
from inquirer.themes import GreenPassion

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure Django settings for CLI usage
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


class InteractiveRefactorCLI:
    """Interactive CLI for RefactAI with rich UI components - OpenRouter API + AST Mode"""
    
    def __init__(self):
        self.console = Console()
        # Force hybrid mode with OpenRouter API + AST validation
        self.config = {
            'model': 'anthropic/claude-3.5-sonnet',  # Default OpenRouter model
            'processing_mode': 'hybrid_openrouter',  # Force OpenRouter + AST
            'create_backup': True,
            'dry_run': False,
            'use_ast_validation': True
        }
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Display the RefactAI banner"""
        banner_text = Text("RefactAI", style="bold cyan")
        banner_text.append(" - AI-Powered Code Refactoring", style="bold white")
        
        banner = Panel(
            Align.center(banner_text),
            style="cyan",
            padding=(1, 2)
        )
        self.console.print(banner)
        self.console.print("")
    
    def show_current_config(self):
        """Display current configuration"""
        config_table = Table(show_header=False, box=None, padding=(0, 2))
        config_table.add_column("Setting", style="cyan", justify="right")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("🤖 Model:", self.config['model'])
        config_table.add_row("⚙️  Mode:", "HYBRID + OPENROUTER + AST")
        config_table.add_row("🌐 API:", "OpenRouter (Required)")
        config_table.add_row("✅ AST Validation:", "Enabled")
        config_table.add_row("💾 Backup:", "Yes" if self.config['create_backup'] else "No")
        config_table.add_row("🔍 Dry Run:", "Yes" if self.config['dry_run'] else "No")
        
        config_panel = Panel(
            config_table,
            title="[bold]Current Configuration[/bold]",
            border_style="blue"
        )
        self.console.print(config_panel)
        self.console.print("")
    
    def main_menu(self) -> str:
        """Display main menu and get user choice"""
        self.clear_screen()
        self.show_banner()
        self.show_current_config()
        
        questions = [
            inquirer.List(
                'action',
                message="What would you like to do?",
                choices=[
                    ('🔄 Refactor a single file', 'refactor_file'),
                    ('📁 Refactor a directory', 'refactor_directory'),
                    ('🚀 Refactor and Push to Git', 'refactor_and_push'),
                    ('⚙️  Configure settings', 'configure'),
                    ('🧪 Test LLM connection', 'test_llm'),
                    ('📊 View refactoring statistics', 'view_stats'),
                    ('❓ Help & Documentation', 'help'),
                    ('🚪 Exit', 'exit')
                ],
                carousel=True
            )
        ]
        
        answers = inquirer.prompt(questions, theme=GreenPassion())
        return answers['action'] if answers else 'exit'
    
    def configure_settings(self):
        """Configure RefactAI settings - OpenRouter focused"""
        self.clear_screen()
        self.show_banner()
        
        # OpenRouter model selection
        model_questions = [
            inquirer.List(
                'model',
                message="Select OpenRouter model:",
                choices=[
                    ('Claude 3.5 Sonnet (Recommended)', 'anthropic/claude-3.5-sonnet'),
                    ('GPT-4 Turbo', 'openai/gpt-4-turbo'),
                    ('GPT-4o', 'openai/gpt-4o'),
                    ('Claude 3 Opus', 'anthropic/claude-3-opus'),
                    ('Gemini Pro 1.5', 'google/gemini-pro-1.5'),
                    ('DeepSeek Coder V2', 'deepseek/deepseek-coder'),
                    ('🔧 Custom model...', 'custom')
                ],
                default=self.config['model']
            )
        ]
        
        model_answer = inquirer.prompt(model_questions, theme=GreenPassion())
        if not model_answer:
            return
            
        if model_answer['model'] == 'custom':
            custom_model = Prompt.ask("Enter custom OpenRouter model name", default=self.config['model'])
            self.config['model'] = custom_model
        else:
            self.config['model'] = model_answer['model']
        
        # Processing is fixed to hybrid + OpenRouter + AST
        self.console.print("\n[yellow]ℹ️  Processing mode is fixed to: Hybrid + OpenRouter + AST[/yellow]")
        
        # Other settings
        other_questions = [
            inquirer.Confirm(
                'backup',
                message="Create backup files?",
                default=self.config['create_backup']
            ),
            inquirer.Confirm(
                'dry_run',
                message="Enable dry run mode (preview only)?",
                default=self.config['dry_run']
            )
        ]
        
        other_answers = inquirer.prompt(other_questions, theme=GreenPassion())
        if other_answers:
            self.config['create_backup'] = other_answers['backup']
            self.config['dry_run'] = other_answers['dry_run']
        
        self.console.print("\n[green]✅ Configuration updated successfully![/green]")
        self.console.input("\nPress Enter to continue...")
    
    def get_file_path(self, mode: str = "file") -> Optional[str]:
        """Get file or directory path from user"""
        if mode == "file":
            prompt_text = "Enter the path to the file you want to refactor"
        else:
            prompt_text = "Enter the path to the directory you want to refactor"
        
        while True:
            path = Prompt.ask(f"\n{prompt_text}")
            
            if not path:
                return None
            
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            if mode == "file" and os.path.isfile(path):
                return path
            elif mode == "directory" and os.path.isdir(path):
                return path
            else:
                error_msg = f"❌ {'File' if mode == 'file' else 'Directory'} not found: {path}"
                self.console.print(f"[red]{error_msg}[/red]")
                
                if not Confirm.ask("Would you like to try again?", default=True):
                    return None
    
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
                '.cs': 'C#',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.go': 'Go',
                '.rs': 'Rust',
                '.swift': 'Swift',
                '.kt': 'Kotlin'
            }
            return ext_map.get(ext, 'Unknown')
    
    def is_supported_language(self, language: str) -> bool:
        """Check if the language is supported for refactoring"""
        supported = ['Python', 'JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'C#']
        return language in supported
    
    def backup_file(self, file_path: str) -> str:
        """Create a backup of the original file"""
        backup_path = f"{file_path}.backup"
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        return backup_path
    
    def validate_refactored_code(self, original_code: str, refactored_code: str, language: str) -> List[str]:
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
    
    def refactor_single_file(self, file_path: str) -> bool:
        """Refactor a single file with progress display"""
        if not os.path.exists(file_path):
            self.console.print(f"[red]❌ Error: File not found: {file_path}[/red]")
            return False
        
        # Detect language
        language = self.detect_language_from_file(file_path)
        if not self.is_supported_language(language):
            self.console.print(f"[yellow]⚠️  Skipping {file_path}: {language} is not supported[/yellow]")
            return True
        
        self.console.print(f"\n[cyan]🔄 Refactoring {os.path.basename(file_path)} ({language})...[/cyan]")
        
        try:
            # Read original code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Skip empty files
            if not original_code.strip():
                self.console.print(f"[yellow]⚠️  Skipping {file_path}: File is empty[/yellow]")
                return True
            
            # Skip very large files (>100KB)
            if len(original_code) > 100000:
                self.console.print(f"[yellow]⚠️  Skipping {file_path}: File too large (>100KB)[/yellow]")
                return True
            
            # Show progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                
                # Force hybrid mode with OpenRouter API + AST validation
                progress.update(task, description="Initializing OpenRouter API client...")
                client = LLMClient(use_hybrid_approach=True, use_local_llm=False)  # Force API usage
                
                progress.update(task, description="Running OpenRouter refactoring...")
                
                # Always use OpenRouter API refactoring
                result = client.refactor_code(
                    code=original_code,
                    language=language.lower(),
                    file_path=file_path,
                    session_id=f'cli_{os.path.basename(file_path)}'
                )
                
                progress.update(task, description="Validating with AST...")
            
            if not result['success']:
                self.console.print(f"[red]❌ Failed to refactor {file_path}: {result['error']}[/red]")
                return False
            
            refactored_code = result['refactored_code']
            
            # Enhanced AST validation
            warnings = self.validate_refactored_code(original_code, refactored_code, language)
            if warnings:
                self.console.print(f"[yellow]⚠️  Validation warnings for {file_path}:[/yellow]")
                for warning in warnings:
                    self.console.print(f"   [yellow]- {warning}[/yellow]")
            
            # Show diff in dry run mode
            if self.config['dry_run']:
                self.console.print(f"\n[blue]📋 Dry run preview for {file_path}:[/blue]")
                preview_panel = Panel(
                    refactored_code[:1000] + ("..." if len(refactored_code) > 1000 else ""),
                    title="Refactored Code Preview",
                    border_style="blue",
                    expand=False
                )
                self.console.print(preview_panel)
                return True
            
            # Create backup if requested
            if self.config['create_backup']:
                backup_path = self.backup_file(file_path)
                self.console.print(f"[blue]💾 Backup created: {backup_path}[/blue]")
            
            # Write refactored code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
            
            self.console.print(f"[green]✅ Successfully refactored {file_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error refactoring {file_path}: {str(e)}[/red]")
            return False
    
    def refactor_directory_interactive(self, directory: str) -> bool:
        """Refactor all supported files in a directory with interactive options"""
        if not os.path.isdir(directory):
            self.console.print(f"[red]❌ Error: Directory not found: {directory}[/red]")
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
            self.console.print(f"[yellow]⚠️  No supported code files found in {directory}[/yellow]")
            return True
        
        self.console.print(f"\n[cyan]🔍 Found {len(code_files)} code files to refactor[/cyan]")
        
        # Show files and ask for confirmation
        files_table = Table(title="Files to Refactor", show_header=True, header_style="bold magenta")
        files_table.add_column("File", style="cyan", justify="left")
        files_table.add_column("Language", style="green", justify="center")
        files_table.add_column("Size", style="yellow", justify="right")
        
        for file_path in code_files[:10]:  # Show first 10 files
            language = self.detect_language_from_file(file_path)
            size = os.path.getsize(file_path)
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f}KB"
            files_table.add_row(os.path.relpath(file_path, directory), language, size_str)
        
        if len(code_files) > 10:
            files_table.add_row("...", f"and {len(code_files) - 10} more files", "")
        
        self.console.print(files_table)
        
        if not Confirm.ask(f"\nProceed with refactoring {len(code_files)} files?"):
            return False
        
        # Process files with progress bar
        success_count = 0
        with Progress(console=self.console) as progress:
            task = progress.add_task("Refactoring files...", total=len(code_files))
            
            for file_path in code_files:
                progress.update(task, description=f"Processing {os.path.basename(file_path)}...")
                if self.refactor_single_file(file_path):
                    success_count += 1
                progress.advance(task)
        
        # Show results
        if success_count == len(code_files):
            self.console.print(f"\n[green]🎉 All files refactored successfully![/green]")
        else:
            self.console.print(f"\n[yellow]📊 Refactoring complete: {success_count}/{len(code_files)} files processed successfully[/yellow]")
        
        return success_count == len(code_files)
    
    def test_llm_connection(self):
        """Test LLM connection with detailed feedback"""
        self.clear_screen()
        self.show_banner()
        
        self.console.print("[cyan]🧪 Testing Local LLM Connection...[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Connecting to LLM...", total=None)
            
            client = LocalLLMClient(model_name=self.config['model'])
            test_result = client.test_connection()
            
            progress.update(task, description="Testing complete")
        
        if test_result['available']:
            success_panel = Panel(
                f"✅ Local LLM ({self.config['model']}) is available and working!\n\n"
                f"🔗 Connection: Successful\n"
                f"🤖 Model: {self.config['model']}\n"
                f"⚡ Response Time: Fast",
                title="[green]Connection Test Successful[/green]",
                border_style="green"
            )
            self.console.print(success_panel)
        else:
            error_panel = Panel(
                f"❌ Local LLM not available: {test_result['error']}\n\n"
                f"Please install one of the following:\n"
                f"• Ollama: https://ollama.ai/\n"
                f"• LM Studio: https://lmstudio.ai/\n"
                f"• llama.cpp: https://github.com/ggerganov/llama.cpp",
                title="[red]Connection Test Failed[/red]",
                border_style="red"
            )
            self.console.print(error_panel)
        
        self.console.input("\nPress Enter to continue...")
    
    def refactor_and_push_to_git(self):
        """Refactor files and push to Git repository"""
        self.clear_screen()
        self.show_banner()
        
        # Check if we're in a Git repository
        try:
            result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode != 0:
                self.console.print("[red]❌ Not in a Git repository or Git not available[/red]")
                return
        except Exception as e:
            self.console.print(f"[red]❌ Git command failed: {str(e)}[/red]")
            return
        
        self.console.print("[bold cyan]🚀 Refactor and Push to Git[/bold cyan]\n")
        
        # Step 1: Ask what files to process
        file_selection_method = inquirer.prompt([
            inquirer.List(
                'method',
                message="How would you like to select files to refactor?",
                choices=[
                    ('📁 All modified files (git status)', 'modified'),
                    ('🎯 Specific files by pattern', 'pattern'),
                    ('📝 Manual file selection', 'manual'),
                    ('🔙 Cancel', 'cancel')
                ]
            )
        ])
        
        if not file_selection_method or file_selection_method['method'] == 'cancel':
            return
        
        files_to_process = []
        method = file_selection_method['method']
        
        if method == 'modified':
            # Get modified files from git status
            try:
                result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=os.getcwd())
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            # Parse git status output (format: XY filename)
                            file_path = line[3:].strip()
                            if os.path.exists(file_path) and self.is_supported_file(file_path):
                                files_to_process.append(file_path)
                
                if not files_to_process:
                    self.console.print("[yellow]⚠️  No modified supported code files found[/yellow]")
                    return
                    
            except Exception as e:
                self.console.print(f"[red]❌ Failed to get modified files: {str(e)}[/red]")
                return
                
        elif method == 'pattern':
            # Ask for file pattern
            pattern = Prompt.ask("Enter file pattern (e.g., *.py, src/**/*.js, test_*.py)")
            if not pattern:
                return
                
            try:
                files_to_process = glob.glob(pattern, recursive=True)
                files_to_process = [f for f in files_to_process if os.path.isfile(f) and self.is_supported_file(f)]
                
                if not files_to_process:
                    self.console.print(f"[yellow]⚠️  No files found matching pattern: {pattern}[/yellow]")
                    return
                    
            except Exception as e:
                self.console.print(f"[red]❌ Invalid pattern: {str(e)}[/red]")
                return
                
        elif method == 'manual':
            # Ask for individual files
            files_input = Prompt.ask("Enter file paths (comma separated)")
            if not files_input:
                return
                
            files_to_process = [f.strip() for f in files_input.split(',')]
            files_to_process = [f for f in files_to_process if os.path.exists(f) and self.is_supported_file(f)]
            
            if not files_to_process:
                self.console.print("[yellow]⚠️  No valid files specified[/yellow]")
                return
        
        # Show files to be processed
        self.console.print(f"\n[bold]Files to refactor ({len(files_to_process)}):[/bold]")
        for i, file_path in enumerate(files_to_process, 1):
            self.console.print(f"  {i}. [cyan]{file_path}[/cyan]")
        
        if not Confirm.ask(f"\nProceed with refactoring {len(files_to_process)} file(s)?", default=True):
            return
        
        # Step 2: Refactor the files
        self.console.print("\n[bold]🔄 Starting refactoring process...[/bold]")
        
        refactored_files = []
        failed_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Refactoring files...", total=len(files_to_process))
            
            for file_path in files_to_process:
                progress.update(task, description=f"Processing {file_path}...")
                
                # Use the existing refactor method but capture result
                original_method = self.refactor_single_file
                result = self.refactor_file_internal(file_path)
                
                if result['success']:
                    refactored_files.append(file_path)
                    self.console.print(f"  ✅ [green]{file_path}[/green]")
                else:
                    failed_files.append((file_path, result.get('error', 'Unknown error')))
                    self.console.print(f"  ❌ [red]{file_path}[/red]: {result.get('error', 'Unknown error')}")
                
                progress.advance(task)
        
        # Step 3: Show results
        self.console.print(f"\n[bold]📊 Refactoring Results:[/bold]")
        self.console.print(f"  ✅ Successfully refactored: {len(refactored_files)}")
        self.console.print(f"  ❌ Failed: {len(failed_files)}")
        
        if not refactored_files:
            self.console.print("[yellow]⚠️  No files were successfully refactored. Nothing to commit.[/yellow]")
            return
        
        # Step 4: Git operations
        if not Confirm.ask(f"\nProceed with Git operations for {len(refactored_files)} refactored file(s)?", default=True):
            return
        
        # Ask for commit message
        commit_message = Prompt.ask("Enter commit message", default=f"Refactor {len(refactored_files)} file(s) using RefactAI")
        
        # Ask about remote and branch
        branch_info = inquirer.prompt([
            inquirer.Text('remote', message="Remote name", default='origin'),
            inquirer.Text('branch', message="Branch name", default='master')
        ])
        
        if not branch_info:
            return
        
        remote = branch_info['remote']
        branch = branch_info['branch']
        
        # Execute Git commands
        self.console.print("\n[bold]🔧 Executing Git commands...[/bold]")
        
        try:
            # Git add
            self.console.print("  📝 Adding files to staging area...")
            for file_path in refactored_files:
                result = subprocess.run(['git', 'add', file_path], capture_output=True, text=True, cwd=os.getcwd())
                if result.returncode != 0:
                    self.console.print(f"    ❌ Failed to add {file_path}: {result.stderr}")
                    return
                self.console.print(f"    ✅ Added {file_path}")
            
            # Git commit
            self.console.print(f"  💾 Committing with message: '{commit_message}'...")
            result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode != 0:
                self.console.print(f"    ❌ Commit failed: {result.stderr}")
                return
            self.console.print("    ✅ Commit successful")
            
            # Git push
            if Confirm.ask(f"Push to {remote}/{branch}?", default=True):
                self.console.print(f"  🚀 Pushing to {remote}/{branch}...")
                result = subprocess.run(['git', 'push', remote, branch], capture_output=True, text=True, cwd=os.getcwd())
                if result.returncode != 0:
                    self.console.print(f"    ❌ Push failed: {result.stderr}")
                    return
                self.console.print("    ✅ Push successful")
                
                self.console.print(f"\n[bold green]🎉 Successfully refactored and pushed {len(refactored_files)} file(s)![/bold green]")
            else:
                self.console.print(f"\n[bold yellow]📝 Files committed locally. Push manually when ready.[/bold yellow]")
                
        except Exception as e:
            self.console.print(f"[red]❌ Git operation failed: {str(e)}[/red]")
    
    def refactor_file_internal(self, file_path: str) -> Dict[str, Any]:
        """Internal method to refactor a single file and return result"""
        try:
            # Read original code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Skip empty files
            if not original_code.strip():
                return {
                    'success': False,
                    'error': 'File is empty'
                }
            
            # Detect language
            language = self.detect_language_from_file(file_path)
            if not self.is_supported_language(language):
                return {
                    'success': False,
                    'error': f'{language} is not supported'
                }
            
            # Use the same LLM client as the main CLI
            from refactai_app.utils.llm_client import LLMClient
            
            client = LLMClient(use_hybrid_approach=True, use_local_llm=False)  # Force API usage
            
            # Always use OpenRouter API refactoring
            result = client.refactor_code(
                code=original_code,
                language=language.lower(),
                file_path=file_path,
                session_id=f'git_cli_{os.path.basename(file_path)}'
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': result['error']
                }
            
            refactored_code = result['refactored_code']
            
            # Write refactored code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
            
            return {
                'success': True,
                'refactored_code': refactored_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file is supported for refactoring"""
        supported_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.php'}
        return Path(file_path).suffix.lower() in supported_extensions
    
    def show_help(self):
        """Display help and documentation"""
        self.clear_screen()
        self.show_banner()
        
        help_content = """
[bold cyan]RefactAI Interactive CLI Help[/bold cyan]

[bold]🔄 Refactor a single file:[/bold]
• Select a file from your filesystem
• Choose processing mode (hybrid/local/api)
• Preview changes with dry run mode
• Automatic backup creation

[bold]📁 Refactor a directory:[/bold]
• Process all supported code files
• Skip hidden and build directories
• Progress tracking with file count
• Batch processing with individual results

[bold]⚙️ Configuration Options:[/bold]
• Model Selection: Choose from various LLM models
• Processing Mode: Hybrid, local-only, or API-only
• Backup: Enable/disable automatic backups
• Dry Run: Preview changes without modifying files

[bold]🧪 Test LLM Connection:[/bold]
• Verify local LLM availability
• Test model responsiveness
• Connection diagnostics

[bold]📊 Supported Languages:[/bold]
• Python, JavaScript, TypeScript
• Java, C, C++, C#
• And more coming soon!

[bold]🎯 Tips:[/bold]
• Use dry run mode to preview changes
• Keep backups enabled for safety
• Hybrid mode provides best reliability
• Large files (>100KB) are automatically skipped
        """
        
        help_panel = Panel(
            help_content,
            title="[bold]Help & Documentation[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(help_panel)
        self.console.input("\nPress Enter to continue...")
    
    def show_stats(self):
        """Display refactoring statistics (placeholder)"""
        self.clear_screen()
        self.show_banner()
        
        stats_content = """
[bold cyan]Refactoring Statistics[/bold cyan]

[yellow]📊 This feature is coming soon![/yellow]

Future statistics will include:
• Files processed today/this week
• Success rate and error analysis
• Performance metrics
• Language breakdown
• Time saved through refactoring
        """
        
        stats_panel = Panel(
            stats_content,
            title="[bold]Statistics Dashboard[/bold]",
            border_style="yellow",
            padding=(1, 2)
        )
        self.console.print(stats_panel)
        self.console.input("\nPress Enter to continue...")
    
    def run(self):
        """Main application loop"""
        while True:
            try:
                action = self.main_menu()
                
                if action == 'exit':
                    self.console.print("\n[cyan]👋 Thank you for using RefactAI! Goodbye![/cyan]")
                    break
                elif action == 'refactor_file':
                    file_path = self.get_file_path("file")
                    if file_path:
                        self.refactor_single_file(file_path)
                        self.console.input("\nPress Enter to continue...")
                elif action == 'refactor_directory':
                    dir_path = self.get_file_path("directory")
                    if dir_path:
                        self.refactor_directory_interactive(dir_path)
                        self.console.input("\nPress Enter to continue...")
                elif action == 'refactor_and_push':
                    self.refactor_and_push_to_git()
                    self.console.input("\nPress Enter to continue...")
                elif action == 'configure':
                    self.configure_settings()
                elif action == 'test_llm':
                    self.test_llm_connection()
                elif action == 'view_stats':
                    self.show_stats()
                elif action == 'help':
                    self.show_help()
                    
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]⚠️  Operation cancelled by user[/yellow]")
                if Confirm.ask("Do you want to exit RefactAI?", default=False):
                    break
            except Exception as e:
                self.console.print(f"\n[red]❌ An unexpected error occurred: {str(e)}[/red]")
                self.console.input("Press Enter to continue...")


def main():
    """Main entry point"""
    try:
        app = InteractiveRefactorCLI()
        app.run()
        return 0
    except Exception as e:
        console = Console()
        console.print(f"[red]❌ Fatal error: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
