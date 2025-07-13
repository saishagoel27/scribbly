import os 
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    SIMPLIFIED: Clean configuration management for AI Study Helper
    
    Removed redundant properties and backward compatibility bloat
    """
    
    # ========== AZURE SERVICES ==========
    # Azure Document Intelligence
    AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    AZURE_DOC_INTELLIGENCE_KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    
    # Azure Language Services
    AZURE_LANGUAGE_ENDPOINT = os.getenv('AZURE_LANGUAGE_ENDPOINT')
    AZURE_LANGUAGE_KEY = os.getenv('AZURE_LANGUAGE_KEY')
    
    # ========== AI SERVICES ==========
    # Google Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # ========== APP SETTINGS ==========
    # File handling
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    SUPPORTED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx']
    
    # Streamlit UI
    PAGE_TITLE = "🧠 AI Study Helper"
    PAGE_ICON = "🧠"
    LAYOUT = "wide"
    
    # Processing limits
    MAX_TOTAL_CARDS = 15
    AZURE_TIMEOUT = 30
    DEFAULT_FLASHCARD_COUNT = 10
    
    # Caching
    CACHE_ENABLED = True
    CACHE_TTL_HOURS = 24
    CACHE_DIR = Path("cache")
    
    # ========== SERVICE AVAILABILITY CHECKS ==========
    
    @classmethod
    def has_document_intelligence(cls) -> bool:
        """Check if Azure Document Intelligence is configured"""
        return bool(cls.AZURE_DOC_INTELLIGENCE_ENDPOINT and cls.AZURE_DOC_INTELLIGENCE_KEY)
    
    @classmethod
    def has_language_service(cls) -> bool:
        """Check if Azure Language Service is configured"""
        return bool(cls.AZURE_LANGUAGE_ENDPOINT and cls.AZURE_LANGUAGE_KEY)
    
    @classmethod
    def has_gemini(cls) -> bool:
        """Check if Google Gemini is configured"""
        return bool(cls.GEMINI_API_KEY)
    
    @classmethod
    def get_available_services(cls) -> Dict[str, bool]:
        """Get status of all AI services"""
        return {
            "azure_document": cls.has_document_intelligence(),
            "azure_language": cls.has_language_service(),
            "gemini": cls.has_gemini()
        }
    
    @classmethod
    def get_missing_services(cls) -> List[str]:
        """Get list of missing critical services"""
        missing = []
        if not cls.has_document_intelligence():
            missing.append("Azure Document Intelligence")
        if not cls.has_gemini():
            missing.append("Google Gemini")
        return missing
    
    @classmethod
    def is_production_ready(cls) -> Tuple[bool, str]:
        """Check if app is ready for production use"""
        missing = cls.get_missing_services()
        
        if missing:
            return False, f"Missing services: {', '.join(missing)}"
        
        return True, "All services configured"
    
    # ========== INITIALIZATION ==========
    
    @classmethod
    def initialize_app(cls) -> Tuple[bool, str]:
        """Simple app initialization with clear feedback"""
        try:
            # Check critical services
            is_ready, message = cls.is_production_ready()
            
            if not is_ready:
                return False, message
            
            # Setup cache directory
            if cls.CACHE_ENABLED:
                cls.CACHE_DIR.mkdir(exist_ok=True)
            
            # Setup logging
            cls.setup_logging()
            
            return True, "Application initialized successfully"
            
        except Exception as e:
            return False, f"Initialization error: {str(e)}"
    
    @classmethod
    def setup_logging(cls):
        """SIMPLIFIED: Basic logging setup"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log') if cls.CACHE_ENABLED else logging.NullHandler()
            ]
        )
    
    # ========== ENVIRONMENT INFO ==========
    
    @classmethod
    def get_environment_info(cls) -> Dict[str, any]:
        """Get environment configuration info for debugging"""
        return {
            "services_configured": cls.get_available_services(),
            "file_limits": {
                "max_size_mb": cls.MAX_FILE_SIZE_MB,
                "supported_types": cls.SUPPORTED_FILE_TYPES
            },
            "processing_limits": {
                "max_cards": cls.MAX_TOTAL_CARDS,
                "azure_timeout": cls.AZURE_TIMEOUT
            },
            "caching": {
                "enabled": cls.CACHE_ENABLED,
                "cache_dir": str(cls.CACHE_DIR)
            }
        }
    
    # ========== VALIDATION HELPERS ==========
    
    @classmethod
    def validate_file_type(cls, file_extension: str) -> bool:
        """Validate if file type is supported"""
        return file_extension.lower() in cls.SUPPORTED_FILE_TYPES
    
    @classmethod
    def validate_file_size(cls, file_size_bytes: int) -> bool:
        """Validate if file size is within limits"""
        return file_size_bytes <= cls.MAX_FILE_SIZE_BYTES
    
    @classmethod
    def get_azure_config(cls) -> Dict[str, Optional[str]]:
        """Get Azure configuration for debugging"""
        return {
            "document_endpoint": cls.AZURE_DOC_INTELLIGENCE_ENDPOINT,
            "document_key_configured": bool(cls.AZURE_DOC_INTELLIGENCE_KEY),
            "language_endpoint": cls.AZURE_LANGUAGE_ENDPOINT,
            "language_key_configured": bool(cls.AZURE_LANGUAGE_KEY)
        }

# Create global config instance for easy access
config = Config()

# Auto-initialize logging when module is imported
Config.setup_logging()

# ========== HELPER FUNCTIONS ==========

def get_service_status_message() -> str:
    """Get human-readable service status"""
    services = Config.get_available_services()
    
    available = [name for name, status in services.items() if status]
    missing = [name for name, status in services.items() if not status]
    
    message = []
    
    if available:
        message.append(f"✅ Available: {', '.join(available)}")
    
    if missing:
        message.append(f"❌ Missing: {', '.join(missing)}")
    
    return " | ".join(message) if message else "No services configured"

def check_environment_variables() -> Dict[str, bool]:
    """Quick check of all required environment variables"""
    required_vars = {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')),
        'AZURE_DOCUMENT_INTELLIGENCE_KEY': bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')),
        'GEMINI_API_KEY': bool(os.getenv('GEMINI_API_KEY'))
    }
    
    optional_vars = {
        'AZURE_LANGUAGE_ENDPOINT': bool(os.getenv('AZURE_LANGUAGE_ENDPOINT')),
        'AZURE_LANGUAGE_KEY': bool(os.getenv('AZURE_LANGUAGE_KEY')),
        'MAX_FILE_SIZE_MB': bool(os.getenv('MAX_FILE_SIZE_MB'))
    }
    
    return {
        "required": required_vars,
        "optional": optional_vars,
        "all_required_present": all(required_vars.values())
    }