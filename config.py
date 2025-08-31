import os
import logging
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Logging for configuration issues
logger = logging.getLogger(__name__)

# Safely loaded environment variables
try:
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")

class Config:
    """Configuration for Scribbly - AI Study Helper"""
    
    # Service Credentials
    AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")
    AZURE_LANGUAGE_KEY = os.getenv("AZURE_LANGUAGE_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Application Settings
    PAGE_TITLE = "🧠 Scribbly - AI Study Helper"
    PAGE_ICON = "🧠"
    PROGRESS_STEPS = ["📁 Upload", "🎯 Choose", "🔍 Process", "📚 Study"]
    
    # File Processing Settings
    SUPPORTED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx']
    
    # Content Generation Settings
    DEFAULT_FLASHCARD_COUNT = 5
    MAX_FLASHCARD_COUNT = 20
    MAX_KEY_PHRASES = 15
    
    # Processing Configuration
    class ProcessingLimits:
        """Centralized processing limits with business justification"""
        CHUNK_SIZE_DEFAULT = 4000        # (Azure 5KB limit)
        SUMMARY_SENTENCES_MAX = 5        # Optimal summary length for study
        KEY_PHRASES_MAX = 15             # Good balance for flashcard generation
        FLASHCARD_INPUT_MAX_WORDS = 1000 # Prevents API token limit issues
    
    @classmethod
    def _safe_int_from_env(cls, key: str, default: int) -> int:
        """Safely parse integer from environment variable"""
        try:
            value = int(os.getenv(key, str(default)))
            logger.debug(f"Loaded {key}={value}")
            return value
        except (ValueError, TypeError):
            logger.warning(f"Invalid {key} in environment, using default: {default}")
            return default
    
    # Initializes calculated values safely
    MAX_FILE_SIZE_MB = _safe_int_from_env.__func__(None, 'MAX_FILE_SIZE_MB', 10)
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Service availability checks
    @classmethod
    def has_azure_document(cls) -> bool:
        """Check if Azure Document Intelligence is configured"""
        return bool(cls.AZURE_DOC_INTELLIGENCE_ENDPOINT and cls.AZURE_DOC_INTELLIGENCE_KEY)
    
    @classmethod
    def has_azure_language(cls) -> bool:
        """Check if Azure Language Services is configured"""
        return bool(cls.AZURE_LANGUAGE_ENDPOINT and cls.AZURE_LANGUAGE_KEY)
    
    @classmethod
    def has_gemini(cls) -> bool:
        """Check if Gemini AI is configured"""
        return bool(cls.GEMINI_API_KEY)
    
    @classmethod
    def get_available_services(cls) -> Dict[str, bool]:
        """Get status of all AI services"""
        return {
            "azure_document_intelligence": cls.has_azure_document(),
            "azure_language_services": cls.has_azure_language(),
            "gemini_ai": cls.has_gemini()
        }
    
    @classmethod
    def validate_file_type(cls, file_extension: str) -> bool:
        """Check if file type is supported"""
        return file_extension.lower() in cls.SUPPORTED_FILE_TYPES
    
    @classmethod
    def validate_file_size(cls, file_size_bytes: int) -> Dict[str, any]:
        """Validate file size with detailed error message"""
        is_valid = file_size_bytes <= cls.MAX_FILE_SIZE_BYTES
        if is_valid:
            return {'valid': True}
        
        size_mb = file_size_bytes / (1024 * 1024)
        return {
            'valid': False,
            'error': f"File too large ({size_mb:.1f}MB). Maximum allowed: {cls.MAX_FILE_SIZE_MB}MB"
        }
    
    @classmethod
    def is_ready(cls) -> Tuple[bool, str]:
        """Check if minimum services are available for basic functionality"""
        if not cls.has_azure_document():
            return False, "Missing Azure Document Intelligence credentials"
        if not cls.has_gemini():
            return False, "Missing Gemini API key"
        return True, "Ready"
    
    @classmethod
    def get_missing_services(cls) -> List[str]:
        """Get list of missing service configurations for debugging"""
        missing = []
        if not cls.has_azure_document():
            missing.append("Azure Document Intelligence")
        if not cls.has_azure_language():
            missing.append("Azure Language Services")
        if not cls.has_gemini():
            missing.append("Gemini AI")
        return missing