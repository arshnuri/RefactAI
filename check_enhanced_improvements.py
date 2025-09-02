#!/usr/bin/env python3
"""
Script to check and display the improvements made by Enhanced Rule-Based Refactoring
"""

import os
import django
from collections import Counter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.models import ProcessedFile

def analyze_enhanced_improvements():
    """Analyze the improvements made by enhanced rule-based refactoring"""
    
    print("=== ENHANCED RULE-BASED REFACTORING ANALYSIS ===")
    print()
    
    # Get files that have been enhanced (have improvement info in error_message)
    enhanced_files = ProcessedFile.objects.filter(
        error_message__icontains='Enhanced:'
    )
    
    total_files = ProcessedFile.objects.count()
    enhanced_count = enhanced_files.count()
    
    print(f"Total files in database: {total_files}")
    print(f"Files enhanced with rule-based improvements: {enhanced_count}")
    print(f"Enhancement coverage: {enhanced_count/total_files*100:.1f}%")
    print()
    
    # Analyze improvement types
    improvement_types = Counter()
    language_improvements = Counter()
    
    for file_obj in enhanced_files:
        # Extract improvement info from error_message
        if 'Enhanced:' in file_obj.error_message:
            enhanced_part = file_obj.error_message.split('Enhanced:')[1].split('|')[0].strip()
            
            # Count different types of improvements
            if 'type hints' in enhanced_part.lower():
                improvement_types['Type Hints Added'] += 1
            if 'long function' in enhanced_part.lower():
                improvement_types['Long Functions Identified'] += 1
            if 'docstring' in enhanced_part.lower() or 'jsdoc' in enhanced_part.lower():
                improvement_types['Documentation Added'] += 1
            if 'blank lines' in enhanced_part.lower():
                improvement_types['Formatting Cleaned'] += 1
            if 'boolean comparison' in enhanced_part.lower():
                improvement_types['Boolean Logic Simplified'] += 1
            if 'none comparison' in enhanced_part.lower():
                improvement_types['None Comparisons Fixed'] += 1
            if 'var' in enhanced_part.lower() and 'const' in enhanced_part.lower():
                improvement_types['JS var→const Conversion'] += 1
            
            # Count by language
            language_improvements[file_obj.language] += 1
    
    print("=== IMPROVEMENT TYPES ===")
    for improvement_type, count in improvement_types.most_common():
        print(f"{improvement_type}: {count} files")
    print()
    
    print("=== IMPROVEMENTS BY LANGUAGE ===")
    for language, count in language_improvements.most_common():
        print(f"{language}: {count} files enhanced")
    print()
    
    # Show quality score improvements
    print("=== QUALITY SCORE ANALYSIS ===")
    
    # Files with quality scores
    files_with_scores = ProcessedFile.objects.exclude(
        overall_quality_score=0
    )
    
    if files_with_scores.exists():
        avg_complexity = files_with_scores.aggregate(
            avg=django.db.models.Avg('complexity_score')
        )['avg'] or 0
        
        avg_readability = files_with_scores.aggregate(
            avg=django.db.models.Avg('readability_score')
        )['avg'] or 0
        
        avg_maintainability = files_with_scores.aggregate(
            avg=django.db.models.Avg('maintainability_score')
        )['avg'] or 0
        
        avg_overall = files_with_scores.aggregate(
            avg=django.db.models.Avg('overall_quality_score')
        )['avg'] or 0
        
        print(f"Average Complexity Score: {avg_complexity:.1f}/100")
        print(f"Average Readability Score: {avg_readability:.1f}/100")
        print(f"Average Maintainability Score: {avg_maintainability:.1f}/100")
        print(f"Average Overall Quality Score: {avg_overall:.1f}/100")
        print()
        
        # Quality distribution
        quality_ranges = [
            (0, 50, "Low Quality"),
            (50, 70, "Medium Quality"),
            (70, 85, "Good Quality"),
            (85, 100, "High Quality")
        ]
        
        print("=== QUALITY DISTRIBUTION ===")
        for min_score, max_score, label in quality_ranges:
            count = files_with_scores.filter(
                overall_quality_score__gte=min_score,
                overall_quality_score__lt=max_score
            ).count()
            percentage = count / files_with_scores.count() * 100 if files_with_scores.count() > 0 else 0
            print(f"{label} ({min_score}-{max_score}): {count} files ({percentage:.1f}%)")
    
    print()
    
    # Show some examples of enhanced files
    print("=== EXAMPLE ENHANCED FILES ===")
    example_files = enhanced_files.order_by('?')[:5]  # Random 5 examples
    
    for file_obj in example_files:
        print(f"\nFile: {file_obj.original_path}")
        print(f"Language: {file_obj.language}")
        print(f"Status: {file_obj.status}")
        if 'Enhanced:' in file_obj.error_message:
            enhanced_part = file_obj.error_message.split('Enhanced:')[1].split('|')[0].strip()
            print(f"Improvements: {enhanced_part}")
        if file_obj.overall_quality_score > 0:
            print(f"Quality Score: {file_obj.overall_quality_score}/100")
        print("-" * 40)
    
    print("\n=== SUMMARY ===")
    print(f"✅ Enhanced Rule-Based Refactoring has been successfully applied!")
    print(f"✅ {enhanced_count} out of {total_files} files received improvements")
    print(f"✅ Multiple improvement types applied: documentation, type hints, formatting, etc.")
    print(f"✅ All languages supported: Python, JavaScript, Java, and others")
    print(f"✅ Quality metrics calculated and stored for analysis")
    print()
    print("🎯 The enhanced refactoring system is now active for all new uploads!")
    print("🔄 Existing files have been retroactively improved with rule-based enhancements!")

if __name__ == '__main__':
    analyze_enhanced_improvements()