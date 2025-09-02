import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from django.conf import settings
from typing import List, Tuple


class ZipHandler:
    """Handles ZIP file extraction and processing"""
    
    def __init__(self, zip_file):
        self.zip_file = zip_file
        self.temp_dir = None
        self.extracted_files = []
    
    def extract_zip(self) -> str:
        """Extract ZIP file to temporary directory"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR)
        
        try:
            with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(self.temp_dir)
                
                # Get list of extracted files
                self.extracted_files = self._get_code_files(self.temp_dir)
                
            return self.temp_dir
            
        except Exception as e:
            # Clean up on error
            self.cleanup()
            raise Exception(f"Error extracting ZIP file: {str(e)}")
    
    def _get_code_files(self, directory: str) -> List[Tuple[str, str]]:
        """Recursively get all code files from directory"""
        code_files = []
        allowed_extensions = settings.ALLOWED_CODE_EXTENSIONS
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'node_modules', '.git', '.svn', 'venv', 'env',
                'build', 'dist', 'target', 'bin', 'obj'
            ]]
            
            for file in files:
                # Skip hidden files and binary files
                if file.startswith('.') or self._is_binary_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                # Check if it's a code file
                if file_ext in allowed_extensions:
                    # Get relative path from temp directory
                    relative_path = os.path.relpath(file_path, directory)
                    code_files.append((file_path, relative_path))
        
        return code_files
    
    def _is_binary_file(self, filename: str) -> bool:
        """Check if file is likely binary based on extension"""
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.dat',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flv',
            '.ttf', '.otf', '.woff', '.woff2', '.eot'
        }
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in binary_extensions
    
    def get_file_content(self, file_path: str) -> str:
        """Read file content with proper encoding handling"""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise Exception(f"Error reading file {file_path}: {str(e)}")
        
        raise Exception(f"Could not decode file {file_path} with any supported encoding")
    
    def create_refactored_zip(self, session_files, output_path: str) -> str:
        """Create ZIP file with refactored code"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file_obj in session_files:
                # Use refactored content if available, otherwise original
                content = file_obj.refactored_content or file_obj.original_content
                
                # Write file to ZIP
                zip_ref.writestr(file_obj.original_path, content)
        
        return output_path
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory {self.temp_dir}: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()