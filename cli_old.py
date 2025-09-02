#!/usr/bin/env python3
"""
Interactive CLI interface for RefactAI local refactoring
Provides a user-friendly menu-driven interface for code refactoring
"""

import sys
import os
import time
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
        SECRET_KEY=os.getenv('DJANGO_SECRET_KEY', 'old-cli-dev-key-change-in-production'),
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
    """Interactive CLI for RefactAI with rich UI components"""
    
    def __init__(self):
        self.console = Console()
        self.config = {
            'model': 'deepseek-coder:6.7b',
            'processing_mode': 'hybrid',
            'create_backup': True,
            'dry_run': False
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
        config_table.add_row("⚙️  Mode:", self.config['processing_mode'].upper())
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
        """Configure RefactAI settings"""
        self.clear_screen()
        self.show_banner()
        
        # Model selection
        model_questions = [
            inquirer.List(
                'model',
                message="Select LLM model:",
                choices=[
                    ('DeepSeek Coder 6.7B (Recommended)', 'deepseek-coder:6.7b'),
                    ('Qwen2.5 Coder 7B', 'qwen2.5-coder:7b'),
                    ('Qwen2.5 Coder 3B (Faster)', 'qwen2.5-coder:3b'),
                    ('Qwen2.5 Coder 1.5B (Fastest)', 'qwen2.5-coder:1.5b'),
                    ('CodeLlama 7B', 'codellama:7b'),
                    ('Mistral 7B', 'mistral:7b'),
                    ('🔧 Custom model...', 'custom')
                ],
                default=self.config['model']
            )
        ]
        
        model_answer = inquirer.prompt(model_questions, theme=GreenPassion())
        if not model_answer:
            return
            
        if model_answer['model'] == 'custom':
            custom_model = Prompt.ask("Enter custom model name", default=self.config['model'])
            self.config['model'] = custom_model
        else:
            self.config['model'] = model_answer['model']
        
        # Processing mode selection
        mode_questions = [
            inquirer.List(
                'mode',
                message="Select processing mode:",
                choices=[
                    ('🔀 Hybrid (Local + API fallback)', 'hybrid'),
                    ('🏠 Local LLM only', 'local'),
                    ('🌐 API only', 'api')
                ],
                default=self.config['processing_mode']
            )
        ]
        
        mode_answer = inquirer.prompt(mode_questions, theme=GreenPassion())
        if mode_answer:
            self.config['processing_mode'] = mode_answer['mode']
        
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
        
        self.console.print(f"[cyan]🔄 Refactoring {os.path.basename(file_path)} ({language})...[/cyan]")
        
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
                
                # Initialize LLM client based on processing mode
                if self.config['processing_mode'] == "hybrid":
                    client = LLMClient(use_hybrid_approach=True, use_local_llm=True)
                elif self.config['processing_mode'] == "local":
                    client = LocalLLMClient(model_name=self.config['model'])
                elif self.config['processing_mode'] == "api":
                    client = LLMClient(use_hybrid_approach=False, use_local_llm=False)
                else:
                    # Default to hybrid
                    client = LLMClient(use_hybrid_approach=True, use_local_llm=True)
                
                progress.update(task, description="Running refactoring...")
                
                # Use appropriate method based on client type
                if self.config['processing_mode'] == "local":
                    result = client.run_llm_refactor(original_code, language.lower())
                else:
                    result = client.refactor_code(
                        code=original_code,
                        language=language.lower(),
                        file_path=file_path,
                        session_id=f'cli_{os.path.basename(file_path)}'
                    )
                
                progress.update(task, description="Validating results...")
            
            if not result['success']:
                self.console.print(f"[red]❌ Failed to refactor {file_path}: {result['error']}[/red]")
                return False
            
            refactored_code = result['refactored_code']
            
            # Validate refactored code
            warnings = self.validate_refactored_code(original_code, refactored_code, language)
            if warnings:
                self.console.print(f"[yellow]⚠️  Validation warnings for {file_path}:[/yellow]")
                for warning in warnings:
                    self.console.print(f"   [yellow]- {warning}[/yellow]")
            
            # Show diff in dry run mode
            if self.config['dry_run']:
                self.console.print(f"[blue]📋 Dry run preview for {file_path}:[/blue]")
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


def refactor_directory(directory: str, model: str = "deepseek-coder:6.7b", 
                      create_backup: bool = True, dry_run: bool = False, 
                      processing_mode: str = "hybrid") -> bool:
    """Refactor all supported files in a directory"""
    if not os.path.isdir(directory):
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
        print(f"⚠️  No supported code files found in {directory}")
        return True
    
    print(f"🔍 Found {len(code_files)} code files to refactor")
        
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