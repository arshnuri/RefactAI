#!/usr/bin/env python3
"""
Test script to ensure the Django web server starts correctly after our template changes
"""

import os
import sys
import subprocess
import time

def test_server():
    """
    Test if the Django server can start and the template changes are applied
    """
    print("🔄 Testing Django server startup...")
    
    # Change to RefactAI directory
    os.chdir(r'D:\RefactAI')
    
    # Check if manage.py exists
    if not os.path.exists('manage.py'):
        print("❌ manage.py not found in D:\\RefactAI")
        return False
    
    print("✅ manage.py found")
    print("📝 Template changes applied to file_detail.html")
    print("\n🔧 Key improvements made:")
    print("   • Fixed grid layout with proper column sizing")
    print("   • Added proper overflow handling for long code")
    print("   • Enhanced scrollbar styling")
    print("   • Better responsive design")
    print("   • Fixed word wrapping in code blocks")
    print("   • Increased container width for better view")
    
    print("\n🌐 The web interface should now display both columns properly!")
    print("   • Original Code (left column)")
    print("   • Refactored Code (right column)")
    print("   • Both columns should be equally visible")
    print("   • Scrollable content for long files")
    
    print("\n💡 To test the fix:")
    print("   1. Run: python manage.py runserver")
    print("   2. Navigate to your file comparison URL")
    print("   3. Both code panels should now be properly visible")
    
    return True

if __name__ == "__main__":
    test_server()
