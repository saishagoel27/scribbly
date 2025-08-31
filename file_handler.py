import streamlit as st
from typing import Dict, Optional, Any
from datetime import datetime
from PIL import Image
import io

from config import Config

class FileHandler:
    """ File handler for managing file uploads and processing """

    def create_upload_interface(self) -> Optional[Dict[str, Any]]:
        """Simple file upload interface"""
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=Config.SUPPORTED_FILE_TYPES,
            help=f"Maximum file size: {Config.MAX_FILE_SIZE_MB}MB"
        )

        if uploaded_file is not None:
            return self._process_uploaded_file(uploaded_file)

        return None

    def _process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """Process uploaded file - simplified"""
        try:
            # Validate file
            validation = self.validate_file(uploaded_file)
            if not validation['valid']:
                return {"error": validation['error']}

            # Basic metadata
            metadata = {
                "filename": uploaded_file.name,
                "file_extension": uploaded_file.name.split('.')[-1].lower(),
                "file_size_mb": uploaded_file.size / (1024 * 1024),
                "upload_timestamp": datetime.now().isoformat()
            }

            # Prepare file data
            file_data = {
                "file_bytes": uploaded_file.getvalue(),
                "content_type": self._get_content_type(uploaded_file.name),
                "needs_ocr": metadata["file_extension"] in ['pdf', 'jpg', 'jpeg', 'png']
            }

            return {
                "file_data": file_data,
                "metadata": metadata,
                "status": "ready_for_processing"
            }

        except Exception as e:
            return {"error": f"File processing failed: {str(e)}"}

    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """Simple file validation"""
        try:
            # Check file size
            size_check = Config.validate_file_size(uploaded_file.size)
            if not size_check['valid']:
                return size_check

            # Check file type
            extension = uploaded_file.name.split('.')[-1].lower()
            if not Config.validate_file_type(extension):
                return {
                    'valid': False,
                    'error': f"Unsupported file type. Supported: {', '.join(Config.SUPPORTED_FILE_TYPES)}"
                }

            # Basic image validation for image files
            if extension in ['jpg', 'jpeg', 'png']:
                try:
                    Image.open(io.BytesIO(uploaded_file.getvalue()))
                except Exception:
                    return {'valid': False, 'error': "Invalid image file"}

            return {'valid': True}

        except Exception as e:
            return {'valid': False, 'error': f"File validation failed: {str(e)}"}

    def _get_content_type(self, filename: str) -> str:
        """Get content type for Azure"""
        extension = filename.split('.')[-1].lower()
        content_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'txt': 'text/plain',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(extension, 'application/octet-stream')

# Create global instance
file_handler = FileHandler()