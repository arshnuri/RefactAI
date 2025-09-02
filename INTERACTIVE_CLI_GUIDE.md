# RefactAI Interactive CLI - User Guide

## 🎯 Overview

The RefactAI CLI has been completely redesigned with an interactive, menu-driven interface that provides a user-friendly experience for code refactoring. No more complex command-line arguments - just run the CLI and navigate through beautiful menus!

## 🚀 Getting Started

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install rich inquirer colorama
```

### Running the Interactive CLI

Simply run:

```bash
python cli.py
```

The interactive interface will start immediately with a beautiful banner and main menu.

## 🎨 Features

### ✨ Beautiful UI
- **Rich Terminal UI**: Colored output, panels, tables, and progress bars
- **Interactive Menus**: Navigate with arrow keys and Enter
- **Live Configuration Display**: See current settings at a glance
- **Progress Indicators**: Spinning wheels and progress bars for long operations

### 🔧 Configuration Management
- **Model Selection**: Choose from popular coding models:
  - DeepSeek Coder 6.7B (Recommended)
  - Qwen2.5 Coder (7B, 3B, 1.5B variants)
  - CodeLlama 7B
  - Mistral 7B
  - Custom models
- **Processing Modes**:
  - 🔀 **Hybrid**: Local LLM with API fallback (recommended)
  - 🏠 **Local**: Local LLM only
  - 🌐 **API**: API only
- **Safety Settings**:
  - Backup creation toggle
  - Dry run mode for previewing changes

### 📁 File Operations
- **Single File Refactoring**: Interactive file selection with path validation
- **Directory Refactoring**: Batch processing with file preview and confirmation
- **Smart File Detection**: Automatically detects and processes supported file types
- **Progress Tracking**: Real-time progress bars for batch operations

## 🎮 Main Menu Options

### 🔄 Refactor a Single File
1. **File Selection**: Enter the path to your file (supports relative and absolute paths)
2. **Validation**: Automatic path validation and file existence checks
3. **Language Detection**: Automatically detects programming language
4. **Processing**: Real-time progress indicator during refactoring
5. **Results**: Clear success/failure feedback with validation warnings

### 📁 Refactor a Directory
1. **Directory Selection**: Choose the directory to process
2. **File Discovery**: Automatic scanning for supported code files
3. **Preview Table**: See all files to be processed with language and size info
4. **Confirmation**: Review and confirm before processing
5. **Batch Processing**: Progress bar showing individual file processing
6. **Summary**: Complete results summary with success/failure counts

### ⚙️ Configure Settings
Interactive configuration with immediate feedback:

#### Model Selection
- **Predefined Options**: Popular coding models with descriptions
- **Custom Models**: Support for any model name
- **Recommendations**: Clear guidance on model selection

#### Processing Mode
- **Hybrid Mode**: Best reliability with local + API fallback
- **Local Only**: Complete offline processing
- **API Only**: Cloud-based processing

#### Safety Options
- **Backup Creation**: Toggle automatic `.backup` file creation
- **Dry Run Mode**: Preview changes without modifying files

### 🧪 Test LLM Connection
- **Connection Testing**: Verify local LLM availability
- **Model Validation**: Test specific model responsiveness
- **Diagnostics**: Detailed error reporting and setup guidance
- **Performance Info**: Connection status and response time

### 📊 View Statistics *(Coming Soon)*
Future features will include:
- Files processed statistics
- Success rate analytics
- Performance metrics
- Language breakdown
- Time saved calculations

### ❓ Help & Documentation
Comprehensive in-app help with:
- Feature explanations
- Usage tips
- Supported languages
- Best practices
- Troubleshooting guidance

## 🎯 Usage Tips

### 🛡️ Safety First
- **Always use backups** when refactoring important code
- **Test with dry run** to preview changes before applying
- **Start small** with single files before processing directories
- **Verify results** after refactoring

### ⚡ Performance Optimization
- **Use faster models** (1.5B variants) for quick iterations
- **Hybrid mode** provides best reliability
- **Local models** for complete offline operation
- **Skip large files** (>100KB are automatically skipped)

### 🎨 Interface Navigation
- **Arrow Keys**: Navigate menu options
- **Enter**: Select option
- **Ctrl+C**: Cancel current operation (with confirmation)
- **Tab**: Auto-complete file paths (in some terminals)

## 🔧 Technical Details

### Supported Languages
- Python 🐍
- JavaScript 📜
- TypeScript 🔷
- Java ☕
- C/C++ ⚡
- C# 🔷

### File Processing Rules
- **Hidden directories**: Automatically skipped (`.git`, `.vscode`, etc.)
- **Build directories**: Skipped (`node_modules`, `__pycache__`, `build`, `dist`)
- **Large files**: Files >100KB are automatically skipped
- **Empty files**: Skipped with warning
- **Binary files**: Automatically detected and skipped

### Error Handling
- **Graceful failures**: Continue processing other files if one fails
- **Detailed error messages**: Clear explanation of what went wrong
- **Recovery options**: Retry prompts for transient errors
- **Safe exit**: Ctrl+C handling with confirmation

### Progress Tracking
- **Spinner animations**: For indeterminate operations
- **Progress bars**: For batch operations with known file counts
- **Status updates**: Real-time feedback on current operation
- **Completion summaries**: Detailed results after operations

## 🆚 Comparison with Old CLI

| Feature | Old CLI | New Interactive CLI |
|---------|---------|-------------------|
| **Interface** | Command arguments | Interactive menus |
| **Configuration** | Command flags | Visual configuration |
| **File Selection** | Manual paths | Interactive prompts with validation |
| **Progress** | Text output | Rich progress bars and spinners |
| **Error Handling** | Basic messages | Detailed panels with recovery options |
| **Help** | `--help` flag | Built-in interactive help system |
| **Safety** | Manual flags | Interactive confirmations |
| **User Experience** | CLI expertise required | Beginner-friendly |

## 🚀 Advanced Usage

### Environment Variables
The CLI respects these environment variables:
- `PREFER_LOCAL_LLM`: Set to 'true' for local-first processing
- `DEFAULT_MODEL`: Default model name
- `OPENROUTER_API_KEY`: API key for fallback processing

### Custom Models
When selecting "Custom model" option, you can specify any model name that your local LLM setup supports.

### Batch Processing Best Practices
1. **Start with dry run** to preview changes
2. **Enable backups** for safety
3. **Process smaller directories** first
4. **Review the file list** before confirming
5. **Monitor progress** and cancel if needed

## 🔄 Migration from Old CLI

The old CLI has been backed up as `cli_old.py`. If you have scripts that use the old command-line interface, you can:

1. **Update scripts** to use the new interactive CLI
2. **Use the old CLI** by running `python cli_old.py` with the old syntax
3. **Create wrapper scripts** that automate the interactive CLI

## 🎉 What's New

✅ **Complete UI Redesign**: Beautiful, modern terminal interface
✅ **Interactive Navigation**: No more memorizing command flags  
✅ **Real-time Feedback**: Progress bars and status updates
✅ **Enhanced Safety**: Interactive confirmations and previews
✅ **Better Error Handling**: Detailed error panels with recovery options
✅ **In-app Help**: Comprehensive documentation without leaving the CLI
✅ **Configuration Management**: Visual settings with immediate feedback
✅ **Batch Processing**: Enhanced directory processing with file preview

---

**Enjoy the new RefactAI Interactive CLI experience!** 🚀
