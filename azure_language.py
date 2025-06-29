import streamlit as st
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
import logging
import json
import re
import random
from typing import Dict, List, Optional, Tuple
from config import config
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureLanguageProcessor:
    """Azure Text Analytics (Language Service) processor for comprehensive text analysis"""
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure Text Analytics client with proper configuration for East US"""
        try:
            if config.has_language_service():
                self.client = TextAnalyticsClient(
                    endpoint=config.language_endpoint,
                    credential=AzureKeyCredential(config.language_key)
                )
                self.is_available = True
                logger.info("✅ Azure Text Analytics (Language Service) initialized successfully")
            else:
                logger.warning("❌ Azure Language Service credentials not configured")
                self.is_available = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Language Service: {e}")
            self.is_available = False
    
    def comprehensive_text_analysis(self, text: str, progress_callback=None) -> Dict:
        """
        Perform comprehensive text analysis including summary, key phrases, sentiment, and entities
        """
        if not self.is_available:
            return self._create_fallback_analysis_result("Azure Language Service not available")
        
        if not text or len(text.strip()) < 10:
            return self._create_fallback_analysis_result("Insufficient text for analysis")
        
        results = {
            "summary": {},
            "key_phrases": {},
            "sentiment": {},
            "entities": {},
            "qa_pairs": [],
            "flashcards": [],
            "language_detection": {},
            "metadata": {}
        }
        
        try:
            if progress_callback:
                progress_callback("🧠 Starting comprehensive language analysis...")
            
            # Split text into manageable chunks for Azure API limits
            text_chunks = self._split_text_for_processing(text)
            
            # 1. Language Detection
            if progress_callback:
                progress_callback("🌍 Detecting language...")
            results["language_detection"] = self._detect_language(text_chunks[0])
            
            # 2. Key Phrase Extraction
            if progress_callback:
                progress_callback("🔑 Extracting key phrases...")
            results["key_phrases"] = self._extract_key_phrases(text_chunks)
            
            # 3. Sentiment Analysis
            if progress_callback:
                progress_callback("😊 Analyzing sentiment...")
            results["sentiment"] = self._analyze_sentiment(text_chunks)
            
            # 4. Named Entity Recognition
            if progress_callback:
                progress_callback("🏷️ Recognizing entities...")
            results["entities"] = self._recognize_entities(text_chunks)
            
            # 5. Text Summarization
            if progress_callback:
                progress_callback("📝 Generating summary...")
            results["summary"] = self._generate_summary(text, text_chunks)
            
            # 6. Generate Study Materials
            if progress_callback:
                progress_callback("🎴 Creating study materials...")
            results["qa_pairs"] = self._generate_qa_pairs(text, results["key_phrases"])
            results["flashcards"] = self._generate_flashcards(text, results["key_phrases"], results["entities"])
            
            # 7. Compile metadata
            results["metadata"] = self._compile_analysis_metadata(results, text)
            
            if progress_callback:
                progress_callback("✅ Language analysis complete!")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive text analysis failed: {e}")
            return self._create_fallback_analysis_result(f"Analysis failed: {str(e)}")
    
    def _split_text_for_processing(self, text: str, max_chunk_size: int = 5000) -> List[str]:
        """Split text into chunks that fit Azure API limits"""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_chunk_size]]
    
    def _detect_language(self, text: str) -> Dict:
        """Detect the language of the input text"""
        try:
            response = self.client.detect_language(documents=[text])
            
            for doc in response:
                if not doc.is_error:
                    primary_language = doc.primary_language
                    return {
                        "language": primary_language.name,
                        "iso6391_name": primary_language.iso6391_name,
                        "confidence_score": primary_language.confidence_score,
                        "status": "success"
                    }
                else:
                    logger.error(f"Language detection error: {doc.error}")
            
            return {"status": "failed", "error": "Language detection failed"}
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _extract_key_phrases(self, text_chunks: List[str]) -> Dict:
        """Extract key phrases from text chunks"""
        try:
            all_phrases = []
            phrase_frequencies = {}
            
            for chunk in text_chunks:
                response = self.client.extract_key_phrases(documents=[chunk])
                
                for doc in response:
                    if not doc.is_error:
                        for phrase in doc.key_phrases:
                            phrase_lower = phrase.lower()
                            if phrase_lower not in phrase_frequencies:
                                phrase_frequencies[phrase_lower] = {
                                    "phrase": phrase,
                                    "count": 1,
                                    "importance": self._calculate_phrase_importance(phrase)
                                }
                            else:
                                phrase_frequencies[phrase_lower]["count"] += 1
                    else:
                        logger.error(f"Key phrase extraction error: {doc.error}")
            
            # Sort phrases by importance and frequency
            sorted_phrases = sorted(
                phrase_frequencies.values(),
                key=lambda x: (x["importance"], x["count"]),
                reverse=True
            )
            
            return {
                "phrases": [p["phrase"] for p in sorted_phrases],
                "phrase_data": sorted_phrases,
                "total_phrases": len(sorted_phrases),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in key phrase extraction: {e}")
            return {"status": "failed", "error": str(e), "phrases": []}
    
    def _calculate_phrase_importance(self, phrase: str) -> float:
        """Calculate importance score for a phrase"""
        base_score = 0.5
        
        # Length-based scoring
        if 10 <= len(phrase) <= 50:
            base_score += 0.2
        
        # Check for important indicators
        important_words = ['important', 'key', 'main', 'primary', 'essential', 'critical', 'significant']
        if any(word in phrase.lower() for word in important_words):
            base_score += 0.3
        
        # Check for capitalization (proper nouns)
        if phrase[0].isupper() and not phrase.isupper():
            base_score += 0.1
        
        # Check for technical terms (contains numbers or special chars)
        if re.search(r'[0-9%$]', phrase):
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _analyze_sentiment(self, text_chunks: List[str]) -> Dict:
        """Analyze sentiment across text chunks"""
        try:
            sentiments = []
            sentence_sentiments = []
            
            for chunk in text_chunks:
                response = self.client.analyze_sentiment(
                    documents=[chunk],
                    show_opinion_mining=True
                )
                
                for doc in response:
                    if not doc.is_error:
                        sentiments.append({
                            "sentiment": doc.sentiment,
                            "confidence": max(
                                doc.confidence_scores.positive,
                                doc.confidence_scores.neutral,
                                doc.confidence_scores.negative
                            ),
                            "scores": {
                                "positive": doc.confidence_scores.positive,
                                "neutral": doc.confidence_scores.neutral,
                                "negative": doc.confidence_scores.negative
                            }
                        })
                        
                        # Collect sentence-level sentiments
                        for sentence in doc.sentences:
                            sentence_sentiments.append({
                                "text": sentence.text,
                                "sentiment": sentence.sentiment,
                                "confidence": max(
                                    sentence.confidence_scores.positive,
                                    sentence.confidence_scores.neutral,
                                    sentence.confidence_scores.negative
                                )
                            })
                    else:
                        logger.error(f"Sentiment analysis error: {doc.error}")
            
            if not sentiments:
                return {"status": "failed", "error": "No sentiment data extracted"}
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(sentiments)
            
            return {
                "overall_sentiment": overall_sentiment["sentiment"],
                "confidence": overall_sentiment["confidence"],
                "detailed_scores": overall_sentiment["scores"],
                "sentence_sentiments": sentence_sentiments,
                "chunk_sentiments": sentiments,
                "method": "Azure Text Analytics",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _calculate_overall_sentiment(self, sentiments: List[Dict]) -> Dict:
        """Calculate overall sentiment from multiple chunks"""
        if not sentiments:
            return {"sentiment": "neutral", "confidence": 0.0, "scores": {}}
        
        total_positive = sum(s["scores"]["positive"] for s in sentiments)
        total_neutral = sum(s["scores"]["neutral"] for s in sentiments)
        total_negative = sum(s["scores"]["negative"] for s in sentiments)
        
        count = len(sentiments)
        avg_positive = total_positive / count
        avg_neutral = total_neutral / count
        avg_negative = total_negative / count
        
        # Determine overall sentiment
        max_score = max(avg_positive, avg_neutral, avg_negative)
        
        if max_score == avg_positive:
            overall_sentiment = "positive"
        elif max_score == avg_negative:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        return {
            "sentiment": overall_sentiment,
            "confidence": max_score,
            "scores": {
                "positive": avg_positive,
                "neutral": avg_neutral,
                "negative": avg_negative
            }
        }
    
    def _recognize_entities(self, text_chunks: List[str]) -> Dict:
        """Recognize named entities in text chunks"""
        try:
            all_entities = []
            entity_categories = {}
            
            for chunk in text_chunks:
                response = self.client.recognize_entities(documents=[chunk])
                
                for doc in response:
                    if not doc.is_error:
                        for entity in doc.entities:
                            entity_data = {
                                "text": entity.text,
                                "category": entity.category,
                                "subcategory": entity.subcategory,
                                "confidence_score": entity.confidence_score,
                                "offset": entity.offset,
                                "length": entity.length
                            }
                            
                            all_entities.append(entity_data)
                            
                            # Group by category
                            category = entity.category
                            if category not in entity_categories:
                                entity_categories[category] = []
                            entity_categories[category].append(entity_data)
                    else:
                        logger.error(f"Entity recognition error: {doc.error}")
            
            # Remove duplicates and sort by confidence
            unique_entities = self._deduplicate_entities(all_entities)
            
            return {
                "entities": unique_entities,
                "by_category": entity_categories,
                "total_entities": len(unique_entities),
                "categories_found": list(entity_categories.keys()),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in entity recognition: {e}")
            return {"status": "failed", "error": str(e), "entities": []}
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities and keep highest confidence"""
        entity_map = {}
        
        for entity in entities:
            key = (entity["text"].lower(), entity["category"])
            if key not in entity_map or entity["confidence_score"] > entity_map[key]["confidence_score"]:
                entity_map[key] = entity
        
        return sorted(entity_map.values(), key=lambda x: x["confidence_score"], reverse=True)
    
    def _generate_summary(self, full_text: str, text_chunks: List[str]) -> Dict:
        """Generate intelligent summary using multiple methods"""
        try:
            # Method 1: Azure Extractive Summarization (if available)
            azure_summary = self._try_azure_summarization(text_chunks)
            
            # Method 2: Rule-based summarization
            rule_based_summary = self._rule_based_summarization(full_text)
            
            # Method 3: Key sentences extraction
            key_sentences_summary = self._extract_key_sentences(full_text)
            
            # Choose best summary
            best_summary = self._select_best_summary(azure_summary, rule_based_summary, key_sentences_summary)
            
            return best_summary
            
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _try_azure_summarization(self, text_chunks: List[str]) -> Dict:
        """Try Azure's extractive summarization"""
        try:
            # Note: Azure extractive summarization might not be available in all regions
            # This is a placeholder for when the feature becomes available
            # For now, we'll use a simplified approach
            
            return {
                "text": "Azure summarization not available in current configuration",
                "method": "azure_extractive",
                "confidence": 0.0,
                "status": "unavailable"
            }
            
        except Exception as e:
            logger.warning(f"Azure summarization not available: {e}")
            return {"status": "failed", "method": "azure_extractive"}
    
    def _rule_based_summarization(self, text: str, max_sentences: int = 3) -> Dict:
        """Rule-based summarization using sentence scoring"""
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if len(sentences) <= max_sentences:
                summary_text = ". ".join(sentences)
                return {
                    "text": summary_text,
                    "method": "rule_based",
                    "confidence": 0.8,
                    "status": "success"
                }
            
            # Score sentences
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = self._score_sentence_for_summary(sentence, i, len(sentences))
                scored_sentences.append((sentence, score))
            
            # Select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
            
            summary_text = ". ".join(top_sentences)
            
            return {
                "text": summary_text,
                "method": "rule_based",
                "confidence": 0.7,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based summarization: {e}")
            return {"status": "failed", "method": "rule_based"}
    
    def _score_sentence_for_summary(self, sentence: str, position: int, total_sentences: int) -> float:
        """Score a sentence for summary inclusion"""
        score = 0.0
        
        # Position scoring (first and last sentences often important)
        if position == 0:
            score += 0.3
        elif position == total_sentences - 1:
            score += 0.2
        elif position < total_sentences * 0.3:
            score += 0.1
        
        # Length scoring
        word_count = len(sentence.split())
        if 15 <= word_count <= 30:
            score += 0.2
        elif 10 <= word_count <= 40:
            score += 0.1
        
        # Important words
        important_words = ['important', 'significant', 'key', 'main', 'primary', 'essential', 'conclusion', 'result']
        for word in important_words:
            if word in sentence.lower():
                score += 0.15
        
        # Numbers and data
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # Proper nouns (capitalized words)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+', sentence)
        score += min(len(capitalized_words) * 0.05, 0.2)
        
        return score
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> Dict:
        """Extract key sentences based on keyword frequency"""
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if len(sentences) <= max_sentences:
                summary_text = ". ".join(sentences)
                return {
                    "text": summary_text,
                    "method": "key_sentences",
                    "confidence": 0.6,
                    "status": "success"
                }
            
            # Get word frequencies
            word_freq = self._calculate_word_frequencies(text)
            
            # Score sentences based on word frequencies
            sentence_scores = []
            for sentence in sentences:
                score = self._calculate_sentence_frequency_score(sentence, word_freq)
                sentence_scores.append((sentence, score))
            
            # Select top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
            
            summary_text = ". ".join(top_sentences)
            
            return {
                "text": summary_text,
                "method": "key_sentences",
                "confidence": 0.6,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in key sentence extraction: {e}")
            return {"status": "failed", "method": "key_sentences"}
    
    def _calculate_word_frequencies(self, text: str) -> Dict[str, int]:
        """Calculate word frequencies excluding common stop words"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        return word_freq
    
    def _calculate_sentence_frequency_score(self, sentence: str, word_freq: Dict[str, int]) -> float:
        """Calculate sentence score based on word frequencies"""
        words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
        if not words:
            return 0.0
        
        total_score = sum(word_freq.get(word, 0) for word in words)
        return total_score / len(words)
    
    def _select_best_summary(self, azure_summary: Dict, rule_based: Dict, key_sentences: Dict) -> Dict:
        """Select the best summary from available methods"""
        summaries = [azure_summary, rule_based, key_sentences]
        valid_summaries = [s for s in summaries if s.get("status") == "success"]
        
        if not valid_summaries:
            return {"status": "failed", "error": "All summarization methods failed"}
        
        # Select summary with highest confidence
        best_summary = max(valid_summaries, key=lambda x: x.get("confidence", 0))
        
        return best_summary
    
    def _generate_qa_pairs(self, text: str, key_phrases_data: Dict, max_pairs: int = 5) -> List[Dict]:
        """Generate question-answer pairs from text and key phrases"""
        try:
            qa_pairs = []
            key_phrases = key_phrases_data.get("phrases", [])[:10]  # Use top 10 key phrases
            
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            for phrase in key_phrases:
                # Find sentences containing the key phrase
                relevant_sentences = [s for s in sentences if phrase.lower() in s.lower()]
                
                if relevant_sentences:
                    # Generate different types of questions
                    question_types = [
                        f"What is {phrase}?",
                        f"Explain {phrase}.",
                        f"What do you know about {phrase}?",
                        f"Define {phrase}.",
                        f"Describe {phrase}."
                    ]
                    
                    question = random.choice(question_types)
                    answer = relevant_sentences[0]  # Use the first relevant sentence
                    
                    qa_pairs.append({
                        "question": question,
                        "answer": answer,
                        "key_phrase": phrase,
                        "confidence": 0.7,
                        "type": "definition"
                    })
                    
                    if len(qa_pairs) >= max_pairs:
                        break
            
            # Add some general questions
            if len(qa_pairs) < max_pairs and sentences:
                general_questions = [
                    ("What is the main topic of this text?", sentences[0]),
                    ("What are the key points mentioned?", ". ".join(sentences[:2])),
                    ("What is the conclusion?", sentences[-1] if sentences else "")
                ]
                
                for question, answer in general_questions:
                    if len(qa_pairs) < max_pairs and answer:
                        qa_pairs.append({
                            "question": question,
                            "answer": answer,
                            "key_phrase": "general",
                            "confidence": 0.6,
                            "type": "general"
                        })
            
            return qa_pairs
            
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            return []
    
    def _generate_flashcards(self, text: str, key_phrases_data: Dict, entities_data: Dict, max_cards: int = 8) -> List[Dict]:
        """Generate study flashcards from text analysis"""
        try:
            flashcards = []
            key_phrases = key_phrases_data.get("phrases", [])
            entities = entities_data.get("entities", [])
            
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
            
            # Generate flashcards from key phrases
            for phrase in key_phrases[:5]:
                relevant_sentences = [s for s in sentences if phrase.lower() in s.lower()]
                
                if relevant_sentences:
                    flashcards.append({
                        "question": f"What is the significance of '{phrase}'?",
                        "answer": relevant_sentences[0],
                        "type": "key_concept",
                        "difficulty": "medium",
                        "confidence": 0.8,
                        "source": "key_phrases"
                    })
            
            # Generate flashcards from entities
            person_entities = [e for e in entities if e.get("category") == "Person"][:3]
            for entity in person_entities:
                relevant_sentences = [s for s in sentences if entity["text"] in s]
                
                if relevant_sentences:
                    flashcards.append({
                        "question": f"Who is {entity['text']}?",
                        "answer": relevant_sentences[0],
                        "type": "person",
                        "difficulty": "easy",
                        "confidence": entity.get("confidence_score", 0.7),
                        "source": "entities"
                    })
            
            # Generate definition flashcards
            definition_indicators = ['is defined as', 'refers to', 'means', 'is a', 'are']
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in definition_indicators):
                    # Try to extract the term being defined
                    parts = sentence.split()
                    if len(parts) > 3:
                        potential_term = " ".join(parts[:3])
                        flashcards.append({
                            "question": f"Define: {potential_term}",
                            "answer": sentence,
                            "type": "definition",
                            "difficulty": "medium",
                            "confidence": 0.6,
                            "source": "definitions"
                        })
                
                if len(flashcards) >= max_cards:
                    break
            
            # Add some general comprehension questions
            if len(flashcards) < max_cards and sentences:
                general_cards = [
                    {
                        "question": "What is the main idea of this content?",
                        "answer": sentences[0],
                        "type": "comprehension",
                        "difficulty": "medium",
                        "confidence": 0.7,
                        "source": "general"
                    },
                    {
                        "question": "What are the important details mentioned?",
                        "answer": ". ".join(sentences[1:3]) if len(sentences) > 2 else sentences[0],
                        "type": "detail",
                        "difficulty": "hard",
                        "confidence": 0.6,
                        "source": "general"
                    }
                ]
                
                for card in general_cards:
                    if len(flashcards) < max_cards:
                        flashcards.append(card)
            
            return flashcards[:max_cards]
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            return []
    
    def _compile_analysis_metadata(self, results: Dict, original_text: str) -> Dict:
        """Compile comprehensive metadata about the analysis"""
        try:
            return {
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "text_statistics": {
                    "character_count": len(original_text),
                    "word_count": len(original_text.split()),
                    "sentence_count": len(re.split(r'[.!?]+', original_text)),
                    "paragraph_count": len([p for p in original_text.split('\n\n') if p.strip()])
                },
                "analysis_results": {
                    "language_detected": results.get("language_detection", {}).get("status") == "success",
                    "key_phrases_extracted": len(results.get("key_phrases", {}).get("phrases", [])),
                    "entities_found": len(results.get("entities", {}).get("entities", [])),
                    "sentiment_analyzed": results.get("sentiment", {}).get("status") == "success",
                    "summary_generated": results.get("summary", {}).get("status") == "success",
                    "qa_pairs_created": len(results.get("qa_pairs", [])),
                    "flashcards_created": len(results.get("flashcards", []))
                },
                "quality_indicators": {
                    "text_length_adequate": len(original_text) > 100,
                    "has_structure": len(re.split(r'[.!?]+', original_text)) > 3,
                    "entity_richness": len(results.get("entities", {}).get("entities", [])) > 2,
                    "concept_density": len(results.get("key_phrases", {}).get("phrases", [])) > 3
                },
                "processing_info": {
                    "azure_language_service": "Azure Text Analytics",
                    "api_region": "East US",
                    "analysis_methods_used": [
                        "language_detection",
                        "key_phrase_extraction", 
                        "sentiment_analysis",
                        "entity_recognition",
                        "summarization",
                        "qa_generation",
                        "flashcard_creation"
                ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error compiling metadata: {e}")
            return {"error": str(e)}
    
    def _create_fallback_analysis_result(self, error_message: str) -> Dict:
        """Create fallback result when analysis fails"""
        return {
            "summary": {"status": "failed", "error": error_message},
            "key_phrases": {"status": "failed", "error": error_message, "phrases": []},
            "sentiment": {"status": "failed", "error": error_message},
            "entities": {"status": "failed", "error": error_message, "entities": []},
            "qa_pairs": [],
            "flashcards": [],
            "language_detection": {"status": "failed", "error": error_message},
            "metadata": {
                "analysis_failed": True,
                "error": error_message,
                "fallback_used": True
            }
        }

# Create global instance
azure_language_processor = AzureLanguageProcessor()