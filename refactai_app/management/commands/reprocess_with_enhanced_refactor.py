#!/usr/bin/env python3
"""
Django management command to reprocess existing ProcessedFile records
with the new Enhanced Rule-Based Refactoring system.

Usage:
    python manage.py reprocess_with_enhanced_refactor
    python manage.py reprocess_with_enhanced_refactor --session-id <session_id>
    python manage.py reprocess_with_enhanced_refactor --language python
    python manage.py reprocess_with_enhanced_refactor --status failed
    python manage.py reprocess_with_enhanced_refactor --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from refactai_app.models import ProcessedFile, RefactorSession
from refactai_app.utils.enhanced_rule_based_refactor import EnhancedRuleBasedRefactor
from refactai_app.utils.code_quality_analyzer import CodeQualityAnalyzer
import time


class Command(BaseCommand):
    help = 'Reprocess existing ProcessedFile records with Enhanced Rule-Based Refactoring'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='Reprocess files from a specific session only'
        )
        parser.add_argument(
            '--language',
            type=str,
            choices=['python', 'javascript', 'java', 'all'],
            default='all',
            help='Reprocess files of a specific language only'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['completed', 'failed', 'all'],
            default='all',
            help='Reprocess files with a specific status only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of files to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if files already have enhanced refactoring'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Enhanced Rule-Based Reprocessing...'))
        
        # Build query filters
        filters = {}
        
        if options['session_id']:
            try:
                session = RefactorSession.objects.get(id=options['session_id'])
                filters['session'] = session
                self.stdout.write(f"Filtering by session: {session.original_filename}")
            except RefactorSession.DoesNotExist:
                raise CommandError(f"Session with ID {options['session_id']} does not exist")
        
        if options['language'] != 'all':
            filters['language__iexact'] = options['language']
            self.stdout.write(f"Filtering by language: {options['language']}")
        
        if options['status'] != 'all':
            filters['status'] = options['status']
            self.stdout.write(f"Filtering by status: {options['status']}")
        
        # Get files to process
        queryset = ProcessedFile.objects.filter(**filters)
        
        # Exclude files that are too large or empty
        queryset = queryset.exclude(original_content__exact='')
        
        if options['limit']:
            queryset = queryset[:options['limit']]
            
        total_files = queryset.count()
        
        if total_files == 0:
            self.stdout.write(self.style.WARNING('No files found matching the criteria.'))
            return
        
        self.stdout.write(f"Found {total_files} files to process")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            for file_obj in queryset[:10]:  # Show first 10 in dry run
                self.stdout.write(f"  Would process: {file_obj.original_path} ({file_obj.language})")
            if total_files > 10:
                self.stdout.write(f"  ... and {total_files - 10} more files")
            return
        
        # Initialize components
        enhanced_refactor = EnhancedRuleBasedRefactor()
        quality_analyzer = CodeQualityAnalyzer()
        
        # Process files
        processed_count = 0
        improved_count = 0
        failed_count = 0
        start_time = time.time()
        
        for file_obj in queryset:
            try:
                self.stdout.write(f"Processing: {file_obj.original_path}")
                
                # Use original content as base for enhancement
                base_code = file_obj.original_content
                
                # If file was previously successfully refactored, use that as base
                if file_obj.status == 'completed' and file_obj.refactored_content:
                    base_code = file_obj.refactored_content
                
                # Apply enhanced rule-based refactoring
                enhancement_result = enhanced_refactor.refactor_code(
                    base_code, 
                    file_obj.language, 
                    file_obj.original_path
                )
                
                if enhancement_result.get('success', False):
                    enhanced_code = enhancement_result['refactored_code']
                    improvements = enhancement_result.get('improvements', [])
                    
                    # Only update if improvements were made
                    if improvements and enhanced_code != base_code:
                        with transaction.atomic():
                            # Update the refactored content
                            file_obj.refactored_content = enhanced_code
                            
                            # Update status if it was previously failed
                            if file_obj.status == 'failed':
                                file_obj.status = 'completed'
                            
                            # Add improvement info to error message (as info)
                            improvement_info = f"Enhanced: {', '.join(improvements[:3])}"
                            if file_obj.error_message:
                                file_obj.error_message += f" | {improvement_info}"
                            else:
                                file_obj.error_message = improvement_info
                            
                            # Calculate and update quality metrics
                            try:
                                metrics = quality_analyzer.analyze_code(enhanced_code, file_obj.language)
                                overall_score = quality_analyzer.calculate_overall_score(metrics)
                                
                                file_obj.complexity_score = int(metrics.get('complexity', 0))
                                file_obj.readability_score = int(metrics.get('readability', 0))
                                file_obj.maintainability_score = int(metrics.get('maintainability', 0))
                                file_obj.overall_quality_score = int(overall_score)
                            except Exception as quality_error:
                                self.stdout.write(
                                    self.style.WARNING(f"  Quality analysis failed: {quality_error}")
                                )
                            
                            file_obj.save()
                            improved_count += 1
                            
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✓ Enhanced: {', '.join(improvements[:2])}")
                            )
                    else:
                        self.stdout.write("  - No improvements needed")
                else:
                    error_msg = enhancement_result.get('error', 'Unknown enhancement error')
                    self.stdout.write(self.style.WARNING(f"  ✗ Enhancement failed: {error_msg}"))
                    failed_count += 1
                
                processed_count += 1
                
                # Progress update every 10 files
                if processed_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed
                    eta = (total_files - processed_count) / rate if rate > 0 else 0
                    self.stdout.write(
                        f"Progress: {processed_count}/{total_files} "
                        f"({processed_count/total_files*100:.1f}%) "
                        f"- ETA: {eta/60:.1f} minutes"
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing {file_obj.original_path}: {e}")
                )
                failed_count += 1
                processed_count += 1
                continue
        
        # Final summary
        elapsed = time.time() - start_time
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS('Enhanced Rule-Based Reprocessing Complete!'))
        self.stdout.write(f"Total files processed: {processed_count}")
        self.stdout.write(f"Files improved: {improved_count}")
        self.stdout.write(f"Files failed: {failed_count}")
        self.stdout.write(f"Files unchanged: {processed_count - improved_count - failed_count}")
        self.stdout.write(f"Processing time: {elapsed/60:.1f} minutes")
        
        if improved_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 Successfully enhanced {improved_count} files with rule-based improvements!"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nNo files were improved. They may already be optimized or need different enhancements."
                )
            )