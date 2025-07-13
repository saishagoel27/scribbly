import streamlit as st
import hashlib
import json
import os
import io 
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from PIL import Image

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    """
    FIXED: File upload, validation, and processing handler with no duplicate displays
    """
    
    def __init__(self):
        # Create cache directory if it doesn't exist
        self.cache_dir = Path("cache/files")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def create_upload_interface(self) -> Optional[Dict[str, Any]]:
        """FIXED: Complete file upload interface with no duplicate displays"""
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=Config.SUPPORTED_FILE_TYPES,
            help=f"Maximum file size: {Config.MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file is not None:
            return self._process_uploaded_file(uploaded_file)
        
        return None
    
    def _process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """FIXED: Process uploaded file with single display of file info"""
        try:
            # Step 1: Validate file
            validation_result = self.validate_file(uploaded_file)
            
            if not validation_result['valid']:
                return {"error": validation_result['error']}
            
            # Step 2: Extract metadata
            metadata = self._extract_basic_metadata(uploaded_file)
            
            # Step 3: Check cache
            file_hash = self._calculate_file_hash(uploaded_file.getvalue())
            cached_result = self._check_cache_simple(file_hash)
            
            # Step 4: Prepare for processing
            file_data = self._prepare_for_processing(uploaded_file, metadata)
            
            if 'error' in file_data:
                return {"error": file_data['error']}
            
            # FIXED: Single display of cache info (no duplicate file metrics)
            if cached_result:
                st.info("⚡ Found cached results - processing will be faster!")
                metadata['cache_hit'] = True
                metadata['cached_result'] = cached_result
            
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
        """Validate uploaded file with comprehensive checks"""
        try:
            # Check file size
            if uploaded_file.size > Config.MAX_FILE_SIZE_BYTES:
                return {
                    'valid': False,
                    'error': f"File too large. Maximum size: {Config.MAX_FILE_SIZE_MB}MB"
                }
            
            # Check minimum file size
            if uploaded_file.size < 100:  # Less than 100 bytes
                return {
                    'valid': False,
                    'error': "File too small or empty"
                }
            
            # Check file type
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if not Config.validate_file_type(file_extension):
                return {
                    'valid': False,
                    'error': f"Unsupported file type. Supported: {', '.join(Config.SUPPORTED_FILE_TYPES)}"
                }
            
            # Additional validation for images
            if file_extension in ['jpg', 'jpeg', 'png']:
                image_validation = self._validate_image_comprehensive(uploaded_file.getvalue())
                if not image_validation['valid']:
                    return image_validation
            
            # Validate PDF files
            if file_extension == 'pdf':
                pdf_validation = self._validate_pdf_basic(uploaded_file.getvalue())
                if not pdf_validation['valid']:
                    return pdf_validation
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"File validation failed: {str(e)}"
            }
    
    def _validate_image_comprehensive(self, file_bytes: bytes) -> Dict[str, Any]:
        """Enhanced image validation"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Check image dimensions
            if image.width < 50 or image.height < 50:
                return {
                    'valid': False,
                    'error': "Image too small for text extraction (minimum 50x50 pixels)"
                }
            
            # Check if image is too large (memory consideration)
            if image.width * image.height > 50_000_000:  # 50 megapixels
                return {
                    'valid': False,
                    'error': "Image too large for processing (max 50MP)"
                }
            
            # Check image mode
            if image.mode not in ['RGB', 'RGBA', 'L', 'P']:
                return {
                    'valid': False,
                    'error': f"Unsupported image mode: {image.mode}"
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Invalid image file: {str(e)}"
            }
    
    def _validate_pdf_basic(self, file_bytes: bytes) -> Dict[str, Any]:
        """Basic PDF validation"""
        try:
            # Check PDF magic number
            if not file_bytes.startswith(b'%PDF-'):
                return {
                    'valid': False,
                    'error': "Invalid PDF file format"
                }
            
            # Check if PDF has EOF marker
            if b'%%EOF' not in file_bytes[-1024:]:
                return {
                    'valid': False,
                    'error': "Corrupted PDF file (missing EOF)"
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"PDF validation failed: {str(e)}"
            }
    
    def _extract_basic_metadata(self, uploaded_file) -> Dict[str, Any]:
        """Extract comprehensive file metadata"""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        metadata = {
            "filename": uploaded_file.name,
            "file_extension": file_extension,
            "file_size_bytes": uploaded_file.size,
            "file_size_mb": file_size_mb,
            "upload_timestamp": datetime.now().isoformat(),
            "estimated_pages": self._estimate_pages_advanced(uploaded_file.size, file_extension),
            "processing_complexity": self._estimate_processing_complexity(file_extension, file_size_mb)
        }
        
        # Add file-specific metadata
        if file_extension in ['jpg', 'jpeg', 'png']:
            metadata.update(self._extract_image_metadata(uploaded_file.getvalue()))
        elif file_extension == 'pdf':
            metadata.update(self._extract_pdf_metadata(uploaded_file.getvalue()))
        
        return metadata
    
    def _extract_image_metadata(self, file_bytes: bytes) -> Dict[str, Any]:
        """Extract image-specific metadata"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            return {
                "image_width": image.width,
                "image_height": image.height,
                "image_mode": image.mode,
                "image_format": image.format,
                "estimated_text_density": self._estimate_text_density(image)
            }
        except Exception:
            return {"image_metadata_error": "Could not extract image metadata"}
    
    def _extract_pdf_metadata(self, file_bytes: bytes) -> Dict[str, Any]:
        """Extract PDF-specific metadata"""
        try:
            # Basic PDF analysis
            pdf_text = file_bytes.decode('latin-1', errors='ignore')
            
            # Count pages (rough estimate)
            page_count = pdf_text.count('/Type /Page')
            if page_count == 0:
                page_count = pdf_text.count('%%Page:')
            
            return {
                "pdf_estimated_pages": max(1, page_count),
                "pdf_has_text": '/Font' in pdf_text or 'Tj' in pdf_text,
                "pdf_has_images": '/Image' in pdf_text or '/XObject' in pdf_text
            }
        except Exception:
            return {"pdf_metadata_error": "Could not extract PDF metadata"}
    
    def _estimate_text_density(self, image: Image.Image) -> str:
        """Estimate text density in image"""
        # Simple heuristic based on image characteristics
        width, height = image.size
        total_pixels = width * height
        
        if total_pixels < 100_000:  # Small image
            return "low"
        elif image.mode == 'L' or (image.mode == 'RGB' and self._is_mostly_text_colors(image)):
            return "high"
        else:
            return "medium"
    
    def _is_mostly_text_colors(self, image: Image.Image) -> bool:
        """Check if image has typical text colors (black/white dominant)"""
        try:
            # Convert to grayscale for analysis
            grayscale = image.convert('L')
            # Sample pixels
            pixels = list(grayscale.getdata())
            
            # Count black/white-ish pixels
            text_like_pixels = sum(1 for p in pixels[::100] if p < 50 or p > 200)
            sample_size = len(pixels[::100])
            
            return (text_like_pixels / sample_size) > 0.6 if sample_size > 0 else False
        except Exception:
            return False
    
    def _estimate_pages_advanced(self, file_size: int, extension: str) -> int:
        """Advanced page estimation with better accuracy"""
        if extension == 'pdf':
            # Better PDF page estimation
            if file_size < 50_000:  # < 50KB
                return 1
            elif file_size < 500_000:  # < 500KB
                return max(1, file_size // 80_000)
            else:
                return max(1, file_size // 120_000)
        elif extension in ['jpg', 'jpeg', 'png']:
            return 1
        elif extension == 'txt':
            # Text files: ~3KB per page
            return max(1, file_size // 3_000)
        elif extension == 'docx':
            # Word docs: ~50KB per page
            return max(1, file_size // 50_000)
        else:
            return 1
    
    def _estimate_processing_complexity(self, extension: str, file_size_mb: float) -> str:
        """Estimate processing complexity"""
        if extension == 'txt':
            return "low"
        elif extension in ['jpg', 'jpeg', 'png']:
            if file_size_mb > 5:
                return "high"
            elif file_size_mb > 2:
                return "medium"
            else:
                return "low"
        elif extension == 'pdf':
            if file_size_mb > 10:
                return "high"
            elif file_size_mb > 3:
                return "medium"
            else:
                return "low"
        else:
            return "medium"
    
    def _prepare_for_processing(self, uploaded_file, metadata: Dict) -> Dict[str, Any]:
        """Prepare file data for Azure processing with optimization"""
        try:
            file_bytes = uploaded_file.getvalue()
            extension = metadata["file_extension"]
            
            # Enhanced content type mapping
            content_type_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'txt': 'text/plain',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
            content_type = content_type_map.get(extension, 'application/octet-stream')
            
            processed_data = {
                "file_bytes": file_bytes,
                "content_type": content_type,
                "processing_info": {
                    "needs_ocr": extension in ['pdf', 'jpg', 'jpeg', 'png'],
                    "is_text_file": extension == 'txt',
                    "azure_compatible": extension in ['pdf', 'jpg', 'jpeg', 'png'],
                    "direct_text_available": extension == 'txt',
                    "estimated_processing_time": self._estimate_processing_time(metadata),
                    "optimization_applied": False
                }
            }
            
            # Handle text files directly
            if extension == 'txt':
                text_result = self._extract_text_from_txt(file_bytes)
                processed_data.update(text_result)
            
            # Optimize large images for processing
            elif extension in ['jpg', 'jpeg', 'png'] and metadata.get('file_size_mb', 0) > 3:
                optimized_result = self._optimize_image_for_processing(file_bytes)
                if optimized_result.get('success'):
                    processed_data["file_bytes"] = optimized_result["optimized_bytes"]
                    processed_data["processing_info"]["optimization_applied"] = True
                    processed_data["processing_info"]["original_size_mb"] = metadata['file_size_mb']
                    processed_data["processing_info"]["optimized_size_mb"] = len(optimized_result["optimized_bytes"]) / (1024 * 1024)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"File preparation error: {e}")
            return {"error": f"Failed to prepare file: {str(e)}"}
    
    def _extract_text_from_txt(self, file_bytes: bytes) -> Dict[str, Any]:
        """Extract text from TXT files with encoding detection"""
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                text_content = file_bytes.decode(encoding)
                return {
                    "direct_text": text_content,
                    "text_length": len(text_content),
                    "encoding_used": encoding,
                    "word_count": len(text_content.split()),
                    "line_count": text_content.count('\n') + 1
                }
            except UnicodeDecodeError:
                continue
        
        return {
            "direct_text": None,
            "text_error": "Could not decode text file with any supported encoding"
        }
    
    def _optimize_image_for_processing(self, file_bytes: bytes) -> Dict[str, Any]:
        """Optimize large images for better processing"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Calculate optimal size (target: ~2MP for OCR)
            width, height = image.size
            total_pixels = width * height
            
            if total_pixels > 2_000_000:  # 2 megapixels
                # Calculate scale factor
                scale_factor = (2_000_000 / total_pixels) ** 0.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # Resize image
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to bytes
                output_buffer = io.BytesIO()
                
                # Optimize format and quality
                if image.format == 'PNG':
                    resized_image.save(output_buffer, format='PNG', optimize=True)
                else:
                    # Convert to JPEG for better compression
                    if resized_image.mode in ('RGBA', 'LA', 'P'):
                        resized_image = resized_image.convert('RGB')
                    resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                
                optimized_bytes = output_buffer.getvalue()
                
                return {
                    "success": True,
                    "optimized_bytes": optimized_bytes,
                    "original_size": len(file_bytes),
                    "optimized_size": len(optimized_bytes),
                    "compression_ratio": len(optimized_bytes) / len(file_bytes),
                    "new_dimensions": (new_width, new_height),
                    "original_dimensions": (width, height)
                }
            
            return {"success": False, "reason": "No optimization needed"}
            
        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            return {"success": False, "error": str(e)}
    
    def _estimate_processing_time(self, metadata: Dict) -> str:
        """Estimate processing time based on file characteristics"""
        extension = metadata.get('file_extension', '')
        file_size_mb = metadata.get('file_size_mb', 0)
        complexity = metadata.get('processing_complexity', 'medium')
        
        if extension == 'txt':
            return "< 5 seconds"
        elif complexity == 'low':
            return "5-15 seconds"
        elif complexity == 'medium':
            return "15-45 seconds"
        else:
            return "45-120 seconds"
    
    def _calculate_file_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash for better caching"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]  # Use first 16 chars
    
    def _check_cache_simple(self, file_hash: str) -> Optional[Dict]:
        """Check if cached result exists with expiry"""
        cache_file = self.cache_dir / f"{file_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is expired (24 hours)
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', ''))
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    return cached_data
                else:
                    # Remove expired cache
                    cache_file.unlink()
                    
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        return None
    
    def cache_result(self, file_hash: str, result_data: Dict) -> bool:
        """Cache processing result with metadata"""
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            
            # Add cache metadata
            cache_data = {
                **result_data,
                "cache_metadata": {
                    "cached_at": datetime.now().isoformat(),
                    "cache_version": "1.0",
                    "file_hash": file_hash
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached result for file hash: {file_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    def get_processing_recommendations(self, file_metadata: Dict) -> Dict[str, str]:
        """Get intelligent processing recommendations"""
        recommendations = {}
        
        file_size_mb = file_metadata.get('file_size_mb', 0)
        file_extension = file_metadata.get('file_extension', '')
        complexity = file_metadata.get('processing_complexity', 'medium')
        
        if file_size_mb > 10:
            recommendations['size'] = "⚠️ Large file - processing may take 2-3 minutes"
        elif file_size_mb > 5:
            recommendations['size'] = "📊 Medium file - processing may take 1-2 minutes"
        
        if file_extension in ['jpg', 'jpeg', 'png']:
            recommendations['image'] = "📸 Ensure image has clear, readable text for best results"
            if file_metadata.get('estimated_text_density') == 'low':
                recommendations['text_density'] = "⚠️ Low text density detected - results may be limited"
        
        if file_extension == 'pdf':
            if file_metadata.get('pdf_has_text'):
                recommendations['pdf'] = "✅ Text-based PDF detected - excellent for processing"
            else:
                recommendations['pdf'] = "📄 Scanned PDF detected - OCR will be used"
        
        if complexity == 'high':
            recommendations['complexity'] = "🔧 Complex file - consider breaking into smaller parts"
        
        return recommendations
    
    def cleanup_old_cache(self, days_old: int = 7) -> int:
        """Clean up old cache files"""
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (days_old * 86400)
            
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned {cleaned_count} old cache files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

# Create global instance
file_handler = FileHandler()