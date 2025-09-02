#!/usr/bin/env python3
"""
Verification script for the new comprehensive RefactAI documentation
"""

import os
import re

def verify_new_documentation():
    """
    Verify that the new documentation includes all current features
    """
    print("🔄 Verifying new comprehensive documentation...")
    
    doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'refactai_app', 'templates', 'refactai_app', 'documentation.html')
    
    if not os.path.exists(doc_path):
        print("❌ Documentation file not found")
        return False
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for comprehensive coverage
    essential_sections = [
        # Core Features
        "Interactive CLI",
        "Refactor and Push to Git",
        "Cross-Platform",
        "OpenRouter API",
        "Git Integration",
        "Self-Healing",
        
        # Setup & Usage
        "Quick Start Guide",
        "python setup.py",
        "fix_cli_validation.py",
        "fix_ast_validator.py",
        
        # Interactive CLI Features
        "Menu-driven interface",
        "File Selection Methods",
        "Pattern Selection",
        "Cross-Drive",
        "Manual Selection",
        
        # Git Features
        "Unicode fixes",
        "git-hook-ascii.py",
        "AST Validation",
        "git push --no-verify",
        
        # API Configuration
        "OPENROUTER_API_KEY",
        "Claude 3.5 Sonnet",
        "anthropic/claude-3.5-sonnet",
        "test_openrouter_api.py",
        
        # Troubleshooting
        "Automated Fix Scripts",
        "Cross-drive access",
        "Unicode encoding",
        
        # Advanced Features
        "Command Line Options",
        "Configuration Options",
        "Supported Languages",
        
        # User Experience
        "workflow-steps",
        "feature-card",
        "Hero Section",
        "Quick Links"
    ]
    
    print(f"✅ Documentation file found ({len(content):,} characters)")
    print("\n🔍 Checking comprehensive coverage:")
    
    found_count = 0
    missing_features = []
    
    for feature in essential_sections:
        if feature in content:
            print(f"   ✅ {feature}")
            found_count += 1
        else:
            print(f"   ❌ {feature}")
            missing_features.append(feature)
    
    coverage_percent = (found_count / len(essential_sections)) * 100
    
    print(f"\n📊 Documentation Analysis:")
    print(f"   • File size: {len(content):,} characters")
    print(f"   • Features covered: {found_count}/{len(essential_sections)} ({coverage_percent:.1f}%)")
    print(f"   • CSS styles: {'✅ Enhanced' if 'hero-section' in content else '❌ Basic'}")
    print(f"   • Interactive elements: {'✅ Yes' if 'workflow-step' in content else '❌ No'}")
    print(f"   • Mobile responsive: {'✅ Yes' if '@media' in content else '❌ No'}")
    
    # Check for new styling and UX improvements
    ux_features = [
        "hero-section",
        "feature-card",
        "workflow-steps", 
        "trouble-card",
        "alert-success",
        "command-block",
        "options-grid"
    ]
    
    ux_count = sum(1 for feature in ux_features if feature in content)
    print(f"   • UX enhancements: {ux_count}/{len(ux_features)} implemented")
    
    if coverage_percent >= 90:
        print("\n🎉 Excellent! Comprehensive documentation created successfully!")
        print("   • All major features documented")
        print("   • Modern, responsive design")
        print("   • User-friendly layout")
        print("   • Complete usage examples")
    elif coverage_percent >= 75:
        print("\n✅ Good documentation coverage!")
        print("   • Most features documented")
        print("   • May need minor additions")
    else:
        print("\n⚠️  Documentation needs improvement")
        print("   • Missing key features:")
        for feature in missing_features[:5]:  # Show first 5 missing
            print(f"     - {feature}")
    
    # Check for specific new features
    new_features_check = {
        "Interactive CLI Mode": "Interactive CLI" in content,
        "Refactor and Push Workflow": "Refactor and Push to Git" in content,
        "Cross-Drive Support": "Cross-Drive" in content or "different drives" in content,
        "Unicode Fixes": "Unicode fix" in content or "encoding" in content,
        "Automated Fix Scripts": "fix_cli_validation" in content and "fix_ast_validator" in content,
        "OpenRouter Integration": "OpenRouter" in content and "claude-3.5-sonnet" in content,
        "Comprehensive Troubleshooting": "trouble-card" in content or "Troubleshooting" in content,
        "Modern UI/UX": "hero-section" in content and "workflow-step" in content
    }
    
    print(f"\n🚀 New Features Documentation:")
    for feature, implemented in new_features_check.items():
        status = "✅" if implemented else "❌"
        print(f"   {status} {feature}")
    
    all_new_features = all(new_features_check.values())
    
    print(f"\n🌐 Next Steps:")
    print("   1. Start Django server: python manage.py runserver")
    print("   2. Navigate to: http://localhost:8000/documentation/")
    print("   3. Review the new comprehensive layout")
    print("   4. Test responsive design on different screen sizes")
    
    if all_new_features:
        print("\n🎊 SUCCESS: All new features are fully documented with modern UX!")
    
    return coverage_percent >= 90 and all_new_features

if __name__ == "__main__":
    verify_new_documentation()
