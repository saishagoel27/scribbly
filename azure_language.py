import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime
import json

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError, ServiceRequestError
from spellchecker import SpellChecker

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTextProcessor:
    """Enhanced text processing for better OCR output handling and study material optimization"""

    def __init__(self):
        """Initialize enhanced text processor with spell checker"""
        try:
            self.spell_checker = SpellChecker()
            self.study_keywords = self._load_study_keywords()
            logger.info("✅ Enhanced text processor initialized")
        except Exception as e:
            logger.warning(f"⚠️ Spell checker initialization failed: {e}")
            self.spell_checker = None

    def _load_study_keywords(self) -> Dict[str, List[str]]:
        """Load comprehensive study-related keywords for content analysis"""
        return {
            "definitions": [
                "definition", "define", "meaning", "concept", "term", "refers to",
                "is defined as", "can be described as", "is known as", "is called"
            ],
            "explanations": [
                "because", "since", "due to", "as a result", "therefore", "thus",
                "consequently", "leads to", "causes", "results in", "explains why"
            ],
            "examples": [
                "for example", "such as", "including", "like", "instance", "case",
                "illustration", "demonstrates", "shows", "exemplifies"
            ],
            "processes": [
                "process", "procedure", "method", "technique", "approach", "way",
                "steps", "stages", "phases", "sequence", "algorithm"
            ],
            "comparisons": [
                "compared to", "in contrast", "however", "whereas", "unlike",
                "similar to", "different from", "distinction", "versus"
            ],
            "importance": [
                "important", "significant", "crucial", "essential", "vital",
                "key", "primary", "major", "fundamental", "critical"
            ]
        }

    def clean_ocr_text(self, text: str) -> str:
        """
        Comprehensive OCR text cleaning and optimization
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned and optimized text
        """
        try:
            if not text or not text.strip():
                return ""

            # Step 1: Basic normalization
            cleaned = text.strip()
            
            # Step 2: Fix common OCR errors
            cleaned = self._fix_common_ocr_errors(cleaned)
            
            # Step 3: Normalize whitespace and formatting
            cleaned = self._normalize_formatting(cleaned)
            
            # Step 4: Fix sentence boundaries
            cleaned = self._fix_sentence_boundaries(cleaned)
            
            # Step 5: Spell check and correct (if available)
            if self.spell_checker:
                cleaned = self._spell_check_text(cleaned)
            
            # Step 6: Optimize for study content
            cleaned = self._optimize_for_study_content(cleaned)
            
            logger.info(f"📝 Text cleaned: {len(text)} → {len(cleaned)} characters")
            return cleaned
            
        except Exception as e:
            logger.error(f"Text cleaning error: {e}")
            return text  # Return original if cleaning fails

    def _fix_common_ocr_errors(self, text: str) -> str:
        """Fix common OCR recognition errors"""
        # Common character substitutions
        ocr_fixes = {
            # Number/letter confusion
            '0': 'O', '1': 'I', '5': 'S', '8': 'B',
            # Special characters
            '|': 'l', '¡': 'i', '©': 'c', '®': 'r',
            # Punctuation
            '.,': '.', '..': '.', ';;': ';', '::': ':',
            # Spacing issues
            ' ,': ',', ' .': '.', ' ;': ';', ' :': ':',
            # Line breaks
            '\r\n': '\n', '\r': '\n'
        }
        
        # Apply context-aware fixes
        for wrong, right in ocr_fixes.items():
            # Only fix in appropriate contexts
            if wrong in ['0', '1', '5', '8'] and text.count(wrong) > text.count(right) * 2:
                # Likely actual numbers, don't fix
                continue
            text = text.replace(wrong, right)
        
        return text

    def _normalize_formatting(self, text: str) -> str:
        """Normalize text formatting and spacing"""
        # Remove excessive whitespace
        text = re.sub(r' +', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        # Remove trailing/leading spaces on lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        # Fix spacing around punctuation
        text = re.sub(r' +([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])([A-Za-z])', r'\1 \2', text)
        
        return text

    def _fix_sentence_boundaries(self, text: str) -> str:
        """Fix sentence boundary detection issues"""
        # Add missing spaces after periods
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        # Fix missing periods at line ends
        lines = text.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.endswith(('.', '!', '?', ':', ';')):
                # Check if next line starts with capital (new sentence)
                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_line = lines[i + 1].strip()
                    if next_line[0].isupper():
                        line += '.'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

    def _spell_check_text(self, text: str) -> str:
        """Apply spell checking with academic context awareness"""
        if not self.spell_checker:
            return text
        
        try:
            words = text.split()
            corrected_words = []
            
            for word in words:
                # Extract actual word (remove punctuation for checking)
                clean_word = re.sub(r'[^\w]', '', word.lower())
                
                if len(clean_word) > 2 and clean_word not in self.spell_checker:
                    # Get correction candidates
                    candidates = self.spell_checker.candidates(clean_word)
                    if candidates:
                        # Use the most likely candidate
                        correction = min(candidates, key=lambda x: self.spell_checker.word_frequency.get(x, 0))
                        if correction != clean_word:
                            # Apply correction while preserving case and punctuation
                            word = self._apply_correction(word, clean_word, correction)
                
                corrected_words.append(word)
            
            return ' '.join(corrected_words)
            
        except Exception as e:
            logger.warning(f"Spell check error: {e}")
            return text

    def _apply_correction(self, original_word: str, wrong: str, correction: str) -> str:
        """Apply spell correction while preserving formatting"""
        # Simple case preservation
        if wrong.isupper():
            correction = correction.upper()
        elif wrong.istitle():
            correction = correction.capitalize()
        
        return original_word.replace(wrong, correction)

    def _optimize_for_study_content(self, text: str) -> str:
        """Optimize text specifically for study material and flashcard generation"""
        # Enhance definition patterns
        text = re.sub(r'(\w+)\s*:\s*([A-Z])', r'\1: \2', text)
        
        # Improve list formatting
        text = re.sub(r'([0-9]+)\.\s*', r'\n\1. ', text)
        text = re.sub(r'([•-])\s*', r'\n\1 ', text)
        
        # Enhance emphasis indicators
        emphasis_patterns = [
            (r'\*\*([^*]+)\*\*', r'**\1**'),  # Bold
            (r'\*([^*]+)\*', r'*\1*'),        # Italic
            (r'_([^_]+)_', r'_\1_')           # Underline
        ]
        
        for pattern, replacement in emphasis_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text

    @staticmethod
    def extract_key_concepts(text: str) -> List[str]:
        """Extract key concepts and terms from text"""
        try:
            # Find capitalized terms (likely proper nouns/concepts)
            concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            
            # Find definition patterns
            definition_patterns = [
                r'(\w+)\s+is\s+(?:a|an|the)?\s*([^.]+)',
                r'(\w+)\s*:\s*([^.]+)',
                r'(?:define|definition of)\s+(\w+)',
            ]
            
            for pattern in definition_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                concepts.extend([match[0] if isinstance(match, tuple) else match for match in matches])
            
            # Remove duplicates and filter
            unique_concepts = list(set(concepts))
            return [concept for concept in unique_concepts if len(concept) > 2]
            
        except Exception as e:
            logger.warning(f"Concept extraction error: {e}")
            return []

    @staticmethod
    def assess_text_complexity(text: str) -> Dict[str, Any]:
        """Assess text complexity for flashcard generation optimization"""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            # Basic metrics
            word_count = len(words)
            sentence_count = len([s for s in sentences if s.strip()])
            avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Complexity indicators
            complex_words = [word for word in words if len(word) > 6]
            complex_word_ratio = len(complex_words) / word_count if word_count > 0 else 0
            
            # Reading level estimation
            if avg_sentence_length <= 15 and complex_word_ratio <= 0.15:
                reading_level = "easy"
            elif avg_sentence_length <= 20 and complex_word_ratio <= 0.25:
                reading_level = "medium"
            else:
                reading_level = "hard"
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": round(avg_word_length, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "complex_word_ratio": round(complex_word_ratio, 2),
                "reading_level": reading_level,
                "flashcard_suitability": "good" if reading_level in ["easy", "medium"] else "challenging"
            }
            
        except Exception as e:
            logger.warning(f"Complexity assessment error: {e}")
            return {"error": str(e)}

class AzureLanguageProcessor:
    """Enhanced Azure Text Analytics processor focused on study materials and flashcard generation"""

    def __init__(self):
        """Initialize Azure Language client and enhanced text processor"""
        self.client = None
        self.is_available = False
        self.endpoint = Config.AZURE_LANGUAGE_ENDPOINT
        self.key = Config.AZURE_LANGUAGE_KEY
        self.timeout = Config.AZURE_TIMEOUT
        
        # Initialize enhanced text processor
        self.text_processor = EnhancedTextProcessor()
        
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Azure Text Analytics client with proper error handling"""
        try:
            if not self.endpoint or not self.key:
                logger.warning("❌ Azure Language Service credentials not configured")
                self.is_available = False
                return

            # Create client with proper credentials
            credential = AzureKeyCredential(self.key)
            self.client = TextAnalyticsClient(
                endpoint=self.endpoint,
                credential=credential
            )
            
            # Test connection
            self._test_connection()
            self.is_available = True
            logger.info("✅ Azure Language Service client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Language Service: {e}")
            self.is_available = False

    def _test_connection(self):
        """Test Azure Language Service connection"""
        try:
            # Simple test with minimal text
            test_docs = ["Test connection"]
            self.client.detect_language(documents=test_docs)
            logger.info("🔗 Azure Language Service connection verified")
        except Exception as e:
            logger.warning(f"⚠️ Azure Language Service connection test failed: {e}")
            raise

    def analyze_for_study_materials(self, text: str, progress_callback=None) -> Dict:
        """
        Comprehensive analysis optimized for study material and flashcard generation
        
        Args:
            text: Input text to analyze
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing comprehensive analysis results
        """
        if not self.is_available:
            return self._create_fallback_analysis(text)

        try:
            if progress_callback:
                progress_callback("🧠 Starting Azure Language analysis...")

            # Step 1: Clean and preprocess text
            if progress_callback:
                progress_callback("🧹 Cleaning and preprocessing text...")
            
            cleaned_text = self.text_processor.clean_ocr_text(text)
            if len(cleaned_text.strip()) < 10:
                return {"error": "Insufficient text for analysis after cleaning"}

            # Step 2: Split text into manageable chunks
            text_chunks = self._split_text_for_analysis(cleaned_text)
            
            # Step 3: Extract key phrases with study focus
            if progress_callback:
                progress_callback("🔍 Extracting key phrases and concepts...")
            
            key_phrases_result = self._extract_key_phrases_focused(text_chunks, cleaned_text)

            # Step 4: Generate enhanced summary
            if progress_callback:
                progress_callback("📝 Generating study-focused summary...")
            
            summary_result = self._generate_enhanced_summary(cleaned_text, text_chunks)

            # Step 5: Analyze sentiment and tone
            if progress_callback:
                progress_callback("😊 Analyzing content sentiment...")
            
            sentiment_result = self._analyze_sentiment(text_chunks)

            # Step 6: Extract entities (people, places, concepts)
            if progress_callback:
                progress_callback("🏷️ Identifying key entities...")
            
            entities_result = self._extract_entities(text_chunks)

            # Step 7: Assess study material quality
            if progress_callback:
                progress_callback("📊 Assessing study material quality...")
            
            study_assessment = self._assess_study_quality(cleaned_text, key_phrases_result, entities_result)

            # Step 8: Generate flashcard recommendations
            if progress_callback:
                progress_callback("🎴 Generating flashcard recommendations...")
            
            flashcard_recommendations = self._generate_flashcard_recommendations(
                cleaned_text, key_phrases_result, entities_result, study_assessment
            )

            if progress_callback:
                progress_callback("✅ Language analysis completed!")

            # Combine all results
            comprehensive_result = {
                "status": "success",
                "cleaned_text": cleaned_text,
                "key_phrases": key_phrases_result,
                "summary": summary_result,
                "sentiment": sentiment_result,
                "entities": entities_result,
                "study_assessment": study_assessment,
                "flashcard_recommendations": flashcard_recommendations,
                "text_complexity": self.text_processor.assess_text_complexity(cleaned_text),
                "processing_metadata": {
                    "original_length": len(text),
                    "cleaned_length": len(cleaned_text),
                    "chunks_processed": len(text_chunks),
                    "azure_services_used": ["key_phrases", "entities", "sentiment"],
                    "processing_time": datetime.now().isoformat()
                }
            }

            return comprehensive_result

        except Exception as e:
            error_msg = f"Azure Language analysis failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg, text)

    def _split_text_for_analysis(self, text: str, max_chunk_size: int = 5000) -> List[str]:
        """Split text into chunks suitable for Azure Language Services"""
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if adding this sentence would exceed limit
            if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    for i in range(0, len(words), 100):  # 100 words per chunk
                        word_chunk = ' '.join(words[i:i+100])
                        chunks.append(word_chunk)
            else:
                current_chunk += (". " if current_chunk else "") + sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _extract_key_phrases_focused(self, text_chunks: List[str], full_text: str) -> Dict:
        """Extract key phrases with focus on study-relevant content"""
        try:
            all_key_phrases = []
            confidence_scores = []

            # Process chunks through Azure
            for chunk in text_chunks:
                if len(chunk.strip()) < 10:
                    continue

                try:
                    response = self.client.extract_key_phrases(documents=[chunk])
                    
                    for doc in response:
                        if not doc.is_error:
                            for phrase in doc.key_phrases:
                                # Filter for study relevance
                                if self._is_study_relevant_phrase(phrase):
                                    all_key_phrases.append(phrase)
                                    # Calculate importance score
                                    importance = self._calculate_study_importance(phrase, full_text)
                                    confidence_scores.append(importance)
                        else:
                            logger.warning(f"Key phrase extraction error: {doc.error}")

                except Exception as e:
                    logger.warning(f"Error processing chunk for key phrases: {e}")
                    continue

            # Remove duplicates and sort by importance
            phrase_scores = list(zip(all_key_phrases, confidence_scores))
            unique_phrases = {}
            for phrase, score in phrase_scores:
                if phrase not in unique_phrases or score > unique_phrases[phrase]:
                    unique_phrases[phrase] = score

            # Sort by importance
            sorted_phrases = sorted(unique_phrases.items(), key=lambda x: x[1], reverse=True)

            # Also extract concepts using local processing
            local_concepts = self.text_processor.extract_key_concepts(full_text)

            return {
                "azure_key_phrases": [phrase for phrase, score in sorted_phrases[:15]],
                "local_concepts": local_concepts[:10],
                "phrase_importance_scores": dict(sorted_phrases[:15]),
                "total_phrases_found": len(all_key_phrases),
                "study_relevant_phrases": len([p for p in all_key_phrases if self._is_study_relevant_phrase(p)])
            }

        except Exception as e:
            logger.error(f"Key phrase extraction error: {e}")
            return {
                "azure_key_phrases": [],
                "local_concepts": self.text_processor.extract_key_concepts(full_text),
                "error": str(e)
            }

    def _is_study_relevant_phrase(self, phrase: str) -> bool:
        """Determine if a phrase is relevant for study materials"""
        phrase_lower = phrase.lower()
        
        # Filter out common non-study phrases
        irrelevant_patterns = [
            r'^(the|a|an|and|or|but|in|on|at|to|for|of|with|by)$',
            r'^\d+$',  # Pure numbers
            r'^(page|chapter|section)\s+\d+$',  # Page references
            r'^(figure|table|diagram)\s+\d+$',  # Figure references
        ]
        
        for pattern in irrelevant_patterns:
            if re.match(pattern, phrase_lower):
                return False
        
        # Prefer phrases that indicate concepts
        study_indicators = [
            'concept', 'theory', 'principle', 'method', 'process', 'technique',
            'definition', 'formula', 'equation', 'rule', 'law', 'property',
            'characteristic', 'feature', 'example', 'application', 'use'
        ]
        
        # Check if phrase contains study indicators
        for indicator in study_indicators:
            if indicator in phrase_lower:
                return True
        
        # Check phrase length and complexity
        if 2 <= len(phrase.split()) <= 4 and len(phrase) >= 5:
            return True
        
        return False

    def _calculate_study_importance(self, phrase: str, full_text: str) -> float:
        """Calculate importance score for a phrase in study context"""
        try:
            # Base importance
            importance = 0.5
            
            # Frequency in text (normalized)
            frequency = full_text.lower().count(phrase.lower())
            frequency_score = min(0.3, frequency / 10)  # Cap at 0.3
            importance += frequency_score
            
            # Length bonus (moderate length preferred)
            word_count = len(phrase.split())
            if 2 <= word_count <= 3:
                importance += 0.2
            elif word_count == 4:
                importance += 0.1
            
            # Capitalization bonus (proper nouns/concepts)
            if phrase[0].isupper():
                importance += 0.1
            
            # Study keyword bonus
            study_keywords = [
                'concept', 'theory', 'principle', 'method', 'process',
                'definition', 'formula', 'example', 'application'
            ]
            for keyword in study_keywords:
                if keyword in phrase.lower():
                    importance += 0.15
                    break
            
            return min(importance, 1.0)  # Cap at 1.0
            
        except Exception:
            return 0.5

    def _generate_enhanced_summary(self, cleaned_text: str, text_chunks: List[str]) -> Dict:
        """Generate enhanced summary optimized for study materials"""
        try:
            # Use Azure extractive summarization if available
            azure_summary = None
            if len(cleaned_text) > 200:
                try:
                    # For longer texts, use Azure's summarization
                    from azure.ai.textanalytics import ExtractiveSummaryAction
                    
                    # Create summarization request
                    actions = [ExtractiveSummaryAction(max_sentence_count=5)]
                    poller = self.client.begin_analyze_actions(
                        documents=[cleaned_text[:10000]],  # Limit for API
                        actions=actions
                    )
                    
                    result = poller.result()
                    for result_page in result:
                        for action_result in result_page:
                            if not action_result.is_error:
                                sentences = [sentence.text for sentence in action_result.sentences]
                                azure_summary = ' '.join(sentences)
                                break
                
                except Exception as e:
                    logger.warning(f"Azure summarization failed: {e}")

            # Generate concept-based summary using local processing
            concept_summary = self._concept_based_summarization(cleaned_text)

            # Create comprehensive summary
            summary_result = {
                "azure_extractive_summary": azure_summary,
                "concept_based_summary": concept_summary,
                "key_sentences": self._extract_key_sentences(cleaned_text),
                "summary_length": len(azure_summary) if azure_summary else len(concept_summary.get("summary", "")),
                "compression_ratio": self._calculate_compression_ratio(cleaned_text, azure_summary or concept_summary.get("summary", ""))
            }

            return summary_result

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {
                "error": str(e),
                "concept_based_summary": self._concept_based_summarization(cleaned_text)
            }

    def _concept_based_summarization(self, text: str) -> Dict:
        """Generate concept-based summary for study materials"""
        try:
            sentences = re.split(r'[.!?]+', text)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            # Score sentences based on study relevance
            sentence_scores = []
            for sentence in meaningful_sentences:
                score = self._score_sentence_for_study(sentence, text)
                sentence_scores.append((sentence, score))
            
            # Sort by score and take top sentences
            sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in sorted_sentences[:5]]
            
            # Create summary
            summary_text = '. '.join(top_sentences) + '.' if top_sentences else ""
            
            return {
                "summary": summary_text,
                "top_sentences": top_sentences,
                "sentence_count": len(meaningful_sentences),
                "selected_count": len(top_sentences)
            }
            
        except Exception as e:
            logger.warning(f"Concept summarization error: {e}")
            return {"summary": text[:500] + "..." if len(text) > 500 else text}

    def _score_sentence_for_study(self, sentence: str, full_text: str) -> float:
        """Score a sentence for its study material relevance"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Study keyword indicators
        study_keywords = {
            'definition': 1.0, 'concept': 0.9, 'theory': 0.9, 'principle': 0.8,
            'method': 0.7, 'process': 0.7, 'example': 0.6, 'application': 0.6,
            'important': 0.8, 'significant': 0.7, 'key': 0.6, 'main': 0.5
        }
        
        for keyword, weight in study_keywords.items():
            if keyword in sentence_lower:
                score += weight
        
        # Position bonus (first and last sentences often important)
        sentences = re.split(r'[.!?]+', full_text)
        if sentence in sentences[:3]:  # First 3 sentences
            score += 0.3
        elif sentence in sentences[-3:]:  # Last 3 sentences
            score += 0.2
        
        # Length penalty/bonus
        word_count = len(sentence.split())
        if 10 <= word_count <= 30:  # Optimal length
            score += 0.2
        elif word_count < 5:  # Too short
            score -= 0.3
        elif word_count > 50:  # Too long
            score -= 0.2
        
        # Capitalization bonus (proper nouns)
        capitalized_words = [word for word in sentence.split() if word[0].isupper()]
        if len(capitalized_words) > 1:
            score += 0.1
        
        return score

    def _extract_key_sentences(self, text: str) -> List[str]:
        """Extract key sentences for study focus"""
        sentences = re.split(r'[.!?]+', text)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        # Look for sentences with strong study indicators
        key_sentences = []
        for sentence in meaningful_sentences:
            if any(indicator in sentence.lower() for indicator in [
                'definition', 'concept', 'important', 'key', 'main', 'primary',
                'theory', 'principle', 'method', 'process', 'example'
            ]):
                key_sentences.append(sentence)
        
        return key_sentences[:7]  # Return top 7 key sentences

    def _calculate_compression_ratio(self, original: str, summary: str) -> float:
        """Calculate compression ratio of summary"""
        if not original or not summary:
            return 0.0
        return round(len(summary) / len(original), 3)

    def _analyze_sentiment(self, text_chunks: List[str]) -> Dict:
        """Analyze sentiment and tone of the content"""
        try:
            sentiments = []
            confidences = []
            
            for chunk in text_chunks:
                if len(chunk.strip()) < 10:
                    continue
                
                try:
                    response = self.client.analyze_sentiment(documents=[chunk])
                    
                    for doc in response:
                        if not doc.is_error:
                            sentiments.append(doc.sentiment)
                            confidences.append(doc.confidence_scores)
                        else:
                            logger.warning(f"Sentiment analysis error: {doc.error}")
                
                except Exception as e:
                    logger.warning(f"Error in sentiment analysis: {e}")
                    continue
            
            # Aggregate results
            if sentiments:
                overall_sentiment = max(set(sentiments), key=sentiments.count)
                avg_confidence = {
                    "positive": sum(c.positive for c in confidences) / len(confidences),
                    "neutral": sum(c.neutral for c in confidences) / len(confidences),
                    "negative": sum(c.negative for c in confidences) / len(confidences)
                }
            else:
                overall_sentiment = "neutral"
                avg_confidence = {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
            
            return {
                "overall_sentiment": overall_sentiment,
                "confidence_scores": avg_confidence,
                "sentiment_distribution": {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)},
                "study_tone_assessment": self._assess_study_tone(overall_sentiment, avg_confidence)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "overall_sentiment": "neutral",
                "error": str(e),
                "study_tone_assessment": "unknown"
            }

    def _assess_study_tone(self, sentiment: str, confidence: Dict) -> str:
        """Assess if the tone is appropriate for study materials"""
        if sentiment == "neutral" and confidence["neutral"] > 0.7:
            return "academic"
        elif sentiment == "positive" and confidence["positive"] > 0.6:
            return "engaging"
        elif sentiment == "negative":
            return "critical_analysis"
        else:
            return "mixed"

    def _extract_entities(self, text_chunks: List[str]) -> Dict:
        """Extract named entities relevant to study materials"""
        try:
            all_entities = []
            
            for chunk in text_chunks:
                if len(chunk.strip()) < 10:
                    continue
                
                try:
                    response = self.client.recognize_entities(documents=[chunk])
                    
                    for doc in response:
                        if not doc.is_error:
                            for entity in doc.entities:
                                # Filter for study-relevant entity types
                                if entity.category in ['Person', 'Organization', 'Location', 'Event', 'Product', 'Skill']:
                                    all_entities.append({
                                        "text": entity.text,
                                        "category": entity.category,
                                        "confidence": entity.confidence_score,
                                        "subcategory": getattr(entity, 'subcategory', None)
                                    })
                        else:
                            logger.warning(f"Entity recognition error: {doc.error}")
                
                except Exception as e:
                    logger.warning(f"Error in entity recognition: {e}")
                    continue
            
            # Group entities by category
            entities_by_category = {}
            for entity in all_entities:
                category = entity["category"]
                if category not in entities_by_category:
                    entities_by_category[category] = []
                entities_by_category[category].append(entity)
            
            # Remove duplicates and sort by confidence
            for category in entities_by_category:
                seen_texts = set()
                unique_entities = []
                for entity in sorted(entities_by_category[category], key=lambda x: x["confidence"], reverse=True):
                    if entity["text"] not in seen_texts:
                        unique_entities.append(entity)
                        seen_texts.add(entity["text"])
                entities_by_category[category] = unique_entities[:5]  # Top 5 per category
            
            return {
                "entities_by_category": entities_by_category,
                "total_entities": len(all_entities),
                "unique_entities": sum(len(entities) for entities in entities_by_category.values()),
                "study_relevant_entities": self._filter_study_relevant_entities(entities_by_category)
            }
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {
                "entities_by_category": {},
                "error": str(e)
            }

    def _filter_study_relevant_entities(self, entities_by_category: Dict) -> Dict:
        """Filter entities most relevant for study materials"""
        study_relevant = {}
        
        # Priority categories for study materials
        priority_categories = ['Person', 'Organization', 'Event', 'Product']
        
        for category in priority_categories:
            if category in entities_by_category:
                # Filter high-confidence entities
                relevant_entities = [
                    entity for entity in entities_by_category[category]
                    if entity["confidence"] > 0.7
                ]
                if relevant_entities:
                    study_relevant[category] = relevant_entities
        
        return study_relevant

    def _assess_study_quality(self, text: str, key_phrases: Dict, entities: Dict) -> Dict:
        """Assess overall quality of content for study purposes"""
        try:
            # Text complexity assessment
            complexity = self.text_processor.assess_text_complexity(text)
            
            # Content richness assessment
            phrase_count = len(key_phrases.get("azure_key_phrases", []))
            entity_count = entities.get("unique_entities", 0)
            study_phrases = key_phrases.get("study_relevant_phrases", 0)
            
            # Calculate study quality score
            quality_score = 0.0
            
            # Text length contribution (20%)
            word_count = len(text.split())
            if 200 <= word_count <= 5000:
                quality_score += 0.2
            elif word_count > 5000:
                quality_score += 0.15
            elif word_count > 50:
                quality_score += 0.1
            
            # Content richness (30%)
            if phrase_count > 10:
                quality_score += 0.15
            elif phrase_count > 5:
                quality_score += 0.1
            
            if entity_count > 5:
                quality_score += 0.15
            elif entity_count > 2:
                quality_score += 0.1
            
            # Study relevance (30%)
            if study_phrases > phrase_count * 0.6:  # >60% study relevant
                quality_score += 0.3
            elif study_phrases > phrase_count * 0.4:  # >40% study relevant
                quality_score += 0.2
            elif study_phrases > 0:
                quality_score += 0.1
            
            # Readability (20%)
            reading_level = complexity.get("reading_level", "medium")
            if reading_level in ["easy", "medium"]:
                quality_score += 0.2
            elif reading_level == "hard":
                quality_score += 0.1
            
            # Determine overall quality
            if quality_score >= 0.8:
                overall_quality = "excellent"
            elif quality_score >= 0.6:
                overall_quality = "good"
            elif quality_score >= 0.4:
                overall_quality = "fair"
            else:
                overall_quality = "poor"
            
            return {
                "overall_quality": overall_quality,
                "quality_score": round(quality_score, 2),
                "content_metrics": {
                    "word_count": word_count,
                    "key_phrases_count": phrase_count,
                    "entities_count": entity_count,
                    "study_relevant_phrases": study_phrases
                },
                "recommendations": self._generate_quality_recommendations(quality_score, complexity, phrase_count)
            }
            
        except Exception as e:
            logger.error(f"Study quality assessment error: {e}")
            return {"error": str(e), "overall_quality": "unknown"}

    def _generate_quality_recommendations(self, quality_score: float, complexity: Dict, phrase_count: int) -> List[str]:
        """Generate recommendations for improving study material quality"""
        recommendations = []
        
        if quality_score < 0.4:
            recommendations.append("Consider using more detailed source material")
        
        if phrase_count < 5:
            recommendations.append("Content may benefit from more key concepts and terms")
        
        reading_level = complexity.get("reading_level", "medium")
        if reading_level == "hard":
            recommendations.append("Content complexity is high - consider breaking into smaller sections")
        
        word_count = complexity.get("word_count", 0)
        if word_count < 100:
            recommendations.append("Content is quite short - additional material may improve flashcard generation")
        elif word_count > 10000:
            recommendations.append("Content is very long - consider processing in smaller sections")
        
        if not recommendations:
            recommendations.append("Content quality is good for flashcard generation")
        
        return recommendations

    def _generate_flashcard_recommendations(self, text: str, key_phrases: Dict, entities: Dict, study_assessment: Dict) -> Dict:
        """Generate specific recommendations for flashcard creation"""
        try:
            recommendations = {
                "recommended_types": [],
                "optimal_count": 0,
                "difficulty_distribution": {},
                "content_focus_areas": [],
                "generation_strategy": ""
            }
            
            # Determine recommended flashcard types based on content
            phrase_count = len(key_phrases.get("azure_key_phrases", []))
            entity_count = entities.get("unique_entities", 0)
            quality = study_assessment.get("overall_quality", "unknown")
            
            # Type recommendations
            if phrase_count > 8:
                recommendations["recommended_types"].extend(["definition", "conceptual"])
            if entity_count > 3:
                recommendations["recommended_types"].append("detail")
            if "example" in text.lower() or "application" in text.lower():
                recommendations["recommended_types"].append("application")
            
            # Default types if none detected
            if not recommendations["recommended_types"]:
                recommendations["recommended_types"] = ["definition", "conceptual"]
            
            # Optimal count based on content length and quality
            word_count = len(text.split())
            if quality == "excellent":
                recommendations["optimal_count"] = min(15, max(5, word_count // 200))
            elif quality == "good":
                recommendations["optimal_count"] = min(12, max(4, word_count // 250))
            else:
                recommendations["optimal_count"] = min(8, max(3, word_count // 300))
            
            # Difficulty distribution
            complexity_level = study_assessment.get("content_metrics", {}).get("complexity", "medium")
            if complexity_level == "easy":
                recommendations["difficulty_distribution"] = {"easy": 60, "medium": 30, "hard": 10}
            elif complexity_level == "hard":
                recommendations["difficulty_distribution"] = {"easy": 20, "medium": 40, "hard": 40}
            else:
                recommendations["difficulty_distribution"] = {"easy": 40, "medium": 40, "hard": 20}
            
            # Content focus areas
            top_phrases = key_phrases.get("azure_key_phrases", [])[:5]
            entity_categories = list(entities.get("entities_by_category", {}).keys())
            
            recommendations["content_focus_areas"] = top_phrases + entity_categories
            
            # Generation strategy
            if quality in ["excellent", "good"]:
                recommendations["generation_strategy"] = "comprehensive"
            else:
                recommendations["generation_strategy"] = "focused"
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Flashcard recommendations error: {e}")
            return {
                "recommended_types": ["definition", "conceptual"],
                "optimal_count": 5,
                "error": str(e)
            }

    def _create_fallback_analysis(self, text: str) -> Dict:
        """Create fallback analysis when Azure is not available"""
        logger.info("🔄 Creating fallback analysis without Azure Language Service...")
        
        try:
            # Clean text using local processor
            cleaned_text = self.text_processor.clean_ocr_text(text)
            
            # Extract concepts locally
            local_concepts = self.text_processor.extract_key_concepts(cleaned_text)
            
            # Assess complexity
            complexity = self.text_processor.assess_text_complexity(cleaned_text)
            
            # Create basic summary
            sentences = re.split(r'[.!?]+', cleaned_text)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            basic_summary = '. '.join(meaningful_sentences[:3]) + '.' if meaningful_sentences else cleaned_text[:200]
            
            return {
                "status": "fallback",
                "cleaned_text": cleaned_text,
                "key_phrases": {
                    "local_concepts": local_concepts,
                    "azure_key_phrases": [],
                    "fallback_used": True
                },
                "summary": {
                    "concept_based_summary": {"summary": basic_summary},
                    "azure_extractive_summary": None
                },
                "sentiment": {
                    "overall_sentiment": "neutral",
                    "study_tone_assessment": "academic"
                },
                "entities": {"entities_by_category": {}},
                "text_complexity": complexity,
                "study_assessment": {
                    "overall_quality": "fair",
                    "quality_score": 0.5,
                    "recommendations": ["Azure Language Service not available - using local processing"]
                },
                "flashcard_recommendations": {
                    "recommended_types": ["definition", "conceptual"],
                    "optimal_count": min(8, max(3, len(cleaned_text.split()) // 300)),
                    "generation_strategy": "basic"
                },
                "processing_metadata": {
                    "azure_available": False,
                    "fallback_used": True,
                    "local_processing_only": True
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {"error": f"Analysis failed: {e}", "status": "error"}

    def _create_error_response(self, error_message: str, original_text: str) -> Dict:
        """Create standardized error response"""
        return {
            "status": "error",
            "error": error_message,
            "fallback_analysis": self._create_fallback_analysis(original_text),
            "processing_metadata": {
                "error_occurred": True,
                "azure_available": self.is_available,
                "timestamp": datetime.now().isoformat()
            }
        }

# Create global instance
azure_language_processor = AzureLanguageProcessor()