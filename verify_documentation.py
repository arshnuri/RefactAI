#!/usr/bin/env python3
"""
Test script to verify the updated documentation page
"""

import os
import sys

def verify_documentation_updates():
    """
    Verify that the documentation has been updated with new features
    """
    print("🔄 Verifying documentation updates...")
    
    doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'refactai_app', 'templates', 'refactai_app', 'documentation.html')
    
    if not os.path.exists(doc_path):
        print("❌ Documentation file not found")
        return False
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for new features
    new_features = [
        "Refactor and Push to Git",
        "Cross-Drive Support", 
        "Unicode Fixes",
        "OpenRouter Integration",
        "Interactive CLI Mode",
        "fix_cli_validation.py",
        "fix_ast_validator.py"
    ]
    
    print("✅ Documentation file found")
    print("\n🔍 Checking for new feature documentation:")
    
    all_found = True
    for feature in new_features:
        if feature in content:
            print(f"   ✅ {feature}")
        else:
            print(f"   ❌ {feature} - not found")
            all_found = False
    
    print(f"\n📊 Documentation Status:")
    print(f"   • File size: {len(content):,} characters")
    print(f"   • New features documented: {sum(1 for f in new_features if f in content)}/{len(new_features)}")
    
    if all_found:
        print("\n🎉 All new features are documented!")
    else:
        print("\n⚠️  Some features may need additional documentation")
    
    print("\n📝 Updated sections include:")
    print("   • What's New summary")
    print("   • Interactive CLI mode")
    print("   • Refactor and Push to Git feature")
    print("   • Enhanced Git Hook setup")
    print("   • OpenRouter API configuration")
    print("   • Troubleshooting with fix scripts")
    print("   • Cross-drive file support")
    
    print("\n🌐 To view the updated documentation:")
    print("   1. Start Django server: python manage.py runserver")
    print("   2. Navigate to: http://localhost:8000/documentation/")
    print("   3. Use the toggle switch to view CLI and Git Hook sections")
    
    return all_found

if __name__ == "__main__":
    verify_documentation_updates()
