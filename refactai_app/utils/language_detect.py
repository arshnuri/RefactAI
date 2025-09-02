import os
import re
from typing import Optional


class LanguageDetector:
    """Detects programming language from file extension and content"""
    
    # Language mappings based on file extensions
    EXTENSION_MAP = {
        # Python
        '.py': 'Python',
        '.pyw': 'Python',
        '.pyi': 'Python',
        '.pyx': 'Python',
        
        # JavaScript/TypeScript
        '.js': 'JavaScript',
        '.mjs': 'JavaScript',
        '.cjs': 'JavaScript',
        '.jsx': 'JSX',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.d.ts': 'TypeScript',
        
        # Java/JVM languages
        '.java': 'Java',
        '.kt': 'Kotlin',
        '.kts': 'Kotlin',
        '.scala': 'Scala',
        '.clj': 'Clojure',
        '.cljs': 'Clojure',
        '.cljc': 'Clojure',
        
        # C/C++
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c++': 'C++',
        '.h': 'C/C++',
        '.hpp': 'C++',
        '.hxx': 'C++',
        '.h++': 'C++',
        
        # C#/.NET
        '.cs': 'C#',
        '.csx': 'C#',
        '.vb': 'Visual Basic',
        '.fs': 'F#',
        '.fsx': 'F#',
        
        # Web languages
        '.php': 'PHP',
        '.phtml': 'PHP',
        '.php3': 'PHP',
        '.php4': 'PHP',
        '.php5': 'PHP',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.xhtml': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.styl': 'Stylus',
        
        # Other popular languages
        '.rb': 'Ruby',
        '.rbw': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.dart': 'Dart',
        '.elm': 'Elm',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.hs': 'Haskell',
        '.lhs': 'Haskell',
        '.ml': 'OCaml',
        '.mli': 'OCaml',
        '.pas': 'Pascal',
        '.pp': 'Pascal',
        '.pl': 'Perl',
        '.pm': 'Perl',
        '.lua': 'Lua',
        
        # Data/Config formats
        '.xml': 'XML',
        '.json': 'JSON',
        '.jsonc': 'JSON',
        '.json5': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Configuration',
        '.conf': 'Configuration',
        '.config': 'Configuration',
        '.properties': 'Properties',
        
        # Shell/Scripts
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.zsh': 'Shell',
        '.fish': 'Shell',
        '.ksh': 'Shell',
        '.csh': 'Shell',
        '.ps1': 'PowerShell',
        '.psm1': 'PowerShell',
        '.psd1': 'PowerShell',
        '.bat': 'Batch',
        '.cmd': 'Batch',
        
        # Database
        '.sql': 'SQL',
        '.mysql': 'SQL',
        '.pgsql': 'SQL',
        '.sqlite': 'SQL',
        
        # Scientific/Math
        '.r': 'R',
        '.R': 'R',
        '.m': 'MATLAB',
        '.nb': 'Mathematica',
        
        # Assembly
        '.asm': 'Assembly',
        '.s': 'Assembly',
        '.S': 'Assembly',
        
        # Documentation
        '.md': 'Markdown',
        '.markdown': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
        '.txt': 'Text',
        
        # Build/Project files
        '.gradle': 'Gradle',
        '.cmake': 'CMake',
        '.make': 'Makefile',
        '.mk': 'Makefile',
    }
    
    # Content-based heuristics for language detection
    CONTENT_PATTERNS = {
        'Python': [
            r'^\s*def\s+\w+\s*\(',
            r'^\s*class\s+\w+\s*[\(:]',
            r'^\s*import\s+\w+',
            r'^\s*from\s+\w+\s+import',
            r'if\s+__name__\s*==\s*["\']__main__["\']',
        ],
        'JavaScript': [
            r'function\s+\w+\s*\(',
            r'var\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'const\s+\w+\s*=',
            r'console\.log\s*\(',
            r'require\s*\(',
            r'module\.exports',
        ],
        'JSX': [
            r'<\w+[^>]*>',
            r'</\w+>',
            r'className\s*=',
            r'onClick\s*=',
            r'useState\s*\(',
            r'useEffect\s*\(',
            r'import\s+React',
            r'export\s+default',
        ],
        'TypeScript': [
            r'interface\s+\w+\s*{',
            r'type\s+\w+\s*=',
            r':\s*\w+\s*[=;]',
            r'export\s+interface',
            r'export\s+type',
        ],
        'Java': [
            r'public\s+class\s+\w+',
            r'private\s+\w+\s+\w+',
            r'public\s+static\s+void\s+main',
            r'import\s+java\.',
            r'package\s+\w+',
        ],
        'C++': [
            r'#include\s*<\w+>',
            r'using\s+namespace\s+std',
            r'std::\w+',
            r'class\s+\w+\s*{',
            r'int\s+main\s*\(',
        ],
        'C': [
            r'#include\s*<\w+\.h>',
            r'int\s+main\s*\(',
            r'printf\s*\(',
            r'scanf\s*\(',
        ],
        'C#': [
            r'using\s+System',
            r'namespace\s+\w+',
            r'public\s+class\s+\w+',
            r'Console\.WriteLine',
        ],
        'PHP': [
            r'<\?php',
            r'\$\w+\s*=',
            r'function\s+\w+\s*\(',
            r'echo\s+',
        ],
        'Ruby': [
            r'def\s+\w+',
            r'class\s+\w+',
            r'require\s+["\']\w+["\']',
            r'puts\s+',
        ],
        'Go': [
            r'package\s+\w+',
            r'import\s+["\']\w+["\']',
            r'func\s+\w+\s*\(',
            r'fmt\.Print',
        ],
        'Rust': [
            r'fn\s+\w+\s*\(',
            r'let\s+\w+\s*=',
            r'use\s+\w+',
            r'println!\s*\(',
        ],
        'HTML': [
            r'<!DOCTYPE\s+html>',
            r'<html\b',
            r'<head\b',
            r'<body\b',
            r'<div\b',
        ],
        'CSS': [
            r'\w+\s*{[^}]*}',
            r'@media\s+',
            r'@import\s+',
            r'#\w+\s*{',
            r'\.\w+\s*{',
        ],
    }
    
    @classmethod
    def detect_language(cls, file_path: str, content: Optional[str] = None) -> str:
        """Detect programming language from file path and optionally content
        
        Priority order:
        1. File extension (most reliable)
        2. Content-based detection (fallback)
        3. Unknown (last resort)
        """
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # ALWAYS prioritize extension-based detection when available
        if ext in cls.EXTENSION_MAP:
            detected_lang = cls.EXTENSION_MAP[ext]
            
            # For most cases, trust the file extension
            # Only validate with content if it's a potentially ambiguous extension
            ambiguous_extensions = {'.h', '.m', '.s'}  # Could be multiple languages
            
            if ext in ambiguous_extensions and content:
                # For ambiguous extensions, use content to disambiguate
                content_lang = cls._detect_from_content(content)
                if content_lang and content_lang != detected_lang:
                    # If content strongly suggests a different language, use it
                    if cls._has_strong_content_match(content, content_lang):
                        return content_lang
            
            return detected_lang
        
        # If no extension match, try content-based detection
        if content:
            content_lang = cls._detect_from_content(content)
            if content_lang:
                return content_lang
        
        # Default fallback - try to guess from filename patterns
        filename = os.path.basename(file_path.lower())
        if 'makefile' in filename or filename == 'makefile':
            return 'Makefile'
        elif 'dockerfile' in filename or filename == 'dockerfile':
            return 'Dockerfile'
        elif filename.endswith('rc') or filename.startswith('.'):
            return 'Configuration'
        
        return 'Unknown'
    
    @classmethod
    def _detect_from_content(cls, content: str) -> Optional[str]:
        """Detect language based on content patterns"""
        content_lines = content.split('\n')[:50]  # Check first 50 lines
        content_sample = '\n'.join(content_lines)
        
        scores = {}
        
        for language, patterns in cls.CONTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_sample, re.MULTILINE | re.IGNORECASE))
                score += matches
            
            if score > 0:
                scores[language] = score
        
        if scores:
            # Return language with highest score
            return max(scores, key=scores.get)
        
        return None
    
    @classmethod
    def _matches_content_patterns(cls, content: str, language: str) -> bool:
        """Check if content matches expected patterns for the language"""
        if language not in cls.CONTENT_PATTERNS:
            return True  # No patterns to check
        
        content_lines = content.split('\n')[:20]  # Check first 20 lines
        content_sample = '\n'.join(content_lines)
        
        patterns = cls.CONTENT_PATTERNS[language]
        matches = 0
        
        for pattern in patterns:
            if re.search(pattern, content_sample, re.MULTILINE | re.IGNORECASE):
                matches += 1
        
        # Consider it a match if at least 1 pattern matches
        return matches > 0
    
    @classmethod
    def _has_strong_content_match(cls, content: str, language: str) -> bool:
        """Check if content has strong indicators for the language"""
        if language not in cls.CONTENT_PATTERNS:
            return False
        
        content_lines = content.split('\n')[:30]  # Check first 30 lines
        content_sample = '\n'.join(content_lines)
        
        patterns = cls.CONTENT_PATTERNS[language]
        matches = 0
        
        for pattern in patterns:
            if re.search(pattern, content_sample, re.MULTILINE | re.IGNORECASE):
                matches += 1
        
        # Consider it a strong match if at least 2 patterns match
        return matches >= 2
    
    @classmethod
    def get_language_for_llm_prompt(cls, language: str) -> str:
        """Get language name suitable for LLM prompts"""
        # Map some languages to more specific names for better LLM understanding
        llm_language_map = {
            'C/C++': 'C or C++',
            'HTML': 'HTML',
            'CSS': 'CSS',
            'SCSS': 'SCSS/Sass',
            'Less': 'Less CSS',
            'Unknown': 'code'
        }
        
        return llm_language_map.get(language, language)