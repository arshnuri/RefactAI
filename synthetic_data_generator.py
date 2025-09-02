#!/usr/bin/env python3
"""
Synthetic Training Data Generator for Nested If Refactoring

This module generates synthetic code examples with deeply nested if statements
and their corresponding optimal refactorings for training ML models.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime

class RefactoringPattern(Enum):
    GUARD_CLAUSES = "guard_clauses"
    EARLY_RETURN = "early_return"
    METHOD_EXTRACTION = "method_extraction"
    STRATEGY_PATTERN = "strategy_pattern"
    SWITCH_STATEMENT = "switch_statement"

class Language(Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    CSHARP = "csharp"

@dataclass
class TrainingExample:
    """Represents a single training example with before/after code"""
    language: str
    original_code: str
    refactored_code: str
    pattern: str
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    complexity_reduction: int
    depth_reduction: int
    description: str

class SyntheticDataGenerator:
    """Generates synthetic training data for nested if refactoring"""
    
    def __init__(self):
        self.examples = []
        self.variable_names = [
            "score", "value", "data", "input", "result", "status", "level", "grade",
            "amount", "count", "size", "length", "weight", "height", "age", "price"
        ]
        self.conditions = [
            "> 0", "< 100", ">= 50", "<= 90", "== 0", "!= null", "is not None",
            "> threshold", "< limit", "in range", "is valid", "is empty"
        ]
        
    def generate_dataset(self, num_examples: int = 1000) -> List[TrainingExample]:
        """Generate a complete dataset of training examples"""
        examples_per_language = num_examples // 4
        
        for language in Language:
            for _ in range(examples_per_language):
                # Generate different complexity levels
                depth = random.randint(3, 8)
                pattern = random.choice(list(RefactoringPattern))
                
                example = self._generate_example(language, depth, pattern)
                if example:
                    self.examples.append(example)
        
        return self.examples
    
    def _generate_example(self, language: Language, depth: int, pattern: RefactoringPattern) -> TrainingExample:
        """Generate a single training example"""
        if language == Language.PYTHON:
            return self._generate_python_example(depth, pattern)
        elif language == Language.JAVA:
            return self._generate_java_example(depth, pattern)
        elif language == Language.JAVASCRIPT:
            return self._generate_javascript_example(depth, pattern)
        elif language == Language.CSHARP:
            return self._generate_csharp_example(depth, pattern)
    
    def _generate_python_example(self, depth: int, pattern: RefactoringPattern) -> TrainingExample:
        """Generate Python nested if example"""
        var_name = random.choice(self.variable_names)
        
        # Generate original nested code
        original = self._create_python_nested_structure(var_name, depth)
        
        # Generate refactored version based on pattern
        if pattern == RefactoringPattern.GUARD_CLAUSES:
            refactored = self._create_python_guard_clauses(var_name, depth)
        elif pattern == RefactoringPattern.EARLY_RETURN:
            refactored = self._create_python_early_return(var_name, depth)
        elif pattern == RefactoringPattern.METHOD_EXTRACTION:
            refactored = self._create_python_method_extraction(var_name, depth)
        else:
            refactored = self._create_python_guard_clauses(var_name, depth)  # fallback
        
        return TrainingExample(
            language="python",
            original_code=original,
            refactored_code=refactored,
            pattern=pattern.value,
            metrics_before={"depth": depth, "complexity": depth * 10, "lines": depth * 3 + 5},
            metrics_after={"depth": max(1, depth - 2), "complexity": max(10, depth * 8), "lines": depth * 2 + 8},
            complexity_reduction=depth * 2,
            depth_reduction=min(2, depth - 1),
            description=f"Refactor {depth}-level nested if using {pattern.value}"
        )
    
    def _create_python_nested_structure(self, var_name: str, depth: int) -> str:
        """Create deeply nested Python if structure"""
        indent = "    "
        code_lines = [f"def process_{var_name}({var_name}):"]
        
        for i in range(depth):
            condition = self._get_python_condition(var_name, i)
            code_lines.append(f"{indent * (i + 1)}if {condition}:")
        
        # Add final action
        code_lines.append(f"{indent * (depth + 1)}return 'success'")
        
        # Add else clauses
        for i in range(depth - 1, -1, -1):
            code_lines.append(f"{indent * (i + 1)}else:")
            code_lines.append(f"{indent * (i + 2)}return 'failed_at_level_{i}'")
        
        return "\n".join(code_lines)
    
    def _create_python_guard_clauses(self, var_name: str, depth: int) -> str:
        """Create Python code with guard clauses"""
        indent = "    "
        code_lines = [f"def process_{var_name}({var_name}):"]
        
        # Add guard clauses
        for i in range(depth):
            condition = self._get_python_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if {condition}:")
            code_lines.append(f"{indent * 2}return 'failed_at_level_{i}'")
            code_lines.append("")
        
        # Add main logic
        code_lines.append(f"{indent}# Main processing logic")
        code_lines.append(f"{indent}return 'success'")
        
        return "\n".join(code_lines)
    
    def _create_python_early_return(self, var_name: str, depth: int) -> str:
        """Create Python code with early returns"""
        indent = "    "
        code_lines = [f"def process_{var_name}({var_name}):"]
        
        for i in range(depth):
            condition = self._get_python_condition(var_name, i)
            code_lines.append(f"{indent}if not {condition}:")
            code_lines.append(f"{indent * 2}return 'failed_at_level_{i}'")
        
        code_lines.append(f"{indent}return 'success'")
        
        return "\n".join(code_lines)
    
    def _create_python_method_extraction(self, var_name: str, depth: int) -> str:
        """Create Python code with extracted methods"""
        indent = "    "
        code_lines = []
        
        # Create validation methods
        for i in range(depth):
            condition = self._get_python_condition(var_name, i)
            code_lines.append(f"def validate_level_{i}({var_name}):")
            code_lines.append(f"{indent}return {condition}")
            code_lines.append("")
        
        # Main method
        code_lines.append(f"def process_{var_name}({var_name}):")
        for i in range(depth):
            code_lines.append(f"{indent}if not validate_level_{i}({var_name}):")
            code_lines.append(f"{indent * 2}return 'failed_at_level_{i}'")
        
        code_lines.append(f"{indent}return 'success'")
        
        return "\n".join(code_lines)
    
    def _generate_java_example(self, depth: int, pattern: RefactoringPattern) -> TrainingExample:
        """Generate Java nested if example"""
        var_name = random.choice(self.variable_names)
        
        original = self._create_java_nested_structure(var_name, depth)
        
        if pattern == RefactoringPattern.GUARD_CLAUSES:
            refactored = self._create_java_guard_clauses(var_name, depth)
        elif pattern == RefactoringPattern.STRATEGY_PATTERN:
            refactored = self._create_java_strategy_pattern(var_name, depth)
        else:
            refactored = self._create_java_early_return(var_name, depth)
        
        return TrainingExample(
            language="java",
            original_code=original,
            refactored_code=refactored,
            pattern=pattern.value,
            metrics_before={"depth": depth, "complexity": depth * 12, "lines": depth * 4 + 8},
            metrics_after={"depth": max(1, depth - 3), "complexity": max(15, depth * 8), "lines": depth * 3 + 12},
            complexity_reduction=depth * 4,
            depth_reduction=min(3, depth - 1),
            description=f"Refactor {depth}-level nested if using {pattern.value}"
        )
    
    def _create_java_nested_structure(self, var_name: str, depth: int) -> str:
        """Create deeply nested Java if structure"""
        indent = "    "
        code_lines = [
            f"public String process{var_name.capitalize()}(int {var_name}) {{"
        ]
        
        for i in range(depth):
            condition = self._get_java_condition(var_name, i)
            code_lines.append(f"{indent * (i + 1)}if ({condition}) {{")
        
        code_lines.append(f"{indent * (depth + 1)}return \"success\";")
        
        for i in range(depth - 1, -1, -1):
            code_lines.append(f"{indent * (i + 1)}}} else {{")
            code_lines.append(f"{indent * (i + 2)}return \"failed_at_level_{i}\";")
            code_lines.append(f"{indent * (i + 1)}}}")
        
        code_lines.append("}")
        return "\n".join(code_lines)
    
    def _create_java_guard_clauses(self, var_name: str, depth: int) -> str:
        """Create Java code with guard clauses"""
        indent = "    "
        code_lines = [
            f"public String process{var_name.capitalize()}(int {var_name}) {{"
        ]
        
        for i in range(depth):
            condition = self._get_java_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if ({condition}) {{")
            code_lines.append(f"{indent * 2}return \"failed_at_level_{i}\";")
            code_lines.append(f"{indent}}}")
            code_lines.append("")
        
        code_lines.append(f"{indent}return \"success\";")
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def _create_java_strategy_pattern(self, var_name: str, depth: int) -> str:
        """Create Java code using strategy pattern"""
        indent = "    "
        code_lines = [
            "interface ValidationStrategy {",
            f"{indent}boolean validate(int {var_name});",
            f"{indent}String getErrorMessage();",
            "}",
            ""
        ]
        
        # Create strategy implementations
        for i in range(depth):
            condition = self._get_java_condition(var_name, i)
            code_lines.extend([
                f"class Level{i}Validator implements ValidationStrategy {{",
                f"{indent}public boolean validate(int {var_name}) {{",
                f"{indent * 2}return {condition};",
                f"{indent}}}",
                f"{indent}public String getErrorMessage() {{",
                f"{indent * 2}return \"failed_at_level_{i}\";",
                f"{indent}}}",
                "}",
                ""
            ])
        
        # Main method
        code_lines.extend([
            f"public String process{var_name.capitalize()}(int {var_name}) {{",
            f"{indent}ValidationStrategy[] validators = {{"
        ])
        
        for i in range(depth):
            code_lines.append(f"{indent * 2}new Level{i}Validator(),")
        
        code_lines.extend([
            f"{indent}}};",
            "",
            f"{indent}for (ValidationStrategy validator : validators) {{",
            f"{indent * 2}if (!validator.validate({var_name})) {{",
            f"{indent * 3}return validator.getErrorMessage();",
            f"{indent * 2}}}",
            f"{indent}}}",
            "",
            f"{indent}return \"success\";",
            "}"
        ])
        
        return "\n".join(code_lines)
    
    def _create_java_early_return(self, var_name: str, depth: int) -> str:
        """Create Java code with early returns"""
        indent = "    "
        code_lines = [
            f"public String process{var_name.capitalize()}(int {var_name}) {{"
        ]
        
        for i in range(depth):
            condition = self._get_java_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if ({condition}) {{")
            code_lines.append(f"{indent * 2}return \"failed_at_level_{i}\";")
            code_lines.append(f"{indent}}}")
        
        code_lines.append(f"{indent}return \"success\";")
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def _generate_javascript_example(self, depth: int, pattern: RefactoringPattern) -> TrainingExample:
        """Generate JavaScript nested if example"""
        var_name = random.choice(self.variable_names)
        
        original = self._create_javascript_nested_structure(var_name, depth)
        
        if pattern == RefactoringPattern.EARLY_RETURN:
            refactored = self._create_javascript_early_return(var_name, depth)
        else:
            refactored = self._create_javascript_guard_clauses(var_name, depth)
        
        return TrainingExample(
            language="javascript",
            original_code=original,
            refactored_code=refactored,
            pattern=pattern.value,
            metrics_before={"depth": depth, "complexity": depth * 11, "lines": depth * 3 + 6},
            metrics_after={"depth": max(1, depth - 2), "complexity": max(12, depth * 7), "lines": depth * 2 + 10},
            complexity_reduction=depth * 4,
            depth_reduction=min(2, depth - 1),
            description=f"Refactor {depth}-level nested if using {pattern.value}"
        )
    
    def _create_javascript_nested_structure(self, var_name: str, depth: int) -> str:
        """Create deeply nested JavaScript if structure"""
        indent = "  "
        code_lines = [f"function process{var_name.capitalize()}({var_name}) {{"]
        
        for i in range(depth):
            condition = self._get_javascript_condition(var_name, i)
            code_lines.append(f"{indent * (i + 1)}if ({condition}) {{")
        
        code_lines.append(f"{indent * (depth + 1)}return 'success';")
        
        for i in range(depth - 1, -1, -1):
            code_lines.append(f"{indent * (i + 1)}}} else {{")
            code_lines.append(f"{indent * (i + 2)}return 'failed_at_level_{i}';")
            code_lines.append(f"{indent * (i + 1)}}}")
        
        code_lines.append("}")
        return "\n".join(code_lines)
    
    def _create_javascript_early_return(self, var_name: str, depth: int) -> str:
        """Create JavaScript code with early returns"""
        indent = "  "
        code_lines = [f"function process{var_name.capitalize()}({var_name}) {{"]
        
        for i in range(depth):
            condition = self._get_javascript_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if ({condition}) {{")
            code_lines.append(f"{indent * 2}return 'failed_at_level_{i}';")
            code_lines.append(f"{indent}}}")
        
        code_lines.append(f"{indent}return 'success';")
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def _create_javascript_guard_clauses(self, var_name: str, depth: int) -> str:
        """Create JavaScript code with guard clauses"""
        indent = "  "
        code_lines = [f"function process{var_name.capitalize()}({var_name}) {{"]
        
        for i in range(depth):
            condition = self._get_javascript_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if ({condition}) {{")
            code_lines.append(f"{indent * 2}return 'failed_at_level_{i}';")
            code_lines.append(f"{indent}}}")
        
        code_lines.append(f"{indent}return 'success';")
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def _get_python_condition(self, var_name: str, level: int, negate: bool = False) -> str:
        """Generate Python condition for given level"""
        conditions = [
            f"{var_name} is not None",
            f"{var_name} > {level * 10}",
            f"{var_name} < {100 - level * 5}",
            f"len(str({var_name})) > {level}",
            f"{var_name} % {level + 2} == 0"
        ]
        condition = conditions[level % len(conditions)]
        return f"not ({condition})" if negate else condition
    
    def _get_java_condition(self, var_name: str, level: int, negate: bool = False) -> str:
        """Generate Java condition for given level"""
        conditions = [
            f"{var_name} > {level * 10}",
            f"{var_name} < {100 - level * 5}",
            f"{var_name} >= {level * 15}",
            f"{var_name} <= {90 - level * 3}",
            f"{var_name} % {level + 2} == 0"
        ]
        condition = conditions[level % len(conditions)]
        return f"!({condition})" if negate else condition
    
    def _get_javascript_condition(self, var_name: str, level: int, negate: bool = False) -> str:
        """Generate JavaScript condition for given level"""
        conditions = [
            f"{var_name} != null",
            f"{var_name} > {level * 10}",
            f"{var_name} < {100 - level * 5}",
            f"{var_name}.toString().length > {level}",
            f"{var_name} % {level + 2} === 0"
        ]
        condition = conditions[level % len(conditions)]
        return f"!({condition})" if negate else condition
    
    def _generate_csharp_example(self, depth: int, pattern: RefactoringPattern) -> TrainingExample:
        """Generate C# nested if example"""
        # Similar to Java but with C# syntax
        var_name = random.choice(self.variable_names)
        
        original = self._create_csharp_nested_structure(var_name, depth)
        refactored = self._create_csharp_guard_clauses(var_name, depth)
        
        return TrainingExample(
            language="csharp",
            original_code=original,
            refactored_code=refactored,
            pattern=pattern.value,
            metrics_before={"depth": depth, "complexity": depth * 12, "lines": depth * 4 + 8},
            metrics_after={"depth": max(1, depth - 2), "complexity": max(15, depth * 8), "lines": depth * 3 + 10},
            complexity_reduction=depth * 4,
            depth_reduction=min(2, depth - 1),
            description=f"Refactor {depth}-level nested if using {pattern.value}"
        )
    
    def _create_csharp_nested_structure(self, var_name: str, depth: int) -> str:
        """Create deeply nested C# if structure"""
        indent = "    "
        code_lines = [
            f"public string Process{var_name.capitalize()}(int {var_name})",
            "{"
        ]
        
        for i in range(depth):
            condition = self._get_java_condition(var_name, i)  # Similar to Java
            code_lines.append(f"{indent * (i + 1)}if ({condition})")
            code_lines.append(f"{indent * (i + 1)}{{")
        
        code_lines.append(f"{indent * (depth + 1)}return \"success\";")
        
        for i in range(depth - 1, -1, -1):
            code_lines.append(f"{indent * (i + 1)}}}")
            code_lines.append(f"{indent * (i + 1)}else")
            code_lines.append(f"{indent * (i + 1)}{{")
            code_lines.append(f"{indent * (i + 2)}return \"failed_at_level_{i}\";")
            code_lines.append(f"{indent * (i + 1)}}}")
        
        code_lines.append("}")
        return "\n".join(code_lines)
    
    def _create_csharp_guard_clauses(self, var_name: str, depth: int) -> str:
        """Create C# code with guard clauses"""
        indent = "    "
        code_lines = [
            f"public string Process{var_name.capitalize()}(int {var_name})",
            "{"
        ]
        
        for i in range(depth):
            condition = self._get_java_condition(var_name, i, negate=True)
            code_lines.append(f"{indent}if ({condition})")
            code_lines.append(f"{indent}{{")
            code_lines.append(f"{indent * 2}return \"failed_at_level_{i}\";")
            code_lines.append(f"{indent}}}")
            code_lines.append("")
        
        code_lines.append(f"{indent}return \"success\";")
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def save_dataset(self, filename: str = None) -> str:
        """Save the generated dataset to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_refactoring_dataset_{timestamp}.json"
        
        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_examples": len(self.examples),
                "languages": list(set(ex.language for ex in self.examples)),
                "patterns": list(set(ex.pattern for ex in self.examples))
            },
            "examples": [
                {
                    "id": i,
                    "language": ex.language,
                    "pattern": ex.pattern,
                    "description": ex.description,
                    "original_code": ex.original_code,
                    "refactored_code": ex.refactored_code,
                    "metrics_before": ex.metrics_before,
                    "metrics_after": ex.metrics_after,
                    "complexity_reduction": ex.complexity_reduction,
                    "depth_reduction": ex.depth_reduction
                }
                for i, ex in enumerate(self.examples)
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        return filename

def main():
    """Generate synthetic training dataset"""
    print("🔄 Generating synthetic training data for nested if refactoring...")
    
    generator = SyntheticDataGenerator()
    examples = generator.generate_dataset(num_examples=500)  # Start with 500 examples
    
    print(f"✅ Generated {len(examples)} training examples")
    
    # Save dataset
    filename = generator.save_dataset()
    print(f"💾 Dataset saved to: {filename}")
    
    # Print statistics
    languages = {}
    patterns = {}
    
    for ex in examples:
        languages[ex.language] = languages.get(ex.language, 0) + 1
        patterns[ex.pattern] = patterns.get(ex.pattern, 0) + 1
    
    print("\n📊 Dataset Statistics:")
    print("Languages:")
    for lang, count in languages.items():
        print(f"  • {lang}: {count} examples")
    
    print("\nRefactoring Patterns:")
    for pattern, count in patterns.items():
        print(f"  • {pattern}: {count} examples")
    
    # Calculate average improvements
    avg_complexity_reduction = sum(ex.complexity_reduction for ex in examples) / len(examples)
    avg_depth_reduction = sum(ex.depth_reduction for ex in examples) / len(examples)
    
    print(f"\n🎯 Average Improvements:")
    print(f"  • Complexity reduction: {avg_complexity_reduction:.1f}")
    print(f"  • Depth reduction: {avg_depth_reduction:.1f}")
    
    print("\n🚀 Next steps:")
    print("  1. Review generated examples for quality")
    print("  2. Fine-tune language model on this dataset")
    print("  3. Evaluate model performance on test set")
    print("  4. Integrate improved model into RefactAI")

if __name__ == "__main__":
    main()