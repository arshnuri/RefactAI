#!/usr/bin/env python3
"""
Local LLM interface for RefactAI
Handles communication with local LLM models for code refactoring
"""

import subprocess
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class LocalLLMClient:
    """Client for interfacing with local LLM models"""
    
    def __init__(self, model_name: str = "deepseek-coder:6.7b", temperature: float = 0.2):
        self.model_name = model_name
        self.temperature = temperature
        self.prompt_path = Path(__file__).parent / "prompt.txt"
        
    def load_prompt(self) -> str:
        """Load the system prompt from prompt.txt"""
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise RuntimeError(f"Prompt file not found: {self.prompt_path}")
    
    def run_llm_refactor(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Run local LLM to refactor code"""
        try:
            prompt = self.load_prompt()
            input_text = f"{prompt}\n\nLanguage: {language}\n\n```{language}\n{code}\n```"
            
            # Try different local LLM runners in order of preference
            runners = [
                self._try_ollama,
                self._try_lmstudio,
                self._try_llamacpp,
                self._try_generic_llm
            ]
            

            
            for runner in runners:
                result = runner(input_text)
                if result:
                    return {
                        'success': True,
                        'refactored_code': self._clean_response(result),
                        'error': None,
                        'validation_warnings': []
                    }
            
            return {
                'success': False,
                'refactored_code': code,  # Return original on failure
                'error': 'No local LLM runner available. Please install Ollama, LM Studio, or llama.cpp',
                'validation_warnings': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'refactored_code': code,  # Return original on error
                'error': f"Local LLM error: {str(e)}",
                'validation_warnings': []
            }
    
    def _try_ollama(self, input_text: str) -> Optional[str]:
        """Try using Ollama for local LLM"""
        # Try different model names in order of preference
        models_to_try = [
            self.model_name,
            "qwen2.5-coder:7b",
            "qwen2.5-coder:1.5b",
            "qwen2.5-coder:3b",
            "qwen2-coder:7b",
            "deepseek-coder:6.7b",
            "codellama:7b", 
            "mistral:7b"
        ]
        
        for model in models_to_try:
            try:
                result = subprocess.run(
                    ["ollama", "run", model],
                    input=input_text,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        return None
    
    def _try_lmstudio(self, input_text: str) -> Optional[str]:
        """Try using LM Studio CLI for local LLM"""
        try:
            # LM Studio typically runs on localhost:1234
            import requests
            
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": input_text}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 4000
                },
                timeout=300
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except (ImportError, Exception):
            pass
        return None
    
    def _try_llamacpp(self, input_text: str) -> Optional[str]:
        """Try using llama.cpp for local LLM"""
        try:
            # Look for common llama.cpp executables
            executables = ["llama-cli", "main", "llama.cpp"]
            
            for exe in executables:
                try:
                    result = subprocess.run(
                        [exe, "-m", self.model_name, "-p", input_text, "-n", "4000", "--temp", str(self.temperature)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        return result.stdout.strip()
                except FileNotFoundError:
                    continue
        except Exception:
            pass
        return None
    
    def _try_generic_llm(self, input_text: str) -> Optional[str]:
        """Try using generic 'llm' command"""
        try:
            result = subprocess.run(
                ["llm", "--model", self.model_name, "--temperature", str(self.temperature)],
                input=input_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        return None
    
    def fix_syntax_errors(self, broken_code: str, error_msg: str, original_code: str, max_attempts: int = 2) -> str:
        """Fix syntax errors using local LLM"""
        current_code = broken_code
        
        for attempt in range(max_attempts):
            try:
                # Create error correction prompt with stricter instructions
                prompt = f"""You are a Python syntax error fixer. Fix ONLY the syntax error, do not add explanations or comments.

BROKEN CODE:
```python
{current_code}
```

ERROR: {error_msg}

Output the corrected Python code only, no explanations:
```python"""
                
                # Try different local LLM runners
                runners = [self._try_ollama, self._try_lmstudio, self._try_llamacpp]
                
                for runner in runners:
                    result = runner(prompt)
                    if result:
                        corrected_code = self._clean_syntax_fix_response(result)
                        # Validate the corrected code is actually different and valid
                        if corrected_code != current_code and len(corrected_code.strip()) > 0:
                            # Basic syntax check - should have similar structure
                            if self._is_reasonable_fix(corrected_code, current_code):
                                return corrected_code
                        break
                
                # If no runner worked, break
                break
                
            except Exception:
                break
        
        # Return original broken code if fixing fails
        return broken_code
    
    def _clean_syntax_fix_response(self, response: str) -> str:
        """Clean LLM response specifically for syntax error fixes"""
        # Remove everything before and after code blocks
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```python') or line.strip().startswith('```'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                break
            elif in_code_block:
                code_lines.append(line)
            elif not in_code_block and line.strip() and not any(line.strip().startswith(prefix) for prefix in ['Here', 'The', 'I', 'This', 'Fixed', 'Corrected', '#']):
                # If no code block markers, try to extract code-like lines
                if ('def ' in line or 'import ' in line or 'print(' in line or 'return ' in line or line.strip().startswith('    ')):
                    code_lines.append(line)
        
        if code_lines:
            result = '\n'.join(code_lines).strip()
            # Remove any trailing comments or explanations
            result_lines = result.split('\n')
            clean_lines = []
            for line in result_lines:
                # Remove lines that are clearly comments or explanations
                if line.strip().startswith('#') and ('Fixed' in line or 'Calling' in line or 'because' in line):
                    continue
                clean_lines.append(line)
            return '\n'.join(clean_lines).strip()
        
        # Fallback: return original response cleaned
        return response.strip()
    
    def _is_reasonable_fix(self, fixed_code: str, original_code: str) -> bool:
        """Check if the fixed code is a reasonable fix (similar length, structure)"""
        # Should not be dramatically longer (avoid verbose explanations)
        if len(fixed_code) > len(original_code) * 3:
            return False
        
        # Should contain similar keywords
        original_keywords = set(['def', 'return', 'print', 'if', 'for', 'while', 'import'])
        fixed_has_keywords = any(keyword in fixed_code for keyword in original_keywords if keyword in original_code)
        
        return fixed_has_keywords
    
    def _clean_response(self, response: str) -> str:
        """Clean the LLM response to extract only the code"""
        # Remove markdown code blocks if present
        lines = response.split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block or not any(line.strip().startswith(prefix) for prefix in ['Here', 'The', 'I', 'This']):
                cleaned_lines.append(line)
        
        # If we found code blocks, return the cleaned content
        if any('```' in response for response in [response]):
            return '\n'.join(cleaned_lines).strip()
        
        # Otherwise, return the response as-is
        return response.strip()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test if local LLM is available"""
        test_code = "print('hello world')"
        result = self.run_llm_refactor(test_code, "python")
        return {
            'available': result['success'],
            'error': result['error'] if not result['success'] else None
        }


def refactor_code(code: str, language: str = "python", model: str = "qwen2.5-coder:7b") -> Dict[str, Any]:
    """Main function to refactor code using local LLM"""
    client = LocalLLMClient(model_name=model)
    return client.run_llm_refactor(code, language)


if __name__ == "__main__":
    # Test the local LLM client
    client = LocalLLMClient()
    test_result = client.test_connection()
    
    if test_result['available']:
        print("✅ Local LLM is available and working!")
    else:
        print(f"❌ Local LLM not available: {test_result['error']}")
        print("\nPlease install one of the following:")
        print("- Ollama: https://ollama.ai/")
        print("- LM Studio: https://lmstudio.ai/")
        print("- llama.cpp: https://github.com/ggerganov/llama.cpp")