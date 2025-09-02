#!/usr/bin/env python3
"""
LLM Suggestor Module

Handles communication with external LLM APIs to get structured refactoring suggestions.
Returns JSON-formatted suggestions for naming, documentation, and transformations.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from abc import ABC, abstractmethod


class SuggestionType(Enum):
    """Types of suggestions the LLM can provide"""
    RENAME = "rename"
    DOCSTRING = "docstring"
    COMMENT = "comment"
    TRANSFORMATION = "transformation"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    BEST_PRACTICE = "best_practice"


@dataclass
class RenameSuggestion:
    """Suggestion for renaming variables/functions"""
    old_name: str
    new_name: str
    reason: str
    confidence: float
    location: Optional[str] = None


@dataclass
class DocstringSuggestion:
    """Suggestion for adding/improving docstrings"""
    target_type: str  # 'function', 'class', 'method'
    target_name: str
    docstring: str
    style: str  # 'google', 'numpy', 'sphinx'
    location: Optional[str] = None


@dataclass
class TransformationSuggestion:
    """Suggestion for code transformation"""
    transformation_type: str
    description: str
    location: str
    before_snippet: Optional[str] = None
    after_snippet: Optional[str] = None
    confidence: float = 0.8
    safety_level: str = "safe"  # 'safe', 'moderate', 'risky'


@dataclass
class PerformanceSuggestion:
    """Performance improvement suggestion"""
    issue_type: str
    description: str
    suggestion: str
    impact: str  # 'low', 'medium', 'high'
    location: Optional[str] = None


@dataclass
class LLMResponse:
    """Structured response from LLM"""
    renames: List[RenameSuggestion]
    docstrings: List[DocstringSuggestion]
    transformations: List[TransformationSuggestion]
    performance: List[PerformanceSuggestion]
    comments: List[Dict[str, str]]
    metadata: Dict[str, Any]


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate refactoring suggestions for the given code"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for refactoring suggestions"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate suggestions using OpenAI API"""
        prompt = self._create_refactoring_prompt(code, language, context)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return self._parse_llm_response(content)
            else:
                print(f"OpenAI API error: {response.status_code}")
                return self._empty_response()
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._empty_response()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for refactoring"""
        return """
You are a code refactoring expert. Analyze the provided code and return structured JSON suggestions for improvements.

Your response MUST be valid JSON with this exact structure:
{
  "renames": [
    {
      "old_name": "original_name",
      "new_name": "better_name",
      "reason": "explanation",
      "confidence": 0.8,
      "location": "line 10" (optional)
    }
  ],
  "docstrings": [
    {
      "target_type": "function",
      "target_name": "function_name",
      "docstring": "Complete docstring text",
      "style": "google",
      "location": "line 5" (optional)
    }
  ],
  "transformations": [
    {
      "transformation_type": "merge_nested_ifs",
      "description": "Merge nested if statements for better readability",
      "location": "lines 15-20",
      "confidence": 0.9,
      "safety_level": "safe"
    }
  ],
  "performance": [
    {
      "issue_type": "inefficient_loop",
      "description": "Loop can be optimized",
      "suggestion": "Use list comprehension instead",
      "impact": "medium",
      "location": "line 25"
    }
  ],
  "comments": [
    {
      "location": "line 30",
      "comment": "Explain complex logic here"
    }
  ],
  "metadata": {
    "analysis_confidence": 0.85,
    "suggestions_count": 5
  }
}

Focus on:
1. Better variable/function names (clear, descriptive)
2. Missing or poor docstrings
3. Safe code transformations (merge conditions, extract functions, etc.)
4. Performance improvements
5. Code readability enhancements

Only suggest transformations that are SAFE and maintain code logic.
"""
    
    def _create_refactoring_prompt(self, code: str, language: str, context: Dict[str, Any]) -> str:
        """Create a detailed prompt for refactoring suggestions"""
        prompt = f"""
Analyze this {language} code and provide refactoring suggestions:

```{language}
{code}
```

Context information:
"""
        
        if context.get('git_context'):
            git_info = context['git_context']
            prompt += f"""
- File has {len(git_info.get('file_history', []))} recent commits
- Recent changes: {', '.join([c.get('message', '') for c in git_info.get('recent_changes', [])][:3])}
"""
        
        if context.get('naming_patterns'):
            patterns = context['naming_patterns']
            prompt += f"""
- Naming conventions in codebase: {', '.join([p.description for p in patterns[:2]])}
"""
        
        if context.get('file_type'):
            prompt += f"""
- File type: {context['file_type']}
"""
        
        prompt += """

Provide suggestions following the JSON structure specified in the system prompt.
Focus on practical, safe improvements that maintain code functionality.
"""
        
        return prompt
    
    def _parse_llm_response(self, content: str) -> LLMResponse:
        """Parse LLM response into structured format"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'{.*}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            data = json.loads(json_str)
            
            # Convert to structured objects
            renames = [RenameSuggestion(**item) for item in data.get('renames', [])]
            docstrings = [DocstringSuggestion(**item) for item in data.get('docstrings', [])]
            transformations = [TransformationSuggestion(**item) for item in data.get('transformations', [])]
            performance = [PerformanceSuggestion(**item) for item in data.get('performance', [])]
            comments = data.get('comments', [])
            metadata = data.get('metadata', {})
            
            return LLMResponse(
                renames=renames,
                docstrings=docstrings,
                transformations=transformations,
                performance=performance,
                comments=comments,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response content: {content[:500]}...")
            return self._empty_response()
    
    def _empty_response(self) -> LLMResponse:
        """Return empty response structure"""
        return LLMResponse(
            renames=[],
            docstrings=[],
            transformations=[],
            performance=[],
            comments=[],
            metadata={"error": "Failed to generate suggestions"}
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for refactoring suggestions"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def is_available(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.headers,
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                },
                timeout=5
            )
            return response.status_code in [200, 400]  # 400 is expected for minimal request
        except Exception:
            return False
    
    def generate_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate suggestions using Anthropic API"""
        prompt = self._create_refactoring_prompt(code, language, context)
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.headers,
                json={
                    "model": self.model,
                    "max_tokens": 2000,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                return self._parse_llm_response(content)
            else:
                print(f"Anthropic API error: {response.status_code}")
                return self._empty_response()
                
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return self._empty_response()
    
    def _create_refactoring_prompt(self, code: str, language: str, context: Dict[str, Any]) -> str:
        """Create prompt for Anthropic Claude"""
        return f"""
You are a code refactoring expert. Analyze this {language} code and provide structured JSON suggestions.

Code to analyze:
```{language}
{code}
```

Return ONLY valid JSON with this structure:
{{
  "renames": [
    {{
      "old_name": "current_name",
      "new_name": "better_name",
      "reason": "why this is better",
      "confidence": 0.8
    }}
  ],
  "docstrings": [
    {{
      "target_type": "function",
      "target_name": "function_name",
      "docstring": "Complete docstring",
      "style": "google"
    }}
  ],
  "transformations": [
    {{
      "transformation_type": "extract_function",
      "description": "Extract repeated code into function",
      "location": "lines 10-15",
      "confidence": 0.9,
      "safety_level": "safe"
    }}
  ],
  "performance": [
    {{
      "issue_type": "inefficient_operation",
      "description": "Performance issue description",
      "suggestion": "How to improve",
      "impact": "medium"
    }}
  ],
  "comments": [],
  "metadata": {{
    "analysis_confidence": 0.85
  }}
}}

Focus on safe, practical improvements. Only suggest transformations that preserve code logic.
"""
    
    def _parse_llm_response(self, content: str) -> LLMResponse:
        """Parse Anthropic response (reuse OpenAI parser)"""
        return OpenAIProvider._parse_llm_response(self, content)
    
    def _empty_response(self) -> LLMResponse:
        """Return empty response structure"""
        return OpenAIProvider._empty_response(self)


class LocalLLMProvider(LLMProvider):
    """Local LLM provider (e.g., Ollama, local API)"""
    
    def __init__(self, base_url: str, model: str = "codellama"):
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def is_available(self) -> bool:
        """Check if local LLM is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate suggestions using local LLM"""
        prompt = self._create_simple_prompt(code, language)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                return self._parse_simple_response(content)
            else:
                return self._empty_response()
                
        except Exception as e:
            print(f"Error calling local LLM: {e}")
            return self._empty_response()
    
    def _create_simple_prompt(self, code: str, language: str) -> str:
        """Create simplified prompt for local LLM"""
        return f"""
Analyze this {language} code and suggest improvements:

{code}

Provide suggestions for:
1. Better variable names
2. Missing docstrings
3. Code simplifications

Format as JSON with 'renames', 'docstrings', and 'transformations' arrays.
"""
    
    def _parse_simple_response(self, content: str) -> LLMResponse:
        """Parse simple response from local LLM"""
        try:
            # Try to extract JSON
            json_match = re.search(r'{.*}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                # Convert to structured format with defaults
                renames = []
                for item in data.get('renames', []):
                    if isinstance(item, dict) and 'old_name' in item and 'new_name' in item:
                        renames.append(RenameSuggestion(
                            old_name=item['old_name'],
                            new_name=item['new_name'],
                            reason=item.get('reason', 'Improved naming'),
                            confidence=item.get('confidence', 0.7)
                        ))
                
                return LLMResponse(
                    renames=renames,
                    docstrings=[],
                    transformations=[],
                    performance=[],
                    comments=[],
                    metadata={"source": "local_llm"}
                )
            else:
                return self._empty_response()
                
        except Exception as e:
            print(f"Error parsing local LLM response: {e}")
            return self._empty_response()
    
    def _empty_response(self) -> LLMResponse:
        """Return empty response structure"""
        return LLMResponse(
            renames=[],
            docstrings=[],
            transformations=[],
            performance=[],
            comments=[],
            metadata={"error": "Failed to generate suggestions"}
        )


class LLMSuggestor:
    """Main class for managing LLM suggestions"""
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.fallback_enabled = True
    
    def add_provider(self, provider: LLMProvider):
        """Add an LLM provider"""
        self.providers.append(provider)
    
    def get_suggestions(self, code: str, language: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Get refactoring suggestions using available providers"""
        context = context or {}
        
        for provider in self.providers:
            if provider.is_available():
                try:
                    response = provider.generate_suggestions(code, language, context)
                    if response and (response.renames or response.docstrings or response.transformations):
                        return response
                except Exception as e:
                    print(f"Provider {type(provider).__name__} failed: {e}")
                    continue
        
        # Return empty response if all providers fail
        return LLMResponse(
            renames=[],
            docstrings=[],
            transformations=[],
            performance=[],
            comments=[],
            metadata={"error": "No providers available"}
        )
    
    def validate_suggestions(self, suggestions: LLMResponse, code: str, language: str) -> LLMResponse:
        """Validate and filter suggestions for safety"""
        # Filter transformations by safety level
        safe_transformations = [
            t for t in suggestions.transformations 
            if t.safety_level in ['safe', 'moderate'] and t.confidence > 0.6
        ]
        
        # Filter renames with high confidence
        safe_renames = [
            r for r in suggestions.renames 
            if r.confidence > 0.7 and self._is_valid_name(r.new_name, language)
        ]
        
        return LLMResponse(
            renames=safe_renames,
            docstrings=suggestions.docstrings,  # Docstrings are generally safe
            transformations=safe_transformations,
            performance=suggestions.performance,
            comments=suggestions.comments,
            metadata=suggestions.metadata
        )
    
    def _is_valid_name(self, name: str, language: str) -> bool:
        """Check if a name is valid for the given language"""
        if not name or not name.replace('_', '').replace('-', '').isalnum():
            return False
        
        # Language-specific validation
        if language == 'python':
            return name.islower() or '_' in name  # snake_case preferred
        elif language in ['javascript', 'java']:
            return name[0].islower() and '_' not in name  # camelCase preferred
        
        return True