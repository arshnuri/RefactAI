#!/usr/bin/env python3
"""
Refactoring Accuracy Calculator

This script calculates the true accuracy of refactoring operations by analyzing:
1. Success rates across different file types and languages
2. Quality improvement metrics (complexity, readability, maintainability)
3. Validation success rates
4. Error patterns and failure analysis
5. Overall effectiveness metrics
"""

import os
import sys
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from refactai_app.models import RefactorSession, ProcessedFile
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Calculate comprehensive refactoring accuracy metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file for detailed accuracy report (JSON format)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed breakdown by language and file type'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        output_file = options.get('output_file')
        verbose = options['verbose']
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== REFACTORING ACCURACY ANALYSIS ==="
            )
        )
        self.stdout.write(f"Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        self.stdout.write(f"Total Days: {days}\n")
        
        # Get sessions in date range
        sessions = RefactorSession.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Get all processed files in date range
        files = ProcessedFile.objects.filter(
            session__in=sessions
        )
        
        # Calculate overall metrics
        accuracy_report = self._calculate_overall_accuracy(sessions, files)
        
        # Calculate language-specific metrics
        language_metrics = self._calculate_language_accuracy(files)
        
        # Calculate quality improvement metrics
        quality_metrics = self._calculate_quality_improvements(files)
        
        # Calculate error analysis
        error_analysis = self._analyze_errors(files)
        
        # Calculate validation accuracy
        validation_metrics = self._calculate_validation_accuracy(files)
        
        # Display results
        self._display_results(
            accuracy_report, language_metrics, quality_metrics, 
            error_analysis, validation_metrics, verbose
        )
        
        # Save detailed report if requested
        if output_file:
            detailed_report = {
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'overall_accuracy': accuracy_report,
                'language_metrics': language_metrics,
                'quality_metrics': quality_metrics,
                'error_analysis': error_analysis,
                'validation_metrics': validation_metrics,
                'generated_at': timezone.now().isoformat()
            }
            
            with open(output_file, 'w') as f:
                json.dump(detailed_report, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"\nDetailed report saved to: {output_file}")
            )
    
    def _calculate_overall_accuracy(self, sessions, files):
        """Calculate overall refactoring accuracy metrics"""
        total_sessions = sessions.count()
        total_files = files.count()
        
        # Session-level metrics
        completed_sessions = sessions.filter(status='completed').count()
        failed_sessions = sessions.filter(status='failed').count()
        processing_sessions = sessions.filter(status='processing').count()
        
        # File-level metrics
        completed_files = files.filter(status='completed').count()
        failed_files = files.filter(status='failed').count()
        processing_files = files.filter(status='processing').count()
        
        # Calculate success rates
        session_success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        file_success_rate = (completed_files / total_files * 100) if total_files > 0 else 0
        
        # Calculate true accuracy (files with actual improvements)
        files_with_quality_metrics = files.filter(
            status='completed',
            overall_quality_score__gt=0
        ).count()
        
        true_accuracy = (files_with_quality_metrics / total_files * 100) if total_files > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'total_files': total_files,
            'session_success_rate': round(session_success_rate, 2),
            'file_success_rate': round(file_success_rate, 2),
            'true_accuracy': round(true_accuracy, 2),
            'completed_sessions': completed_sessions,
            'failed_sessions': failed_sessions,
            'processing_sessions': processing_sessions,
            'completed_files': completed_files,
            'failed_files': failed_files,
            'processing_files': processing_files,
            'files_with_quality_metrics': files_with_quality_metrics
        }
    
    def _calculate_language_accuracy(self, files):
        """Calculate accuracy metrics by programming language"""
        language_stats = {}
        
        languages = files.values_list('language', flat=True).distinct()
        
        for language in languages:
            lang_files = files.filter(language=language)
            total = lang_files.count()
            completed = lang_files.filter(status='completed').count()
            failed = lang_files.filter(status='failed').count()
            
            # Quality metrics for completed files
            completed_with_metrics = lang_files.filter(
                status='completed',
                overall_quality_score__gt=0
            )
            
            avg_quality = completed_with_metrics.aggregate(
                avg_complexity=Avg('complexity_score'),
                avg_readability=Avg('readability_score'),
                avg_maintainability=Avg('maintainability_score'),
                avg_overall=Avg('overall_quality_score')
            )
            
            success_rate = (completed / total * 100) if total > 0 else 0
            quality_rate = (completed_with_metrics.count() / total * 100) if total > 0 else 0
            
            language_stats[language] = {
                'total_files': total,
                'completed_files': completed,
                'failed_files': failed,
                'success_rate': round(success_rate, 2),
                'quality_accuracy': round(quality_rate, 2),
                'avg_complexity': round(avg_quality['avg_complexity'] or 0, 1),
                'avg_readability': round(avg_quality['avg_readability'] or 0, 1),
                'avg_maintainability': round(avg_quality['avg_maintainability'] or 0, 1),
                'avg_overall_quality': round(avg_quality['avg_overall'] or 0, 1)
            }
        
        return language_stats
    
    def _calculate_quality_improvements(self, files):
        """Calculate quality improvement metrics"""
        completed_files = files.filter(status='completed', overall_quality_score__gt=0)
        
        if not completed_files.exists():
            return {
                'files_analyzed': 0,
                'avg_complexity_score': 0,
                'avg_readability_score': 0,
                'avg_maintainability_score': 0,
                'avg_overall_score': 0,
                'quality_distribution': {}
            }
        
        # Calculate averages
        quality_stats = completed_files.aggregate(
            avg_complexity=Avg('complexity_score'),
            avg_readability=Avg('readability_score'),
            avg_maintainability=Avg('maintainability_score'),
            avg_overall=Avg('overall_quality_score')
        )
        
        # Quality score distribution
        quality_ranges = {
            'excellent': completed_files.filter(overall_quality_score__gte=90).count(),
            'good': completed_files.filter(
                overall_quality_score__gte=75,
                overall_quality_score__lt=90
            ).count(),
            'fair': completed_files.filter(
                overall_quality_score__gte=60,
                overall_quality_score__lt=75
            ).count(),
            'poor': completed_files.filter(overall_quality_score__lt=60).count()
        }
        
        total_analyzed = completed_files.count()
        quality_distribution = {
            range_name: {
                'count': count,
                'percentage': round((count / total_analyzed * 100) if total_analyzed > 0 else 0, 1)
            }
            for range_name, count in quality_ranges.items()
        }
        
        return {
            'files_analyzed': total_analyzed,
            'avg_complexity_score': round(quality_stats['avg_complexity'] or 0, 1),
            'avg_readability_score': round(quality_stats['avg_readability'] or 0, 1),
            'avg_maintainability_score': round(quality_stats['avg_maintainability'] or 0, 1),
            'avg_overall_score': round(quality_stats['avg_overall'] or 0, 1),
            'quality_distribution': quality_distribution
        }
    
    def _analyze_errors(self, files):
        """Analyze error patterns and failure reasons"""
        failed_files = files.filter(status='failed')
        
        # Common error patterns
        error_patterns = {}
        for file in failed_files:
            if file.error_message:
                # Categorize errors
                error_msg = file.error_message.lower()
                if 'syntax' in error_msg:
                    error_patterns['syntax_errors'] = error_patterns.get('syntax_errors', 0) + 1
                elif 'timeout' in error_msg:
                    error_patterns['timeout_errors'] = error_patterns.get('timeout_errors', 0) + 1
                elif 'llm' in error_msg:
                    error_patterns['llm_errors'] = error_patterns.get('llm_errors', 0) + 1
                elif 'validation' in error_msg:
                    error_patterns['validation_errors'] = error_patterns.get('validation_errors', 0) + 1
                else:
                    error_patterns['other_errors'] = error_patterns.get('other_errors', 0) + 1
        
        # Error rate by language
        error_by_language = {}
        languages = files.values_list('language', flat=True).distinct()
        
        for language in languages:
            lang_files = files.filter(language=language)
            lang_failed = lang_files.filter(status='failed').count()
            lang_total = lang_files.count()
            
            error_rate = (lang_failed / lang_total * 100) if lang_total > 0 else 0
            error_by_language[language] = {
                'failed_files': lang_failed,
                'total_files': lang_total,
                'error_rate': round(error_rate, 2)
            }
        
        return {
            'total_failed_files': failed_files.count(),
            'error_patterns': error_patterns,
            'error_by_language': error_by_language
        }
    
    def _calculate_validation_accuracy(self, files):
        """Calculate validation and syntax accuracy"""
        # Files that completed without validation errors
        clean_completions = files.filter(
            status='completed',
            error_message=''
        ).count()
        
        # Files that completed but with warnings
        completed_with_warnings = files.filter(
            status='completed'
        ).exclude(error_message='').count()
        
        total_completed = files.filter(status='completed').count()
        total_files = files.count()
        
        validation_accuracy = (clean_completions / total_files * 100) if total_files > 0 else 0
        warning_rate = (completed_with_warnings / total_completed * 100) if total_completed > 0 else 0
        
        return {
            'clean_completions': clean_completions,
            'completed_with_warnings': completed_with_warnings,
            'total_completed': total_completed,
            'validation_accuracy': round(validation_accuracy, 2),
            'warning_rate': round(warning_rate, 2)
        }
    
    def _display_results(self, overall, language_metrics, quality_metrics, 
                        error_analysis, validation_metrics, verbose):
        """Display comprehensive accuracy results"""
        
        # Overall Accuracy Summary
        self.stdout.write(self.style.SUCCESS("\n=== OVERALL ACCURACY SUMMARY ==="))
        self.stdout.write(f"Total Sessions: {overall['total_sessions']}")
        self.stdout.write(f"Total Files: {overall['total_files']}")
        self.stdout.write(f"")
        self.stdout.write(f"Session Success Rate: {overall['session_success_rate']}%")
        self.stdout.write(f"File Success Rate: {overall['file_success_rate']}%")
        self.stdout.write(self.style.WARNING(f"TRUE ACCURACY: {overall['true_accuracy']}%"))
        self.stdout.write(f"")
        self.stdout.write(f"Files with Quality Metrics: {overall['files_with_quality_metrics']}")
        self.stdout.write(f"Validation Accuracy: {validation_metrics['validation_accuracy']}%")
        
        # Quality Metrics Summary
        self.stdout.write(self.style.SUCCESS("\n=== QUALITY METRICS SUMMARY ==="))
        self.stdout.write(f"Files Analyzed: {quality_metrics['files_analyzed']}")
        self.stdout.write(f"Average Complexity Score: {quality_metrics['avg_complexity_score']}")
        self.stdout.write(f"Average Readability Score: {quality_metrics['avg_readability_score']}")
        self.stdout.write(f"Average Maintainability Score: {quality_metrics['avg_maintainability_score']}")
        self.stdout.write(f"Average Overall Score: {quality_metrics['avg_overall_score']}")
        
        # Quality Distribution
        self.stdout.write("\nQuality Distribution:")
        for range_name, data in quality_metrics['quality_distribution'].items():
            self.stdout.write(f"  {range_name.capitalize()}: {data['count']} files ({data['percentage']}%)")
        
        # Error Analysis
        self.stdout.write(self.style.SUCCESS("\n=== ERROR ANALYSIS ==="))
        self.stdout.write(f"Total Failed Files: {error_analysis['total_failed_files']}")
        self.stdout.write("\nError Patterns:")
        for error_type, count in error_analysis['error_patterns'].items():
            self.stdout.write(f"  {error_type.replace('_', ' ').title()}: {count}")
        
        # Language-specific metrics (if verbose)
        if verbose:
            self.stdout.write(self.style.SUCCESS("\n=== LANGUAGE-SPECIFIC ACCURACY ==="))
            for language, metrics in language_metrics.items():
                self.stdout.write(f"\n{language.upper()}:")
                self.stdout.write(f"  Total Files: {metrics['total_files']}")
                self.stdout.write(f"  Success Rate: {metrics['success_rate']}%")
                self.stdout.write(f"  Quality Accuracy: {metrics['quality_accuracy']}%")
                self.stdout.write(f"  Avg Quality Score: {metrics['avg_overall_quality']}")
                
                # Error rate for this language
                if language in error_analysis['error_by_language']:
                    error_data = error_analysis['error_by_language'][language]
                    self.stdout.write(f"  Error Rate: {error_data['error_rate']}%")
        
        # Final Assessment
        self.stdout.write(self.style.SUCCESS("\n=== ACCURACY ASSESSMENT ==="))
        
        true_accuracy = overall['true_accuracy']
        if true_accuracy >= 90:
            assessment = "EXCELLENT"
            color = self.style.SUCCESS
        elif true_accuracy >= 75:
            assessment = "GOOD"
            color = self.style.SUCCESS
        elif true_accuracy >= 60:
            assessment = "FAIR"
            color = self.style.WARNING
        else:
            assessment = "NEEDS IMPROVEMENT"
            color = self.style.ERROR
        
        self.stdout.write(color(f"Overall Refactoring Accuracy: {assessment} ({true_accuracy}%)"))
        
        # Recommendations
        self.stdout.write("\nRecommendations:")
        if true_accuracy < 75:
            self.stdout.write("  • Review and improve error handling for failed refactorings")
        if validation_metrics['warning_rate'] > 20:
            self.stdout.write("  • Investigate validation warnings to improve code quality")
        if error_analysis['total_failed_files'] > overall['total_files'] * 0.1:
            self.stdout.write("  • Analyze common error patterns to prevent failures")
        if quality_metrics['avg_overall_score'] < 75:
            self.stdout.write("  • Enhance refactoring algorithms to improve quality scores")