import logging
import base64
import io
from typing import Dict, Optional, Callable
from datetime import datetime

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureDocumentProcessor:
    """
    SIMPLIFIED: Azure Document Intelligence processor for text extraction
    
    Removed complex fallback patterns and over-engineered processing
    """
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure Document Intelligence client"""
        try:
            if Config.AZURE_DOC_INTELLIGENCE_ENDPOINT and Config.AZURE_DOC_INTELLIGENCE_KEY:
                self.client = DocumentIntelligenceClient(
                    endpoint=Config.AZURE_DOC_INTELLIGENCE_ENDPOINT,
                    credential=AzureKeyCredential(Config.AZURE_DOC_INTELLIGENCE_KEY)
                )
                self.is_available = True
                logger.info("Azure Document Intelligence client initialized successfully")
            else:
                logger.warning("Azure Document Intelligence credentials not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Document Intelligence: {e}")
            self.is_available = False
    
    def extract_text_with_handwriting(self, 
                                    file_bytes: bytes, 
                                    content_type: str, 
                                    progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict:
        """
        FIXED: Extract text using Azure Document Intelligence
        
        Args:
            file_bytes: File content as bytes
            content_type: MIME type of file
            progress_callback: Optional callback for progress updates (message, progress)
            
        Returns:
            Dict with extraction results
        """
        
        if not self.is_available:
            return self._create_error_response("Azure Document Intelligence not available")
        
        try:
            if progress_callback:
                progress_callback("🔍 Connecting to Azure Document Intelligence...", 0.1)
            
            # Convert file to base64
            base64_content = base64.b64encode(file_bytes).decode('utf-8')
            
            if progress_callback:
                progress_callback("📄 Analyzing document structure...", 0.3)
            
            # Use prebuilt-read model for general text extraction
            poller = self.client.begin_analyze_document(
                "prebuilt-read", 
                {"base64Source": base64_content}
            )
            
            if progress_callback:
                progress_callback("⏳ Processing document (this may take a moment)...", 0.6)
            
            # Wait for completion
            result = poller.result()
            
            if progress_callback:
                progress_callback("✅ Document analysis complete!", 0.9)
            
            # Extract text content
            extracted_text = self._extract_text_content(result)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                return self._create_fallback_response("Insufficient text extracted")
            
            # FIXED: Extract the text from the result structure
            if hasattr(result, 'text_extraction'):
                final_text = result.text_extraction.get('extracted_text', extracted_text)
            else:
                final_text = extracted_text
            
            return self._format_success_response(final_text, result)
            
        except AzureError as e:
            error_msg = f"Azure API error: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg)
            
        except Exception as e:
            error_msg = f"Document processing error: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg)
    
    def _extract_text_content(self, result) -> str:
        """Extract clean text from Azure result"""
        try:
            if hasattr(result, 'content') and result.content:
                return result.content
            
            # Fallback: extract from pages
            if hasattr(result, 'pages') and result.pages:
                text_parts = []
                for page in result.pages:
                    if hasattr(page, 'lines') and page.lines:
                        for line in page.lines:
                            if hasattr(line, 'content'):
                                text_parts.append(line.content)
                
                return '\n'.join(text_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return ""
    
    def _calculate_quality_metrics(self, result) -> Dict:
        """Calculate basic quality metrics"""
        try:
            metrics = {
                "total_pages": len(result.pages) if hasattr(result, 'pages') and result.pages else 1,
                "total_lines": 0,
                "average_confidence": 0.0,
                "has_handwriting": False
            }
            
            if hasattr(result, 'pages') and result.pages:
                total_confidence = 0
                line_count = 0
                
                for page in result.pages:
                    if hasattr(page, 'lines') and page.lines:
                        for line in page.lines:
                            line_count += 1
                            if hasattr(line, 'confidence'):
                                total_confidence += line.confidence
                
                metrics["total_lines"] = line_count
                metrics["average_confidence"] = total_confidence / line_count if line_count > 0 else 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {"error": str(e)}
    
    def _format_success_response(self, extracted_text: str, result) -> Dict:
        """Format successful extraction response"""
        quality_metrics = self._calculate_quality_metrics(result)
        confidence_score = quality_metrics.get('average_confidence', 0.0)
        
        return {
            "status": "success",
            "extracted_text": extracted_text,  # FIXED: Return text directly at root level
            "confidence_score": confidence_score,  # FIXED: Add confidence at root level
            "text_extraction": {
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "processing_metadata": {
                    "processor": "azure_document_intelligence",
                    "model": "prebuilt-read",
                    "extraction_time": datetime.now().isoformat(),
                    "quality_metrics": quality_metrics,
                    "azure_available": True
                }
            }
        }
    
    def _create_fallback_response(self, message: str) -> Dict:
        """Create fallback response"""
        return {
            "status": "fallback",
            "extracted_text": "",  # FIXED: Add at root level
            "confidence_score": 0.0,  # FIXED: Add at root level
            "text_extraction": {
                "extracted_text": "",
                "processing_metadata": {
                    "processor": "azure_fallback",
                    "fallback_reason": message,
                    "azure_available": self.is_available
                }
            }
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            "status": "error",
            "error": error_message,
            "extracted_text": "",  # FIXED: Add at root level
            "confidence_score": 0.0,  # FIXED: Add at root level
            "text_extraction": {
                "extracted_text": "",
                "processing_metadata": {
                    "processor": "azure_error",
                    "error_time": datetime.now().isoformat(),
                    "azure_available": self.is_available
                }
            }
        }
    
    # ========== OPTIONAL: TEXT FILE DIRECT PROCESSING ==========
    
    def process_text_file_directly(self, file_bytes: bytes) -> Dict:
        """Process text file without Azure (fallback)"""
        try:
            # Try to decode text
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = file_bytes.decode(encoding)
                    return {
                        "status": "success",
                        "extracted_text": text_content,  # FIXED: Add at root level
                        "confidence_score": 1.0,  # FIXED: Add at root level
                        "text_extraction": {
                            "extracted_text": text_content,
                            "processing_metadata": {
                                "processor": "direct_text",
                                "encoding_used": encoding,
                                "azure_available": self.is_available
                            }
                        }
                    }
                except UnicodeDecodeError:
                    continue
            
            return self._create_error_response("Could not decode text file")
            
        except Exception as e:
            return self._create_error_response(f"Text processing error: {str(e)}")

# Create global instance
azure_document_processor = AzureDocumentProcessor()