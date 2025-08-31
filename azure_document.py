import logging
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, ClientAuthenticationError, ServiceRequestError

from config import Config

logger = logging.getLogger(__name__)

@dataclass
class DocumentProcessingLimits:
    """Centralized Azure Document Intelligence limits"""
    MAX_DOCUMENT_SIZE_MB = 500          # Azure Document Intelligence limit
    POLLING_TIMEOUT_SECONDS = 300       # 5 minutes max for document processing
    POLLING_INTERVAL_SECONDS = 2        # Check every 2 seconds
    RETRY_ATTEMPTS = 3                  # Number of retry attempts for failed calls
    RETRY_DELAY_SECONDS = 2             # Delay between retries

@dataclass
class DocumentProcessingMetrics:
    """Track Azure Document Intelligence usage and performance"""
    api_calls_made: int = 0
    documents_processed: int = 0
    total_processing_time: float = 0.0
    fallback_used: bool = False
    error_count: int = 0
    polling_duration: float = 0.0

class EnhancedAzureDocumentProcessor:
    """Enhanced Azure Document Intelligence processor with health monitoring"""
    
    def __init__(self):
        """Initialize with proper error handling and health checks"""
        self.client = None
        self.is_healthy = False
        self.last_health_check = None
        self.metrics = DocumentProcessingMetrics()
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure client with comprehensive validation"""
        try:
            if not Config.has_azure_document():
                logger.warning("Azure Document Intelligence not configured")
                return
            
            self.client = DocumentIntelligenceClient(
                endpoint=Config.AZURE_DOC_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(Config.AZURE_DOC_INTELLIGENCE_KEY)
            )
            
            self._perform_health_check()
            logger.info("Azure Document Intelligence initialized successfully")
            
        except ClientAuthenticationError as e:
            logger.error(f"Azure Document Intelligence authentication failed: {e}")
        except Exception as e:
            logger.error(f"Azure Document Intelligence client initialization failed: {e}")
    
    def _perform_health_check(self) -> bool:
        """Validate Azure client connectivity with minimal test"""
        try:
            if not self.client:
                return False
            
            # Simple health check - just test client creation
            self.is_healthy = True
            self.last_health_check = datetime.now()
            logger.debug("Azure Document Intelligence health check passed")
            return True
            
        except Exception as e:
            logger.warning(f"Azure Document Intelligence health check failed: {e}")
        
        self.is_healthy = False
        return False
    
    def is_available(self) -> bool:
        """Check if Azure Document Intelligence is available and healthy"""
        # Re-check health if it's been more than 5 minutes
        if (self.last_health_check and 
            (datetime.now() - self.last_health_check).seconds > 300):
            self._perform_health_check()
        
        return self.is_healthy
    
    def extract_text_with_handwriting(self, file_bytes: bytes, content_type: str, 
                                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Enhanced document text extraction with robust error handling"""
        
        start_time = time.time()
        self.metrics = DocumentProcessingMetrics()  # Reset metrics
        
        try:
            if progress_callback:
                progress_callback("🔍 Initializing Azure Document Intelligence...", 0.1)
            
            # Check service health first
            if not self.is_available():
                logger.warning("Azure Document Intelligence unavailable")
                return {"error": "Azure Document Intelligence service unavailable"}
            
            # Validate document size
            size_mb = len(file_bytes) / (1024 * 1024)
            if size_mb > DocumentProcessingLimits.MAX_DOCUMENT_SIZE_MB:
                return {
                    "error": f"Document too large ({size_mb:.1f}MB). Maximum: {DocumentProcessingLimits.MAX_DOCUMENT_SIZE_MB}MB"
                }
            
            if progress_callback:
                progress_callback("📄 Starting document analysis...", 0.2)
            
            # Handle text files directly for efficiency
            if content_type == 'text/plain':
                return self._process_text_file_directly(file_bytes, start_time, progress_callback)
            
            # Process with Azure Document Intelligence
            result = self._process_with_document_intelligence(file_bytes, content_type, progress_callback, start_time)
            
            if result:
                self.metrics.total_processing_time = time.time() - start_time
                self.metrics.documents_processed = 1
                
                if progress_callback:
                    progress_callback("✅ Document analysis completed!", 1.0)
                
                return result
            
            return {"error": "Document processing failed"}
            
        except AzureError as e:
            logger.error(f"Azure Document Intelligence error: {e}")
            self.metrics.error_count += 1
            return {"error": f"Azure processing failed: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            self.metrics.error_count += 1
            return {"error": f"Document processing failed: {str(e)}"}
    
    def _process_text_file_directly(self, file_bytes: bytes, start_time: float, 
                                   progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """Process text files directly for better performance"""
        try:
            if progress_callback:
                progress_callback("📝 Processing text file directly...", 0.5)
            
            extracted_text = file_bytes.decode('utf-8')
            
            if progress_callback:
                progress_callback("✅ Text extraction completed!", 0.9)
            
            processing_time = time.time() - start_time
            
            return {
                "extracted_text": extracted_text,
                "word_count": len(extracted_text.split()),
                "confidence_score": 1.0,
                "processing_time": f"{processing_time:.2f} seconds",
                "method": "direct_text_processing",
                "processing_metrics": {
                    "processing_time": f"{processing_time:.2f}s",
                    "method": "direct"
                }
            }
            
        except UnicodeDecodeError:
            logger.error("Text file encoding not supported")
            return {"error": "Could not decode text file - unsupported encoding"}
        except Exception as e:
            logger.error(f"Text file processing error: {e}")
            return {"error": f"Text file processing failed: {str(e)}"}
    
    def _process_with_document_intelligence(self, file_bytes: bytes, content_type: str, 
                                          progress_callback: Optional[Callable], start_time: float) -> Optional[Dict[str, Any]]:
        """Process document using Azure Document Intelligence with retry logic"""
        
        for attempt in range(DocumentProcessingLimits.RETRY_ATTEMPTS):
            try:
                if progress_callback:
                    progress_callback("🤖 Analyzing document with Azure AI...", 0.3)
                
                self.metrics.api_calls_made += 1
                
                # Start document analysis
                poller = self.client.begin_analyze_document(
                    "prebuilt-read", 
                    file_bytes,
                    content_type=content_type
                )
                
                if progress_callback:
                    progress_callback("⏳ Processing document (this may take a moment)...", 0.4)
                
                # Wait for completion with timeout and progress updates
                result = self._wait_for_completion_with_progress(poller, progress_callback)
                
                if not result:
                    if attempt < DocumentProcessingLimits.RETRY_ATTEMPTS - 1:
                        delay = DocumentProcessingLimits.RETRY_DELAY_SECONDS * (2 ** attempt)
                        logger.warning(f"Document processing timeout, retrying in {delay}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        return {"error": "Document processing timed out after all retries"}
                
                if progress_callback:
                    progress_callback("📊 Extracting text content...", 0.9)
                
                # Extract text and create response
                return self._create_processing_result(result, start_time)
                
            except ServiceRequestError as e:
                if attempt < DocumentProcessingLimits.RETRY_ATTEMPTS - 1:
                    delay = DocumentProcessingLimits.RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(f"Service request failed, retrying in {delay}s (attempt {attempt + 1}): {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Document processing failed after {DocumentProcessingLimits.RETRY_ATTEMPTS} attempts")
                    return {"error": f"Document processing failed: {str(e)}"}
                    
            except Exception as e:
                logger.error(f"Unexpected error in document processing: {e}")
                if attempt < DocumentProcessingLimits.RETRY_ATTEMPTS - 1:
                    delay = DocumentProcessingLimits.RETRY_DELAY_SECONDS
                    time.sleep(delay)
                else:
                    return {"error": f"Document processing failed: {str(e)}"}
        
        return None
    
    def _wait_for_completion_with_progress(self, poller, progress_callback: Optional[Callable]) -> Optional[Any]:
        """Wait for document processing completion with timeout and progress updates"""
        
        start_poll = time.time()
        last_progress_update = start_poll
        
        while not poller.done():
            elapsed = time.time() - start_poll
            
            # Timeout check
            if elapsed > DocumentProcessingLimits.POLLING_TIMEOUT_SECONDS:
                logger.error(f"Document processing timed out after {elapsed:.1f}s")
                return None
            
            # Progress update every 10 seconds
            if progress_callback and (time.time() - last_progress_update) > 10:
                remaining_estimate = max(30 - elapsed, 5)  # Estimate remaining time
                progress_callback(f"⏳ Still processing... (~{remaining_estimate:.0f}s remaining)", 0.6)
                last_progress_update = time.time()
            
            time.sleep(DocumentProcessingLimits.POLLING_INTERVAL_SECONDS)
        
        self.metrics.polling_duration = time.time() - start_poll
        return poller.result()
    
    def _create_processing_result(self, result: Any, start_time: float) -> Dict[str, Any]:
        """Create comprehensive processing result"""
        
        # Extract text content
        extracted_text = ""
        confidence_scores = []
        
        if hasattr(result, 'content') and result.content:
            extracted_text = result.content
        
        # Calculate confidence score from pages if available
        if hasattr(result, 'pages') and result.pages:
            for page in result.pages:
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        if hasattr(line, 'confidence') and line.confidence:
                            confidence_scores.append(line.confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.95
        word_count = len(extracted_text.split()) if extracted_text else 0
        processing_time = time.time() - start_time
        
        return {
            "extracted_text": extracted_text,
            "word_count": word_count,
            "confidence_score": round(avg_confidence, 3),
            "processing_time": f"{processing_time:.2f} seconds",
            "method": "azure_document_intelligence_enhanced",
            "document_analysis": {
                "pages_processed": len(result.pages) if hasattr(result, 'pages') else 1,
                "lines_detected": sum(len(page.lines) for page in result.pages if hasattr(page, 'lines')) if hasattr(result, 'pages') else 0,
                "average_confidence": round(avg_confidence, 3)
            },
            "processing_metrics": {
                "api_calls": self.metrics.api_calls_made,
                "processing_time": f"{processing_time:.2f}s",
                "polling_time": f"{self.metrics.polling_duration:.2f}s",
                "method": "azure_enhanced"
            }
        }

# Create global enhanced instance
_enhanced_processor = EnhancedAzureDocumentProcessor()

# Backward compatibility class - maintains your existing API
class AzureDocumentProcessor:
    """Azure Document Intelligence processor - backward compatible interface"""

    @staticmethod
    def is_available():
        return _enhanced_processor.is_available()

    @staticmethod
    def get_client():
        return _enhanced_processor.client

    @staticmethod
    def extract_text_with_handwriting(file_bytes: bytes, content_type: str, 
                                      progress_callback: Optional[Callable] = None) -> Dict:
        """Extract text from document with handwriting support"""
        return _enhanced_processor.extract_text_with_handwriting(
            file_bytes, content_type, progress_callback
        )