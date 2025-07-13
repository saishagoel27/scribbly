import logging
import re
import string
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from azure.ai.textanalytics import TextAnalyticsClient, ExtractiveSummaryAction, AbstractiveSummaryAction
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureLanguageProcessor:
    """
     Azure Language Services processor with advanced summarization
    
    """

    def __init__(self):
        self.client = None
        self.is_available = False
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Azure Language client"""
        try:
            if Config.AZURE_LANGUAGE_ENDPOINT and Config.AZURE_LANGUAGE_KEY:
                self.client = TextAnalyticsClient(
                    endpoint=Config.AZURE_LANGUAGE_ENDPOINT,
                    credential=AzureKeyCredential(Config.AZURE_LANGUAGE_KEY)
                )
                self.is_available = True
                logger.info("Azure Language client initialized successfully")
            else:
                logger.warning("Azure Language credentials not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Language: {e}")
            self.is_available = False

    def analyze_for_study_materials(self, text: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        ENHANCED: Advanced analysis using Azure's native summarization APIs
        
        Args:
            text: Input text to analyze
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing enhanced analysis results with better summaries
        """
        if not self.is_available:
            return self._create_fallback_analysis(text)

        try:
            if progress_callback:
                progress_callback("🧠 Starting advanced content analysis...")

            # Step 1: Basic text cleaning (enhanced)
            if progress_callback:
                progress_callback("🧹 Preparing text for Azure analysis...")
            
            cleaned_text = self._enhanced_text_clean(text)
            
            if len(cleaned_text.strip()) < 50:
                return {"error": "Insufficient text for analysis after cleaning"}

            # Step 2: ENHANCED - Use Azure's native summarization
            if progress_callback:
                progress_callback("📝 Creating AI-powered summaries...")
            
            summary_result = self._generate_azure_summaries(cleaned_text)

            # Step 3: Enhanced key phrase extraction
            if progress_callback:
                progress_callback("🔍 Extracting key educational concepts...")
            
            key_phrases = self._extract_educational_key_phrases(cleaned_text)

            # Step 4: Educational entity extraction
            if progress_callback:
                progress_callback("🏷️ Identifying educational entities...")
            
            entities = self._extract_educational_entities(cleaned_text)

            # Step 5: Advanced sentiment analysis
            if progress_callback:
                progress_callback("😊 Analyzing educational tone...")
            
            sentiment = self._analyze_educational_sentiment(cleaned_text)

            # Step 6: Enhanced study quality assessment
            if progress_callback:
                progress_callback("📊 Assessing educational value...")
            
            study_assessment = self._assess_educational_quality(cleaned_text, key_phrases, entities)

            if progress_callback:
                progress_callback("✅ Advanced analysis completed!")

            # ENHANCED: Return structure with better summaries
            return {
                "status": "success",
                "cleaned_text": cleaned_text,
                "summary": summary_result,  # Now contains multiple summary types
                "key_phrases": {
                    "azure_key_phrases": key_phrases,
                    "educational_concepts": self._categorize_educational_concepts(key_phrases)
                },
                "sentiment": sentiment,
                "entities": entities,
                "study_assessment": study_assessment,
                "text_complexity": self._assess_educational_complexity(cleaned_text),
                "processing_metadata": {
                    "original_length": len(text),
                    "cleaned_length": len(cleaned_text),
                    "azure_services_used": ["extractive_summary", "abstractive_summary", "key_phrases", "entities", "sentiment"],
                    "processing_time": datetime.now().isoformat(),
                    "azure_api_version": "2023-04-01"
                }
            }

        except Exception as e:
            error_msg = f"Azure Language analysis failed: {str(e)}"
            logger.error(error_msg)
            return self._create_fallback_analysis(text)

    def _enhanced_text_clean(self, text: str) -> str:
        """Enhanced text cleaning for educational content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors in educational texts
        text = re.sub(r'[|]', 'l', text)
        text = re.sub(r'[0O](?=[a-z])', 'o', text)
        text = re.sub(r'\b([A-Z])\s+([a-z])', r'\1\2', text)  # Fix spaced capitals
        
        # Preserve educational formatting
        text = re.sub(r'(\d+)\.\s+', r'\n\1. ', text)  # Preserve numbered lists
        text = re.sub(r'([a-z])\s*\n\s*([A-Z])', r'\1. \2', text)  # Fix sentence breaks
        
        # Remove special characters but keep educational punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\/\%\$\°]', ' ', text)
        
        return text.strip()

    def _generate_azure_summaries(self, text: str) -> Dict[str, str]:
        """ENHANCED: Generate multiple types of summaries using Azure APIs"""
        summaries = {}
        
        try:
            # Prepare documents (Azure has character limits)
            max_chars = 125000  # Azure limit
            if len(text) > max_chars:
                text = text[:max_chars]
            
            documents = [text]
            
            # 1. EXTRACTIVE SUMMARY - Azure selects key sentences
            try:
                extractive_action = ExtractiveSummaryAction(max_sentence_count=5)
                poller = self.client.begin_analyze_actions(
                    documents,
                    actions=[extractive_action]
                )
                
                result = poller.result()
                for action_result in result:
                    for document_result in action_result:
                        if hasattr(document_result, 'sentences'):
                            extractive_sentences = [sentence.text for sentence in document_result.sentences]
                            summaries["extractive"] = ' '.join(extractive_sentences)
                        
            except Exception as e:
                logger.warning(f"Extractive summarization failed: {e}")
                summaries["extractive"] = self._fallback_extractive_summary(text)

            # 2. ABSTRACTIVE SUMMARY - Azure generates new summary text
            try:
                abstractive_action = AbstractiveSummaryAction(max_sentence_count=3)
                poller = self.client.begin_analyze_actions(
                    documents,
                    actions=[abstractive_action]
                )
                
                result = poller.result()
                for action_result in result:
                    for document_result in action_result:
                        if hasattr(document_result, 'summaries'):
                            for summary in document_result.summaries:
                                summaries["abstractive"] = summary.text
                                break
                        
            except Exception as e:
                logger.warning(f"Abstractive summarization failed: {e}")
                summaries["abstractive"] = self._generate_concept_summary(text)

            # 3. EDUCATIONAL SUMMARY - Custom for study materials
            summaries["educational"] = self._generate_educational_summary(text, summaries)
            
            # 4. Best summary selection
            summaries["best"] = self._select_best_summary(summaries)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {
                "extractive": self._fallback_extractive_summary(text),
                "abstractive": self._generate_concept_summary(text),
                "educational": text[:200] + "..." if len(text) > 200 else text,
                "best": text[:200] + "..." if len(text) > 200 else text
            }

    def _generate_educational_summary(self, text: str, existing_summaries: Dict[str, str]) -> str:
        """Generate study-focused summary"""
        try:
            # Prioritize educational content
            educational_keywords = [
                'definition', 'concept', 'theory', 'principle', 'method', 'process',
                'example', 'application', 'important', 'key', 'main', 'primary',
                'fundamental', 'essential', 'basic', 'advanced', 'formula', 'equation'
            ]
            
            sentences = re.split(r'[.!?]+', text)
            scored_sentences = []
            
            for sentence in sentences:
                if len(sentence.strip()) < 20:
                    continue
                    
                score = 0
                sentence_lower = sentence.lower()
                
                # Score based on educational keywords
                for keyword in educational_keywords:
                    if keyword in sentence_lower:
                        score += 2
                
                # Score based on sentence position (important concepts often appear early)
                position_bonus = max(0, 3 - (len(scored_sentences) * 0.1))
                score += position_bonus
                
                # Score based on sentence length (not too short, not too long)
                length = len(sentence.split())
                if 10 <= length <= 30:
                    score += 1
                
                scored_sentences.append((sentence.strip(), score))
            
            # Select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent[0] for sent in scored_sentences[:4]]
            
            educational_summary = '. '.join(top_sentences) + '.'
            
            # Fallback to extractive if educational summary is too short
            if len(educational_summary) < 100 and existing_summaries.get('extractive'):
                return existing_summaries['extractive']
                
            return educational_summary
            
        except Exception as e:
            logger.error(f"Educational summary generation failed: {e}")
            return text[:300] + "..." if len(text) > 300 else text

    def _select_best_summary(self, summaries: Dict[str, str]) -> str:
        """Select the best summary from available options"""
        # Priority order
        priority = ['educational', 'extractive', 'abstractive']
        
        for summary_type in priority:
            if summary_type in summaries and summaries[summary_type]:
                if len(summaries[summary_type].strip()) > 50:  # Minimum length check
                    return summaries[summary_type]
        
        # Fallback
        for summary in summaries.values():
            if summary and len(summary.strip()) > 20:
                return summary
        
        return "Summary not available"

    def _extract_educational_key_phrases(self, text: str) -> List[str]:
        """Enhanced key phrase extraction focused on educational content"""
        try:
            if not self.client:
                return []
            
            # Split text if too long
            max_length = 5000
            if len(text) > max_length:
                text = text[:max_length]
            
            documents = [text]
            response = self.client.extract_key_phrases(documents)
            
            educational_phrases = []
            for doc in response:
                if hasattr(doc, 'key_phrases'):
                    for phrase in doc.key_phrases:
                        if self._is_educational_relevant(phrase):
                            educational_phrases.append(phrase)
            
            # Enhance with custom extraction
            custom_phrases = self._extract_custom_educational_phrases(text)
            
            # Combine and deduplicate
            all_phrases = list(set(educational_phrases + custom_phrases))
            
            # Score and sort by educational relevance
            scored_phrases = [(phrase, self._score_educational_relevance(phrase, text)) 
                            for phrase in all_phrases]
            scored_phrases.sort(key=lambda x: x[1], reverse=True)
            
            return [phrase[0] for phrase in scored_phrases[:20]]
            
        except Exception as e:
            logger.error(f"Educational key phrase extraction error: {e}")
            return []

    def _is_educational_relevant(self, phrase: str) -> bool:
        """Enhanced check for educational relevance"""
        # Filter out very short phrases
        if len(phrase) < 3:
            return False
        
        # Filter out pure numbers or dates
        if phrase.isdigit() or re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', phrase):
            return False
        
        # Filter out common stop phrases
        stop_phrases = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        if phrase.lower() in stop_phrases:
            return False
        
        # Boost educational terms
        educational_indicators = [
            'theory', 'concept', 'principle', 'method', 'process', 'system',
            'analysis', 'synthesis', 'evaluation', 'application', 'definition',
            'model', 'framework', 'approach', 'technique', 'strategy'
        ]
        
        phrase_lower = phrase.lower()
        for indicator in educational_indicators:
            if indicator in phrase_lower:
                return True
        
        # Check if phrase contains academic/technical language
        if any(c.isupper() for c in phrase) and len(phrase) > 5:  # Acronyms or proper nouns
            return True
            
        return len(phrase.split()) >= 2  # Prefer multi-word phrases

    def _extract_custom_educational_phrases(self, text: str) -> List[str]:
        """Extract custom educational phrases using patterns"""
        phrases = []
        
        # Pattern 1: "X is defined as Y"
        definition_pattern = r'([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:is|are)\s+defined\s+as\s+([^.]+)'
        for match in re.finditer(definition_pattern, text):
            phrases.append(match.group(1))
        
        # Pattern 2: Technical terms (capitalized multi-word phrases)
        technical_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(technical_pattern, text):
            phrases.append(match.group(1))
        
        # Pattern 3: Numbered concepts
        numbered_pattern = r'\d+\.\s+([A-Z][^.]+)'
        for match in re.finditer(numbered_pattern, text):
            concept = match.group(1).strip()
            if len(concept) > 5 and len(concept) < 50:
                phrases.append(concept)
        
        return phrases[:10]  # Limit custom phrases

    def _score_educational_relevance(self, phrase: str, context: str) -> float:
        """Score phrase based on educational relevance"""
        score = 0.0
        
        # Length scoring
        word_count = len(phrase.split())
        if 2 <= word_count <= 4:
            score += 1.0
        elif word_count == 1:
            score += 0.3
        else:
            score += 0.5
        
        # Educational keyword scoring
        educational_keywords = {
            'high': ['definition', 'concept', 'theory', 'principle', 'method'],
            'medium': ['process', 'system', 'analysis', 'application', 'example'],
            'low': ['important', 'main', 'key', 'basic', 'essential']
        }
        
        phrase_lower = phrase.lower()
        for level, keywords in educational_keywords.items():
            for keyword in keywords:
                if keyword in phrase_lower:
                    if level == 'high':
                        score += 2.0
                    elif level == 'medium':
                        score += 1.5
                    else:
                        score += 1.0
        
        # Frequency in context
        frequency = context.lower().count(phrase.lower())
        if frequency > 1:
            score += min(frequency * 0.5, 2.0)
        
        return score

    def _categorize_educational_concepts(self, key_phrases: List[str]) -> Dict[str, List[str]]:
        """Categorize key phrases by educational type"""
        categories = {
            "definitions": [],
            "processes": [],
            "theories": [],
            "applications": [],
            "general": []
        }
        
        for phrase in key_phrases:
            phrase_lower = phrase.lower()
            
            if any(word in phrase_lower for word in ['definition', 'defined as', 'is a', 'refers to']):
                categories["definitions"].append(phrase)
            elif any(word in phrase_lower for word in ['process', 'method', 'procedure', 'step', 'approach']):
                categories["processes"].append(phrase)
            elif any(word in phrase_lower for word in ['theory', 'principle', 'law', 'rule', 'concept']):
                categories["theories"].append(phrase)
            elif any(word in phrase_lower for word in ['application', 'example', 'use', 'implementation']):
                categories["applications"].append(phrase)
            else:
                categories["general"].append(phrase)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _extract_educational_entities(self, text: str) -> Dict:
        """Enhanced entity extraction for educational content"""
        try:
            if not self.client:
                return {"people": [], "locations": [], "organizations": [], "concepts": []}
            
            max_length = 5000
            if len(text) > max_length:
                text = text[:max_length]
            
            documents = [text]
            response = self.client.recognize_entities(documents)
            
            entities = {
                "people": [],
                "locations": [],
                "organizations": [],
                "concepts": [],
                "dates": [],
                "quantities": []
            }
            
            for doc in response:
                if hasattr(doc, 'entities'):
                    for entity in doc.entities:
                        category = entity.category.lower()
                        text_val = entity.text
                        confidence = getattr(entity, 'confidence_score', 0.0)
                        
                        # Only include high-confidence entities
                        if confidence < 0.7:
                            continue
                        
                        if category == "person":
                            entities["people"].append(text_val)
                        elif category in ["location", "gpe"]:
                            entities["locations"].append(text_val)
                        elif category == "organization":
                            entities["organizations"].append(text_val)
                        elif category in ["event", "skill", "product"]:
                            entities["concepts"].append(text_val)
                        elif category in ["datetime", "date"]:
                            entities["dates"].append(text_val)
                        elif category in ["quantity", "number", "percentage"]:
                            entities["quantities"].append(text_val)
            
            # Remove duplicates and limit
            for key in entities:
                entities[key] = list(set(entities[key]))[:8]
            
            return entities
            
        except Exception as e:
            logger.error(f"Educational entity extraction error: {e}")
            return {"people": [], "locations": [], "organizations": [], "concepts": []}

    def _analyze_educational_sentiment(self, text: str) -> Dict:
        """Enhanced sentiment analysis for educational content"""
        try:
            if not self.client:
                return {"sentiment": "neutral", "confidence": 0.5, "educational_tone": "informational"}
            
            max_length = 5000
            if len(text) > max_length:
                text = text[:max_length]
            
            documents = [text]
            response = self.client.analyze_sentiment(documents)
            
            for doc in response:
                if hasattr(doc, 'sentiment'):
                    confidence_scores = getattr(doc, 'confidence_scores', None)
                    main_confidence = 0.5
                    
                    if confidence_scores:
                        sentiment = doc.sentiment
                        if sentiment == "positive":
                            main_confidence = confidence_scores.positive
                        elif sentiment == "negative":
                            main_confidence = confidence_scores.negative
                        else:
                            main_confidence = confidence_scores.neutral
                    
                    educational_tone = self._determine_educational_tone(doc.sentiment, text)
                    learning_difficulty = self._assess_learning_difficulty(text)
                    
                    return {
                        "sentiment": doc.sentiment,
                        "confidence": main_confidence,
                        "educational_tone": educational_tone,
                        "learning_difficulty": learning_difficulty,
                        "engagement_level": self._assess_engagement_level(doc.sentiment, text)
                    }
            
            return {
                "sentiment": "neutral", 
                "confidence": 0.5, 
                "educational_tone": "informational",
                "learning_difficulty": "moderate",
                "engagement_level": "neutral"
            }
            
        except Exception as e:
            logger.error(f"Educational sentiment analysis error: {e}")
            return {
                "sentiment": "neutral", 
                "confidence": 0.5, 
                "educational_tone": "informational",
                "learning_difficulty": "moderate",
                "engagement_level": "neutral"
            }

    def _determine_educational_tone(self, sentiment: str, text: str) -> str:
        """Determine educational tone beyond basic sentiment"""
        text_lower = text.lower()
        
        # Check for instructional language
        instructional_words = ['learn', 'understand', 'study', 'remember', 'practice', 'apply']
        if any(word in text_lower for word in instructional_words):
            return "instructional"
        
        # Check for explanatory language
        explanatory_words = ['because', 'therefore', 'for example', 'such as', 'in other words']
        if any(phrase in text_lower for phrase in explanatory_words):
            return "explanatory"
        
        # Check for challenging content
        challenging_words = ['complex', 'difficult', 'advanced', 'sophisticated', 'intricate']
        if any(word in text_lower for word in challenging_words):
            return "challenging"
        
        # Default mapping
        tone_map = {
            "positive": "encouraging",
            "negative": "cautionary", 
            "neutral": "informational"
        }
        return tone_map.get(sentiment, "informational")

    def _assess_learning_difficulty(self, text: str) -> str:
        """Assess the learning difficulty of the content"""
        # Simple heuristics for difficulty assessment
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Technical vocabulary indicators
        technical_indicators = ['analysis', 'synthesis', 'methodology', 'implementation', 
                              'optimization', 'configuration', 'specification']
        technical_count = sum(1 for word in technical_indicators if word in text.lower())
        
        if avg_sentence_length > 25 or technical_count > 3:
            return "advanced"
        elif avg_sentence_length > 15 or technical_count > 1:
            return "intermediate"
        else:
            return "beginner"

    def _assess_engagement_level(self, sentiment: str, text: str) -> str:
        """Assess how engaging the content is for learning"""
        engagement_indicators = {
            'high': ['example', 'imagine', 'consider', 'think about', 'what if'],
            'medium': ['important', 'note that', 'remember', 'keep in mind'],
            'low': ['definition', 'formal', 'standard', 'conventional']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for level, indicators in engagement_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            scores[level] = score
        
        max_level = max(scores, key=scores.get)
        
        # Adjust based on sentiment
        if sentiment == "positive" and max_level != "high":
            max_level = "medium" if max_level == "low" else "high"
        
        return max_level

    def _assess_educational_quality(self, text: str, key_phrases: List[str], entities: Dict) -> Dict:
        """Enhanced quality assessment for educational content"""
        try:
            word_count = len(text.split())
            sentence_count = len(re.split(r'[.!?]+', text))
            
            # Basic metrics
            avg_sentence_length = word_count / max(sentence_count, 1)
            key_phrase_density = len(key_phrases) / max(word_count / 100, 1)
            
            # Educational quality indicators
            educational_score = 0.0
            
            # Content richness
            if word_count > 200:
                educational_score += 1.0
            elif word_count > 100:
                educational_score += 0.5
            
            # Key phrase quality
            if len(key_phrases) > 10:
                educational_score += 1.0
            elif len(key_phrases) > 5:
                educational_score += 0.7
            
            # Entity richness (indicates diverse content)
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            if total_entities > 5:
                educational_score += 0.8
            elif total_entities > 2:
                educational_score += 0.4
            
            # Sentence structure (good for learning)
            if 12 < avg_sentence_length < 25:
                educational_score += 0.7
            elif avg_sentence_length <= 12:
                educational_score += 0.4  # Too simple
            
            # Educational vocabulary
            educational_vocab = ['concept', 'theory', 'principle', 'method', 'analysis', 
                                'application', 'definition', 'example', 'process']
            vocab_count = sum(1 for word in educational_vocab if word in text.lower())
            educational_score += min(vocab_count * 0.2, 1.0)
            
            # Normalize score
            educational_score = min(educational_score / 5.0, 1.0)
            
            # Determine quality level
            if educational_score >= 0.8:
                quality_level = "excellent"
            elif educational_score >= 0.6:
                quality_level = "good"
            elif educational_score >= 0.4:
                quality_level = "fair"
            else:
                quality_level = "needs_improvement"
            
            return {
                "overall_quality": quality_level,
                "quality_score": round(educational_score, 2),
                "educational_score": round(educational_score, 2),
                "word_count": word_count,
                "sentence_count": sentence_count,
                "key_phrase_count": len(key_phrases),
                "entity_count": total_entities,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "readability": "good" if 12 < avg_sentence_length < 25 else "challenging",
                "educational_indicators": {
                    "has_examples": "example" in text.lower(),
                    "has_definitions": any(word in text.lower() for word in ['definition', 'defined as']),
                    "has_processes": any(word in text.lower() for word in ['process', 'method', 'procedure']),
                    "has_concepts": any(word in text.lower() for word in ['concept', 'theory', 'principle'])
                }
            }
            
        except Exception as e:
            logger.error(f"Educational quality assessment error: {e}")
            return {
                "overall_quality": "unknown",
                "quality_score": 0.5,
                "error": str(e)
            }

    def _assess_educational_complexity(self, text: str) -> Dict:
        """Enhanced complexity assessment for educational content"""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            word_count = len(words)
            sentence_count = len([s for s in sentences if s.strip()])
            
            # Advanced metrics
            avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            # Vocabulary complexity
            long_words = [word for word in words if len(word) > 6]
            long_word_ratio = len(long_words) / max(word_count, 1)
            
            # Technical term density
            technical_suffixes = ['tion', 'sion', 'ment', 'ness', 'ity', 'ism']
            technical_words = [word for word in words 
                             if any(word.lower().endswith(suffix) for suffix in technical_suffixes)]
            technical_ratio = len(technical_words) / max(word_count, 1)
            
            # Complexity scoring
            complexity_score = 0.0
            complexity_score += min(avg_sentence_length / 20, 1.0)  # Sentence length factor
            complexity_score += min(avg_word_length / 6, 1.0)      # Word length factor
            complexity_score += min(long_word_ratio * 2, 1.0)       # Long word factor
            complexity_score += min(technical_ratio * 3, 1.0)       # Technical term factor
            
            complexity_score = complexity_score / 4.0  # Normalize
            
            # Determine complexity level
            if complexity_score >= 0.7:
                complexity_level = "advanced"
            elif complexity_score >= 0.4:
                complexity_level = "intermediate"
            else:
                complexity_level = "basic"
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": round(avg_word_length, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "long_word_ratio": round(long_word_ratio, 3),
                "technical_word_ratio": round(technical_ratio, 3),
                "complexity_score": round(complexity_score, 2),
                "complexity_level": complexity_level,
                "readability_estimate": self._estimate_reading_level(avg_sentence_length, long_word_ratio)
            }
            
        except Exception as e:
            logger.error(f"Educational complexity assessment error: {e}")
            return {"error": str(e)}

    def _estimate_reading_level(self, avg_sentence_length: float, long_word_ratio: float) -> str:
        """Estimate reading level using simplified metrics"""
        # Simplified Flesch-Kincaid approximation
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * long_word_ratio)
        
        if score >= 90:
            return "elementary"
        elif score >= 80:
            return "middle_school"
        elif score >= 70:
            return "high_school"
        elif score >= 60:
            return "college"
        else:
            return "graduate"

    def _fallback_extractive_summary(self, text: str) -> str:
        """Improved fallback extractive summary"""
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
            
            if len(sentences) <= 3:
                return '. '.join(sentences) + '.'
            
            # Score sentences
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = 0
                
                # Position scoring (earlier sentences often more important)
                position_score = max(0, 2 - (i * 0.1))
                score += position_score
                
                # Length scoring (prefer medium length)
                word_count = len(sentence.split())
                if 15 <= word_count <= 25:
                    score += 1
                elif 10 <= word_count <= 30:
                    score += 0.5
                
                # Keyword scoring
                important_words = ['important', 'key', 'main', 'primary', 'essential', 'fundamental']
                for word in important_words:
                    if word in sentence.lower():
                        score += 1
                
                scored_sentences.append((sentence, score))
            
            # Select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent[0] for sent in scored_sentences[:3]]
            
            return '. '.join(top_sentences) + '.'
            
        except Exception as e:
            logger.error(f"Fallback extractive summary error: {e}")
            return text[:200] + "..." if len(text) > 200 else text

    def _generate_concept_summary(self, text: str) -> str:
        """Generate concept-based summary as fallback for abstractive"""
        try:
            # Extract sentences with key concepts
            concept_words = ['concept', 'theory', 'principle', 'method', 'process', 
                           'definition', 'important', 'key', 'main']
            
            sentences = re.split(r'[.!?]+', text)
            concept_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue
                    
                sentence_lower = sentence.lower()
                concept_count = sum(1 for word in concept_words if word in sentence_lower)
                
                if concept_count > 0:
                    concept_sentences.append((sentence, concept_count))
            
            # Sort by concept density and take top sentences
            concept_sentences.sort(key=lambda x: x[1], reverse=True)
            selected_sentences = [sent[0] for sent in concept_sentences[:3]]
            
            if selected_sentences:
                return '. '.join(selected_sentences) + '.'
            else:
                return self._fallback_extractive_summary(text)
                
        except Exception as e:
            logger.error(f"Concept summary generation error: {e}")
            return text[:200] + "..." if len(text) > 200 else text

    def _create_fallback_analysis(self, text: str) -> Dict:
        """Enhanced fallback analysis when Azure is unavailable"""
        try:
            cleaned_text = self._enhanced_text_clean(text)
            
            # Simple key phrase extraction (improved)
            words = cleaned_text.split()
            word_freq = {}
            
            # Better stopword filtering
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 
                'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
                'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'
            }
            
            for word in words:
                word_clean = re.sub(r'[^\w]', '', word.lower())
                if len(word_clean) > 3 and word_clean not in stopwords:
                    word_freq[word_clean] = word_freq.get(word_clean, 0) + 1
            
            # Get top words as key phrases, prefer longer words
            key_phrases = sorted(word_freq.items(), 
                               key=lambda x: x[1] * len(x[0]), reverse=True)[:15]
            key_phrases = [phrase[0] for phrase in key_phrases]
            
            return {
                "status": "fallback_success",
                "cleaned_text": cleaned_text,
                "summary": {
                    "extractive": self._fallback_extractive_summary(cleaned_text),
                    "educational": self._generate_concept_summary(cleaned_text),
                    "best": self._fallback_extractive_summary(cleaned_text)
                },
                "key_phrases": {
                    "azure_key_phrases": key_phrases,
                    "educational_concepts": {"general": key_phrases}
                },
                "sentiment": {
                    "sentiment": "neutral", 
                    "confidence": 0.5,
                    "educational_tone": "informational"
                },
                "entities": {"people": [], "locations": [], "organizations": [], "concepts": []},
                "study_assessment": {
                    "overall_quality": "fair",
                    "quality_score": 0.6,
                    "educational_score": 0.6
                },
                "text_complexity": self._assess_educational_complexity(cleaned_text),
                "processing_metadata": {
                    "fallback_used": True,
                    "azure_available": False,
                    "processing_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Enhanced fallback analysis failed: {str(e)}"
            }

# Create global instance
azure_language_processor = AzureLanguageProcessor()