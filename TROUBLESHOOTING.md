# Troubleshooting Common CLI Issues

## AST Validation Error
If you encounter the following error when refactoring files:
```
❌ Error refactoring <file_path>: 'InteractiveRefactorCLI' object has no attribute 'validate_refactored_code_with_ast'
```

This issue has been fixed in the latest version. Run the following fix script:
```bash
python D:\RefactAI\fix_cli_validation.py
```

This script updates the CLI code to use the correct validation method name.

## AST Validator Syntax Error
If you encounter a warning about AST validation:
```
Validation error: 'ASTValidator' object has no attribute 'validate_syntax'
```

Run the following fix script:
```bash
python D:\RefactAI\fix_ast_validator.py
```

This script adds the missing `validate_syntax` method to the `ASTValidator` class.

## Other Common Issues

### "LLMClient" errors
If you encounter errors related to the LLMClient:
1. Check that your API key is set correctly in the `.env` file
2. Verify your internet connection
3. Make sure you have the latest version of the RefactAI code

### File Path Issues
When refactoring files from different drives:
1. Always use absolute paths
2. Ensure the paths are correctly formatted for Windows (e.g., `D:\project\file.py`)
3. Make sure the files exist and are readable

### Git Integration Issues
If you encounter issues with Git integration:
1. Ensure Git is installed and configured on your system
2. Check that your repository is properly set up with remotes
3. Verify you have the necessary permissions to push to the repository
