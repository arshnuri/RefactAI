#!/usr/bin/env python3
"""
Test script for nested if statement detection and refactoring suggestions.
Demonstrates the new capabilities added to CodeQualityAnalyzer.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer

def test_nested_if_detection():
    """Test nested if statement detection across different languages"""
    analyzer = CodeQualityAnalyzer()
    
    # Test files
    test_files = {
        'python': 'test_samples_for_refactoring.py',
        'java': 'TestSamplesForRefactoring.java',
        'javascript': 'test_samples_for_refactoring.js'
    }
    
    results = {}
    
    for language, filename in test_files.items():
        print(f"\n{'='*60}")
        print(f"Testing {language.upper()} - {filename}")
        print(f"{'='*60}")
        
        if not os.path.exists(filename):
            print(f"❌ File {filename} not found")
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Detect nested if statements
            nested_ifs = analyzer.detect_nested_if_statements(code, language)
            
            print(f"\n📊 Analysis Results for {language}:")
            print(f"   • Total nested if patterns found: {len(nested_ifs)}")
            
            if nested_ifs:
                print(f"\n🔍 Detailed Findings:")
                for i, nested_if in enumerate(nested_ifs, 1):
                    print(f"\n   {i}. {nested_if['type'].replace('_', ' ').title()}")
                    print(f"      📍 Lines: {nested_if['line_start']}-{nested_if['line_end']}")
                    print(f"      📏 Nesting depth: {nested_if['depth']}")
                    print(f"      ⚠️  Severity: {nested_if['severity']}")
                    print(f"      💡 Suggestion: {nested_if['suggestion']}")
                
                # Generate refactoring suggestions
                suggestions = analyzer.suggest_refactoring_for_nested_ifs(code, language, nested_ifs)
                
                print(f"\n🛠️  Refactoring Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"\n   {i}. {suggestion['type'].replace('_', ' ').title()}")
                    print(f"      💡 {suggestion['suggestion']}")
                    
                    if 'example' in suggestion:
                        print(f"      📝 Example:")
                        example_lines = suggestion['example'].split('\n')
                        for line in example_lines[:10]:  # Show first 10 lines
                            print(f"         {line}")
                        if len(example_lines) > 10:
                            print(f"         ... (truncated)")
                    
                    print(f"      ✅ Benefits: {', '.join(suggestion['benefits'])}")
            else:
                print(f"   ✅ No deeply nested if statements found (good!)")
            
            results[language] = {
                'file': filename,
                'nested_ifs_count': len(nested_ifs),
                'nested_ifs': nested_ifs,
                'suggestions_count': len(analyzer.suggest_refactoring_for_nested_ifs(code, language, nested_ifs))
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {filename}: {str(e)}")
            results[language] = {'error': str(e)}
    
    return results

def test_specific_nested_code():
    """Test with specific examples of nested if statements"""
    analyzer = CodeQualityAnalyzer()
    
    print(f"\n{'='*60}")
    print(f"Testing Specific Nested If Examples")
    print(f"{'='*60}")
    
    # Python example with deeply nested ifs
    python_nested = '''
def categorize_score(score):
    if score >= 0:
        if score <= 100:
            if score >= 90:
                if score == 100:
                    return "Perfect"
                else:
                    return "Excellent"
            elif score >= 80:
                if score >= 85:
                    return "Very Good"
                else:
                    return "Good"
            elif score >= 70:
                return "Average"
            else:
                if score >= 60:
                    return "Below Average"
                else:
                    return "Poor"
        else:
            return "Invalid score (too high)"
    else:
        return "Invalid score (negative)"
'''
    
    # Java example with deeply nested ifs
    java_nested = '''
public String categorizeScore(int score) {
    if (score >= 0) {
        if (score <= 100) {
            if (score >= 90) {
                if (score == 100) {
                    return "Perfect";
                } else {
                    return "Excellent";
                }
            } else if (score >= 80) {
                if (score >= 85) {
                    return "Very Good";
                } else {
                    return "Good";
                }
            } else if (score >= 70) {
                return "Average";
            } else {
                if (score >= 60) {
                    return "Below Average";
                } else {
                    return "Poor";
                }
            }
        } else {
            return "Invalid score (too high)";
        }
    } else {
        return "Invalid score (negative)";
    }
}
'''
    
    # JavaScript example with deeply nested ifs
    js_nested = '''
function categorizeScore(score) {
    if (score >= 0) {
        if (score <= 100) {
            if (score >= 90) {
                if (score === 100) {
                    return "Perfect";
                } else {
                    return "Excellent";
                }
            } else if (score >= 80) {
                if (score >= 85) {
                    return "Very Good";
                } else {
                    return "Good";
                }
            } else if (score >= 70) {
                return "Average";
            } else {
                if (score >= 60) {
                    return "Below Average";
                } else {
                    return "Poor";
                }
            }
        } else {
            return "Invalid score (too high)";
        }
    } else {
        return "Invalid score (negative)";
    }
}
'''
    
    examples = {
        'python': python_nested,
        'java': java_nested,
        'javascript': js_nested
    }
    
    for language, code in examples.items():
        print(f"\n🔍 Analyzing {language.upper()} nested if example:")
        
        nested_ifs = analyzer.detect_nested_if_statements(code, language)
        print(f"   • Nested if patterns found: {len(nested_ifs)}")
        
        for nested_if in nested_ifs:
            print(f"   • Depth: {nested_if['depth']}, Severity: {nested_if['severity']}")
            print(f"   • Lines: {nested_if['line_start']}-{nested_if['line_end']}")
        
        suggestions = analyzer.suggest_refactoring_for_nested_ifs(code, language, nested_ifs)
        print(f"   • Refactoring suggestions: {len(suggestions)}")
        
        if suggestions:
            print(f"   • Primary suggestion: {suggestions[0]['suggestion']}")

def generate_report(results):
    """Generate a summary report"""
    print(f"\n{'='*60}")
    print(f"NESTED IF DETECTION SUMMARY REPORT")
    print(f"{'='*60}")
    
    total_files = len(results)
    total_nested_ifs = sum(r.get('nested_ifs_count', 0) for r in results.values() if 'error' not in r)
    total_suggestions = sum(r.get('suggestions_count', 0) for r in results.values() if 'error' not in r)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   • Files analyzed: {total_files}")
    print(f"   • Total nested if patterns found: {total_nested_ifs}")
    print(f"   • Total refactoring suggestions generated: {total_suggestions}")
    
    print(f"\n📋 Per-Language Breakdown:")
    for language, result in results.items():
        if 'error' in result:
            print(f"   • {language.upper()}: ❌ Error - {result['error']}")
        else:
            print(f"   • {language.upper()}: {result['nested_ifs_count']} nested patterns, {result['suggestions_count']} suggestions")
    
    # Save detailed results to JSON
    report_file = f"nested_if_detection_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    import time
    
    print("🚀 Starting Nested If Statement Detection Test")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test with existing files
    results = test_nested_if_detection()
    
    # Test with specific examples
    test_specific_nested_code()
    
    # Generate summary report
    generate_report(results)
    
    print(f"\n✅ Testing completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Next steps:")
    print("   1. Review the detected nested if patterns")
    print("   2. Implement the suggested refactoring patterns")
    print("   3. Integrate this detection into the main refactoring engine")
    print("   4. Add automated refactoring for simple cases")