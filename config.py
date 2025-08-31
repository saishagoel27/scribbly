import os
import logging
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Set up logging for configuration issues
logger = logging.getLogger(__name__)

# Safely load environment variables
try:
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")
class Config:
    """Configuration for Scribbly - AI Study Helper"""
    
    # Azure services
    AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")
    AZURE_LANGUAGE_KEY = os.getenv("AZURE_LANGUAGE_KEY")
    
    # Google AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # App settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    SUPPORTED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx']
    
    # UI settings
    PAGE_TITLE = "🧠 Scribbly - AI Study Helper"
    PAGE_ICON = "🧠"
    PROGRESS_STEPS = ["📁 Upload", "🎯 Choose", "🔍 Process", "📚 Study"]
    
    # Processing limits
    DEFAULT_FLASHCARD_COUNT = 5
    MAX_FLASHCARD_COUNT = 20
    MAX_TOTAL_CARDS = 20  
    MAX_KEY_PHRASES = 15
    
    # Azure processing limits 
    AZURE_FALLBACK_SUMMARY_TOPICS = 5
    FLASHCARD_MAX_INPUT_WORDS = 1000
    AZURE_KEY_PHRASE_CHUNK_SIZE = 5000
    AZURE_SUMMARY_CHUNK_SIZE = 3000
    AZURE_MAX_SUMMARY_SENTENCES = 3
    AZURE_SMART_SUMMARY_SENTENCES = 5
    AZURE_SMART_SUMMARY_TOPICS = 5
    AZURE_STUDY_SUMMARY_KEY_PHRASES = 5
    AZURE_STUDY_SUMMARY_SENTENCES = 4
    AZURE_STUDY_SUMMARY_TOPICS = 3
    
    # Service validation methods
    @classmethod
    def has_azure_document(cls) -> bool:
        return bool(cls.AZURE_DOC_INTELLIGENCE_ENDPOINT and cls.AZURE_DOC_INTELLIGENCE_KEY)
    
    @classmethod
    def has_azure_language(cls) -> bool:
        return bool(cls.AZURE_LANGUAGE_ENDPOINT and cls.AZURE_LANGUAGE_KEY)
    
    @classmethod
    def has_gemini(cls) -> bool:
        return bool(cls.GEMINI_API_KEY)
    
    @classmethod
    def validate_azure_language(cls) -> bool:
        return cls.has_azure_language()
    
    @classmethod
    def get_available_services(cls) -> Dict[str, bool]:
        return {
            "azure_document_intelligence": cls.has_azure_document(),
            "azure_language_services": cls.has_azure_language(),
            "gemini_ai": cls.has_gemini()
        }
    
    @classmethod
    def validate_file_type(cls, file_extension: str) -> bool:
        return file_extension.lower() in cls.SUPPORTED_FILE_TYPES
    
    @classmethod
    def validate_file_size(cls, file_size_bytes: int) -> Dict[str, any]:
        is_valid = file_size_bytes <= cls.MAX_FILE_SIZE_BYTES
        if is_valid:
            return {'valid': True}
        else:
            size_mb = file_size_bytes / (1024 * 1024)
            return {
                'valid': False,
                'error': f"File too large ({size_mb:.1f}MB). Maximum allowed: {cls.MAX_FILE_SIZE_MB}MB"
            }
    
    @classmethod
    def is_ready(cls) -> Tuple[bool, str]:
        if not cls.has_azure_document():
            return False, "Missing Azure Document Intelligence credentials"
        if not cls.has_gemini():
            return False, "Missing Gemini API key"
        return True, "Ready"