"""
Validators for file uploads and data
"""
from fastapi import UploadFile, HTTPException, status
from typing import List
import os
from config import settings
from exceptions import FileValidationError


class FileValidator:
    """Validate uploaded files"""
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str] = None) -> bool:
        """Check if file has an allowed extension"""
        if allowed_extensions is None:
            allowed_extensions = settings.ALLOWED_EXTENSIONS
        
        ext = os.path.splitext(filename)[-1].lower().lstrip('.')
        return ext in allowed_extensions
    
    @staticmethod
    def validate_file_size(file: UploadFile, max_size_mb: int = None) -> bool:
        """Check if file size is within limits"""
        if max_size_mb is None:
            max_size_mb = settings.MAX_FILE_SIZE_MB
        
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    @staticmethod
    async def validate_upload(file: UploadFile) -> None:
        """Comprehensive file validation"""
        if not file or not file.filename:
            raise FileValidationError("No file provided")
        
        # Check extension
        if not FileValidator.validate_file_extension(file.filename):
            raise FileValidationError(
                f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check size
        if not FileValidator.validate_file_size(file):
            raise FileValidationError(
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Check if file is empty
        content = await file.read()
        if not content or len(content) == 0:
            raise FileValidationError("File is empty")
        
        # Reset file position
        await file.seek(0)
    
    @staticmethod
    def get_file_info(file: UploadFile) -> dict:
        """Get file information"""
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        return {
            "filename": file.filename,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "extension": os.path.splitext(file.filename)[-1].lower(),
        }


class DataValidator:
    """Validate data inputs"""
    
    @staticmethod
    def validate_column_names(columns: List[str], data_columns: List[str]) -> bool:
        """Check if requested columns exist in data"""
        missing = [col for col in columns if col not in data_columns]
        if missing:
            raise ValueError(f"Columns not found in dataset: {', '.join(missing)}")
        return True
    
    @staticmethod
    def validate_aggregation(agg: str) -> bool:
        """Validate aggregation function"""
        allowed_aggs = ['mean', 'sum', 'count', 'min', 'max', 'median', 'std']
        if agg not in allowed_aggs:
            raise ValueError(f"Invalid aggregation: {agg}. Allowed: {', '.join(allowed_aggs)}")
        return True
    
    @staticmethod
    def validate_positive_integer(value: int, name: str = "value") -> bool:
        """Validate positive integer"""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return True
