#!/usr/bin/env python3
"""
Refactoring Accuracy Analysis Tool
Analyzes refactoring accuracy metrics from the database
"""

import os
import sys
import django
import argparse
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refactai_project.settings')
django.setup()

from refactai_app.models import RefactorSession, ProcessedFile

def calculate_accuracy_metrics(start_date=None, end_date=None, verbose=False):
    """
    Calculate comprehensive refactoring accuracy metrics
    """
    # Filter sessions by date range
    sessions_query = RefactorSession.objects.all()
    if start_date:
        sessions_query = sessions_query.filter(created_at__gte=start_date)
    if end_date:
        sessions_query = sessions_query.filter(created_at__lte=end_date)
    
    sessions = list(sessions_query.order_by('-created_at'))
    
    if not sessions:
        print("No refactoring sessions found in the specified date range.")
        return None
    
    # Initialize metrics
    metrics = {
        'total_sessions': len(sessions),
        'successful_sessions': 0,
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'files_with_improvements': 0,
        'language_stats': defaultdict(lambda: {'total': 0, 'successful': 0, 'avg_quality': {'complexity': 0, 'readability': 0, 'maintainability': 0}}),
        'error_patterns': defaultdict(int),
        'quality_improvements': {'complexity': [], 'readability': [], 'maintainability': []}
    }
    
    # Analyze sessions
    for session in sessions:
        if session.status == 'completed':
            metrics['successful_sessions'] += 1
        
        # Analyze files in this session
        files = ProcessedFile.objects.filter(session=session)
        for file in files:
            metrics['total_files'] += 1
            
            # Language statistics
            lang = file.language or 'unknown'
            metrics['language_stats'][lang]['total'] += 1
            
            if file.status == 'completed':
                metrics['successful_files'] += 1
                metrics['language_stats'][lang]['successful'] += 1
                
                # Quality metrics analysis
                if file.complexity_score and file.readability_score and file.maintainability_score:
                    # Check for quality improvements (scores > baseline)
                    complexity_improved = file.complexity_score > 65  # New baseline
                    readability_improved = file.readability_score > 50
                    maintainability_improved = file.maintainability_score > 50
                    
                    if complexity_improved or readability_improved or maintainability_improved:
                        metrics['files_with_improvements'] += 1
                    
                    # Collect quality scores for language averages
                    lang_stats = metrics['language_stats'][lang]
                    lang_stats['avg_quality']['complexity'] += file.complexity_score
                    lang_stats['avg_quality']['readability'] += file.readability_score
                    lang_stats['avg_quality']['maintainability'] += file.maintainability_score
                    
                    # Store individual improvements
                    metrics['quality_improvements']['complexity'].append(file.complexity_score)
                    metrics['quality_improvements']['readability'].append(file.readability_score)
                    metrics['quality_improvements']['maintainability'].append(file.maintainability_score)
            
            elif file.status == 'failed':
                metrics['failed_files'] += 1
                # Analyze error patterns
                if file.error_message:
                    if 'syntax' in file.error_message.lower():
                        metrics['error_patterns']['syntax_errors'] += 1
                    elif 'timeout' in file.error_message.lower():
                        metrics['error_patterns']['timeout_errors'] += 1
                    else:
                        metrics['error_patterns']['other_errors'] += 1
    
    # Calculate averages for language statistics
    for lang, stats in metrics['language_stats'].items():
        if stats['successful'] > 0:
            stats['avg_quality']['complexity'] /= stats['successful']
            stats['avg_quality']['readability'] /= stats['successful']
            stats['avg_quality']['maintainability'] /= stats['successful']
    
    # Calculate final accuracy metrics
    session_success_rate = (metrics['successful_sessions'] / metrics['total_sessions']) * 100 if metrics['total_sessions'] > 0 else 0
    file_success_rate = (metrics['successful_files'] / metrics['total_files']) * 100 if metrics['total_files'] > 0 else 0
    true_accuracy = (metrics['files_with_improvements'] / metrics['total_files']) * 100 if metrics['total_files'] > 0 else 0
    
    # Calculate average quality scores
    avg_complexity = sum(metrics['quality_improvements']['complexity']) / len(metrics['quality_improvements']['complexity']) if metrics['quality_improvements']['complexity'] else 0
    avg_readability = sum(metrics['quality_improvements']['readability']) / len(metrics['quality_improvements']['readability']) if metrics['quality_improvements']['readability'] else 0
    avg_maintainability = sum(metrics['quality_improvements']['maintainability']) / len(metrics['quality_improvements']['maintainability']) if metrics['quality_improvements']['maintainability'] else 0
    
    results = {
        'analysis_period': {
            'start_date': start_date.isoformat() if start_date else 'N/A',
            'end_date': end_date.isoformat() if end_date else 'N/A',
            'total_sessions': metrics['total_sessions'],
            'total_files': metrics['total_files']
        },
        'accuracy_metrics': {
            'session_success_rate': round(session_success_rate, 2),
            'file_success_rate': round(file_success_rate, 2),
            'true_accuracy': round(true_accuracy, 2),
            'files_with_improvements': metrics['files_with_improvements']
        },
        'quality_scores': {
            'average_complexity': round(avg_complexity, 1),
            'average_readability': round(avg_readability, 1),
            'average_maintainability': round(avg_maintainability, 1)
        },
        'language_breakdown': dict(metrics['language_stats']),
        'error_analysis': dict(metrics['error_patterns']),
        'recommendations': generate_recommendations(metrics, true_accuracy)
    }
    
    if verbose:
        print_detailed_results(results)
    else:
        print_summary_results(results)
    
    return results

def generate_recommendations(metrics, true_accuracy):
    """
    Generate recommendations based on analysis results
    """
    recommendations = []
    
    if true_accuracy < 85:
        recommendations.append("Consider further improving complexity scoring algorithms")
    
    if metrics['error_patterns'].get('syntax_errors', 0) > 0:
        recommendations.append("Implement better syntax error handling and validation")
    
    # Check for languages with low success rates
    for lang, stats in metrics['language_stats'].items():
        success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
        if success_rate < 80 and stats['total'] > 5:
            recommendations.append(f"Improve {lang} language support (current success rate: {success_rate:.1f}%)")
    
    if not recommendations:
        recommendations.append("Accuracy metrics are performing well - continue monitoring")
    
    return recommendations

def print_summary_results(results):
    """
    Print summary of accuracy analysis
    """
    print("\n=== REFACTORING ACCURACY ANALYSIS ===")
    print(f"Analysis Period: {results['analysis_period']['start_date']} to {results['analysis_period']['end_date']}")
    print(f"Total Sessions: {results['analysis_period']['total_sessions']}")
    print(f"Total Files: {results['analysis_period']['total_files']}")
    print("\n=== ACCURACY METRICS ===")
    print(f"Session Success Rate: {results['accuracy_metrics']['session_success_rate']}%")
    print(f"File Success Rate: {results['accuracy_metrics']['file_success_rate']}%")
    print(f"True Accuracy: {results['accuracy_metrics']['true_accuracy']}%")
    print(f"Files with Improvements: {results['accuracy_metrics']['files_with_improvements']}")
    print("\n=== QUALITY SCORES ===")
    print(f"Average Complexity: {results['quality_scores']['average_complexity']}")
    print(f"Average Readability: {results['quality_scores']['average_readability']}")
    print(f"Average Maintainability: {results['quality_scores']['average_maintainability']}")
    print("\n=== RECOMMENDATIONS ===")
    for rec in results['recommendations']:
        print(f"• {rec}")

def print_detailed_results(results):
    """
    Print detailed accuracy analysis
    """
    print_summary_results(results)
    
    print("\n=== LANGUAGE BREAKDOWN ===")
    for lang, stats in results['language_breakdown'].items():
        success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{lang.upper()}:")
        print(f"  Files: {stats['total']} (Success: {success_rate:.2f}%)")
        if stats['successful'] > 0:
            print(f"  Avg Quality - Complexity: {stats['avg_quality']['complexity']:.1f}, "
                  f"Readability: {stats['avg_quality']['readability']:.1f}, "
                  f"Maintainability: {stats['avg_quality']['maintainability']:.1f}")
    
    if results['error_analysis']:
        print("\n=== ERROR ANALYSIS ===")
        total_errors = sum(results['error_analysis'].values())
        for error_type, count in results['error_analysis'].items():
            percentage = (count / total_errors) * 100 if total_errors > 0 else 0
            print(f"{error_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Analyze refactoring accuracy metrics')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--output-json', type=str, help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    # Run analysis
    results = calculate_accuracy_metrics(start_date, end_date, args.verbose)
    
    # Save to JSON if requested
    if args.output_json and results:
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output_json}")

if __name__ == '__main__':
    main()