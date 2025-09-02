import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.utils.llm_client import LLMClient

# Test the refactoring functionality
client = LLMClient()
test_code = '''def add(a, b):
    return a + b

print(add(1, 2))'''

print("Testing API connection first...")
api_test = client.test_api_connection()
print(f"API Test Success: {api_test['success']}")

print("\nTesting refactoring functionality...")
# Let's test the raw API response first
system_prompt = client._create_system_prompt('Python')
user_prompt = client._create_user_prompt(test_code, 'Python')
raw_response = client._make_api_request(system_prompt, user_prompt)

print(f"Raw API Response Success: {raw_response['success']}")
if raw_response['success']:
    print("\nRaw response content:")
    print("---")
    print(repr(raw_response['content']))
    print("---")
    
    # Now test the cleaning
    cleaned = client._clean_response(raw_response['content'], 'Python')
    print("\nCleaned response:")
    print("---")
    print(repr(cleaned))
    print("---")
else:
    print(f"API Error: {raw_response.get('error', 'Unknown')}")