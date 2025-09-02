import requests
import json

# Test the exact same approach as the PowerShell script
headers = {
    'Content-Type': 'application/json'
}

system_prompt = """You are an expert code refactoring engine.

Your job is to take code written in any language and return only the refactored version. Follow these rules strictly:

1. Do not explain anything. Do not use any comments or markdown.
2. Keep the original structure and language.
3. Only refactor: improve naming, simplify logic, remove duplication, add typing (if language supports it), and make code modern and clean.
4. NEVER output text like "Here is the refactored code:" — only output the code.

Your output must be clean, minimal, and production-ready."""

input_code = """def add(a, b):
    return a + b

print(add(1, 2))"""

body = {
    'model': 'deepseek-coder',
    'messages': [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': input_code}
    ]
}

try:
    response = requests.post(
        'http://45.79.125.152:8000/v1/chat/completions',
        headers=headers,
        json=body,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        refactored_code = data['choices'][0]['message']['content']
        print("✅ Refactored Code:")
        print(refactored_code)
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Exception: {e}")