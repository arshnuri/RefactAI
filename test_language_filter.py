#!/usr/bin/env python3
"""
Test script to verify language filtering functionality
"""

import os
import sys
sys.path.append('.')

from refactai_app.utils.language_detect import LanguageDetector

def test_language_detection():
    """Test language detection for different file types"""
    
    test_cases = [
        ('test.py', 'def hello():\n    print("Hello World")', 'Python'),
        ('test.js', 'function hello() {\n    console.log("Hello World");\n}', 'JavaScript'),
        ('test.jsx', 'import React from "react";\nfunction App() {\n    return <div>Hello</div>;\n}', 'JSX'),
        ('test.java', 'public class Test {\n    public static void main(String[] args) {\n        System.out.println("Hello");\n    }\n}', 'Java'),
        ('test.cpp', '#include <iostream>\nint main() {\n    std::cout << "Hello";\n    return 0;\n}', 'C++'),
        ('test.c', '#include <stdio.h>\nint main() {\n    printf("Hello");\n    return 0;\n}', 'C'),
        ('test.ts', 'interface User {\n    name: string;\n}', 'TypeScript'),
        ('test.html', '<!DOCTYPE html>\n<html><body>Hello</body></html>', 'HTML'),
    ]
    
    allowed_languages = ['Python', 'JavaScript', 'Java', 'C', 'C++', 'C/C++', 'JSX']
    
    print("Language Detection Test Results:")
    print("=" * 50)
    
    for filename, content, expected in test_cases:
        detected = LanguageDetector.detect_language(filename, content)
        should_process = detected in allowed_languages
        
        print(f"File: {filename:12} | Detected: {detected:12} | Expected: {expected:12} | Process: {should_process}")
    
    print("\nOnly files marked 'Process: True' will be refactored.")

if __name__ == '__main__':
    test_language_detection()