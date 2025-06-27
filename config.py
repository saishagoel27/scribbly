import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AzureConfig:
    """Azure service configuration"""
    # Language Service
    language_endpoint: Optional[str] = None
    language_key: Optional[str] = None
    
    # Document Intelligence
    document_intelligence_endpoint: Optional[str] = None
    document_intelligence_key: Optional[str] = None
    
    # Service limits
    text_max_length: int = 125000
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Load values from environment variables"""
        self.language_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT", "").rstrip('/')
        self.language_key = os.getenv("AZURE_LANGUAGE_KEY", "")
        
        self.document_intelligence_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "").rstrip('/')
        self.document_intelligence_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
    
    @property
    def is_language_configured(self) -> bool:
        return bool(self.language_endpoint and self.language_key)
    
    @property
    def is_document_intelligence_configured(self) -> bool:
        return bool(self.document_intelligence_endpoint and self.document_intelligence_key)

@dataclass
class AppConfig:
    """Application configuration"""
    # File limits
    max_image_size: int = 4 * 1024 * 1024  # 4MB
    max_document_size: int = 10 * 1024 * 1024  # 10MB
    
    # Processing limits
    max_chunks_to_process: int = 5
    max_flashcards: int = 20
    min_text_length: int = 50
    
    # Cache settings
    cache_dir: str = "cache"
    cache_expiry_days: int = 7
    max_cache_size: int = 100
    
    # Supported file types
    supported_text_formats: tuple = ('.txt', '.docx', '.pdf')
    supported_image_formats: tuple = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
    
    @property
    def all_supported_formats(self) -> tuple:
        return self.supported_text_formats + self.supported_image_formats

# Global configuration instances
azure_config = AzureConfig()
app_config = AppConfig()