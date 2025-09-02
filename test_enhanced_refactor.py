#!/usr/bin/env python3
"""
Test script to demonstrate the Enhanced Rule-Based Refactoring system.
This script shows how the system can improve code quality without LLM integration.
"""

import sys
import os

# Add the refactai_app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'refactai_app'))

from utils.enhanced_rule_based_refactor import EnhancedRuleBasedRefactor
from utils.code_quality_analyzer import CodeQualityAnalyzer

def test_enhanced_refactor():
    """
    Test the enhanced rule-based refactoring system with sample low-quality code.
    """
    
    # Sample low-quality Python code with common issues
    low_quality_python = '''
def calculate_stuff(x, y, z):
    # Poor naming, long line, missing type hints
    if x == True:  # Bad boolean comparison
        result = x + y + z + (1000 * 2000 * 3000)  # Long calculation line
        return result
    else:
        return None



# Too many blank lines above
class data_processor:  # Bad class naming (should be PascalCase)
    def __init__(self):
        self.data = []
        
    def process(self, items):  # Missing type hints
        for item in items:
            if item != None:  # Bad None comparison
                self.data.append(item)
                
    def get_result(self):
        # No docstring, unclear function purpose
        temp = []
        for i in range(len(self.data)):  # Inefficient iteration
            temp.append(self.data[i] * 2)
        return temp
'''

    print("Original Code Quality:")
    print("=" * 50)
    
    # Analyze original code quality
    original_analyzer = CodeQualityAnalyzer()
    original_metrics = original_analyzer.analyze_code(low_quality_python, 'python')
    original_overall = original_analyzer.calculate_overall_score(original_metrics)
    
    print(f"Complexity: {original_metrics['complexity']:.1f}")
    print(f"Readability: {original_metrics['readability']:.1f}")
    print(f"Maintainability: {original_metrics['maintainability']:.1f}")
    print(f"Overall Quality: {original_overall:.1f}")
    
    print("\nApplying Enhanced Rule-Based Refactoring...")
    print("=" * 50)
    
    # Apply enhanced refactoring
    refactor = EnhancedRuleBasedRefactor()
    refactor_result = refactor.refactor_code(low_quality_python, 'python')
    enhanced_code = refactor_result['refactored_code']
    
    print("Enhanced Code:")
    print("-" * 30)
    print(enhanced_code)
    
    print("\nImprovements Applied:")
    print("-" * 30)
    for improvement in refactor_result.get('improvements', []):
        print(f"- {improvement}")
    
    print("\nEnhanced Code Quality:")
    print("=" * 50)
    
    # Analyze enhanced code quality
    enhanced_analyzer = CodeQualityAnalyzer()
    enhanced_metrics = enhanced_analyzer.analyze_code(enhanced_code, 'python')
    enhanced_overall = enhanced_analyzer.calculate_overall_score(enhanced_metrics)
    
    print(f"Complexity: {enhanced_metrics['complexity']:.1f} (was {original_metrics['complexity']:.1f})")
    print(f"Readability: {enhanced_metrics['readability']:.1f} (was {original_metrics['readability']:.1f})")
    print(f"Maintainability: {enhanced_metrics['maintainability']:.1f} (was {original_metrics['maintainability']:.1f})")
    print(f"Overall Quality: {enhanced_overall:.1f} (was {original_overall:.1f})")
    
    print("\nImprovement Summary:")
    print("=" * 50)
    complexity_improvement = enhanced_metrics['complexity'] - original_metrics['complexity']
    readability_improvement = enhanced_metrics['readability'] - original_metrics['readability']
    maintainability_improvement = enhanced_metrics['maintainability'] - original_metrics['maintainability']
    overall_improvement = enhanced_overall - original_overall
    
    print(f"Complexity: {complexity_improvement:+.1f} points")
    print(f"Readability: {readability_improvement:+.1f} points")
    print(f"Maintainability: {maintainability_improvement:+.1f} points")
    print(f"Overall Quality: {overall_improvement:+.1f} points")

if __name__ == "__main__":
    test_enhanced_refactor()