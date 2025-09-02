from django import forms
from django.core.exceptions import ValidationError
import zipfile
import os


class ZipUploadForm(forms.Form):
    """Form for uploading ZIP files containing code"""
    zip_file = forms.FileField(
        label='Upload ZIP file',
        help_text='Upload a ZIP file containing your code (max 25MB)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip',
        })
    )
    
    processing_mode = forms.ChoiceField(
        choices=[
            ('local', 'Local LLM'),
            ('api', 'API'),
            ('hybrid', 'Hybrid'),
        ],
        initial='local',
        required=False,
        widget=forms.HiddenInput()
    )
    
    refactor_type = forms.ChoiceField(
        choices=[
            ('comprehensive', 'Comprehensive'),
            ('performance', 'Performance'),
            ('readability', 'Readability'),
            ('security', 'Security'),
        ],
        initial='comprehensive',
        required=False,
        widget=forms.HiddenInput()
    )
    
    preserve_comments = forms.BooleanField(
        required=False,
        initial=True
    )
    
    add_documentation = forms.BooleanField(
        required=False,
        initial=True
    )
    
    follow_conventions = forms.BooleanField(
        required=False,
        initial=False
    )
    
    def clean_zip_file(self):
        zip_file = self.cleaned_data['zip_file']
        
        # Check file size (25MB limit)
        if zip_file.size > 25 * 1024 * 1024:
            raise ValidationError('File size must be less than 25MB.')
        
        # Check file extension
        if not zip_file.name.lower().endswith('.zip'):
            raise ValidationError('Please upload a ZIP file.')
        
        # Validate that it's a valid ZIP file
        try:
            # Reset file pointer to beginning
            zip_file.seek(0)
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Test the ZIP file integrity
                zip_ref.testzip()
                
                # Check for suspicious file paths
                for file_info in zip_ref.filelist:
                    # Prevent directory traversal attacks
                    if '..' in file_info.filename or file_info.filename.startswith('/'):
                        raise ValidationError('ZIP file contains unsafe file paths.')
                    
                    # Check for excessively long paths
                    if len(file_info.filename) > 500:
                        raise ValidationError('ZIP file contains paths that are too long.')
            
            # Reset file pointer for later use
            zip_file.seek(0)
            
        except zipfile.BadZipFile:
            raise ValidationError('Invalid ZIP file.')
        except Exception as e:
            raise ValidationError(f'Error processing ZIP file: {str(e)}')
        
        return zip_file