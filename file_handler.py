import streamlit as st
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
import mimetypes
from PIL import Image
import io

from config import Config

# Setup logging
logger = logging.getLogger(__name__)

class FileHandler:
    """
    Enhanced file upload, validation, and processing handler
    
    This class manages:
    - File upload interface with Streamlit
    - File validation and security checks
    - File metadata extraction
    - Cache management for processed files
    - Integration with Azure processing pipeline
    """
    
    def __init__(self):
        """Initialize FileHandler with configuration"""
        self.max_size_bytes = Config.MAX_FILE_SIZE_BYTES
        self.supported_types = Config.SUPPORTED_FILE_TYPES
        self.cache_enabled = Config.CACHE_ENABLED
        self.cache_dir = Config.CACHE_DIR / "files"
        
        # Ensure cache directory exists
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # MIME type mapping for validation
        self.mime_type_map = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        
        logger.info("📁 FileHandler initialized successfully")
    
    def create_upload_interface(self) -> Optional[Dict[str, Any]]:
        """
        Creates the enhanced Streamlit file upload interface
        
        Returns:
            Dict containing uploaded file data and metadata, or None if no file
        """
        st.subheader("📁 Upload Your Document")
        
        # Show supported file types with enhanced info
        with st.expander("ℹ️ What files can I upload?", expanded=False):
            st.write("**Supported formats:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("📄 **Text Documents:**")
                st.write("- PDF files (.pdf)")
                st.write("- Word documents (.docx)")
                st.write("- Text files (.txt)")
            
            with col2:
                st.write("🖼️ **Images with Text:**")
                st.write("- JPEG images (.jpg, .jpeg)")
                st.write("- PNG images (.png)")
                st.write("- Handwritten or printed text")
            
            st.write(f"📏 **File Limits:**")
            st.write(f"- Maximum size: {Config.MAX_FILE_SIZE_MB} MB")
            st.write(f"- Best quality: High resolution, clear text")
            st.write(f"- Supported text: English (optimized)")
        
        # Enhanced file uploader widget
        uploaded_file = st.file_uploader(
            "Choose a file to analyze",
            type=self.supported_types,
            help=f"Max size: {Config.MAX_FILE_SIZE_MB}MB. Supported: {', '.join(self.supported_types)}",
            key="main_file_uploader"
        )
        
        if uploaded_file is not None:
            # Process the uploaded file
            return self._process_uploaded_file(uploaded_file)
        
        return None
    
    def _process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Process and validate uploaded file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Dict containing processed file data and metadata
        """
        try:
            # Show processing indicator
            with st.spinner("🔍 Processing uploaded file..."):
                
                # Step 1: Basic validation
                validation_result = self.validate_file(uploaded_file)
                if not validation_result["is_valid"]:
                    st.error(f"❌ {validation_result['error_message']}")
                    return {"error": validation_result["error_message"]}
                
                # Step 2: Extract file metadata
                file_metadata = self._extract_file_metadata(uploaded_file)
                
                # Step 3: Check cache
                file_hash = self._calculate_file_hash(uploaded_file.getvalue())
                cached_result = self._get_cached_result(file_hash) if self.cache_enabled else None
                
                if cached_result:
                    st.success("⚡ Found cached analysis - Loading instantly!")
                    cached_result["metadata"]["source"] = "cache"
                    self._display_file_info(file_metadata, cached=True)
                    return cached_result
                
                # Step 4: Prepare file for processing
                processed_data = self._prepare_file_for_processing(uploaded_file, file_metadata)
                
                # Step 5: Display file information
                self._display_file_info(file_metadata)
                
                st.success("✅ File uploaded and validated successfully!")
                
                return {
                    "file_data": processed_data,
                    "metadata": file_metadata,
                    "file_hash": file_hash,
                    "status": "ready_for_processing"
                }
                
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Comprehensive file validation
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Dict with validation results
        """
        try:
            # Check file size
            if uploaded_file.size > self.max_size_bytes:
                return {
                    "is_valid": False,
                    "error_message": f"File too large. Maximum size is {Config.MAX_FILE_SIZE_MB}MB, your file is {uploaded_file.size / (1024*1024):.1f}MB"
                }
            
            # Check file extension
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in self.supported_types:
                return {
                    "is_valid": False,
                    "error_message": f"Unsupported file type '.{file_extension}'. Supported types: {', '.join(self.supported_types)}"
                }
            
            # Check MIME type for security
            file_bytes = uploaded_file.getvalue()
            detected_mime = self._detect_mime_type(file_bytes, file_extension)
            expected_mime = self.mime_type_map.get(file_extension)
            
            if expected_mime and detected_mime and not detected_mime.startswith(expected_mime.split('/')[0]):
                return {
                    "is_valid": False,
                    "error_message": f"File content doesn't match extension. Expected {expected_mime}, detected {detected_mime}"
                }
            
            # Additional validation for images
            if file_extension in ['jpg', 'jpeg', 'png']:
                image_validation = self._validate_image(file_bytes)
                if not image_validation["is_valid"]:
                    return image_validation
            
            # File name validation
            if len(uploaded_file.name) > 255:
                return {
                    "is_valid": False,
                    "error_message": "File name too long (maximum 255 characters)"
                }
            
            return {
                "is_valid": True,
                "file_extension": file_extension,
                "detected_mime": detected_mime,
                "file_size_mb": uploaded_file.size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {
                "is_valid": False,
                "error_message": f"Validation error: {str(e)}"
            }
    
    def _validate_image(self, file_bytes: bytes) -> Dict[str, Any]:
        """Validate image files for OCR suitability"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Check image dimensions
            width, height = image.size
            
            # Minimum resolution for decent OCR
            if width < 200 or height < 200:
                return {
                    "is_valid": False,
                    "error_message": f"Image resolution too low ({width}x{height}). Minimum recommended: 200x200 pixels for better text recognition."
                }
            
            # Maximum resolution to prevent memory issues
            if width > 10000 or height > 10000:
                return {
                    "is_valid": False,
                    "error_message": f"Image resolution too high ({width}x{height}). Maximum supported: 10000x10000 pixels."
                }
            
            # Check if image has reasonable aspect ratio
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:
                return {
                    "is_valid": False,
                    "error_message": f"Unusual aspect ratio ({aspect_ratio:.1f}:1). Images should be reasonably proportioned for best OCR results."
                }
            
            return {
                "is_valid": True,
                "image_info": {
                    "dimensions": f"{width}x{height}",
                    "mode": image.mode,
                    "format": image.format
                }
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error_message": f"Invalid image file: {str(e)}"
            }
    
    def _detect_mime_type(self, file_bytes: bytes, extension: str) -> Optional[str]:
        """Detect MIME type from file content"""
        try:
            # Check magic numbers for common file types
            if file_bytes.startswith(b'%PDF'):
                return 'application/pdf'
            elif file_bytes.startswith(b'\xFF\xD8\xFF'):
                return 'image/jpeg'
            elif file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif file_bytes.startswith(b'PK\x03\x04') and extension == 'docx':
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                # Fallback to text for txt files
                if extension == 'txt':
                    return 'text/plain'
                return None
                
        except Exception:
            return None
    
    def _extract_file_metadata(self, uploaded_file) -> Dict[str, Any]:
        """Extract comprehensive file metadata"""
        try:
            file_bytes = uploaded_file.getvalue()
            
            metadata = {
                "filename": uploaded_file.name,
                "size_bytes": uploaded_file.size,
                "size_mb": round(uploaded_file.size / (1024 * 1024), 2),
                "file_type": uploaded_file.type,
                "extension": uploaded_file.name.split('.')[-1].lower(),
                "upload_timestamp": datetime.now().isoformat(),
                "file_hash": self._calculate_file_hash(file_bytes)
            }
            
            # Add image-specific metadata
            if metadata["extension"] in ['jpg', 'jpeg', 'png']:
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    metadata.update({
                        "image_dimensions": f"{image.width}x{image.height}",
                        "image_mode": image.mode,
                        "image_format": image.format,
                        "estimated_dpi": getattr(image, 'info', {}).get('dpi', 'Unknown')
                    })
                except Exception:
                    pass
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return {"error": f"Could not extract metadata: {str(e)}"}
    
    def _prepare_file_for_processing(self, uploaded_file, metadata: Dict) -> Dict[str, Any]:
        """
        Prepare file data for Azure processing
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            metadata: File metadata dictionary
            
        Returns:
            Dict containing processed file data ready for Azure APIs
        """
        try:
            file_bytes = uploaded_file.getvalue()
            
            # Determine content type for Azure API
            extension = metadata["extension"]
            
            if extension == 'pdf':
                content_type = 'application/pdf'
            elif extension in ['jpg', 'jpeg']:
                content_type = 'image/jpeg'
            elif extension == 'png':
                content_type = 'image/png'
            elif extension == 'txt':
                content_type = 'text/plain'
            elif extension == 'docx':
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                content_type = 'application/octet-stream'
            
            processed_data = {
                "file_bytes": file_bytes,
                "content_type": content_type,
                "azure_compatible": True,
                "preprocessing_info": {
                    "requires_ocr": extension in ['pdf', 'jpg', 'jpeg', 'png'],
                    "text_extractable": extension in ['txt', 'docx'],
                    "azure_document_intelligence_compatible": extension in ['pdf', 'jpg', 'jpeg', 'png'],
                    "direct_text_available": extension in ['txt']
                }
            }
            
            # For text files, extract content directly
            if extension == 'txt':
                try:
                    text_content = file_bytes.decode('utf-8')
                    processed_data["direct_text"] = text_content
                    processed_data["text_length"] = len(text_content)
                except UnicodeDecodeError:
                    # Try different encodings
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            text_content = file_bytes.decode(encoding)
                            processed_data["direct_text"] = text_content
                            processed_data["text_length"] = len(text_content)
                            processed_data["encoding_used"] = encoding
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        processed_data["direct_text"] = None
                        processed_data["text_extraction_error"] = "Could not decode text with common encodings"
            
            return processed_data
            
        except Exception as e:
            logger.error(f"File preparation error: {e}")
            return {"error": f"Failed to prepare file: {str(e)}"}
    
    def _calculate_file_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash for file content"""
        return hashlib.sha256(file_bytes).hexdigest()
    
    def _get_cached_result(self, file_hash: str) -> Optional[Dict]:
        """Retrieve cached processing result if available"""
        if not self.cache_enabled:
            return None
        
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            if cache_file.exists():
                # Check cache age
                cache_age_hours = (datetime.now().timestamp() - cache_file.stat().st_mtime) / 3600
                if cache_age_hours < Config.CACHE_TTL_HOURS:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    logger.info(f"📁 Cache hit for file hash: {file_hash[:8]}...")
                    return cached_data
                else:
                    # Remove expired cache
                    cache_file.unlink()
                    logger.info(f"🗑️ Removed expired cache for: {file_hash[:8]}...")
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def cache_result(self, file_hash: str, result_data: Dict) -> bool:
        """Cache processing result for future use"""
        if not self.cache_enabled:
            return False
        
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            
            # Add cache metadata
            cache_data = {
                **result_data,
                "cache_metadata": {
                    "cached_at": datetime.now().isoformat(),
                    "file_hash": file_hash,
                    "cache_version": "1.0"
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Cached result for file hash: {file_hash[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return False
    
    def _display_file_info(self, metadata: Dict, cached: bool = False) -> None:
        """Display file information in Streamlit interface"""
        try:
            st.success(f"{'📁 File loaded from cache!' if cached else '📁 File uploaded successfully!'}")
            
            # Create info columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 File Name", metadata.get("filename", "Unknown"))
                st.metric("📏 File Size", f"{metadata.get('size_mb', 0)} MB")
            
            with col2:
                st.metric("🔤 File Type", metadata.get("extension", "Unknown").upper())
                if metadata.get("image_dimensions"):
                    st.metric("📐 Dimensions", metadata["image_dimensions"])
            
            with col3:
                upload_time = metadata.get("upload_timestamp", "")
                if upload_time:
                    # Format timestamp for display
                    try:
                        dt = datetime.fromisoformat(upload_time)
                        formatted_time = dt.strftime("%H:%M:%S")
                        st.metric("⏰ Uploaded", formatted_time)
                    except:
                        st.metric("⏰ Uploaded", "Just now")
                
                if cached:
                    st.metric("⚡ Source", "Cache")
            
            # Show detailed info in expander
            with st.expander("🔍 Detailed File Information", expanded=False):
                for key, value in metadata.items():
                    if key not in ["file_hash"]:  # Hide sensitive info
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        
        except Exception as e:
            logger.error(f"Display error: {e}")
            st.warning("Could not display all file information")
    
    def get_processing_status(self, file_data: Dict) -> Dict[str, Any]:
        """Determine what processing steps are needed for the file"""
        try:
            preprocessing_info = file_data.get("preprocessing_info", {})
            
            status = {
                "needs_ocr": preprocessing_info.get("requires_ocr", False),
                "has_direct_text": preprocessing_info.get("text_extractable", False),
                "azure_compatible": file_data.get("azure_compatible", False),
                "recommended_processing": []
            }
            
            # Determine processing recommendations
            if preprocessing_info.get("azure_document_intelligence_compatible"):
                status["recommended_processing"].append("Azure Document Intelligence (OCR)")
            
            if preprocessing_info.get("direct_text_available"):
                status["recommended_processing"].append("Direct text extraction")
            
            if not status["recommended_processing"]:
                status["recommended_processing"].append("Manual text input required")
            
            return status
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"error": f"Could not determine processing status: {str(e)}"}
    
    def cleanup_cache(self, max_age_hours: int = None) -> Dict[str, int]:
        """Clean up old cache files"""
        if not self.cache_enabled or not self.cache_dir.exists():
            return {"removed": 0, "kept": 0, "errors": 0}
        
        max_age = max_age_hours or Config.CACHE_TTL_HOURS
        current_time = datetime.now().timestamp()
        
        removed = 0
        kept = 0
        errors = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    file_age_hours = (current_time - cache_file.stat().st_mtime) / 3600
                    if file_age_hours > max_age:
                        cache_file.unlink()
                        removed += 1
                    else:
                        kept += 1
                except Exception:
                    errors += 1
            
            logger.info(f"🧹 Cache cleanup: {removed} removed, {kept} kept, {errors} errors")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            errors += 1
        
        return {"removed": removed, "kept": kept, "errors": errors}

# Create global instance
file_handler = FileHandler()