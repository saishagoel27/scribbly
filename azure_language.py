from typing import Dict, List, Optional, Callable, Any
import logging
import time
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from config import Config

logger = logging.getLogger(__name__)

class AzureLanguageProcessor:
    """Simple Azure Language Services processor"""
    
    def __init__(self):
        self.client = None
        if Config.validate_azure_language():
            try:
                self.client = TextAnalyticsClient(
                    endpoint=Config.AZURE_LANGUAGE_ENDPOINT,
                    credential=AzureKeyCredential(Config.AZURE_LANGUAGE_KEY)
                )
            except Exception as e:
                logger.error(f"Azure Language client setup failed: {e}")
    
    def analyze_for_study_materials(self, text: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Create study materials from text"""
        if progress_callback:
            progress_callback("Starting analysis...")
        
        try:
            # Get key phrases first
            key_phrases = self._extract_key_phrases(text)
            if progress_callback:
                progress_callback("Extracting key concepts...")
            
            # Create different types of summaries
            summaries = self._create_study_summaries(text, key_phrases)
            if progress_callback:
                progress_callback("Creating summaries...")
            
            # Basic text analysis
            text_stats = self._analyze_text_complexity(text)
            
            return {
                'summary': summaries,
                'key_phrases': {'azure_key_phrases': key_phrases},
                'text_complexity': text_stats,
                'study_assessment': {'overall_quality': 'good'},
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_fallback_analysis(text)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        if not self.client:
            return self._simple_key_extraction(text)
        
        try:
            # Split text into chunks if too long
            chunks = self._split_text(text, 5000)
            all_phrases = []
            
            for chunk in chunks:
                result = self.client.extract_key_phrases([chunk])[0]
                if not result.is_error:
                    all_phrases.extend(result.key_phrases)
            
            # Remove duplicates and return top phrases
            unique_phrases = list(set(all_phrases))
            return unique_phrases[:20]
            
        except Exception as e:
            logger.error(f"Key phrase extraction failed: {e}")
            return self._simple_key_extraction(text)
    
    def _create_study_summaries(self, text: str, key_phrases: List[str]) -> Dict[str, str]:
        """Create different types of summaries for studying"""
        
        # Method 1: Azure extractive summary (key sentences)
        extractive_summary = self._get_extractive_summary(text)
        
        # Method 2: Simple intelligent summary based on key phrases
        smart_summary = self._create_smart_summary(text, key_phrases)
        
        # Method 3: Study-focused summary
        study_summary = self._create_study_focused_summary(text, key_phrases)
        
        return {
            'extractive': extractive_summary,
            'best': smart_summary,  # This will be the main one shown
            'abstractive': study_summary
        }
    
    def _get_extractive_summary(self, text: str) -> str:
        """Get key sentences using Azure (or fallback)"""
        if not self.client:
            return self._simple_extractive_summary(text)
        
        try:
            # Try Azure extractive summarization
            chunks = self._split_text(text, 3000)
            summaries = []
            
            for chunk in chunks:
                # Use Azure's summarization if available
                result = self.client.extract_summary([chunk], max_sentence_count=3)
                if result and not result[0].is_error:
                    summary_sentences = [sentence.text for sentence in result[0].sentences]
                    summaries.extend(summary_sentences)
            
            return " ".join(summaries) if summaries else self._simple_extractive_summary(text)
            
        except Exception as e:
            logger.error(f"Azure extractive summary failed: {e}")
            return self._simple_extractive_summary(text)
    
    def _create_smart_summary(self, text: str, key_phrases: List[str]) -> str:
        """Create an intelligent summary focusing on key concepts"""
        # Get important sentences that contain key phrases
        sentences = text.split('.')
        important_sentences = []
        
        # Score sentences based on key phrase presence
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            
            for phrase in key_phrases[:10]:  # Use top 10 key phrases
                if phrase.lower() in sentence_lower:
                    score += 1
            
            if score > 0 and len(sentence.strip()) > 20:
                important_sentences.append((sentence.strip(), score))
        
        # Sort by score and get top sentences
        important_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [sent[0] for sent in important_sentences[:5]]
        
        if top_sentences:
            summary = ". ".join(top_sentences)
            # Add conclusion
            summary += f". This content covers key topics including: {', '.join(key_phrases[:5])}."
            return summary
        else:
            return self._simple_extractive_summary(text)
    
    def _create_study_focused_summary(self, text: str, key_phrases: List[str]) -> str:
        """Create a summary focused on study/learning"""
        # Simple approach: identify main concepts and create study notes
        sentences = text.split('.')
        
        # Look for educational indicators
        learning_words = ['define', 'concept', 'theory', 'principle', 'method', 'process', 'important', 'key', 'main']
        study_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence has learning indicators or key phrases
            has_learning = any(word in sentence_lower for word in learning_words)
            has_key_phrase = any(phrase.lower() in sentence_lower for phrase in key_phrases[:5])
            
            if (has_learning or has_key_phrase) and len(sentence.strip()) > 15:
                study_sentences.append(sentence.strip())
        
        if study_sentences:
            # Take top sentences and format for study
            summary = ". ".join(study_sentences[:4])
            summary += f" Key areas to focus on: {', '.join(key_phrases[:3])}."
            return summary
        else:
            return f"Main topics covered: {', '.join(key_phrases[:5])}. Review the full content for detailed understanding."
    
    def _simple_extractive_summary(self, text: str) -> str:
        """Simple fallback summary"""
        sentences = text.split('.')
        # Get first few and last few sentences
        if len(sentences) > 6:
            summary_sentences = sentences[:3] + sentences[-2:]
        else:
            summary_sentences = sentences[:min(4, len(sentences))]
        
        return ". ".join([s.strip() for s in summary_sentences if len(s.strip()) > 10])
    
    def _simple_key_extraction(self, text: str) -> List[str]:
        """Simple keyword extraction fallback"""
        # Basic approach - find frequently mentioned words
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:"()[]').lower()
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word[0] for word in sorted_words[:15]]
    
    def _split_text(self, text: str, max_length: int = 5000) -> List[str]:
        """Split text into chunks"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_length += len(word) + 1
            if current_length > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Basic text analysis"""
        words = text.split()
        sentences = text.split('.')
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / max(len(sentences), 1)
        }
    
    def _create_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback when Azure fails"""
        key_phrases = self._simple_key_extraction(text)
        summaries = {
            'best': self._simple_extractive_summary(text),
            'extractive': self._simple_extractive_summary(text),
            'abstractive': f"Summary of content covering: {', '.join(key_phrases[:5])}"
        }
        
        return {
            'summary': summaries,
            'key_phrases': {'azure_key_phrases': key_phrases},
            'text_complexity': self._analyze_text_complexity(text),
            'study_assessment': {'overall_quality': 'basic'},
            'error': None
        }

# Create global instance
azure_language_processor = AzureLanguageProcessor()