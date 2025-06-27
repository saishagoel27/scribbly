import logging
import time
from functools import wraps
from typing import Dict, List, Optional, Any
from azure.ai.textanalytics import TextAnalyticsClient, ExtractiveSummaryAction
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
from concurrent.futures import TimeoutError

from config import azure_config

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = None, delay: float = None):
    """Decorator for retrying failed Azure operations with exponential backoff"""
    max_retries = max_retries or azure_config.max_retries
    delay = delay or azure_config.retry_delay
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (AzureError, HttpResponseError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
                except Exception as e:
                    logger.error(f"Non-retryable error: {e}")
                    raise e
            raise last_exception
        return wrapper
    return decorator

class AzureLanguageService:
    """Enhanced Azure Language Service client"""
    
    def __init__(self):
        self.client = None
        if azure_config.is_language_configured:
            try:
                self.client = TextAnalyticsClient(
                    endpoint=azure_config.language_endpoint,
                    credential=AzureKeyCredential(azure_config.language_key)
                )
                logger.info("Azure Language Service client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Language Service client: {e}")
    
    @property
    def is_available(self) -> bool:
        return self.client is not None
    
    @retry_on_failure()
    def extract_key_phrases(self, text: str, language: str = "en") -> List[str]:
        """Extract key phrases from text"""
        if not self.client:
            raise Exception("Language service not available")
        
        try:
            response = self.client.extract_key_phrases(
                documents=[text], 
                language=language
            )
            
            if response and not response[0].is_error:
                return response[0].key_phrases
            else:
                error_msg = response[0].error.message if response and response[0].is_error else "Unknown error"
                raise Exception(f"Key phrase extraction failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Key phrase extraction error: {e}")
            raise
    
    @retry_on_failure()
    def summarize_text(self, text: str, max_sentences: int = 3) -> Optional[str]:
        """Summarize text using extractive summarization"""
        if not self.client:
            raise Exception("Language service not available")
        
        try:
            # Use the newer extractive summarization
            poller = self.client.begin_analyze_actions(
                documents=[text],
                actions=[
                    ExtractiveSummaryAction(max_sentence_count=max_sentences, order_by="Rank")
                ]
            )
            
            results = poller.result()
            
            for result in results:
                if result.extract_summary_results:
                    summary_result = result.extract_summary_results[0]
                    if not summary_result.is_error:
                        sentences = [sentence.text for sentence in summary_result.sentences]
                        return " ".join(sentences)
                    else:
                        logger.error(f"Summarization error: {summary_result.error}")
            
            return None
            
        except Exception as e:
            logger.error(f"Text summarization error: {e}")
            raise
    
    @retry_on_failure()
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not self.client:
            raise Exception("Language service not available")
        
        try:
            response = self.client.analyze_sentiment(documents=[text])
            
            if response and not response[0].is_error:
                result = response[0]
                return {
                    "sentiment": result.sentiment,
                    "confidence_scores": {
                        "positive": result.confidence_scores.positive,
                        "neutral": result.confidence_scores.neutral,
                        "negative": result.confidence_scores.negative
                    }
                }
            else:
                error_msg = response[0].error.message if response and response[0].is_error else "Unknown error"
                raise Exception(f"Sentiment analysis failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            raise

class AzureDocumentIntelligence:
    """Enhanced Azure Document Intelligence client"""
    
    def __init__(self):
        self.client = None
        if azure_config.is_document_intelligence_configured:
            try:
                self.client = DocumentAnalysisClient(
                    endpoint=azure_config.document_intelligence_endpoint,
                    credential=AzureKeyCredential(azure_config.document_intelligence_key)
                )
                logger.info("Azure Document Intelligence client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Document Intelligence client: {e}")
    
    @property
    def is_available(self) -> bool:
        return self.client is not None
    
    @retry_on_failure()
    def extract_text_from_document(self, file_bytes: bytes) -> Dict[str, Any]:
        """Extract text from document using layout analysis"""
        if not self.client:
            raise Exception("Document Intelligence service not available")
        
        try:
            poller = self.client.begin_analyze_document(
                "prebuilt-layout", 
                document=file_bytes
            )
            result = poller.result()
            
            # Extract structured information
            structure = {
                "content": result.content or "",
                "paragraphs": [],
                "tables": [],
                "headings": [],
                "key_value_pairs": []
            }
            
            # Process paragraphs with role detection
            for paragraph in result.paragraphs:
                para_info = {
                    "content": paragraph.content.strip(),
                    "role": getattr(paragraph, 'role', 'paragraph'),
                    "confidence": getattr(paragraph, 'confidence', 1.0)
                }
                
                if para_info["role"] in ["title", "sectionHeading"]:
                    structure["headings"].append(para_info["content"])
                else:
                    structure["paragraphs"].append(para_info["content"])
            
            # Process tables
            for table in result.tables:
                if table.cells:
                    table_data = self._format_table(table)
                    structure["tables"].append(table_data)
            
            # Process key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_text = kv_pair.key.content.strip()
                    value_text = kv_pair.value.content.strip()
                    if key_text and value_text:
                        structure["key_value_pairs"].append({
                            "key": key_text,
                            "value": value_text
                        })
            
            logger.info(f"Document analysis complete: {len(structure['paragraphs'])} paragraphs, "
                       f"{len(structure['headings'])} headings, {len(structure['tables'])} tables")
            
            return structure
            
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            raise
    
    @retry_on_failure()
    def extract_text_from_image(self, file_bytes: bytes) -> str:
        """Extract text from image using OCR"""
        if not self.client:
            raise Exception("Document Intelligence service not available")
        
        try:
            poller = self.client.begin_analyze_document(
                "prebuilt-read", 
                document=file_bytes
            )
            result = poller.result()
            
            if result.content:
                return result.content.strip()
            
            # Fallback to line-by-line extraction
            lines = []
            for page in result.pages:
                for line in page.lines:
                    if line.content.strip():
                        lines.append(line.content.strip())
            
            content = "\n".join(lines)
            
            if not content.strip():
                raise Exception("No text detected in image")
            
            logger.info(f"OCR extracted {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            raise
    
    def _format_table(self, table) -> str:
        """Format table data into readable text"""
        try:
            table_rows = {}
            for cell in table.cells:
                row = cell.row_index
                if row not in table_rows:
                    table_rows[row] = []
                table_rows[row].append(cell.content or "")
            
            formatted_rows = []
            for row_idx in sorted(table_rows.keys()):
                formatted_rows.append(" | ".join(table_rows[row_idx]))
            
            return "\n".join(formatted_rows)
        except Exception as e:
            logger.warning(f"Table formatting error: {e}")
            return "Table data (formatting error)"

class AzureServiceManager:
    """Manages all Azure services with health checks"""
    
    def __init__(self):
        self.language_service = AzureLanguageService()
        self.document_intelligence = AzureDocumentIntelligence()
    
    def get_health_status(self) -> Dict[str, bool]:
        """Check health status of all services"""
        return {
            "language_service": self.language_service.is_available,
            "document_intelligence": self.document_intelligence.is_available
        }
    
    def get_available_services(self) -> List[str]:
        """Get list of available services"""
        services = []
        if self.language_service.is_available:
            services.append("language_service")
        if self.document_intelligence.is_available:
            services.append("document_intelligence")
        return services

# Global service manager instance
azure_services = AzureServiceManager()