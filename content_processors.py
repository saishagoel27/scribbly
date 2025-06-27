"""
Content processing utilities for text analysis, summarization, and flashcard generation.
"""
import logging
import random
import re
import unicodedata
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

# NLTK imports with error handling
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from config import app_config, azure_config
from azure_clients import azure_services

logger = logging.getLogger(__name__)

class TextValidator:
    """Validates text for processing"""
    
    @staticmethod
    def validate_for_analysis(text: str) -> bool:
        """Validate text for Azure AI analysis"""
        if not text or not text.strip():
            raise ValueError("Text is empty")
        
        # Clean and normalize text
        text = unicodedata.normalize('NFKD', text).strip()
        
        if len(text) < app_config.min_text_length:
            raise ValueError(f"Text too short for analysis (minimum {app_config.min_text_length} characters)")
        
        if len(text) > azure_config.text_max_length:
            raise ValueError(f"Text too long for analysis (maximum {azure_config.text_max_length:,} characters)")
        
        return True

class TextChunker:
    """Intelligent text chunking utilities"""
    
    @staticmethod
    def chunk_text(text: str, max_chunk_size: int = 5000, overlap: int = 200) -> List[str]:
        """Smart text chunking with overlap to preserve context"""
        if not text:
            return []
        
        if len(text) <= max_chunk_size:
            return [text]
        
        if NLTK_AVAILABLE:
            return TextChunker._nltk_chunking(text, max_chunk_size, overlap)
        else:
            return TextChunker._simple_chunking(text, max_chunk_size, overlap)
    
    @staticmethod
    def _nltk_chunking(text: str, max_chunk_size: int, overlap: int) -> List[str]:
        """NLTK-based intelligent chunking"""
        try:
            sentences = sent_tokenize(text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                    current_chunk += sentence + " "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks if chunks else [text]
            
        except Exception as e:
            logger.warning(f"NLTK chunking failed, using simple method: {e}")
            return TextChunker._simple_chunking(text, max_chunk_size, overlap)
    
    @staticmethod
    def _simple_chunking(text: str, max_chunk_size: int, overlap: int) -> List[str]:
        """Simple chunking with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + max_chunk_size // 2:
                    end = last_period + 1
            
            chunks.append(text[start:end].strip())
            start = max(start + max_chunk_size - overlap, end)
        
        return [chunk for chunk in chunks if chunk]

class ContentSummarizer:
    """Handles text summarization with multiple strategies"""
    
    @staticmethod
    def summarize(text: str, structure: Optional[Dict] = None) -> str:
        """Generate comprehensive summary using best available method"""
        if not text or len(text.strip()) < app_config.min_text_length:
            return "Content too short for meaningful summarization."
        
        try:
            TextValidator.validate_for_analysis(text)
            
            # Try Azure summarization first
            if azure_services.language_service.is_available:
                azure_summary = ContentSummarizer._azure_summarization(text)
                if azure_summary and len(azure_summary) > app_config.min_text_length:
                    logger.info("Using Azure-generated summary")
                    return azure_summary
            
            # Fallback to extractive summarization
            logger.info("Using extractive summarization")
            return ContentSummarizer._extractive_summarization(text, structure)
            
        except ValueError as ve:
            logger.warning(f"Text validation failed: {ve}")
            return ContentSummarizer._extractive_summarization(text, structure)
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return ContentSummarizer._extractive_summarization(text, structure)
    
    @staticmethod
    def _azure_summarization(text: str) -> Optional[str]:
        """Azure-based summarization"""
        try:
            chunks = TextChunker.chunk_text(text, max_chunk_size=5000)
            summaries = []
            
            for i, chunk in enumerate(chunks[:app_config.max_chunks_to_process]):
                try:
                    chunk_summary = azure_services.language_service.summarize_text(chunk, max_sentences=3)
                    if chunk_summary and chunk_summary.strip():
                        summaries.append(chunk_summary)
                        logger.debug(f"Summarized chunk {i+1}/{len(chunks)}")
                except Exception as e:
                    logger.warning(f"Azure summarization failed for chunk {i+1}: {e}")
                    continue
            
            if summaries:
                final_summary = " ".join(summaries)
                logger.info(f"Azure summarization successful: {len(final_summary)} characters")
                return final_summary
            
            return None
            
        except Exception as e:
            logger.error(f"Azure summarization error: {e}")
            return None
    
    @staticmethod
    def _extractive_summarization(text: str, structure: Optional[Dict] = None) -> str:
        """Fallback extractive summarization using basic algorithms"""
        try:
            # Use structured content if available
            if structure:
                return ContentSummarizer._structure_based_summary(structure)
            
            # Basic sentence-based extraction
            sentences = ContentSummarizer._get_sentences(text)
            if len(sentences) <= 3:
                return text
            
            # Score sentences by key indicators
            scored_sentences = ContentSummarizer._score_sentences(sentences, text)
            
            # Select top sentences (max 5)
            top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:5]
            top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Maintain order
            
            summary = " ".join([sent for sent, _ in top_sentences])
            
            logger.info(f"Extractive summary generated: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Extractive summarization error: {e}")
            return text[:500] + "..." if len(text) > 500 else text
    
    @staticmethod
    def _structure_based_summary(structure: Dict) -> str:
        """Generate summary from structured document data"""
        summary_parts = []
        
        # Add headings
        if structure.get("headings"):
            summary_parts.append("Main topics: " + ", ".join(structure["headings"][:3]))
        
        # Add key-value pairs
        if structure.get("key_value_pairs"):
            kv_summary = []
            for kv in structure["key_value_pairs"][:3]:
                kv_summary.append(f"{kv['key']}: {kv['value']}")
            if kv_summary:
                summary_parts.append("Key information: " + "; ".join(kv_summary))
        
        # Add paragraphs
        if structure.get("paragraphs"):
            # Take first few paragraphs
            para_text = " ".join(structure["paragraphs"][:3])
            if len(para_text) > 300:
                para_text = para_text[:300] + "..."
            summary_parts.append(para_text)
        
        # Add table info
        if structure.get("tables"):
            summary_parts.append(f"Contains {len(structure['tables'])} table(s) with structured data.")
        
        return " ".join(summary_parts) if summary_parts else structure.get("content", "")[:500]
    
    @staticmethod
    def _get_sentences(text: str) -> List[str]:
        """Extract sentences from text"""
        if NLTK_AVAILABLE:
            try:
                return [s.strip() for s in sent_tokenize(text) if s.strip()]
            except:
                pass
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    @staticmethod
    def _score_sentences(sentences: List[str], full_text: str) -> List[Tuple[str, float]]:
        """Score sentences for importance"""
        scored = []
        
        # Get word frequency
        words = re.findall(r'\b\w+\b', full_text.lower())
        word_freq = Counter(words)
        
        for i, sentence in enumerate(sentences):
            score = 0.0
            sentence_words = re.findall(r'\b\w+\b', sentence.lower())
            
            # Position score (earlier sentences get higher score)
            score += (len(sentences) - i) / len(sentences) * 0.3
            
            # Length score (prefer medium-length sentences)
            length_score = min(len(sentence_words) / 20, 1.0)
            score += length_score * 0.2
            
            # Word frequency score
            if sentence_words:
                freq_score = sum(word_freq.get(word, 0) for word in sentence_words) / len(sentence_words)
                score += min(freq_score / max(word_freq.values(), 1), 1.0) * 0.5
            
            scored.append((sentence, score))
        
        return scored

class FlashcardGenerator:
    """Generates flashcards from processed content"""
    
    def __init__(self):
        self.question_patterns = [
            "What is {}?",
            "Define {}.",
            "Explain {}.",
            "What does {} mean?",
            "Describe {}.",
        ]
    
    def generate_flashcards(self, text: str, summary: str, structure: Optional[Dict] = None) -> List[Dict[str, str]]:
        """Generate flashcards from text and summary"""
        flashcards = []
        
        try:
            # Generate from key phrases
            if azure_services.language_service.is_available:
                flashcards.extend(self._generate_from_key_phrases(text))
            
            # Generate from structured content
            if structure:
                flashcards.extend(self._generate_from_structure(structure))
            
            # Generate from summary
            flashcards.extend(self._generate_from_summary(summary))
            
            # Generate definition-based cards
            flashcards.extend(self._generate_definition_cards(text))
            
            # Remove duplicates and limit
            unique_flashcards = self._remove_duplicates(flashcards)
            limited_flashcards = unique_flashcards[:app_config.max_flashcards]
            
            logger.info(f"Generated {len(limited_flashcards)} flashcards")
            return limited_flashcards
            
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            return self._generate_basic_flashcards(summary)
    
    def _generate_from_key_phrases(self, text: str) -> List[Dict[str, str]]:
        """Generate flashcards from Azure key phrases"""
        flashcards = []
        
        try:
            key_phrases = azure_services.language_service.extract_key_phrases(text)
            
            for phrase in key_phrases[:10]:  # Limit to top 10
                if len(phrase.split()) <= 4:  # Avoid very long phrases
                    question = random.choice(self.question_patterns).format(phrase)
                    answer = self._find_context_for_phrase(phrase, text)
                    
                    if answer and len(answer) > 20:
                        flashcards.append({
                            "question": question,
                            "answer": answer,
                            "type": "key_phrase",
                            "difficulty": "medium"
                        })
                        
        except Exception as e:
            logger.warning(f"Key phrase flashcard generation failed: {e}")
        
        return flashcards
    
    def _generate_from_structure(self, structure: Dict) -> List[Dict[str, str]]:
        """Generate flashcards from structured document data"""
        flashcards = []
        
        # From key-value pairs
        for kv in structure.get("key_value_pairs", [])[:5]:
            flashcards.append({
                "question": f"What is {kv['key']}?",
                "answer": kv['value'],
                "type": "key_value",
                "difficulty": "easy"
            })
        
        # From headings and related content
        for i, heading in enumerate(structure.get("headings", [])[:3]):
            if i < len(structure.get("paragraphs", [])):
                content = structure["paragraphs"][i][:200]
                flashcards.append({
                    "question": f"What is discussed under '{heading}'?",
                    "answer": content,
                    "type": "heading",
                    "difficulty": "medium"
                })
        
        return flashcards
    
    def _generate_from_summary(self, summary: str) -> List[Dict[str, str]]:
        """Generate flashcards from summary content"""
        flashcards = []
        
        sentences = ContentSummarizer._get_sentences(summary)
        
        for sentence in sentences[:3]:
            if len(sentence) > 30:
                # Create fill-in-the-blank style questions
                words = sentence.split()
                if len(words) > 8:
                    # Remove a key word to create question
                    important_words = [w for w in words if len(w) > 4 and w.isalpha()]
                    if important_words:
                        word_to_remove = random.choice(important_words)
                        question = sentence.replace(word_to_remove, "______", 1)
                        
                        flashcards.append({
                            "question": f"Fill in the blank: {question}",
                            "answer": word_to_remove,
                            "type": "fill_blank",
                            "difficulty": "medium"
                        })
        
        return flashcards
    
    def _generate_definition_cards(self, text: str) -> List[Dict[str, str]]:
        """Generate definition-based flashcards"""
        flashcards = []
        
        # Look for definition patterns
        definition_patterns = [
            r'(\w+(?:\s+\w+){0,2})\s+is\s+([^.!?]+[.!?])',
            r'(\w+(?:\s+\w+){0,2})\s+means\s+([^.!?]+[.!?])',
            r'(\w+(?:\s+\w+){0,2})\s+refers to\s+([^.!?]+[.!?])',
            r'(\w+(?:\s+\w+){0,2}):\s+([^.!?]+[.!?])',
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) > 2 and len(definition) > 20:
                    flashcards.append({
                        "question": f"What is {term}?",
                        "answer": definition,
                        "type": "definition",
                        "difficulty": "easy"
                    })
                    
                    if len(flashcards) >= 5:  # Limit definition cards
                        break
        
        return flashcards
    
    def _find_context_for_phrase(self, phrase: str, text: str) -> str:
        """Find relevant context for a key phrase"""
        sentences = ContentSummarizer._get_sentences(text)
        
        for sentence in sentences:
            if phrase.lower() in sentence.lower():
                # Return the sentence plus some context
                if len(sentence) > 100:
                    return sentence
                else:
                    # Try to add next sentence for more context
                    sentence_index = sentences.index(sentence)
                    if sentence_index < len(sentences) - 1:
                        return sentence + " " + sentences[sentence_index + 1]
                    return sentence
        
        return ""
    
    def _remove_duplicates(self, flashcards: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate flashcards"""
        seen_questions = set()
        unique_cards = []
        
        for card in flashcards:
            question_normalized = re.sub(r'\s+', ' ', card['question'].lower().strip())
            if question_normalized not in seen_questions:
                seen_questions.add(question_normalized)
                unique_cards.append(card)
        
        return unique_cards
    
    def _generate_basic_flashcards(self, summary: str) -> List[Dict[str, str]]:
        """Generate basic flashcards as fallback"""
        sentences = ContentSummarizer._get_sentences(summary)[:3]
        
        flashcards = []
        for i, sentence in enumerate(sentences):
            if len(sentence) > 30:
                flashcards.append({
                    "question": f"Key point {i+1}: What does this mean?",
                    "answer": sentence,
                    "type": "basic",
                    "difficulty": "medium"
                })
        
        return flashcards

class QuestionGenerator:
    """Generates study questions from content"""
    
    def __init__(self):
        self.question_types = [
            "What is the main idea of {}?",
            "How does {} work?",
            "Why is {} important?",
            "What are the key features of {}?",
            "Explain the relationship between {} and {}.",
            "What would happen if {}?",
            "Compare {} with {}.",
            "What are the advantages of {}?",
            "What problems does {} solve?",
            "How can {} be improved?",
        ]
    
    def generate_questions(self, text: str, summary: str, flashcards: List[Dict]) -> List[Dict[str, str]]:
        """Generate study questions from content"""
        questions = []
        
        try:
            # Generate from key concepts
            if azure_services.language_service.is_available:
                questions.extend(self._generate_from_key_phrases(text))
            
            # Generate from summary
            questions.extend(self._generate_from_summary(summary))
            
            # Generate from flashcards
            questions.extend(self._generate_from_flashcards(flashcards))
            
            # Generate analytical questions
            questions.extend(self._generate_analytical_questions(text))
            
            # Remove duplicates and limit
            unique_questions = self._remove_duplicate_questions(questions)
            limited_questions = unique_questions[:15]  # Limit to 15 questions
            
            logger.info(f"Generated {len(limited_questions)} study questions")
            return limited_questions
            
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return self._generate_basic_questions(summary)
    
    def _generate_from_key_phrases(self, text: str) -> List[Dict[str, str]]:
        """Generate questions from key phrases"""
        questions = []
        
        try:
            key_phrases = azure_services.language_service.extract_key_phrases(text)
            
            for phrase in key_phrases[:8]:
                question_template = random.choice(self.question_types)
                if "{}" in question_template:
                    question = question_template.format(phrase)
                    questions.append({
                        "question": question,
                        "type": "key_phrase",
                        "difficulty": "medium",
                        "topic": phrase
                    })
                        
        except Exception as e:
            logger.warning(f"Key phrase question generation failed: {e}")
        
        return questions
    
    def _generate_from_summary(self, summary: str) -> List[Dict[str, str]]:
        """Generate questions from summary"""
        questions = []
        sentences = ContentSummarizer._get_sentences(summary)
        
        for sentence in sentences[:3]:
            # Extract potential topics from sentence
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence)
            if words:
                topic = words[0]
                question_templates = [
                    f"What is the significance of {topic}?",
                    f"How does {topic} relate to the main topic?",
                    f"What are the key aspects of {topic}?",
                ]
                
                questions.append({
                    "question": random.choice(question_templates),
                    "type": "summary",
                    "difficulty": "medium",
                    "topic": topic
                })
        
        return questions
    
    def _generate_from_flashcards(self, flashcards: List[Dict]) -> List[Dict[str, str]]:
        """Generate deeper questions based on flashcard content"""
        questions = []
        
        for card in flashcards[:5]:
            if card.get("type") == "key_phrase":
                topic = card.get("topic", "the topic")
                deeper_questions = [
                    f"How does {topic} impact the overall subject?",
                    f"What are the practical applications of {topic}?",
                    f"What challenges are associated with {topic}?",
                ]
                
                questions.append({
                    "question": random.choice(deeper_questions),
                    "type": "analytical",
                    "difficulty": "hard",
                    "topic": topic
                })
        
        return questions
    
    def _generate_analytical_questions(self, text: str) -> List[Dict[str, str]]:
        """Generate higher-order thinking questions"""
        questions = []
        
        analytical_templates = [
            "What are the main arguments presented in this text?",
            "How could this information be applied in real-world scenarios?",
            "What are the potential limitations or criticisms of these ideas?",
            "How does this content relate to current events or trends?",
            "What questions does this content raise for further investigation?",
            "What would be the consequences if these ideas were implemented?",
            "How might different stakeholders view this information?",
        ]
        
        for template in analytical_templates[:4]:
            questions.append({
                "question": template,
                "type": "analytical",
                "difficulty": "hard",
                "topic": "general"
            })
        
        return questions
    
    def _remove_duplicate_questions(self, questions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate questions"""
        seen_questions = set()
        unique_questions = []
        
        for question in questions:
            question_normalized = re.sub(r'\s+', ' ', question['question'].lower().strip())
            if question_normalized not in seen_questions:
                seen_questions.add(question_normalized)
                unique_questions.append(question)
        
        return unique_questions
    
    def _generate_basic_questions(self, summary: str) -> List[Dict[str, str]]:
        """Generate basic questions as fallback"""
        questions = [
            {
                "question": "What is the main topic of this content?",
                "type": "basic",
                "difficulty": "easy",
                "topic": "general"
            },
            {
                "question": "What are the key points discussed?",
                "type": "basic", 
                "difficulty": "easy",
                "topic": "general"
            },
            {
                "question": "How can this information be summarized?",
                "type": "basic",
                "difficulty": "medium",
                "topic": "general"
            }
        ]
        
        return questions

class ContentProcessor:
    """Main content processing orchestrator"""
    
    def __init__(self):
        self.summarizer = ContentSummarizer()
        self.flashcard_generator = FlashcardGenerator()
        self.question_generator = QuestionGenerator()
    
    def process_content(self, text: str, structure: Optional[Dict] = None) -> Dict[str, Any]:
        """Process content and generate all study materials"""
        logger.info("Starting content processing pipeline")
        
        try:
            # Validate input
            TextValidator.validate_for_analysis(text)
            
            # Generate summary
            logger.info("Generating summary...")
            summary = self.summarizer.summarize(text, structure)
            
            # Generate flashcards
            logger.info("Generating flashcards...")
            flashcards = self.flashcard_generator.generate_flashcards(text, summary, structure)
            
            # Generate questions
            logger.info("Generating study questions...")
            questions = self.question_generator.generate_questions(text, summary, flashcards)
            
            # Compile results
            results = {
                "summary": summary,
                "flashcards": flashcards,
                "questions": questions,
                "metadata": {
                    "original_length": len(text),
                    "summary_length": len(summary),
                    "flashcard_count": len(flashcards),
                    "question_count": len(questions),
                    "processing_method": "azure" if azure_services.language_service.is_available else "extractive"
                }
            }
            
            logger.info(f"Content processing complete: {len(flashcards)} flashcards, {len(questions)} questions")
            return results
            
        except ValueError as ve:
            logger.warning(f"Content validation failed: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            raise Exception(f"Failed to process content: {str(e)}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing capabilities and statistics"""
        return {
            "azure_available": azure_services.language_service.is_available,
            "document_intelligence_available": azure_services.document_intelligence.is_available,
            "nltk_available": NLTK_AVAILABLE,
            "max_text_length": azure_config.text_max_length,
            "max_flashcards": app_config.max_flashcards,
            "supported_features": {
                "summarization": True,
                "flashcard_generation": True,
                "question_generation": True,
                "key_phrase_extraction": azure_services.language_service.is_available,
                "sentiment_analysis": azure_services.language_service.is_available
            }
        }

# Global content processor instance
content_processor = ContentProcessor()