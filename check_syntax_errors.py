#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.models import ProcessedFile

# Query for files with syntax errors
files_with_syntax_errors = ProcessedFile.objects.filter(
    error_message__icontains='syntax'
)

print(f"Found {files_with_syntax_errors.count()} files with syntax errors:")
print("=" * 60)

for file in files_with_syntax_errors[:10]:  # Show first 10
    print(f"File: {file.original_path}")
    print(f"Language: {file.language}")
    print(f"Status: {file.status}")
    print(f"Error: {file.error_message[:300]}...")
    print("-" * 40)

# Also check for files with line number errors
files_with_line_errors = ProcessedFile.objects.filter(
    error_message__icontains='line'
)

print(f"\nFound {files_with_line_errors.count()} files with line-related errors:")
print("=" * 60)

for file in files_with_line_errors[:5]:  # Show first 5
    print(f"File: {file.original_path}")
    print(f"Error: {file.error_message[:300]}...")
    print("-" * 40)