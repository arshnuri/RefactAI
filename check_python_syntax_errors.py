#!/usr/bin/env python3
"""
Check for recent Python syntax errors in RefactAI database
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.models import ProcessedFile, RefactorSession

def check_python_syntax_errors():
    print("🔍 Checking for recent Python syntax errors...\n")
    
    # Check recent sessions
    recent_sessions = RefactorSession.objects.order_by('-created_at')[:5]
    print("Recent Refactor Sessions:")
    print("=" * 50)
    for session in recent_sessions:
        print(f"Session {session.id}: {session.processed_files}/{session.total_files} files, Status: {session.status}")
        print(f"  Mode: {session.processing_mode}, Type: {session.refactor_type}")
        if session.error_message:
            print(f"  Error: {session.error_message}")
        print(f"  Created: {session.created_at}")
        print()
    
    # Check Python files with issues
    python_files = ProcessedFile.objects.filter(
        language='python'
    ).order_by('-created_at')[:10]
    
    print("\nRecent Python Files:")
    print("=" * 50)
    for file in python_files:
        print(f"File: {file.original_path}")
        print(f"  Status: {file.status}")
        print(f"  Complexity: {file.complexity_score}")
        print(f"  Readability: {file.readability_score}")
        print(f"  Maintainability: {file.maintainability_score}")
        print(f"  Session: {file.session_id}")
        print(f"  Created: {file.created_at}")
        print()
    
    # Check for files with low scores (potential syntax issues)
    problematic_files = ProcessedFile.objects.filter(
        language='python',
        complexity_score__lt=10
    ).order_by('-created_at')[:5]
    
    if problematic_files:
        print("\nPotentially Problematic Python Files (Low Complexity):")
        print("=" * 60)
        for file in problematic_files:
            print(f"File: {file.original_path}")
            print(f"  All scores: C:{file.complexity_score}, R:{file.readability_score}, M:{file.maintainability_score}")
            print(f"  Status: {file.status}")
            print()
    else:
        print("\n✅ No files with extremely low complexity scores found.")

if __name__ == "__main__":
    check_python_syntax_errors()