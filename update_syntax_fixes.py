#!/usr/bin/env python3
"""
Script to update ProcessedFile records and mark syntax errors as resolved
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai.settings')
django.setup()

from refactai_app.models import ProcessedFile

def update_syntax_fixes():
    """
    Update ProcessedFile records to mark syntax errors as resolved
    """
    print("Updating syntax error records...")
    
    # Files that we've confirmed are now syntax-error-free
    fixed_files = [
        'foresight chain/api_server.py',
        'foresight chain/enhanced_app.py'
    ]
    
    updated_count = 0
    
    for file_path in fixed_files:
        # Find records with syntax errors for this file
        records = ProcessedFile.objects.filter(
            file_path__icontains=file_path,
            error_message__icontains='syntax'
        )
        
        for record in records:
            print(f"Updating record for {record.file_path}")
            print(f"  Old error: {record.error_message}")
            
            # Update the error message to indicate it's been fixed
            record.error_message = record.error_message.replace(
                'Syntax error', 'Syntax error (FIXED)'
            )
            record.save()
            updated_count += 1
            
            print(f"  New error: {record.error_message}")
            print("  ✅ Updated")
            print()
    
    print(f"Updated {updated_count} records")
    
    # Also check for any remaining syntax errors
    remaining_syntax_errors = ProcessedFile.objects.filter(
        error_message__icontains='syntax'
    ).exclude(
        error_message__icontains='FIXED'
    )
    
    print(f"\nRemaining syntax errors: {remaining_syntax_errors.count()}")
    
    if remaining_syntax_errors.count() > 0:
        print("\nRemaining syntax error files:")
        for record in remaining_syntax_errors[:10]:  # Show first 10
            print(f"  - {record.file_path}: {record.error_message[:100]}...")

if __name__ == '__main__':
    update_syntax_fixes()