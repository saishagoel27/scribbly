from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
import logging
import json
import re
import random
import datetime
from typing import Dict, List, Optional
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTextProcessor:
    """Enhanced text processing for better OCR output handling"""
    
    @staticmethod
    def clean_ocr_text(text: str) -> str:
        """Clean and normalize OCR text output"""
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        ocr_fixes = {
            r'\b0\b': 'o',  # Zero to letter O
            r'\b1\b(?=[a-zA-Z])': 'l',  # Number 1 to letter l
            r'\b5\b(?=[a-zA-Z])': 'S',  # Number 5 to letter S
            r'rn\b': 'm',  # rn to m
            r'\bvv\b': 'w',  # vv to w
            r'([.!?])\s*([a-z])': r'\1 \2',  # Fix sentence spacing
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove standalone punctuation and artifacts
        text = re.sub(r'\b[^\w\s]{1,3}\b', ' ', text)
        
        # Fix sentence boundaries
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        # Remove very short "words" that are likely artifacts
        words = text.split()
        cleaned_words = []
        for word in words:
            # Keep words that are longer than 1 char or are meaningful single chars
            if len(word) > 1 or word.lower() in ['a', 'i', 'o']:
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words).strip()
    
    @staticmethod
    def extract_sentences(text: str, min_length: int = 15) -> List[str]:
        """Extract meaningful sentences from text"""
        # Split by sentence endings
        sentences = re.split(r'[.!?]+', text)
        
        meaningful_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Filter out short fragments and artifacts
            if len(sentence) >= min_length:
                # Check if it has proper word structure
                words = sentence.split()
                if len(words) >= 3:  # At least 3 words
                    # Check if it's not just numbers or single chars
                    word_lengths = [len(w) for w in words if w.isalpha()]
                    if word_lengths and sum(word_lengths) / len(word_lengths) > 2:
                        meaningful_sentences.append(sentence)
        
        return meaningful_sentences
    
    @staticmethod
    def identify_key_concepts(text: str) -> List[Dict]:
        """Identify key concepts using NLP techniques"""
        sentences = EnhancedTextProcessor.extract_sentences(text)
        concepts = []
        
        # Look for definition patterns
        definition_patterns = [
            r'(.+?)\s+(?:is|are|means?|refers? to|defined as)\s+(.+)',
            r'(.+?):\s*(.+)',  # Colon definitions
            r'(.+?)\s*-\s*(.+)',  # Dash definitions
        ]
        
        for sentence in sentences:
            for pattern in definition_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    term = match[0].strip()
                    definition = match[1].strip()
                    
                    # Validate the concept
                    if (3 <= len(term) <= 50 and 
                        10 <= len(definition) <= 200 and
                        len(term.split()) <= 5):
                        
                        concepts.append({
                            "term": term,
                            "definition": definition,
                            "sentence": sentence,
                            "type": "definition",
                            "confidence": 0.8
                        })
        
        return concepts
    
    @staticmethod
    def score_sentence_importance(sentence: str, all_sentences: List[str]) -> float:
        """Score sentence importance using multiple factors"""
        score = 0.0
        
        # Length scoring (prefer medium-length sentences)
        word_count = len(sentence.split())
        if 10 <= word_count <= 25:
            score += 0.3
        elif 6 <= word_count <= 35:
            score += 0.2
        
        # Keyword importance
        important_keywords = [
            'important', 'key', 'main', 'primary', 'essential', 'critical',
            'summary', 'conclusion', 'result', 'finding', 'therefore',
            'however', 'moreover', 'furthermore', 'in addition'
        ]
        
        sentence_lower = sentence.lower()
        for keyword in important_keywords:
            if keyword in sentence_lower:
                score += 0.2
                break
        
        # Position scoring (first and last sentences often important)
        try:
            position = all_sentences.index(sentence)
            total_sentences = len(all_sentences)
            
            if position == 0:  # First sentence
                score += 0.2
            elif position == total_sentences - 1:  # Last sentence
                score += 0.15
            elif position < total_sentences * 0.3:  # Early sentences
                score += 0.1
        except ValueError:
            pass
        
        # Capitalization (proper nouns indicate importance)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+', sentence)
        score += min(len(capitalized_words) * 0.05, 0.2)
        
        # Numbers and data
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # Question or exclamation
        if sentence.endswith('?') or sentence.endswith('!'):
            score += 0.1
        
        return min(score, 1.0)

class AzureLanguageProcessor:
    """Streamlined Azure Text Analytics processor focused on summary and flashcards"""
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self.text_processor = EnhancedTextProcessor()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure Text Analytics client"""
        try:
            if config.has_language_service():
                self.client = TextAnalyticsClient(
                    endpoint=config.language_endpoint,
                    credential=AzureKeyCredential(config.language_key)
                )
                self.is_available = True
                logger.info("✅ Azure Text Analytics initialized successfully")
            else:
                logger.warning("❌ Azure Language Service credentials not configured")
                self.is_available = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Language Service: {e}")
            self.is_available = False
    
    def analyze_for_study_materials(self, text: str, progress_callback=None) -> Dict:
        """
        Focused analysis for generating study materials (summary + flashcards)
        """
        if not self.is_available:
            return self._create_fallback_result("Azure Language Service not available")
        
        if not text or len(text.strip()) < 10:
            return self._create_fallback_result("Insufficient text for analysis")
        
        # Step 1: Clean and process the OCR text
        if progress_callback:
            progress_callback("🧹 Cleaning extracted text...")
        
        cleaned_text = self.text_processor.clean_ocr_text(text)
        
        if len(cleaned_text.strip()) < 20:
            return self._create_fallback_result("Text too short after cleaning")
        
        results = {
            "summary": {},
            "key_phrases": {},
            "flashcards": [],
            "processed_text": cleaned_text,
            "metadata": {}
        }
        
        try:
            if progress_callback:
                progress_callback("🔑 Extracting key concepts...")
            
            # Split text for Azure API limits
            text_chunks = self._split_text_for_processing(cleaned_text)
            
            # 1. Key Phrase Extraction (focused)
            results["key_phrases"] = self._extract_key_phrases_focused(text_chunks, cleaned_text)
            
            # 2. Enhanced Summary Generation (primary focus)
            if progress_callback:
                progress_callback("📝 Generating intelligent summary...")
            results["summary"] = self._generate_enhanced_summary(cleaned_text, text_chunks)
            
            # 3. Generate Study Flashcards (secondary focus)
            if progress_callback:
                progress_callback("🎴 Creating study flashcards...")
            
            key_concepts = self.text_processor.identify_key_concepts(cleaned_text)
            results["flashcards"] = self._generate_study_flashcards(
                cleaned_text, results["key_phrases"], key_concepts
            )
            
            # 4. Compile metadata
            results["metadata"] = self._compile_metadata(results, cleaned_text, text)
            
            if progress_callback:
                progress_callback("✅ Study materials ready!")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Study materials generation failed: {e}")
            return self._create_fallback_result(f"Analysis failed: {str(e)}")
    
    def _extract_key_phrases_focused(self, text_chunks: List[str], full_text: str) -> Dict:
        """Focused key phrase extraction for study materials"""
        try:
            phrase_frequencies = {}
            
            # Get Azure key phrases
            for chunk in text_chunks:
                response = self.client.extract_key_phrases(documents=[chunk])
                
                for doc in response:
                    if not doc.is_error:
                        for phrase in doc.key_phrases:
                            if self._is_study_relevant_phrase(phrase):
                                phrase_lower = phrase.lower()
                                if phrase_lower not in phrase_frequencies:
                                    phrase_frequencies[phrase_lower] = {
                                        "phrase": phrase,
                                        "count": 1,
                                        "importance": self._calculate_study_importance(phrase, full_text)
                                    }
                                else:
                                    phrase_frequencies[phrase_lower]["count"] += 1
                    else:
                        logger.error(f"Key phrase extraction error: {doc.error}")
            
            # Add manually detected concepts (high priority for studies)
            key_concepts = self.text_processor.identify_key_concepts(full_text)
            for concept in key_concepts:
                term = concept["term"]
                if self._is_study_relevant_phrase(term):
                    term_lower = term.lower()
                    if term_lower not in phrase_frequencies:
                        phrase_frequencies[term_lower] = {
                            "phrase": term,
                            "count": 1,
                            "importance": 0.9  # High importance for study concepts
                        }
            
            # Sort by study relevance
            sorted_phrases = sorted(
                phrase_frequencies.values(),
                key=lambda x: (x["importance"], x["count"]),
                reverse=True
            )
            
            # Filter for study materials (top 15 most relevant)
            study_phrases = [p for p in sorted_phrases if p["importance"] > 0.4][:15]
            
            return {
                "phrases": [p["phrase"] for p in study_phrases],
                "phrase_data": study_phrases,
                "total_phrases": len(study_phrases),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in key phrase extraction: {e}")
            return {"status": "failed", "error": str(e), "phrases": []}
    
    def _is_study_relevant_phrase(self, phrase: str) -> bool:
        """Check if phrase is relevant for study materials"""
        if not phrase or len(phrase.strip()) < 3:
            return False
        
        # Remove phrases that are just numbers or punctuation
        if re.match(r'^[0-9\s\-_.,;:!?]+$', phrase):
            return False
        
        # Remove single character "words" and artifacts
        words = phrase.split()
        meaningful_words = [w for w in words if len(w) > 1 or w.lower() in ['a', 'i', 'o']]
        
        if len(meaningful_words) < len(words) * 0.7:
            return False
        
        # Prefer academic/study-relevant terms
        study_indicators = ['concept', 'theory', 'principle', 'method', 'process', 'definition']
        if any(indicator in phrase.lower() for indicator in study_indicators):
            return True
        
        # Check for reasonable length for study materials
        if 3 <= len(phrase) <= 40 and 1 <= len(words) <= 4:
            return True
        
        return False
    
    def _calculate_study_importance(self, phrase: str, full_text: str) -> float:
        """Calculate importance specifically for study materials"""
        base_score = 0.5
        
        # Length-based scoring for study materials
        if 5 <= len(phrase) <= 25:
            base_score += 0.3
        elif 3 <= len(phrase) <= 35:
            base_score += 0.2
        
        # Word count scoring
        word_count = len(phrase.split())
        if 2 <= word_count <= 3:  # Optimal for study terms
            base_score += 0.3
        elif word_count == 1:
            base_score += 0.2
        
        # Study-relevant keywords
        study_keywords = ['important', 'key', 'main', 'definition', 'concept', 'theory', 'principle']
        if any(word in phrase.lower() for word in study_keywords):
            base_score += 0.4
        
        # Capitalization (proper nouns/important terms)
        if phrase[0].isupper() and not phrase.isupper():
            base_score += 0.2
        
        # Frequency in text (important for study materials)
        frequency = full_text.lower().count(phrase.lower())
        if frequency > 1:
            base_score += min(frequency * 0.1, 0.3)
        
        return min(base_score, 1.0)
    
    def _generate_enhanced_summary(self, cleaned_text: str, text_chunks: List[str]) -> Dict:
        """Generate focused summary for study purposes"""
        try:
            # Try multiple summarization methods and pick the best
            summaries = []
            
            # Method 1: Concept-based summary (best for study materials)
            concept_summary = self._concept_based_summarization(cleaned_text)
            if concept_summary.get("status") == "success":
                summaries.append(concept_summary)
            
            # Method 2: Enhanced rule-based summary
            rule_summary = self._enhanced_rule_based_summarization(cleaned_text, max_sentences=3)
            if rule_summary.get("status") == "success":
                summaries.append(rule_summary)
            
            # Method 3: Key sentences extraction
            key_summary = self._extract_key_sentences_enhanced(cleaned_text, max_sentences=3)
            if key_summary.get("status") == "success":
                summaries.append(key_summary)
            
            # Select the best summary for study purposes
            if summaries:
                best_summary = self._select_best_study_summary(summaries)
                return best_summary
            else:
                return {"status": "failed", "error": "All summarization methods failed"}
                
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _concept_based_summarization(self, text: str) -> Dict:
        """Create summary based on identified concepts (best for study materials)"""
        try:
            key_concepts = self.text_processor.identify_key_concepts(text)
            
            if not key_concepts:
                return {"status": "failed", "method": "concept_based", "error": "No concepts found"}
            
            # Create summary from top concepts
            concept_sentences = []
            for concept in key_concepts[:3]:  # Top 3 concepts
                sentence = concept["sentence"]
                if sentence not in concept_sentences:
                    concept_sentences.append(sentence)
            
            if concept_sentences:
                summary_text = ". ".join(concept_sentences)
                return {
                    "text": summary_text,
                    "method": "concept_based",
                    "confidence": 0.95,  # High confidence for concept-based
                    "status": "success",
                    "concepts_used": len(concept_sentences)
                }
            else:
                return {"status": "failed", "method": "concept_based", "error": "No suitable concept sentences"}
                
        except Exception as e:
            logger.error(f"Error in concept-based summarization: {e}")
            return {"status": "failed", "method": "concept_based"}
    
    def _enhanced_rule_based_summarization(self, text: str, max_sentences: int = 3) -> Dict:
        """Enhanced rule-based summarization optimized for study materials"""
        try:
            sentences = self.text_processor.extract_sentences(text, min_length=20)
            
            if len(sentences) <= max_sentences:
                summary_text = ". ".join(sentences)
                return {
                    "text": summary_text,
                    "method": "enhanced_rule_based",
                    "confidence": 0.8,
                    "status": "success"
                }
            
            # Score sentences with study-focused criteria
            scored_sentences = []
            for sentence in sentences:
                score = self._calculate_study_sentence_score(sentence, sentences)
                scored_sentences.append((sentence, score))
            
            # Select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
            
            # Maintain logical order
            ordered_sentences = []
            for sentence in sentences:
                if sentence in top_sentences:
                    ordered_sentences.append(sentence)
            
            summary_text = ". ".join(ordered_sentences)
            
            return {
                "text": summary_text,
                "method": "enhanced_rule_based",
                "confidence": 0.85,
                "status": "success",
                "selected_sentences": len(top_sentences),
                "total_sentences": len(sentences)
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced rule-based summarization: {e}")
            return {"status": "failed", "method": "enhanced_rule_based"}
    
    def _calculate_study_sentence_score(self, sentence: str, all_sentences: List[str]) -> float:
        """Calculate sentence score optimized for study materials"""
        score = self.text_processor.score_sentence_importance(sentence, all_sentences)
        
        # Boost for study-relevant content
        study_keywords = [
            'definition', 'define', 'concept', 'theory', 'principle', 'method',
            'process', 'formula', 'equation', 'rule', 'law', 'property'
        ]
        
        sentence_lower = sentence.lower()
        for keyword in study_keywords:
            if keyword in sentence_lower:
                score += 0.3
                break
        
        # Boost for explanatory sentences
        if any(word in sentence_lower for word in ['because', 'since', 'therefore', 'thus', 'hence']):
            score += 0.2
        
        # Boost for sentences with examples
        if any(word in sentence_lower for word in ['example', 'instance', 'such as', 'like']):
            score += 0.15
        
        return min(score, 1.0)
    
    def _extract_key_sentences_enhanced(self, text: str, max_sentences: int = 3) -> Dict:
        """Extract key sentences optimized for study materials"""
        try:
            sentences = self.text_processor.extract_sentences(text, min_length=15)
            
            if len(sentences) <= max_sentences:
                summary_text = ". ".join(sentences)
                return {
                    "text": summary_text,
                    "method": "enhanced_key_sentences",
                    "confidence": 0.7,
                    "status": "success"
                }
            
            # Calculate word frequencies for study-relevant terms
            word_freq = self._calculate_study_word_frequencies(text)
            
            # Score sentences
            sentence_scores = []
            for sentence in sentences:
                freq_score = self._calculate_sentence_frequency_score(sentence, word_freq)
                study_score = self._calculate_study_sentence_score(sentence, sentences)
                
                # Weighted combination (favor study relevance)
                combined_score = (freq_score * 0.4) + (study_score * 0.6)
                sentence_scores.append((sentence, combined_score))
            
            # Select top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
            
            # Maintain original order
            ordered_sentences = []
            for sentence in sentences:
                if sentence in top_sentences:
                    ordered_sentences.append(sentence)
            
            summary_text = ". ".join(ordered_sentences)
            
            return {
                "text": summary_text,
                "method": "enhanced_key_sentences",
                "confidence": 0.75,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced key sentence extraction: {e}")
            return {"status": "failed", "method": "enhanced_key_sentences"}
    
    def _calculate_study_word_frequencies(self, text: str) -> Dict[str, int]:
        """Calculate word frequencies focused on study-relevant terms"""
        # Study-focused stop words (remove common but non-study words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those', 'there', 'here',
            'then', 'than', 'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose',
            'if', 'unless', 'until', 'while', 'during', 'before', 'after', 'above', 'below',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'once'
        }
        
        # Extract and filter words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        word_freq = {}
        
        for word in words:
            if (word not in stop_words and 
                len(word) > 2 and 
                not word.isdigit() and
                len(word) <= 20):
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Boost study-relevant terms
        study_terms = [
            'concept', 'theory', 'principle', 'method', 'process', 'definition', 
            'formula', 'equation', 'rule', 'law', 'property', 'function'
        ]
        
        for term in study_terms:
            if term in word_freq:
                word_freq[term] *= 2  # Double the weight
        
        # Filter out single occurrences (likely OCR errors)
        filtered_freq = {k: v for k, v in word_freq.items() if v > 1 or len(k) > 4}
        
        return filtered_freq
    
    def _select_best_study_summary(self, summaries: List[Dict]) -> Dict:
        """Select the best summary optimized for study purposes"""
        best_summary = None
        best_score = 0
        
        for summary in summaries:
            score = summary.get("confidence", 0)
            
            # Strong preference for concept-based summaries
            if summary.get("method") == "concept_based":
                score += 0.2
            
            # Bonus for enhanced methods
            if "enhanced" in summary.get("method", ""):
                score += 0.1
            
            # Check text quality for study purposes
            text = summary.get("text", "")
            
            # Penalty for very short summaries (not useful for study)
            if len(text) < 30:
                score -= 0.3
            elif len(text) < 60:
                score -= 0.1
            
            # Bonus for study-relevant keywords in summary
            study_keywords = ['definition', 'concept', 'theory', 'principle', 'method', 'process']
            if any(keyword in text.lower() for keyword in study_keywords):
                score += 0.15
            
            if score > best_score:
                best_score = score
                best_summary = summary
        
        return best_summary or summaries[0]
    
    def _generate_study_flashcards(self, text: str, key_phrases_data: Dict, 
                                 key_concepts: List[Dict], max_cards: int = 8) -> List[Dict]:
        """Generate focused flashcards for study purposes"""
        try:
            flashcards = []
            sentences = self.text_processor.extract_sentences(text, min_length=15)
            
            # 1. Generate flashcards from concepts (highest priority)
            for concept in key_concepts[:3]:
                term = concept["term"]
                definition = concept["definition"]
                
                # Definition flashcard
                flashcards.append({
                    "question": f"What is {term}?",
                    "answer": definition,
                    "type": "definition",
                    "difficulty": "medium",
                    "confidence": concept["confidence"],
                    "source": "concept_extraction"
                })
                
                # Reverse flashcard for shorter definitions
                if len(definition) <= 80:
                    flashcards.append({
                        "question": f"Which term is defined as: '{definition[:60]}...'?",
                        "answer": term,
                        "type": "reverse_definition",
                        "difficulty": "hard",
                        "confidence": concept["confidence"] * 0.9,
                        "source": "concept_extraction"
                    })
            
            # 2. Generate flashcards from key phrases (if we need more)
            if len(flashcards) < max_cards:
                phrases = key_phrases_data.get("phrases", [])[:5]
                
                for phrase in phrases:
                    if len(flashcards) >= max_cards:
                        break
                    
                    # Find best explanatory sentence
                    context_sentence = self._find_best_study_context(phrase, sentences)
                    
                    if context_sentence and self._is_good_study_content(context_sentence):
                        flashcards.append({
                            "question": f"Explain '{phrase}' based on your notes.",
                            "answer": context_sentence,
                            "type": "key_concept",
                            "difficulty": "medium",
                            "confidence": 0.75,
                            "source": "key_phrases"
                        })
            
            # 3. Generate comprehension flashcards (if still need more)
            if len(flashcards) < max_cards and len(sentences) >= 2:
                # Main topic flashcard
                if sentences[0] and self._is_good_study_content(sentences[0]):
                    flashcards.append({
                        "question": "What is the main topic of these notes?",
                        "answer": sentences[0],
                        "type": "comprehension",
                        "difficulty": "easy",
                        "confidence": 0.7,
                        "source": "comprehension"
                    })
                
                # Important detail flashcard
                if len(sentences) > 1:
                    important_sentence = self._find_most_important_sentence(sentences[1:])
                    if important_sentence:
                        flashcards.append({
                            "question": "What is an important detail to remember?",
                            "answer": important_sentence,
                            "type": "detail",
                            "difficulty": "medium",
                            "confidence": 0.65,
                            "source": "comprehension"
                        })
            
            # Remove duplicates and sort by confidence
            unique_flashcards = self._remove_duplicate_flashcards(flashcards)
            
            return unique_flashcards[:max_cards]
            
        except Exception as e:
            logger.error(f"Error generating study flashcards: {e}")
            return []
    
    def _find_best_study_context(self, phrase: str, sentences: List[str]) -> str:
        """Find the sentence that best explains a phrase for study purposes"""
        relevant_sentences = []
        
        for sentence in sentences:
            if phrase.lower() in sentence.lower():
                score = 0
                
                # Prefer explanatory sentences
                explanatory_words = ['is', 'are', 'means', 'refers', 'involves', 'includes', 'defines']
                for word in explanatory_words:
                    if word in sentence.lower():
                        score += 2
                
                # Prefer study-relevant sentences
                study_words = ['because', 'therefore', 'thus', 'since', 'example', 'instance']
                for word in study_words:
                    if word in sentence.lower():
                        score += 1
                
                # Optimal length for study
                word_count = len(sentence.split())
                if 8 <= word_count <= 25:
                    score += 2
                elif 5 <= word_count <= 35:
                    score += 1
                
                relevant_sentences.append((sentence, score))
        
        if relevant_sentences:
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            return relevant_sentences[0][0]
        
        return None
    
    def _is_good_study_content(self, content: str) -> bool:
        """Check if content is suitable for study flashcards"""
        if not content or len(content.strip()) < 15:
            return False
        
        word_count = len(content.split())
        if word_count < 4 or word_count > 35:  # Study-optimized length
            return False
        
        # Must have enough alphabetic content
        alpha_ratio = sum(c.isalpha() for c in content) / len(content)
        if alpha_ratio < 0.65:
            return False
        
        # Avoid list-like content
        if content.count(',') > 3 or content.count(';') > 1:
            return False
        
        return True
    
    def _find_most_important_sentence(self, sentences: List[str]) -> str:
        """Find the most important sentence for study purposes"""
        scored_sentences = []
        
        for sentence in sentences:
            if self._is_good_study_content(sentence):
                score = self._calculate_study_sentence_score(sentence, sentences)
                scored_sentences.append((sentence, score))
        
        if scored_sentences:
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            return scored_sentences[0][0]
        
        return None
    
    def _remove_duplicate_flashcards(self, flashcards: List[Dict]) -> List[Dict]:
        """Remove duplicate flashcards"""
        unique_cards = []
        seen_questions = set()
        seen_answers = set()
        
        for card in flashcards:
            question = card.get("question", "").lower().strip()
            answer = card.get("answer", "").lower().strip()
            
            # Check for exact duplicates
            if question in seen_questions or answer in seen_answers:
                continue
            
            # Check for very similar content
            is_similar = False
            for existing_card in unique_cards:
                existing_q = existing_card.get("question", "").lower().strip()
                existing_a = existing_card.get("answer", "").lower().strip()
                
                # Simple similarity check
                if (self._text_similarity(question, existing_q) > 0.8 or
                    self._text_similarity(answer, existing_a) > 0.8):
                    is_similar = True
                    break
            
            if not is_similar:
                unique_cards.append(card)
                seen_questions.add(question)
                seen_answers.add(answer)
        
        return unique_cards
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _split_text_for_processing(self, text: str, max_chunk_size: int = 5000) -> List[str]:
        """Split text into chunks for Azure API"""
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
    
    def _calculate_sentence_frequency_score(self, sentence: str, word_freq: Dict[str, int]) -> float:
        """Calculate sentence score based on word frequencies"""
        words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
        if not words:
            return 0.0
        
        total_score = sum(word_freq.get(word, 0) for word in words)
        return total_score / len(words)
    
    def _compile_metadata(self, results: Dict, cleaned_text: str, original_text: str) -> Dict:
        """Compile metadata about the analysis"""
        try:
            return {
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "text_statistics": {
                    "original_character_count": len(original_text),
                    "cleaned_character_count": len(cleaned_text),
                    "cleaning_efficiency": len(cleaned_text) / len(original_text) if len(original_text) > 0 else 0,
                    "word_count": len(cleaned_text.split()),
                    "sentence_count": len(self.text_processor.extract_sentences(cleaned_text))
                },
                "analysis_results": {
                    "key_phrases_extracted": len(results.get("key_phrases", {}).get("phrases", [])),
                    "summary_generated": results.get("summary", {}).get("status") == "success",
                    "flashcards_created": len(results.get("flashcards", []))
                },
                "quality_indicators": {
                    "text_length_adequate": len(cleaned_text) > 100,
                    "has_structure": len(self.text_processor.extract_sentences(cleaned_text)) > 3,
                    "summary_method": results.get("summary", {}).get("method", "none"),
                    "study_ready": True
                },
                "processing_info": {
                    "azure_language_service": "Azure Text Analytics",
                    "enhancement_version": "2.0_streamlined",
                    "api_region": "East US",
                    "features_used": [
                        "enhanced_text_cleaning",
                        "concept_extraction",
                        "focused_summarization", 
                        "study_flashcard_generation",
                        "key_phrase_extraction"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error compiling metadata: {e}")
            return {"error": str(e)}
    
    def _create_fallback_result(self, error_message: str) -> Dict:
        """Create fallback result when analysis fails"""
        return {
            "summary": {"status": "failed", "error": error_message},
            "key_phrases": {"status": "failed", "error": error_message, "phrases": []},
            "flashcards": [],
            "metadata": {
                "analysis_failed": True,
                "error": error_message,
                "fallback_used": True
            },
            "processed_text": ""
        }

# Create global instance
azure_language_processor = AzureLanguageProcessor()