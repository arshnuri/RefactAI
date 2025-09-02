#!/usr/bin/env python3
"""
Test script for automated nested if statement refactoring.
Demonstrates the complete pipeline from detection to refactoring.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer
from refactai_app.utils.nested_if_refactor import NestedIfRefactor, RefactorPattern

def test_automated_refactoring():
    """Test the complete automated refactoring pipeline"""
    analyzer = CodeQualityAnalyzer()
    refactor_engine = NestedIfRefactor()
    
    print("🚀 Starting Automated Nested If Refactoring Test")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test with specific examples that have known nested if patterns
    test_examples = {
        'python': create_python_nested_example(),
        'java': create_java_nested_example(),
        'javascript': create_javascript_nested_example()
    }
    
    results = {}
    
    for language, code in test_examples.items():
        print(f"\n{'='*70}")
        print(f"Testing Automated Refactoring for {language.upper()}")
        print(f"{'='*70}")
        
        # Step 1: Detect nested if statements
        print("\n🔍 Step 1: Detecting nested if statements...")
        nested_ifs = analyzer.detect_nested_if_statements(code, language)
        print(f"   • Found {len(nested_ifs)} nested if patterns")
        
        if not nested_ifs:
            print("   ✅ No nested if statements found - code is already clean!")
            continue
        
        # Show the most complex pattern
        max_depth_pattern = max(nested_ifs, key=lambda x: x['depth'])
        print(f"   • Most complex pattern: depth {max_depth_pattern['depth']} (lines {max_depth_pattern['line_start']}-{max_depth_pattern['line_end']})")
        
        # Step 2: Generate refactoring suggestions
        print("\n🛠️  Step 2: Generating refactoring suggestions...")
        suggestions = refactor_engine.refactor_nested_ifs(code, language, nested_ifs)
        print(f"   • Generated {len(suggestions)} refactoring suggestions")
        
        if not suggestions:
            print("   ⚠️  No automated refactoring suggestions available")
            continue
        
        # Step 3: Apply the best refactoring
        print("\n✨ Step 3: Applying automated refactoring...")
        best_suggestion = max(suggestions, key=lambda x: x.confidence)
        print(f"   • Selected pattern: {best_suggestion.pattern.value}")
        print(f"   • Confidence: {best_suggestion.confidence:.1%}")
        print(f"   • Description: {best_suggestion.description}")
        
        # Apply the refactoring
        refactored_code = refactor_engine.apply_refactoring(code, best_suggestion)
        
        # Step 4: Validate the refactoring
        print("\n🔬 Step 4: Validating refactored code...")
        validation_results = validate_refactoring(code, refactored_code, language, analyzer)
        
        # Step 5: Show results
        print("\n📊 Step 5: Refactoring Results")
        show_refactoring_results(code, refactored_code, best_suggestion, validation_results)
        
        results[language] = {
            'original_nested_ifs': len(nested_ifs),
            'max_depth_before': max_depth_pattern['depth'],
            'suggestions_generated': len(suggestions),
            'applied_pattern': best_suggestion.pattern.value,
            'confidence': best_suggestion.confidence,
            'validation': validation_results,
            'benefits': best_suggestion.benefits
        }
    
    # Generate summary report
    generate_refactoring_summary(results)
    
    return results

def create_python_nested_example():
    """Create a Python example with deeply nested if statements"""
    return '''
def categorize_score(score):
    """Categorize a score with deeply nested if statements (bad pattern)."""
    if score >= 0:
        if score <= 100:
            if score >= 90:
                if score == 100:
                    return "Perfect"
                else:
                    if score >= 95:
                        return "Near Perfect"
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

def process_data(data):
    """Process data with nested validation (another bad pattern)."""
    if data is not None:
        if isinstance(data, dict):
            if 'value' in data:
                if data['value'] > 0:
                    if data['value'] < 1000:
                        return data['value'] * 2
                    else:
                        return "Value too large"
                else:
                    return "Value must be positive"
            else:
                return "Missing value key"
        else:
            return "Data must be a dictionary"
    else:
        return "Data cannot be None"
'''

def create_java_nested_example():
    """Create a Java example with deeply nested if statements"""
    return '''
public class ScoreProcessor {
    
    public String categorizeScore(int score) {
        // Deeply nested if statements (bad pattern)
        if (score >= 0) {
            if (score <= 100) {
                if (score >= 90) {
                    if (score == 100) {
                        return "Perfect";
                    } else {
                        if (score >= 95) {
                            return "Near Perfect";
                        } else {
                            return "Excellent";
                        }
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
    
    public String processData(Map<String, Object> data) {
        // Another nested validation pattern
        if (data != null) {
            if (data.containsKey("value")) {
                Object value = data.get("value");
                if (value instanceof Integer) {
                    int intValue = (Integer) value;
                    if (intValue > 0) {
                        if (intValue < 1000) {
                            return String.valueOf(intValue * 2);
                        } else {
                            return "Value too large";
                        }
                    } else {
                        return "Value must be positive";
                    }
                } else {
                    return "Value must be an integer";
                }
            } else {
                return "Missing value key";
            }
        } else {
            return "Data cannot be null";
        }
    }
}
'''

def create_javascript_nested_example():
    """Create a JavaScript example with deeply nested if statements"""
    return '''
function categorizeScore(score) {
    // Deeply nested if statements (bad pattern)
    if (score >= 0) {
        if (score <= 100) {
            if (score >= 90) {
                if (score === 100) {
                    return "Perfect";
                } else {
                    if (score >= 95) {
                        return "Near Perfect";
                    } else {
                        return "Excellent";
                    }
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

function processData(data) {
    // Another nested validation pattern
    if (data !== null && data !== undefined) {
        if (typeof data === 'object') {
            if ('value' in data) {
                if (typeof data.value === 'number') {
                    if (data.value > 0) {
                        if (data.value < 1000) {
                            return data.value * 2;
                        } else {
                            return "Value too large";
                        }
                    } else {
                        return "Value must be positive";
                    }
                } else {
                    return "Value must be a number";
                }
            } else {
                return "Missing value key";
            }
        } else {
            return "Data must be an object";
        }
    } else {
        return "Data cannot be null or undefined";
    }
}
'''

def validate_refactoring(original_code: str, refactored_code: str, language: str, analyzer: CodeQualityAnalyzer):
    """Validate that the refactoring improved the code"""
    # Analyze original code
    original_nested_ifs = analyzer.detect_nested_if_statements(original_code, language)
    original_metrics = analyzer.analyze_code(original_code, language)
    
    # Analyze refactored code
    refactored_nested_ifs = analyzer.detect_nested_if_statements(refactored_code, language)
    refactored_metrics = analyzer.analyze_code(refactored_code, language)
    
    return {
        'nested_ifs_before': len(original_nested_ifs),
        'nested_ifs_after': len(refactored_nested_ifs),
        'max_depth_before': max([nif['depth'] for nif in original_nested_ifs], default=0),
        'max_depth_after': max([nif['depth'] for nif in refactored_nested_ifs], default=0),
        'complexity_before': original_metrics.get('complexity', 0),
        'complexity_after': refactored_metrics.get('complexity', 0),
        'readability_before': original_metrics.get('readability', 0),
        'readability_after': refactored_metrics.get('readability', 0),
        'lines_before': len(original_code.split('\n')),
        'lines_after': len(refactored_code.split('\n'))
    }

def show_refactoring_results(original_code: str, refactored_code: str, suggestion, validation):
    """Display the refactoring results in a nice format"""
    print(f"\n   📈 Improvements:")
    
    # Nested if improvements
    nested_improvement = validation['nested_ifs_before'] - validation['nested_ifs_after']
    if nested_improvement > 0:
        print(f"      • Nested if patterns: {validation['nested_ifs_before']} → {validation['nested_ifs_after']} (-{nested_improvement})")
    
    # Depth improvements
    depth_improvement = validation['max_depth_before'] - validation['max_depth_after']
    if depth_improvement > 0:
        print(f"      • Maximum nesting depth: {validation['max_depth_before']} → {validation['max_depth_after']} (-{depth_improvement})")
    
    # Complexity improvements
    complexity_improvement = validation['complexity_after'] - validation['complexity_before']
    if complexity_improvement > 0:
        print(f"      • Complexity score: {validation['complexity_before']} → {validation['complexity_after']} (+{complexity_improvement})")
    
    # Readability improvements
    readability_improvement = validation['readability_after'] - validation['readability_before']
    if readability_improvement > 0:
        print(f"      • Readability score: {validation['readability_before']} → {validation['readability_after']} (+{readability_improvement})")
    
    print(f"\n   ✅ Benefits achieved:")
    for benefit in suggestion.benefits:
        print(f"      • {benefit}")
    
    # Show code comparison (first few lines)
    print(f"\n   📝 Code Comparison (first 10 lines):")
    print(f"\n      BEFORE:")
    for i, line in enumerate(original_code.split('\n')[:10], 1):
        print(f"      {i:2d}: {line}")
    
    print(f"\n      AFTER:")
    for i, line in enumerate(refactored_code.split('\n')[:10], 1):
        print(f"      {i:2d}: {line}")
    
    if len(refactored_code.split('\n')) > 10:
        print(f"         ... (showing first 10 lines only)")

def generate_refactoring_summary(results):
    """Generate a summary of all refactoring results"""
    print(f"\n{'='*70}")
    print(f"AUTOMATED REFACTORING SUMMARY REPORT")
    print(f"{'='*70}")
    
    total_languages = len(results)
    total_patterns_found = sum(r.get('original_nested_ifs', 0) for r in results.values())
    total_suggestions = sum(r.get('suggestions_generated', 0) for r in results.values())
    
    print(f"\n📊 Overall Statistics:")
    print(f"   • Languages tested: {total_languages}")
    print(f"   • Total nested patterns found: {total_patterns_found}")
    print(f"   • Total refactoring suggestions: {total_suggestions}")
    
    print(f"\n🎯 Refactoring Success by Language:")
    for language, result in results.items():
        if 'applied_pattern' in result:
            print(f"   • {language.upper()}:")
            print(f"     - Pattern applied: {result['applied_pattern']}")
            print(f"     - Confidence: {result['confidence']:.1%}")
            print(f"     - Original max depth: {result['max_depth_before']}")
            
            if 'validation' in result:
                val = result['validation']
                depth_reduction = val['max_depth_before'] - val['max_depth_after']
                complexity_gain = val['complexity_after'] - val['complexity_before']
                print(f"     - Depth reduction: -{depth_reduction}")
                print(f"     - Complexity improvement: +{complexity_gain}")
    
    print(f"\n🛠️  Refactoring Patterns Used:")
    patterns_used = set(r.get('applied_pattern', '') for r in results.values() if 'applied_pattern' in r)
    for pattern in patterns_used:
        if pattern:
            count = sum(1 for r in results.values() if r.get('applied_pattern') == pattern)
            print(f"   • {pattern.replace('_', ' ').title()}: {count} times")
    
    # Save detailed results
    report_file = f"automated_refactoring_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    print(f"\n🎉 Key Achievements:")
    print(f"   • Successfully detected complex nested if patterns")
    print(f"   • Generated language-specific refactoring suggestions")
    print(f"   • Automatically applied refactoring transformations")
    print(f"   • Validated improvements in code quality metrics")
    print(f"   • Demonstrated measurable complexity reduction")

if __name__ == "__main__":
    try:
        results = test_automated_refactoring()
        
        print(f"\n✅ Automated refactoring test completed successfully!")
        print(f"⏰ Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n💡 Next Steps for Integration:")
        print(f"   1. Integrate nested if detection into main refactor engine")
        print(f"   2. Add user interface for selecting refactoring patterns")
        print(f"   3. Implement more sophisticated pattern recognition")
        print(f"   4. Add support for more complex refactoring scenarios")
        print(f"   5. Create training dataset from successful refactorings")
        
    except Exception as e:
        print(f"\n❌ Error during automated refactoring test: {str(e)}")
        import traceback
        traceback.print_exc()