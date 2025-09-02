from django.db import models
import uuid


class RefactorSession(models.Model):
    """Model to track refactoring sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='processing')
    total_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Processing options
    processing_mode = models.CharField(max_length=20, choices=[
        ('local', 'Local LLM'),
        ('api', 'API'),
        ('hybrid', 'Hybrid'),
    ], default='local')
    refactor_type = models.CharField(max_length=20, choices=[
        ('comprehensive', 'Comprehensive'),
        ('performance', 'Performance'),
        ('readability', 'Readability'),
        ('security', 'Security'),
    ], default='comprehensive')
    preserve_comments = models.BooleanField(default=True)
    add_documentation = models.BooleanField(default=True)
    follow_conventions = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Session {self.id} - {self.original_filename}"


class ProcessedFile(models.Model):
    """Model to track individual processed files"""
    session = models.ForeignKey(RefactorSession, on_delete=models.CASCADE, related_name='files')
    original_path = models.CharField(max_length=500)
    language = models.CharField(max_length=50)
    original_content = models.TextField()
    refactored_content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Quality metrics
    complexity_score = models.IntegerField(default=0, help_text="Complexity score (0-100)")
    readability_score = models.IntegerField(default=0, help_text="Readability score (0-100)")
    maintainability_score = models.IntegerField(default=0, help_text="Maintainability score (0-100)")
    overall_quality_score = models.IntegerField(default=0, help_text="Overall quality score (0-100)")
    
    def __str__(self):
        return f"{self.original_path} ({self.language})"