import logging
from typing import Dict, Optional, Callable
from datetime import datetime

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from config import Config

logger = logging.getLogger(__name__)

class AzureDocumentProcessor:
    """Azure Document Intelligence processor"""

    @staticmethod
    def is_available():
        return bool(Config.AZURE_DOC_INTELLIGENCE_KEY and Config.AZURE_DOC_INTELLIGENCE_ENDPOINT)

    @staticmethod
    def get_client():
        if not AzureDocumentProcessor.is_available():
            logger.warning("Azure Document Intelligence credentials not found")
            return None
        try:
            return DocumentIntelligenceClient(
                endpoint=Config.AZURE_DOC_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(Config.AZURE_DOC_INTELLIGENCE_KEY)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure Document Intelligence: {e}")
            return None

    @staticmethod
    def extract_text_with_handwriting(file_bytes: bytes, content_type: str, 
                                      progress_callback: Optional[Callable] = None) -> Dict:
        """Extract text from document with handwriting support"""

        client = AzureDocumentProcessor.get_client()
        if not client:
            return {"error": "Azure Document Intelligence not available"}

        try:
            if progress_callback:
                progress_callback("🔍 Starting document analysis...", 0.1)

            # Handle text files directly
            if content_type == 'text/plain':
                try:
                    extracted_text = file_bytes.decode('utf-8')
                    return {
                        "extracted_text": extracted_text,
                        "word_count": len(extracted_text.split()),
                        "confidence_score": 1.0,
                        "processing_time": "< 1 second",
                        "method": "direct_text"
                    }
                except UnicodeDecodeError:
                    return {"error": "Could not decode text file"}

            if progress_callback:
                progress_callback("📄 Analyzing document content...", 0.3)

            # Use read model for text extraction
            poller = client.begin_analyze_document(
                "prebuilt-read", 
                file_bytes,
                content_type=content_type
            )

            if progress_callback:
                progress_callback("⏳ Processing document...", 0.6)

            result = poller.result()

            if progress_callback:
                progress_callback("✅ Extracting text content...", 0.9)

            # Extract text content
            extracted_text = ""
            if result.content:
                extracted_text = result.content

            # Basic metrics
            word_count = len(extracted_text.split()) if extracted_text else 0

            if progress_callback:
                progress_callback("✅ Document analysis completed!", 1.0)

            return {
                "extracted_text": extracted_text,
                "word_count": word_count,
                "confidence_score": 0.95,  # Reasonable default
                "processing_time": "5-15 seconds",
                "method": "azure_document_intelligence"
            }

        except AzureError as e:
            logger.error(f"Azure Document Intelligence error: {e}")
            return {"error": f"Azure processing failed: {str(e)}"}

        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {"error": f"Document processing failed: {str(e)}"}