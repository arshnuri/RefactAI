
# Automatic Syntax Error Fixing

RefactAI now includes automatic syntax error fixing to handle errors introduced during LLM refactoring.

## How It Works

1. **Detection**: When the LLM refactors code, the system validates the output using AST parsing
2. **Error Identification**: If syntax errors are detected, the specific error message is captured
3. **Automatic Correction**: The system sends the broken code back to the LLM with a specialized error correction prompt
4. **Validation**: The corrected code is validated again to ensure the fix was successful
5. **Retry Logic**: If the first attempt fails, the system can retry up to 3 times with updated error information

## Features

- **Intelligent Error Correction**: Uses specialized prompts designed specifically for syntax error fixing
- **Context Preservation**: Provides both the broken code and original code as context for better fixes
- **Multi-Attempt Logic**: Retries with updated error messages if initial fixes don't work
- **Fallback Mechanisms**: Falls back to simpler fix attempts if LLM-based fixing fails
- **Local and API Support**: Works with both local LLM and API-based refactoring

## Configuration

The following settings control automatic syntax error fixing:

```python
# Enable/disable automatic syntax error fixing
AUTO_FIX_SYNTAX_ERRORS = True

# Maximum number of fix attempts per syntax error
MAX_SYNTAX_FIX_ATTEMPTS = 3

# Enable detailed logging of syntax fix attempts
ENABLE_SYNTAX_FIX_LOGGING = True
```

## Error Types Handled

- Unterminated string literals
- Missing parentheses, brackets, or braces
- Incorrect indentation
- Missing colons in function/class definitions
- Missing except/finally blocks in try statements
- Invalid syntax in expressions

## Benefits

1. **Reduced Manual Intervention**: Automatically fixes common LLM-introduced syntax errors
2. **Improved Success Rate**: Higher percentage of successful refactoring operations
3. **Better User Experience**: Users get working code without manual debugging
4. **Consistent Quality**: Ensures refactored code is always syntactically valid

## Monitoring

The system logs all syntax error fixing attempts, including:
- Original error messages
- Fix attempts and results
- Success/failure rates
- Performance metrics

This allows for continuous improvement of the error fixing mechanisms.
