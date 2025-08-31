import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.exceptions import AzureError, ClientAuthenticationError, ServiceRequestError

from config import Config
from fallbacks import simple_key_extraction, simple_extractive_summary

logger = logging.getLogger(__name__)

@dataclass
class AzureProcessingLimits:
    """Centralized Azure API limits - prevents hardcoded magic numbers"""
    CHUNK_SIZE_MAX = 4000           # Safe chunk size for Azure Language Services
    KEY_PHRASES_MAX = 15            # Maximum key phrases to extract per chunk
    SUMMARY_SENTENCES_MAX = 5       # Maximum sentences in extractive summary
    RETRY_ATTEMPTS = 3              # Number of retry attempts for failed calls
    RETRY_DELAY_SECONDS = 2         # Delay between retries
    BATCH_SIZE = 10                 # Maximum documents per batch request

@dataclass 
class ProcessingMetrics:
    """Track Azure API usage and performance"""
    api_calls_made: int = 0
    chunks_processed: int = 0
    total_processing_time: float = 0.0
    fallback_used: bool = False
    error_count: int = 0

class AzureLanguageProcessor:
    """Production-ready Azure Language Services processor"""
    
    def __init__(self):
        """Initialize with proper error handling and health checks"""
        self.client = None
        self.is_healthy = False
        self.last_health_check = None
        self.metrics = ProcessingMetrics()
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure client with comprehensive validation"""
        try:
            if not Config.has_azure_language():
                logger.warning("Azure Language Services not configured")
                return
            
            self.client = TextAnalyticsClient(
                endpoint=Config.AZURE_LANGUAGE_ENDPOINT,
                credential=AzureKeyCredential(Config.AZURE_LANGUAGE_KEY)
            )
            
            self._perform_health_check()
            logger.info("Azure Language Services initialized successfully")
            
        except ClientAuthenticationError as e:
            logger.error(f"Azure Language authentication failed: {e}")
        except Exception as e:
            logger.error(f"Azure Language client initialization failed: {e}")
    
    def _perform_health_check(self) -> bool:
        """Validate Azure client connectivity"""
        try:
            if not self.client:
                return False
            
            test_result = self.client.detect_language(["Hello world"])
            
            if test_result and not test_result[0].is_error:
                self.is_healthy = True
                self.last_health_check = datetime.now()
                logger.debug("Azure Language Services health check passed")
                return True
            
        except Exception as e:
            logger.warning(f"Azure Language health check failed: {e}")
        
        self.is_healthy = False
        return False
    
    def is_available(self) -> bool:
        """Check if Azure Language Services is available and healthy"""
        if (self.last_health_check and 
            (datetime.now() - self.last_health_check).seconds > 300):
            self._perform_health_check()
        
        return self.is_healthy
    
    def analyze_for_study_materials(self, text: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Analyze text for study materials with robust error handling"""
        
        start_time = time.time()
        self.metrics = ProcessingMetrics()
        
        try:
            if progress_callback:
                progress_callback("🔍 Initializing Azure Language analysis...")
            
            if not self.is_available():
                logger.warning("Azure Language Services unavailable, using fallback")
                return self._create_fallback_analysis(text)
            
            if progress_callback:
                progress_callback("📝 Extracting key phrases...")
            
            key_phrases = self._extract_key_phrases_robust(text)
            
            if progress_callback:
                progress_callback("📄 Creating intelligent summaries...")
            
            summaries = self._create_study_summaries_robust(text, key_phrases)
            
            if progress_callback:
                progress_callback("📊 Analyzing text complexity...")
            
            text_stats = self._analyze_text_complexity(text)
            self.metrics.total_processing_time = time.time() - start_time
            
            if progress_callback:
                progress_callback("✅ Azure analysis complete!")
            
            return {
                'summary': summaries,
                'key_phrases': {'azure_key_phrases': key_phrases},
                'text_complexity': text_stats,
                'study_assessment': self._assess_study_quality(text, key_phrases),
                'processing_metrics': {
                    'api_calls': self.metrics.api_calls_made,
                    'processing_time': f"{self.metrics.total_processing_time:.2f}s",
                    'chunks_processed': self.metrics.chunks_processed
                },
                'error': None
            }
            
        except AzureError as e:
            logger.error(f"Azure Language Services error: {e}")
            self.metrics.error_count += 1
            return self._create_fallback_analysis(text)
            
        except Exception as e:
            logger.error(f"Unexpected error in language analysis: {e}")
            self.metrics.error_count += 1
            return self._create_fallback_analysis(text)
    
    def _extract_key_phrases_robust(self, text: str) -> List[str]:
        """Extract key phrases with retry logic and batching"""
        if not self.client or not self.is_healthy:
            logger.warning("Azure client unavailable for key phrase extraction")
            return simple_key_extraction(text)
        
        try:
            chunks = self._smart_text_splitting(text, AzureProcessingLimits.CHUNK_SIZE_MAX)
            all_phrases = []
            
            for chunk in chunks:
                phrases = self._extract_phrases_with_retry(chunk)
                if phrases:
                    all_phrases.extend(phrases)
                self.metrics.chunks_processed += 1
            
            unique_phrases = list(dict.fromkeys(all_phrases))
            return unique_phrases[:Config.MAX_KEY_PHRASES]
            
        except Exception as e:
            logger.error(f"Robust key phrase extraction failed: {e}")
            return simple_key_extraction(text)
    
    def _extract_phrases_with_retry(self, text: str) -> List[str]:
        """Extract phrases with exponential backoff retry"""
        
        for attempt in range(AzureProcessingLimits.RETRY_ATTEMPTS):
            try:
                self.metrics.api_calls_made += 1
                result = self.client.extract_key_phrases([text])[0]
                
                if not result.is_error:
                    return result.key_phrases
                else:
                    logger.warning(f"Azure key phrases error: {result.error}")
                    
            except ServiceRequestError as e:
                if attempt < AzureProcessingLimits.RETRY_ATTEMPTS - 1:
                    delay = AzureProcessingLimits.RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(f"Retrying key phrase extraction in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                else:
                    logger.error(f"Key phrase extraction failed after {AzureProcessingLimits.RETRY_ATTEMPTS} attempts")
                    
            except Exception as e:
                logger.error(f"Unexpected error in key phrase extraction: {e}")
                break
        
        return []
    
    def _smart_text_splitting(self, text: str, max_chunk_size: int) -> List[str]:
        """Intelligent text splitting that preserves sentence boundaries"""
        
        if len(text) <= max_chunk_size:
            return [text]
        
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence) + 1
            
            if current_length + sentence_length > max_chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks
    
    def _create_study_summaries_robust(self, text: str, key_phrases: List[str]) -> Dict[str, str]:
        """Create multiple summary types with robust error handling"""
        
        summaries = {}
        
        summaries['extractive'] = self._get_azure_extractive_summary(text)
        summaries['best'] = self._create_intelligent_summary(text, key_phrases)
        summaries['abstractive'] = self._create_conceptual_summary(text, key_phrases)
        
        if not any(summaries.values()):
            summaries['best'] = simple_extractive_summary(text)
        
        return summaries
    
    def _get_azure_extractive_summary(self, text: str) -> str:
        """Get extractive summary using Azure with fallback"""
        
        if not self.client or not self.is_healthy:
            return simple_extractive_summary(text)
        
        try:
            chunks = self._smart_text_splitting(text, AzureProcessingLimits.CHUNK_SIZE_MAX)
            summaries = []
            
            for chunk in chunks:
                summary = self._extract_summary_with_retry(chunk)
                if summary:
                    summaries.append(summary)
            
            return ' '.join(summaries) if summaries else simple_extractive_summary(text)
            
        except Exception as e:
            logger.error(f"Azure extractive summary failed: {e}")
            return simple_extractive_summary(text)
    
    def _extract_summary_with_retry(self, text: str) -> str:
        """Extract summary with retry logic"""
        
        for attempt in range(AzureProcessingLimits.RETRY_ATTEMPTS):
            try:
                self.metrics.api_calls_made += 1
                
                result = self.client.extract_summary(
                    [text], 
                    max_sentence_count=AzureProcessingLimits.SUMMARY_SENTENCES_MAX
                )
                
                if result and not result[0].is_error:
                    sentences = [sentence.text for sentence in result[0].sentences]
                    return ' '.join(sentences)
                    
            except ServiceRequestError as e:
                if attempt < AzureProcessingLimits.RETRY_ATTEMPTS - 1:
                    delay = AzureProcessingLimits.RETRY_DELAY_SECONDS * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"Summary extraction failed after all retries")
                    
            except Exception as e:
                logger.error(f"Unexpected summary extraction error: {e}")
                break
        
        return ""
    
    def _create_intelligent_summary(self, text: str, key_phrases: List[str]) -> str:
        """Create intelligent summary focusing on key concepts"""
        
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        scored_sentences = []
        
        for sentence in sentences:
            if len(sentence.strip()) < 20:
                continue
                
            score = 0
            sentence_lower = sentence.lower()
            
            for phrase in key_phrases[:10]:
                if phrase.lower() in sentence_lower:
                    score += 2
            
            educational_words = ['important', 'key', 'main', 'concept', 'theory', 'principle']
            for word in educational_words:
                if word in sentence_lower:
                    score += 1
            
            if score > 0:
                scored_sentences.append((sentence.strip(), score))
        
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:AzureProcessingLimits.SUMMARY_SENTENCES_MAX]]
        
        if top_sentences:
            summary = '. '.join(top_sentences) + '.'
            summary += f" Key concepts include: {', '.join(key_phrases[:5])}."
            return summary
        
        return simple_extractive_summary(text)
    
    def _create_conceptual_summary(self, text: str, key_phrases: List[str]) -> str:
        """Create conceptual summary for study purposes"""
        if len(key_phrases) >= 3:
            return f"This content focuses on {', '.join(key_phrases[:3])}. " \
                   f"Additional topics include: {', '.join(key_phrases[3:8])}."
        elif len(key_phrases) >= 1:
            return f"Main topic: {key_phrases[0]}. " \
                   f"Related concepts: {', '.join(key_phrases[1:5])}."
        else:
            return "General educational content for study review."
    
    def _analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Enhanced text analysis with study metrics"""
        words = text.split()
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s for s in sentences if len(s.strip()) > 10]
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'estimated_reading_time': len(words) / 200  # minutes at 200 WPM
        }
    
    def _assess_study_quality(self, text: str, key_phrases: List[str]) -> Dict[str, Any]:
        """Assess the quality of content for studying"""
        
        word_count = len(text.split())
        concept_density = len(key_phrases) / max(word_count / 100, 1)
        
        if concept_density > 3:
            quality = "excellent"
        elif concept_density > 2:
            quality = "good" 
        elif concept_density > 1:
            quality = "fair"
        else:
            quality = "basic"
        
        return {
            'overall_quality': quality,
            'concept_density': round(concept_density, 2),
            'study_readiness': quality in ['excellent', 'good']
        }
    
    def _create_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback when Azure fails"""
        self.metrics.fallback_used = True
        
        key_phrases = simple_key_extraction(text)
        summaries = {
            'best': simple_extractive_summary(text),
            'extractive': simple_extractive_summary(text),
            'abstractive': f"Key topics identified: {', '.join(key_phrases[:5])}"
        }
        
        return {
            'summary': summaries,
            'key_phrases': {'azure_key_phrases': key_phrases},
            'text_complexity': self._analyze_text_complexity(text),
            'study_assessment': self._assess_study_quality(text, key_phrases),
            'processing_metrics': {
                'fallback_used': True,
                'method': 'local_processing'
            },
            'error': None
        }

# Create global instance
azure_language_processor = AzureLanguageProcessor()