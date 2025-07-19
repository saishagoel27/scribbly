import streamlit as st
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from PIL import Image
import io

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    """ File handler for managing file uploads and processing """
    
    def __init__(self):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
    
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
                "estimated_pages": self._estimate_pages(uploaded_file.size),
                "upload_timestamp": datetime.now().isoformat()
            }
            
            # Check cache
            file_hash = self._calculate_file_hash(uploaded_file.getvalue())
            cached_result = self._check_cache(file_hash)
            if cached_result:
                st.info("⚡ Found cached results - processing will be faster!")
            
            # Prepare file data
            file_data = {
                "file_bytes": uploaded_file.getvalue(),
                "content_type": self._get_content_type(uploaded_file.name),
                "needs_ocr": metadata["file_extension"] in ['pdf', 'jpg', 'jpeg', 'png']
            }
            
            return {
                "file_data": file_data,
                "metadata": metadata,
                "file_hash": file_hash,
                "status": "ready_for_processing"
            }
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
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
    
    def _estimate_pages(self, file_size: int) -> int:
        """Simple page estimation"""
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb < 1:
            return 1
        else:
            return max(1, int(file_size_mb / 0.5))  # Assume ~0.5MB per page
    
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
    
    def _calculate_file_hash(self, file_bytes: bytes) -> str:
        """Simple file hash for caching"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def _check_cache(self, file_hash: str) -> Optional[Dict]:
        """Simple cache check"""
        cache_file = self.cache_dir / f"{file_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is less than 24 hours old
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', ''))
                if (datetime.now() - cache_time).total_seconds() < 86400:
                    return cached_data
                else:
                    cache_file.unlink()  # Remove expired cache
                    
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        return None
    
    def cache_result(self, file_hash: str, result_data: Dict) -> bool:
        """Simple result caching"""
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            
            cache_data = {
                **result_data,
                "timestamp": datetime.now().isoformat(),
                "file_hash": file_hash
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False

# Create global instance
file_handler = FileHandler()