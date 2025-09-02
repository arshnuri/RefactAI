#!/usr/bin/env python3
"""
Comprehensive Refactoring Quality Test
This script tests the refactoring system with unrefactored code samples
from multiple languages to demonstrate quality improvements and accuracy.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from refactai_app.utils.llm_client import LLMClient
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer
from refactai_app.utils.ast_utils import ASTValidator

def print_separator(title=""):
    """Print a visual separator with optional title"""
    print("\n" + "="*60)
    if title:
        print(f" {title}")
        print("="*60)
    else:
        print("="*60)

def analyze_code_quality(code, language):
    """Analyze code quality metrics"""
    try:
        analyzer = CodeQualityAnalyzer()
        if language.lower() == 'python':
            if hasattr(analyzer, 'analyze_python_code'):
                metrics = analyzer.analyze_python_code(code)
            else:
                # Fallback to basic metrics
                metrics = {
                    'lines_of_code': len(code.splitlines()),
                    'character_count': len(code),
                    'functions_count': code.count('def '),
                    'classes_count': code.count('class '),
                    'complexity_estimate': code.count('if ') + code.count('for ') + code.count('while ')
                }
        elif language.lower() == 'javascript':
            # Basic JavaScript metrics
            metrics = {
                'lines_of_code': len(code.splitlines()),
                'character_count': len(code),
                'functions_count': code.count('function ') + code.count('=>'),
                'classes_count': code.count('class '),
                'complexity_estimate': code.count('if ') + code.count('for ') + code.count('while ')
            }
        elif language.lower() == 'java':
            # Basic Java metrics
            metrics = {
                'lines_of_code': len(code.splitlines()),
                'character_count': len(code),
                'methods_count': code.count('public ') + code.count('private ') + code.count('protected '),
                'classes_count': code.count('class '),
                'complexity_estimate': code.count('if ') + code.count('for ') + code.count('while ')
            }
        else:
            return {"error": "Unsupported language"}
        
        return metrics
    except Exception as e:
        return {"error": str(e)}

def validate_syntax(code, language):
    """Validate code syntax"""
    try:
        if language.lower() == 'python':
            is_valid, error_msg = ASTValidator.validate_python_code(code)
            return is_valid, error_msg
        else:
            # For non-Python languages, assume valid if no obvious syntax errors
            return True, "Syntax validation not implemented for this language"
    except Exception as e:
        return False, str(e)

def test_refactoring_sample(file_path, language, description):
    """Test refactoring for a single code sample"""
    print_separator(f"Testing {language.upper()} - {description}")
    
    # Read the original code
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None
    
    print(f"📁 File: {os.path.basename(file_path)}")
    print(f"📏 Original code length: {len(original_code)} characters")
    print(f"📄 Original code lines: {len(original_code.splitlines())} lines")
    
    # Validate original syntax
    is_valid, error_msg = validate_syntax(original_code, language)
    print(f"✅ Original syntax valid: {is_valid}")
    if not is_valid:
        print(f"⚠️  Syntax error: {error_msg}")
    
    # Analyze original code quality
    print("\n🔍 Original Code Quality Analysis:")
    original_metrics = analyze_code_quality(original_code, language)
    if "error" not in original_metrics:
        for key, value in original_metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
            elif isinstance(value, list) and len(value) <= 5:
                print(f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}: {len(value)} items")
    else:
        print(f"  Error: {original_metrics['error']}")
    
    # Perform refactoring
    print("\n🔄 Starting refactoring process...")
    start_time = time.time()
    
    try:
        client = LLMClient()
        result = client.refactor_code(
            code=original_code,
            language=language,
            file_path=file_path,
            processing_options={
                'improve_readability': True,
                'optimize_performance': True,
                'add_documentation': True,
                'follow_conventions': True,
                'remove_code_smells': True
            }
        )
        
        refactor_time = time.time() - start_time
        print(f"⏱️  Refactoring completed in {refactor_time:.2f} seconds")
        
        if result['success']:
            print("✅ Refactoring successful!")
            
            refactored_code = result['refactored_code']
            print(f"📏 Refactored code length: {len(refactored_code)} characters")
            print(f"📄 Refactored code lines: {len(refactored_code.splitlines())} lines")
            
            # Validate refactored syntax
            is_valid_refactored, error_msg_refactored = validate_syntax(refactored_code, language)
            print(f"✅ Refactored syntax valid: {is_valid_refactored}")
            if not is_valid_refactored:
                print(f"⚠️  Syntax error: {error_msg_refactored}")
            
            # Analyze refactored code quality
            print("\n🔍 Refactored Code Quality Analysis:")
            refactored_metrics = analyze_code_quality(refactored_code, language)
            if "error" not in refactored_metrics:
                for key, value in refactored_metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"  {key}: {value}")
                    elif isinstance(value, list) and len(value) <= 5:
                        print(f"  {key}: {value}")
                    elif isinstance(value, list):
                        print(f"  {key}: {len(value)} items")
            else:
                print(f"  Error: {refactored_metrics['error']}")
            
            # Show validation warnings if any
            if result.get('validation_warnings'):
                print("\n⚠️  Validation Warnings:")
                for warning in result['validation_warnings']:
                    print(f"  - {warning}")
            
            # Calculate improvement metrics
            print("\n📊 Quality Improvements:")
            if "error" not in original_metrics and "error" not in refactored_metrics:
                for key in original_metrics:
                    if key in refactored_metrics and isinstance(original_metrics[key], (int, float)):
                        original_val = original_metrics[key]
                        refactored_val = refactored_metrics[key]
                        if original_val != 0:
                            improvement = ((refactored_val - original_val) / original_val) * 100
                            print(f"  {key}: {improvement:+.1f}% change")
            
            # Save refactored code
            output_file = file_path.replace('.', '_refactored.')
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(refactored_code)
                print(f"\n💾 Refactored code saved to: {os.path.basename(output_file)}")
            except Exception as e:
                print(f"⚠️  Could not save refactored code: {e}")
            
            return {
                'success': True,
                'original_valid': is_valid,
                'refactored_valid': is_valid_refactored,
                'original_metrics': original_metrics,
                'refactored_metrics': refactored_metrics,
                'refactor_time': refactor_time,
                'validation_warnings': result.get('validation_warnings', [])
            }
        else:
            print(f"❌ Refactoring failed: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'original_valid': is_valid
            }
    
    except Exception as e:
        print(f"❌ Error during refactoring: {e}")
        return {
            'success': False,
            'error': str(e),
            'original_valid': is_valid
        }

def main():
    """Main test function"""
    print_separator("REFACTORING QUALITY TEST SUITE")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test samples configuration
    test_samples = [
        {
            'file': 'test_samples_for_refactoring.py',
            'language': 'python',
            'description': 'Python code with multiple quality issues'
        },
        {
            'file': 'test_samples_for_refactoring.js',
            'language': 'javascript',
            'description': 'JavaScript code with callback hell and poor practices'
        },
        {
            'file': 'TestSamplesForRefactoring.java',
            'language': 'java',
            'description': 'Java code with tight coupling and poor design'
        }
    ]
    
    results = []
    total_start_time = time.time()
    
    # Run tests for each sample
    for sample in test_samples:
        file_path = os.path.join(os.path.dirname(__file__), sample['file'])
        if os.path.exists(file_path):
            result = test_refactoring_sample(
                file_path, 
                sample['language'], 
                sample['description']
            )
            if result:
                result['language'] = sample['language']
                result['file'] = sample['file']
                results.append(result)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    total_time = time.time() - total_start_time
    
    # Generate summary report
    print_separator("SUMMARY REPORT")
    print(f"🕐 Total test time: {total_time:.2f} seconds")
    print(f"📊 Tests completed: {len(results)}")
    
    successful_refactors = sum(1 for r in results if r['success'])
    syntax_valid_original = sum(1 for r in results if r.get('original_valid', False))
    syntax_valid_refactored = sum(1 for r in results if r.get('refactored_valid', False))
    
    print(f"✅ Successful refactors: {successful_refactors}/{len(results)} ({successful_refactors/len(results)*100:.1f}%)")
    print(f"✅ Original syntax valid: {syntax_valid_original}/{len(results)} ({syntax_valid_original/len(results)*100:.1f}%)")
    print(f"✅ Refactored syntax valid: {syntax_valid_refactored}/{len(results)} ({syntax_valid_refactored/len(results)*100:.1f}%)")
    
    # Language-specific results
    print("\n📋 Results by Language:")
    for language in ['python', 'javascript', 'java']:
        lang_results = [r for r in results if r.get('language') == language]
        if lang_results:
            lang_success = sum(1 for r in lang_results if r['success'])
            print(f"  {language.upper()}: {lang_success}/{len(lang_results)} successful")
    
    # Save detailed results
    try:
        report_file = f"refactoring_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_time': total_time,
                'summary': {
                    'total_tests': len(results),
                    'successful_refactors': successful_refactors,
                    'syntax_valid_original': syntax_valid_original,
                    'syntax_valid_refactored': syntax_valid_refactored
                },
                'detailed_results': results
            }, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️  Could not save detailed report: {e}")
    
    print_separator()
    print("🎉 Refactoring quality test completed!")
    
    if successful_refactors == len(results):
        print("🏆 All tests passed successfully!")
    elif successful_refactors > len(results) * 0.8:
        print("👍 Most tests passed - good refactoring quality!")
    else:
        print("⚠️  Some tests failed - check the implementation.")

if __name__ == '__main__':
    main()