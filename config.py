import os
import logging
from pathlib import Path
from typing import Tuple, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    This class manages all application settings, API credentials, and provides
    validation methods for ensuring proper environment setup.
    """
    
    # Azure Document Intelligence (OCR Service)
    AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    AZURE_DOC_INTELLIGENCE_KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    
    # Azure Language Services (Text Analytics)
    AZURE_LANGUAGE_ENDPOINT = os.getenv('AZURE_LANGUAGE_ENDPOINT')
    AZURE_LANGUAGE_KEY = os.getenv('AZURE_LANGUAGE_KEY')
    
    # Google Gemini API (Flashcard Generation)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Debug and Development
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # File Processing Limits
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    SUPPORTED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx']
    
    # Text Processing Limits
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '50000'))
    MAX_FLASHCARDS_PER_SESSION = int(os.getenv('MAX_FLASHCARDS_PER_SESSION', '20'))
    
    PAGE_TITLE = "🧠 AI-Powered Flashcard Generator"
    PAGE_ICON = "🧠"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    # UI Theme Colors
    PRIMARY_COLOR = "#1f77b4"
    BACKGROUND_COLOR = "#ffffff"
    SECONDARY_BACKGROUND_COLOR = "#f0f2f6"
    TEXT_COLOR = "#262730"
    
    
    FLASHCARD_TYPES = ["definition", "conceptual", "application", "detail"]
    DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
    
    # Flashcard Generation Limits
    MAX_DEFINITION_CARDS = 6
    MAX_CONCEPTUAL_CARDS = 5
    MAX_APPLICATION_CARDS = 4
    MAX_DETAIL_CARDS = 3
    MAX_TOTAL_CARDS = 15
    
    # Quality Thresholds
    MIN_QUESTION_LENGTH = 10
    MAX_QUESTION_LENGTH = 200
    MIN_ANSWER_LENGTH = 10
    MAX_ANSWER_LENGTH = 500
    MIN_CONFIDENCE_SCORE = 0.3
    
    CACHE_DIR = Path("cache")
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))
    
    # API Timeout Settings (in seconds)
    AZURE_TIMEOUT = int(os.getenv('AZURE_TIMEOUT', '30'))
    GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '45'))
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'flashcard_app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # ============================================================================
    # BACKWARD COMPATIBILITY (Legacy property names)
    # ============================================================================
    
    @property
    def doc_intelligence_endpoint(self):
        """Legacy property for backward compatibility"""
        return self.AZURE_DOC_INTELLIGENCE_ENDPOINT
    
    @property
    def doc_intelligence_key(self):
        """Legacy property for backward compatibility"""
        return self.AZURE_DOC_INTELLIGENCE_KEY
    
    @property
    def language_endpoint(self):
        """Legacy property for backward compatibility"""
        return self.AZURE_LANGUAGE_ENDPOINT
    
    @property
    def language_key(self):
        """Legacy property for backward compatibility"""
        return self.AZURE_LANGUAGE_KEY
    
    @property
    def gemini_api_key(self):
        """Legacy property for backward compatibility"""
        return self.GEMINI_API_KEY
    
    @property
    def max_file_size_mb(self):
        """Legacy property for backward compatibility"""
        return self.MAX_FILE_SIZE_MB
    
    @property
    def supported_file_types(self):
        """Legacy property for backward compatibility"""
        return self.SUPPORTED_FILE_TYPES
    
    @classmethod
    def has_document_intelligence(cls) -> bool:
        """Check if Azure Document Intelligence is properly configured"""
        return bool(cls.AZURE_DOC_INTELLIGENCE_ENDPOINT and cls.AZURE_DOC_INTELLIGENCE_KEY)
    
    @classmethod
    def has_language_service(cls) -> bool:
        """Check if Azure Language Service is properly configured"""
        return bool(cls.AZURE_LANGUAGE_ENDPOINT and cls.AZURE_LANGUAGE_KEY)
    
    @classmethod
    def has_gemini(cls) -> bool:
        """Check if Google Gemini API is properly configured"""
        return bool(cls.GEMINI_API_KEY)
    
    @classmethod
    def get_available_services(cls) -> Dict[str, bool]:
        """Get availability status of all services"""
        return {
            "azure_document_intelligence": cls.has_document_intelligence(),
            "azure_language_service": cls.has_language_service(),
            "google_gemini": cls.has_gemini()
        }
    
    @classmethod
    def get_missing_services(cls) -> list:
        """Get list of missing/unavailable services"""
        services = cls.get_available_services()
        return [service for service, available in services.items() if not available]
    
    @classmethod
    def validate_config(cls) -> Tuple[bool, str]:
        """
        Validate all configuration settings
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        missing_vars = []
        warnings = []
        
        # Check required API credentials
        if not cls.has_document_intelligence():
            missing_vars.extend(['AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT', 'AZURE_DOCUMENT_INTELLIGENCE_KEY'])
        
        if not cls.has_language_service():
            missing_vars.extend(['AZURE_LANGUAGE_ENDPOINT', 'AZURE_LANGUAGE_KEY'])
        
        if not cls.has_gemini():
            missing_vars.append('GEMINI_API_KEY')
        
        # Check optional but recommended settings
        if cls.MAX_FILE_SIZE_MB > 50:
            warnings.append(f"Large file size limit ({cls.MAX_FILE_SIZE_MB}MB) may cause performance issues")
        
        if cls.MAX_FLASHCARDS_PER_SESSION > 30:
            warnings.append(f"High flashcard limit ({cls.MAX_FLASHCARDS_PER_SESSION}) may impact user experience")
        
        # Return validation results
        if missing_vars:
            error_msg = f"❌ Missing required environment variables: {', '.join(missing_vars)}"
            if warnings:
                error_msg += f"\n⚠️ Warnings: {'; '.join(warnings)}"
            return False, error_msg
        
        success_msg = "✅ All required configuration is valid"
        if warnings:
            success_msg += f"\n⚠️ Warnings: {'; '.join(warnings)}"
        
        return True, success_msg
    
    @classmethod
    def validate_environment(cls) -> Tuple[bool, str]:
        """
        Comprehensive environment validation including file system checks
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        # First check basic config
        config_valid, config_msg = cls.validate_config()
        if not config_valid:
            return config_valid, config_msg
        
        issues = []
        
        try:
            # Check cache directory permissions
            cls.CACHE_DIR.mkdir(exist_ok=True)
            if not cls.CACHE_DIR.is_dir():
                issues.append("Cannot create cache directory")
            
            # Check log file permissions
            log_path = Path(cls.LOG_FILE)
            try:
                log_path.touch(exist_ok=True)
                if not log_path.exists():
                    issues.append("Cannot create log file")
            except PermissionError:
                issues.append("No permission to create log file")
            
        except Exception as e:
            issues.append(f"File system check failed: {str(e)}")
        
        if issues:
            return False, f"{config_msg}\n❌ Environment issues: {'; '.join(issues)}"
        
        return True, f"{config_msg}\n✅ Environment is fully configured"
    
    @classmethod
    def setup_logging(cls) -> None:
        """Configure application-wide logging"""
        # Ensure log directory exists
        log_path = Path(cls.LOG_FILE)
        log_path.parent.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL, logging.INFO),
            format=cls.LOG_FORMAT,
            datefmt=cls.LOG_DATE_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True  # Override any existing configuration
        )
        
        # Set specific logger levels for external libraries
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('google').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info("🚀 Logging configured successfully")
        
        # Log configuration status
        is_valid, msg = cls.validate_config()
        if is_valid:
            logger.info(msg)
        else:
            logger.error(msg)
    
    @classmethod
    def setup_cache(cls) -> None:
        """Initialize cache directory and settings"""
        if cls.CACHE_ENABLED:
            cls.CACHE_DIR.mkdir(exist_ok=True)
            logger = logging.getLogger(__name__)
            logger.info(f"📁 Cache directory initialized: {cls.CACHE_DIR}")
    
    @classmethod
    def initialize_app(cls) -> Tuple[bool, str]:
        """
        Initialize the entire application configuration
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Setup logging first
            cls.setup_logging()
            
            # Validate environment
            env_valid, env_msg = cls.validate_environment()
            if not env_valid:
                return False, env_msg
            
            # Setup cache
            cls.setup_cache()
            
            # Log successful initialization
            logger = logging.getLogger(__name__)
            logger.info("🎉 Application configuration initialized successfully")
            
            return True, env_msg
            
        except Exception as e:
            error_msg = f"❌ Failed to initialize application: {str(e)}"
            print(error_msg)  # Print to console since logging might not be set up
            return False, error_msg
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get a summary of current configuration for debugging"""
        return {
            "environment": cls.ENVIRONMENT,
            "debug_mode": cls.DEBUG,
            "services_available": cls.get_available_services(),
            "file_limits": {
                "max_size_mb": cls.MAX_FILE_SIZE_MB,
                "supported_types": cls.SUPPORTED_FILE_TYPES
            },
            "flashcard_settings": {
                "max_total": cls.MAX_TOTAL_CARDS,
                "types": cls.FLASHCARD_TYPES,
                "difficulties": cls.DIFFICULTY_LEVELS
            },
            "cache_enabled": cls.CACHE_ENABLED,
            "log_level": cls.LOG_LEVEL
        }

# Create global config instance for backward compatibility
config = Config()

# Auto-initialize logging when module is imported
Config.setup_logging()