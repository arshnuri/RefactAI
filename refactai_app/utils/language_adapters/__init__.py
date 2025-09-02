#!/usr/bin/env python3
"""
Language Adapters Package

This package contains language-specific adapters for the multilanguage
hybrid refactoring engine. Each adapter handles parsing, transformation,
and code generation for a specific programming language.
"""

from .python_adapter import PythonAdapter
from .javascript_adapter import JavaScriptAdapter
from .java_adapter import JavaAdapter
from .cpp_adapter import CppAdapter

__all__ = [
    'PythonAdapter',
    'JavaScriptAdapter', 
    'JavaAdapter',
    'CppAdapter'
]

# Language registry for dynamic loading
LANGUAGE_ADAPTERS = {
    'python': PythonAdapter,
    'javascript': JavaScriptAdapter,
    'java': JavaAdapter,
    'cpp': CppAdapter,
    'c': CppAdapter,  # C uses the same adapter as C++
}

# File extension mappings
EXTENSION_MAP = {
    '.py': 'python',
    '.pyw': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.mjs': 'javascript',
    '.ts': 'javascript',  # TypeScript uses JavaScript adapter for now
    '.tsx': 'javascript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.cxx': 'cpp',
    '.cc': 'cpp',
    '.c': 'c',
    '.h': 'cpp',
    '.hpp': 'cpp',
    '.hxx': 'cpp'
}

def get_adapter_for_language(language: str):
    """Get adapter class for a specific language"""
    return LANGUAGE_ADAPTERS.get(language.lower())

def get_language_for_extension(extension: str):
    """Get language name for a file extension"""
    return EXTENSION_MAP.get(extension.lower())

def get_supported_languages():
    """Get list of all supported languages"""
    return list(LANGUAGE_ADAPTERS.keys())

def get_supported_extensions():
    """Get list of all supported file extensions"""
    return list(EXTENSION_MAP.keys())