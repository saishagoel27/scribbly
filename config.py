import os
from dotenv import load_dotenv

# Loading environment variables from .env file
load_dotenv()
class Config:
    def __init__(self):
        # Azure Document Intelligence (for extracting text from files)
        self.doc_intelligence_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.doc_intelligence_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        # Azure Language Service (for summaries and analysis)
        self.language_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT") 
        self.language_key = os.getenv("AZURE_LANGUAGE_KEY")
        
        # App settings
        self.max_file_size_mb = 100
        self.supported_file_types = ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'docx']
    
    def has_document_intelligence(self):
        """Check if Document Intelligence API is configured"""
        return bool(self.doc_intelligence_endpoint and self.doc_intelligence_key)
    
    def has_language_service(self):
        """Check if Language Service API is configured"""
        return bool(self.language_endpoint and self.language_key)
    
    def get_status(self):
        """Get configuration status for debugging"""
        return {
            "document_intelligence": "✅ Ready" if self.has_document_intelligence() else "❌ Not configured",
            "language_service": "✅ Ready" if self.has_language_service() else "❌ Not configured"
        }

# Created a global config instance that other files can use
config = Config()