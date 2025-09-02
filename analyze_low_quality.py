#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.models import ProcessedFile
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer

def analyze_quality_issues():
    """Analyze files to understand quality issues and improvement opportunities"""
    
    # Get files with actual content and varying quality scores
    files_with_content = ProcessedFile.objects.filter(
        status='completed'
    ).exclude(
        refactored_content__isnull=True
    ).exclude(
        refactored_content__exact=''
    ).order_by('overall_quality_score')
    
    print("=== CODE QUALITY ANALYSIS ===")
    print(f"Total files with content: {files_with_content.count()}")
    print()
    
    analyzer = CodeQualityAnalyzer()
    
    # Analyze different quality ranges
    quality_ranges = [
        (0, 30, "Very Low Quality"),
        (30, 50, "Low Quality"), 
        (50, 70, "Medium Quality"),
        (70, 85, "Good Quality"),
        (85, 100, "High Quality")
    ]
    
    for min_score, max_score, label in quality_ranges:
        range_files = files_with_content.filter(
            overall_quality_score__gte=min_score,
            overall_quality_score__lt=max_score
        )[:2]  # Get 2 examples from each range
        
        if range_files.exists():
            print(f"\n=== {label} ({min_score}-{max_score}) ===")
            
            for file_obj in range_files:
                print(f"\nFile: {file_obj.original_path}")
                print(f"Overall: {file_obj.overall_quality_score}, Complexity: {file_obj.complexity_score}, Readability: {file_obj.readability_score}, Maintainability: {file_obj.maintainability_score}")
                
                if file_obj.refactored_content:
                    # Analyze the code to identify specific issues
                    code = file_obj.refactored_content
                    lines = code.split('\n')
                    
                    # Identify specific quality issues
                    issues = []
                    
                    # Check line length
                    long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
                    if long_lines:
                        issues.append(f"Long lines ({len(long_lines)} lines > 100 chars): {long_lines[:3]}...")
                    
                    # Check for comments
                    comment_lines = sum(1 for line in lines if line.strip().startswith('#') or '//' in line)
                    total_lines = len([line for line in lines if line.strip()])
                    if total_lines > 0:
                        comment_ratio = comment_lines / total_lines
                        if comment_ratio < 0.1:
                            issues.append(f"Low comment ratio: {comment_ratio:.1%}")
                    
                    # Check complexity indicators
                    complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', 'try']
                    complexity_count = sum(code.lower().count(keyword) for keyword in complexity_keywords)
                    if complexity_count > 20:
                        issues.append(f"High complexity: {complexity_count} control structures")
                    
                    # Check function length (for Python)
                    if file_obj.original_path.endswith('.py'):
                        try:
                            import ast
                            tree = ast.parse(code)
                            long_functions = []
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    if hasattr(node, 'end_lineno'):
                                        func_length = node.end_lineno - node.lineno
                                        if func_length > 30:
                                            long_functions.append(f"{node.name}({func_length} lines)")
                            if long_functions:
                                issues.append(f"Long functions: {', '.join(long_functions[:3])}")
                        except:
                            pass
                    
                    # Check for code smells
                    if 'TODO' in code or 'FIXME' in code:
                        issues.append("Contains TODO/FIXME comments")
                    
                    if code.count('\n\n\n') > 0:
                        issues.append("Multiple consecutive blank lines")
                    
                    print(f"Code length: {len(lines)} lines")
                    if issues:
                        print("Quality Issues:")
                        for issue in issues:
                            print(f"  - {issue}")
                    else:
                        print("No obvious quality issues detected")
                    
                    # Show a small code sample
                    print("\nCode sample (first 10 lines):")
                    for i, line in enumerate(lines[:10], 1):
                        print(f"{i:2d}: {line}")
                    
                    if len(lines) > 10:
                        print(f"... ({len(lines) - 10} more lines)")
    
    # Summary of improvement opportunities
    print("\n" + "=" * 60)
    print("=== IMPROVEMENT OPPORTUNITIES ===")
    
    # Count files by quality issues
    low_quality_count = files_with_content.filter(overall_quality_score__lt=50).count()
    medium_quality_count = files_with_content.filter(
        overall_quality_score__gte=50, 
        overall_quality_score__lt=70
    ).count()
    
    print(f"Files needing improvement: {low_quality_count + medium_quality_count}")
    print(f"- Low quality (< 50): {low_quality_count}")
    print(f"- Medium quality (50-70): {medium_quality_count}")
    
    # Analyze common issues across all files
    total_files = files_with_content.count()
    low_complexity = files_with_content.filter(complexity_score__lt=50).count()
    low_readability = files_with_content.filter(readability_score__lt=50).count()
    low_maintainability = files_with_content.filter(maintainability_score__lt=50).count()
    
    print(f"\nCommon issues across {total_files} files:")
    print(f"- Low complexity scores: {low_complexity} files ({low_complexity/total_files:.1%})")
    print(f"- Low readability scores: {low_readability} files ({low_readability/total_files:.1%})")
    print(f"- Low maintainability scores: {low_maintainability} files ({low_maintainability/total_files:.1%})")

if __name__ == '__main__':
    analyze_quality_issues()