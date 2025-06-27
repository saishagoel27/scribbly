"""
File processing utilities for different document types.
"""
import io
import logging
import re
from typing import Optional, Dict, Any
import docx
import pdfplumber
from PIL import Image

from config import app_config
from azure_clients import azure_services

logger = logging.getLogger(__name__)

class FileProcessor:
    """Base class for file processors"""
    
    @staticmethod
    def validate_file_size(file, is_image: bool = False) -> None:
        """Validate file size against limits"""
        max_size = app_config.max_image_size if is_image else app_config.max_document_size
        
        if file.size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise ValueError(f"File too large. Maximum size: {size_mb:.1f}MB")
        
        if file.size == 0:
            raise ValueError("File is empty")
    
    @staticmethod
    def get_file_info(file) -> Dict[str, Any]:
        """Extract file metadata"""
        try:
            size_kb = file.size / 1024
            size_display = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            
            return {
                "filename": file.name,
                "filetype": file.type or "Unknown",
                "filesize": size_display,
                "size_bytes": file.size
            }
        except Exception as e:
            logger.warning(f"Failed to get file info: {e}")
            return {
                "filename": getattr(file, 'name', 'Unknown'),
                "filetype": "Unknown",
                "filesize": "Unknown",
                "size_bytes": 0
            }

class TextFileProcessor(FileProcessor):
    """Processor for text files"""
    
    @classmethod
    def process(cls, file) -> str:
        """Process text file with encoding detection"""
        cls.validate_file_size(file)
        
        try:
            file.seek(0)
            content = file.read()
            
            # Try UTF-8 first
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        file.seek(0)
                        return file.read().decode(encoding)
                    except UnicodeDecodeError:
                        continue
                
                # Last resort - decode with error handling
                file.seek(0)
                return file.read().decode("utf-8", errors="replace")
                
        except Exception as e:
            logger.error(f"Failed to process text file: {e}")
            raise Exception(f"Could not read text file: {str(e)}")

class DOCXProcessor(FileProcessor):
    """Processor for DOCX files"""
    
    @classmethod
    def process(cls, file) -> str:
        """Process DOCX file"""
        cls.validate_file_size(file)
        
        try:
            doc = docx.Document(file)
            paragraphs = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:  # Only add non-empty paragraphs
                    paragraphs.append(text)
            
            if not paragraphs:
                raise Exception("No readable text found in DOCX file")
            
            content = "\n\n".join(paragraphs)
            logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX")
            return content
            
        except Exception as e:
            logger.error(f"Failed to process DOCX file: {e}")
            raise Exception(f"Could not read DOCX file: {str(e)}")

class PDFProcessor(FileProcessor):
    """Processor for PDF files"""
    
    @classmethod
    def process(cls, file, max_pages: int = 50) -> str:
        """Process PDF file with page limits"""
        cls.validate_file_size(file)
        
        try:
            text_parts = []
            page_count = 0
            
            with pdfplumber.open(file) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Processing PDF with {total_pages} pages")
                
                for page_num, page in enumerate(pdf.pages):
                    if page_count >= max_pages:
                        logger.warning(f"Stopped processing PDF at {max_pages} pages limit")
                        break
                    
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            # Clean up the text
                            page_text = re.sub(r'\n+', '\n', page_text)
                            page_text = re.sub(r' +', ' ', page_text)
                            
                            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}")
                            page_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
            
            if not text_parts:
                raise Exception("No readable text found in PDF")
            
            content = "\n\n".join(text_parts)
            logger.info(f"Extracted text from {page_count} pages")
            return content
            
        except Exception as e:
            logger.error(f"Failed to process PDF file: {e}")
            raise Exception(f"Could not read PDF file: {str(e)}")

class ImageProcessor(FileProcessor):
    """Processor for image files using Azure OCR"""
    
    @classmethod
    def process(cls, file) -> str:
        """Process image file using OCR"""
        cls.validate_file_size(file, is_image=True)
        
        if not azure_services.document_intelligence.is_available:
            raise Exception("OCR service not available. Please configure Azure Document Intelligence.")
        
        try:
            file.seek(0)
            file_bytes = file.read()
            
            if len(file_bytes) == 0:
                raise Exception("Image file is empty")
            
            # Validate image format
            try:
                with Image.open(io.BytesIO(file_bytes)) as img:
                    img.verify()
                    logger.info(f"Processing image: {img.format} {img.size}")
            except Exception as e:
                raise Exception(f"Invalid or corrupted image file: {str(e)}")
            
            # Extract text using Azure Document Intelligence
            content = azure_services.document_intelligence.extract_text_from_image(file_bytes)
            
            if not content.strip():
                raise Exception("No readable text found in image")
            
            return content
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise Exception(f"Could not extract text from image: {str(e)}")

class DocumentProcessor:
    """Main document processor that routes to appropriate handlers"""
    
    # File type to processor mapping
    PROCESSORS = {
        '.txt': TextFileProcessor,
        '.docx': DOCXProcessor, 
        '.pdf': PDFProcessor,
        '.jpg': ImageProcessor,
        '.jpeg': ImageProcessor,
        '.png': ImageProcessor,
        '.bmp': ImageProcessor,
        '.tiff': ImageProcessor,
        '.gif': ImageProcessor,
    }
    
    @classmethod
    def process_file(cls, file) -> tuple[str, Dict[str, Any]]:
        """
        Process uploaded file and return text content with metadata
        
        Returns:
            tuple: (extracted_text, file_info_dict)
        """
        if not file:
            raise ValueError("No file provided")
        
        filename = file.name.lower()
        
        # Find appropriate processor
        processor = None
        for ext, proc_class in cls.PROCESSORS.items():
            if filename.endswith(ext):
                processor = proc_class
                break
        
        if not processor:
            supported_types = list(cls.PROCESSORS.keys())
            raise ValueError(f"Unsupported file type. Supported: {', '.join(supported_types)}")
        
        # Process the file
        logger.info(f"Processing {filename} with {processor.__name__}")
        text_content = processor.process(file)
        
        # Get file metadata
        file_info = FileProcessor.get_file_info(file)
        
        # Add processing statistics
        file_info.update({
            "character_count": len(text_content),
            "word_count": len(text_content.split()),
            "processor_used": processor.__name__
        })
        
        logger.info(f"Successfully processed {filename}: {file_info['character_count']} chars")
        
        return text_content, file_info
    
    @classmethod
    def get_supported_formats(cls) -> Dict[str, list]:
        """Get supported file formats categorized"""
        text_formats = [ext for ext in cls.PROCESSORS.keys() 
                       if ext in app_config.supported_text_formats]
        image_formats = [ext for ext in cls.PROCESSORS.keys() 
                        if ext in app_config.supported_image_formats]
        
        return {
            "text_formats": text_formats,
            "image_formats": image_formats,
            "all_formats": list(cls.PROCESSORS.keys())
        }