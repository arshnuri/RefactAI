from django.contrib import admin
from .models import RefactorSession, ProcessedFile


@admin.register(RefactorSession)
class RefactorSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'status', 'total_files', 'processed_files', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('original_filename', 'id')
    readonly_fields = ('id', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('files')


@admin.register(ProcessedFile)
class ProcessedFileAdmin(admin.ModelAdmin):
    list_display = ('original_path', 'language', 'status', 'session', 'created_at')
    list_filter = ('language', 'status', 'created_at')
    search_fields = ('original_path', 'session__original_filename')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('File Information', {
            'fields': ('session', 'original_path', 'language', 'status', 'created_at')
        }),
        ('Content', {
            'fields': ('original_content', 'refactored_content'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )