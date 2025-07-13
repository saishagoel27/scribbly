import google.generativeai as genai
import json
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiFlashcardGenerator:
    """
    Enhanced Gemini AI integration for intelligent flashcard generation
    
    This class provides:
    - Multiple flashcard generation strategies
    - Quality validation and optimization
    - Difficulty balancing
    - Comprehensive fallback system
    - Progress tracking integration
    """
    
    def __init__(self):
        """Initialize Gemini flashcard generator"""
        self.client = None
        self.is_available = False
        self.model = None
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Gemini API client with enhanced error handling"""
        try:
            api_key = Config.GEMINI_API_KEY
            if not api_key:
                logger.warning("❌ Google Gemini API key not configured")
                self.is_available = False
                return
            
            # Configure Gemini API
            genai.configure(api_key=api_key)
            
            # Initialize model with generation config
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                generation_config=self.generation_config
            )
            
            # Test the connection
            self._test_connection()
            self.is_available = True
            logger.info("✅ Google Gemini API initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini API: {e}")
            self.is_available = False
    
    def _test_connection(self):
        """Test Gemini API connection with a simple request"""
        try:
            test_response = self.model.generate_content("Test connection")
            if test_response and test_response.text:
                logger.info("🔗 Gemini API connection verified")
            else:
                raise Exception("Empty response from Gemini API")
        except Exception as e:
            logger.warning(f"⚠️ Gemini API connection test failed: {e}")
            raise
    
    def generate_comprehensive_flashcards(self, 
                                        extracted_text: str, 
                                        summary_data: Dict, 
                                        key_phrases: List[str],
                                        progress_callback: Optional[Callable[[str], None]] = None) -> Dict:
        """
        Generate comprehensive flashcards using Gemini AI with progress tracking
        
        Args:
            extracted_text: Cleaned text from document processing
            summary_data: Summary analysis from Azure Language Services
            key_phrases: Key phrases extracted from the text
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing generated flashcards and metadata
        """
        start_time = time.time()
        
        if not self.is_available:
            if progress_callback:
                progress_callback("⚠️ Gemini API unavailable, using fallback generation...")
            return self._create_fallback_flashcards(extracted_text, key_phrases)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            return {
                "error": "Insufficient text for flashcard generation (minimum 50 characters required)",
                "status": "error"
            }
        
        try:
            if progress_callback:
                progress_callback("🧠 Initializing AI flashcard generation...")
            
            # Prepare content for processing
            processed_content = self._prepare_content_for_generation(
                extracted_text, summary_data, key_phrases
            )
            
            # Generate different types of flashcards with progress updates
            flashcard_sets = {}
            generation_steps = [
                ("definitions", "📚 Creating definition flashcards..."),
                ("conceptual", "💡 Creating conceptual Q&A..."),
                ("application", "🔧 Creating application flashcards..."),
                ("detail", "📝 Creating detail flashcards...")
            ]
            
            for card_type, progress_message in generation_steps:
                if progress_callback:
                    progress_callback(progress_message)
                
                try:
                    if card_type == "definitions":
                        flashcard_sets[card_type] = self._generate_definition_flashcards(
                            processed_content, key_phrases
                        )
                    elif card_type == "conceptual":
                        flashcard_sets[card_type] = self._generate_conceptual_flashcards(
                            processed_content, summary_data
                        )
                    elif card_type == "application":
                        flashcard_sets[card_type] = self._generate_application_flashcards(
                            processed_content, key_phrases
                        )
                    elif card_type == "detail":
                        flashcard_sets[card_type] = self._generate_detail_flashcards(
                            processed_content, summary_data
                        )
                    
                    # Brief pause to prevent rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate {card_type} flashcards: {e}")
                    flashcard_sets[card_type] = []
            
            if progress_callback:
                progress_callback("🎯 Optimizing flashcard set...")
            
            # Combine and optimize flashcards
            combined_flashcards = self._combine_and_optimize_flashcards(flashcard_sets)
            
            # Calculate generation metadata
            generation_metadata = self._calculate_generation_metadata(
                combined_flashcards, flashcard_sets, start_time
            )
            
            result = {
                "flashcards": self._organize_flashcards_by_type(combined_flashcards),
                "generation_metadata": generation_metadata,
                "status": "success"
            }
            
            if progress_callback:
                total_cards = sum(len(cards) for cards in result["flashcards"].values())
                progress_callback(f"✅ Generated {total_cards} flashcards successfully!")
            
            return result
            
        except Exception as e:
            error_msg = f"Gemini flashcard generation failed: {str(e)}"
            logger.error(error_msg)
            
            if progress_callback:
                progress_callback("⚠️ AI generation failed, creating fallback flashcards...")
            
            # Return fallback flashcards on error
            fallback_result = self._create_fallback_flashcards(extracted_text, key_phrases)
            fallback_result["error_details"] = error_msg
            return fallback_result
    
    def _prepare_content_for_generation(self, text: str, summary_data: Dict, key_phrases: List[str]) -> Dict:
        """Prepare and optimize content for flashcard generation"""
        # Get the best available summary
        summary_text = ""
        if summary_data:
            if 'azure_extractive_summary' in summary_data and summary_data['azure_extractive_summary']:
                summary_text = summary_data['azure_extractive_summary']
            elif 'concept_based_summary' in summary_data:
                concept_summary = summary_data['concept_based_summary']
                if isinstance(concept_summary, dict) and 'summary' in concept_summary:
                    summary_text = concept_summary['summary']
        
        # Truncate text for API limits while preserving quality
        max_text_length = 3000
        if len(text) > max_text_length:
            # Try to break at sentence boundaries
            sentences = re.split(r'[.!?]+', text)
            truncated_text = ""
            for sentence in sentences:
                if len(truncated_text) + len(sentence) > max_text_length:
                    break
                truncated_text += sentence + ". "
            text = truncated_text.strip()
        
        return {
            "main_text": text,
            "summary": summary_text,
            "key_phrases": key_phrases[:10],  # Limit to top 10 phrases
            "word_count": len(text.split()),
            "estimated_complexity": self._estimate_content_complexity(text)
        }
    
    def _estimate_content_complexity(self, text: str) -> str:
        """Estimate content complexity for appropriate flashcard difficulty"""
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        if avg_word_length > 6 and avg_sentence_length > 20:
            return "high"
        elif avg_word_length > 4 and avg_sentence_length > 15:
            return "medium"
        else:
            return "low"
    
    def _generate_definition_flashcards(self, content: Dict, key_phrases: List[str]) -> List[Dict]:
        """Generate definition-based flashcards using Gemini AI"""
        try:
            text = content["main_text"]
            phrases = content["key_phrases"]
            
            prompt = f"""You are an expert educator creating study flashcards. Based on the provided educational content, create definition flashcards for the most important terms and concepts.

EDUCATIONAL CONTENT:
{text}

KEY TERMS TO FOCUS ON: {', '.join(phrases)}

INSTRUCTIONS:
1. Create 4-6 definition flashcards
2. Focus on the most important terms and concepts
3. Questions should ask "What is..." or "Define..."
4. Answers should be clear, concise definitions (1-3 sentences)
5. Use appropriate difficulty levels based on concept complexity
6. Return ONLY valid JSON in this exact format:

[
  {{
    "question": "What is [term/concept]?",
    "answer": "Clear, concise definition explaining the term",
    "type": "definition",
    "difficulty": "easy",
    "concept": "main concept category",
    "confidence": 0.85
  }}
]

Return only the JSON array, no other text or formatting."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                flashcards = self._parse_gemini_response(response.text)
                validated_cards = [card for card in flashcards if self._validate_flashcard(card)]
                return validated_cards[:6]  # Limit to 6 definition cards
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating definition flashcards: {e}")
            return []
    
    def _generate_conceptual_flashcards(self, content: Dict, summary_data: Dict) -> List[Dict]:
        """Generate conceptual understanding flashcards"""
        try:
            text = content["main_text"]
            summary = content["summary"]
            
            prompt = f"""You are an expert educator creating study flashcards. Based on the provided educational content, create conceptual understanding flashcards that test deeper comprehension and critical thinking.

EDUCATIONAL CONTENT:
{text}

CONTENT SUMMARY:
{summary}

INSTRUCTIONS:
1. Create 3-5 conceptual flashcards
2. Focus on WHY, HOW, and relationships between concepts
3. Test understanding and analysis, not just memorization
4. Questions should explore significance, relationships, and applications
5. Use medium to hard difficulty levels
6. Return ONLY valid JSON in this exact format:

[
  {{
    "question": "Why is [concept] important for [context]? Explain the relationship.",
    "answer": "Detailed explanation focusing on significance, relationships, and implications",
    "type": "conceptual",
    "difficulty": "medium",
    "concept": "main concept category",
    "confidence": 0.80
  }}
]

Return only the JSON array, no other text or formatting."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                flashcards = self._parse_gemini_response(response.text)
                validated_cards = [card for card in flashcards if self._validate_flashcard(card)]
                return validated_cards[:5]  # Limit to 5 conceptual cards
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating conceptual flashcards: {e}")
            return []
    
    def _generate_application_flashcards(self, content: Dict, key_phrases: List[str]) -> List[Dict]:
        """Generate application and use-case flashcards"""
        try:
            text = content["main_text"]
            phrases = content["key_phrases"]
            
            prompt = f"""You are an expert educator creating study flashcards. Based on the provided educational content, create application and use-case flashcards that test practical knowledge and real-world application.

EDUCATIONAL CONTENT:
{text}

KEY CONCEPTS: {', '.join(phrases)}

INSTRUCTIONS:
1. Create 3-4 application flashcards
2. Focus on practical use cases, real-world applications, and problem-solving
3. Questions should ask HOW to apply concepts in specific scenarios
4. Include specific examples and practical steps where possible
5. Test ability to apply knowledge in new situations
6. Return ONLY valid JSON in this exact format:

[
  {{
    "question": "How would you apply [concept] in [specific scenario]? Provide steps.",
    "answer": "Practical application explanation with specific steps and examples",
    "type": "application",
    "difficulty": "medium",
    "concept": "main concept category",
    "confidence": 0.75
  }}
]

Return only the JSON array, no other text or formatting."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                flashcards = self._parse_gemini_response(response.text)
                validated_cards = [card for card in flashcards if self._validate_flashcard(card)]
                return validated_cards[:4]  # Limit to 4 application cards
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating application flashcards: {e}")
            return []
    
    def _generate_detail_flashcards(self, content: Dict, summary_data: Dict) -> List[Dict]:
        """Generate detail-oriented flashcards for specific facts and information"""
        try:
            text = content["main_text"]
            
            prompt = f"""You are an expert educator creating study flashcards. Based on the provided educational content, create detail-oriented flashcards for specific facts, numbers, dates, and important details.

EDUCATIONAL CONTENT:
{text}

INSTRUCTIONS:
1. Create 2-3 detail flashcards
2. Focus on specific facts, numbers, dates, formulas, or important details mentioned in the content
3. Questions should be clear and ask for specific information
4. Answers should be precise and factual
5. Use easy to medium difficulty levels
6. Return ONLY valid JSON in this exact format:

[
  {{
    "question": "What specific [fact/number/detail] about [topic] is mentioned?",
    "answer": "Specific factual information from the content",
    "type": "detail",
    "difficulty": "easy",
    "concept": "main concept category",
    "confidence": 0.85
  }}
]

Return only the JSON array, no other text or formatting."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                flashcards = self._parse_gemini_response(response.text)
                validated_cards = [card for card in flashcards if self._validate_flashcard(card)]
                return validated_cards[:3]  # Limit to 3 detail cards
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating detail flashcards: {e}")
            return []
    
    def _parse_gemini_response(self, response_text: str) -> List[Dict]:
        """Parse Gemini response and extract JSON flashcards with enhanced error handling"""
        try:
            # Clean the response
            cleaned_response = response_text.strip()
            
            # Remove markdown code blocks if present
            cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
            cleaned_response = re.sub(r'```\s*', '', cleaned_response)
            
            # Try to extract JSON array from response
            json_pattern = r'\[\s*\{.*?\}\s*\]'
            json_match = re.search(json_pattern, cleaned_response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                try:
                    flashcards = json.loads(json_str)
                    if isinstance(flashcards, list):
                        return flashcards
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing error: {e}")
            
            # Try parsing the entire response as JSON
            try:
                flashcards = json.loads(cleaned_response)
                if isinstance(flashcards, list):
                    return flashcards
                elif isinstance(flashcards, dict) and 'flashcards' in flashcards:
                    return flashcards['flashcards']
            except json.JSONDecodeError:
                pass
            
            # Last resort: try to extract individual flashcard objects
            card_pattern = r'\{[^{}]*"question"[^{}]*"answer"[^{}]*\}'
            card_matches = re.findall(card_pattern, cleaned_response, re.DOTALL)
            
            extracted_cards = []
            for card_match in card_matches:
                try:
                    card = json.loads(card_match)
                    extracted_cards.append(card)
                except json.JSONDecodeError:
                    continue
            
            if extracted_cards:
                return extracted_cards
            
            logger.warning("Could not parse any valid flashcards from Gemini response")
            return []
                
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return []
    
    def _validate_flashcard(self, card: Dict) -> bool:
        """Validate flashcard structure and content quality"""
        try:
            required_fields = ["question", "answer", "type", "difficulty"]
            
            # Check required fields exist and are not empty
            for field in required_fields:
                if field not in card or not card[field] or not str(card[field]).strip():
                    logger.debug(f"Flashcard missing or empty field: {field}")
                    return False
            
            # Validate content quality
            question = str(card["question"]).strip()
            answer = str(card["answer"]).strip()
            
            # Check minimum content length
            if len(question) < 10 or len(answer) < 10:
                logger.debug("Flashcard content too short")
                return False
            
            # Check maximum content length
            if len(question) > 300 or len(answer) > 600:
                logger.debug("Flashcard content too long")
                return False
            
            # Validate difficulty value
            valid_difficulties = ["easy", "medium", "hard"]
            if card["difficulty"] not in valid_difficulties:
                logger.debug(f"Invalid difficulty: {card['difficulty']}")
                card["difficulty"] = "medium"  # Default fallback
            
            # Validate type
            valid_types = ["definition", "conceptual", "application", "detail"]
            if card["type"] not in valid_types:
                logger.debug(f"Invalid type: {card['type']}")
                return False
            
            # Add missing optional fields with defaults
            if "concept" not in card:
                card["concept"] = "general"
            
            if "confidence" not in card:
                card["confidence"] = 0.8
            
            # Ensure confidence is a valid number
            try:
                card["confidence"] = float(card["confidence"])
                if not (0.0 <= card["confidence"] <= 1.0):
                    card["confidence"] = 0.8
            except (ValueError, TypeError):
                card["confidence"] = 0.8
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating flashcard: {e}")
            return False
    
    def _combine_and_optimize_flashcards(self, flashcard_sets: Dict) -> List[Dict]:
        """Combine flashcard sets and optimize for learning effectiveness"""
        all_flashcards = []
        
        # Collect all flashcards from different types
        for card_type, cards in flashcard_sets.items():
            if isinstance(cards, list):
                all_flashcards.extend(cards)
        
        if not all_flashcards:
            return []
        
        # Remove duplicates and low-quality cards
        unique_flashcards = self._remove_duplicate_flashcards(all_flashcards)
        
        # Filter out low-confidence cards
        quality_flashcards = [
            card for card in unique_flashcards 
            if card.get("confidence", 0) >= 0.6
        ]
        
        # Sort by quality score (combination of confidence and importance)
        sorted_flashcards = sorted(
            quality_flashcards, 
            key=lambda x: (
                x.get("confidence", 0) * 0.6 + 
                self._calculate_card_importance(x) * 0.4
            ), 
            reverse=True
        )
        
        # Ensure good mix of difficulties and types
        optimized_cards = self._ensure_optimal_distribution(sorted_flashcards)
        
        # Limit total number based on configuration
        max_cards = min(Config.MAX_TOTAL_CARDS, 15)
        return optimized_cards[:max_cards]
    
    def _remove_duplicate_flashcards(self, flashcards: List[Dict]) -> List[Dict]:
        """Remove duplicate flashcards based on content similarity"""
        unique_cards = []
        seen_questions = []
        
        for card in flashcards:
            question = card.get("question", "").lower().strip()
            
            # Check for exact duplicates
            if question in seen_questions:
                continue
            
            # Check for similar questions (similarity threshold: 0.8)
            is_similar = False
            for existing_q in seen_questions:
                if self._calculate_text_similarity(question, existing_q) > 0.8:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_cards.append(card)
                seen_questions.append(question)
        
        return unique_cards
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        try:
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_card_importance(self, card: Dict) -> float:
        """Calculate flashcard importance score based on multiple factors"""
        try:
            importance = 0.0
            
            # Type-based importance scoring
            type_scores = {
                "definition": 0.9,     # High importance for definitions
                "conceptual": 0.8,     # High importance for concepts
                "application": 0.7,    # Medium-high for applications
                "detail": 0.6          # Medium for details
            }
            importance += type_scores.get(card.get("type", ""), 0.5)
            
            # Content length scoring (prefer moderate length)
            question_len = len(card.get("question", ""))
            answer_len = len(card.get("answer", ""))
            
            # Optimal length ranges
            if 30 <= question_len <= 150 and 50 <= answer_len <= 300:
                importance += 0.2
            elif 20 <= question_len <= 200 and 30 <= answer_len <= 400:
                importance += 0.1
            
            # Difficulty distribution bonus
            difficulty = card.get("difficulty", "medium")
            if difficulty == "medium":
                importance += 0.1  # Prefer medium difficulty
            elif difficulty in ["easy", "hard"]:
                importance += 0.05
            
            return min(importance, 1.0)  # Cap at 1.0
            
        except Exception:
            return 0.5  # Default moderate importance
    
    def _ensure_optimal_distribution(self, flashcards: List[Dict]) -> List[Dict]:
        """Ensure optimal distribution of difficulty levels and types"""
        if not flashcards:
            return []
        
        # Separate cards by difficulty
        easy_cards = [c for c in flashcards if c.get("difficulty") == "easy"]
        medium_cards = [c for c in flashcards if c.get("difficulty") == "medium"]
        hard_cards = [c for c in flashcards if c.get("difficulty") == "hard"]
        
        # Target distribution: 40% easy, 40% medium, 20% hard
        total_target = min(len(flashcards), 15)
        easy_target = max(1, int(total_target * 0.4))
        medium_target = max(1, int(total_target * 0.4))
        hard_target = max(0, total_target - easy_target - medium_target)
        
        # Select cards maintaining quality order
        selected_cards = []
        selected_cards.extend(easy_cards[:easy_target])
        selected_cards.extend(medium_cards[:medium_target])
        selected_cards.extend(hard_cards[:hard_target])
        
        # Fill remaining slots with best available cards
        remaining_slots = total_target - len(selected_cards)
        if remaining_slots > 0:
            remaining_cards = [c for c in flashcards if c not in selected_cards]
            selected_cards.extend(remaining_cards[:remaining_slots])
        
        # Ensure type diversity
        return self._ensure_type_diversity(selected_cards)
    
    def _ensure_type_diversity(self, flashcards: List[Dict]) -> List[Dict]:
        """Ensure good diversity of flashcard types"""
        if len(flashcards) <= 4:
            return flashcards  # Too few cards to enforce diversity
        
        # Group by type
        by_type = {}
        for card in flashcards:
            card_type = card.get("type", "general")
            if card_type not in by_type:
                by_type[card_type] = []
            by_type[card_type].append(card)
        
        # If we have good type diversity, return as is
        if len(by_type) >= 3:
            return flashcards
        
        # Otherwise, try to maintain at least 2-3 different types
        diverse_cards = []
        max_per_type = max(2, len(flashcards) // len(by_type))
        
        for card_type, cards in by_type.items():
            diverse_cards.extend(cards[:max_per_type])
        
        return diverse_cards
    
    def _organize_flashcards_by_type(self, flashcards: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize flashcards by type for the final result"""
        organized = {
            "definition": [],
            "conceptual": [],
            "application": [],
            "detail": []
        }
        
        for card in flashcards:
            card_type = card.get("type", "definition")
            if card_type in organized:
                organized[card_type].append(card)
            else:
                organized["definition"].append(card)  # Default fallback
        
        # Remove empty categories
        return {k: v for k, v in organized.items() if v}
    
    def _calculate_generation_metadata(self, flashcards: List[Dict], flashcard_sets: Dict, start_time: float) -> Dict:
        """Calculate comprehensive generation metadata"""
        total_cards = len(flashcards)
        generation_time = time.time() - start_time
        
        # Calculate type distribution
        type_distribution = {}
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        confidence_scores = []
        
        for card in flashcards:
            # Type distribution
            card_type = card.get("type", "unknown")
            type_distribution[card_type] = type_distribution.get(card_type, 0) + 1
            
            # Difficulty distribution
            difficulty = card.get("difficulty", "medium")
            if difficulty in difficulty_distribution:
                difficulty_distribution[difficulty] += 1
            
            # Confidence scores
            confidence = card.get("confidence", 0.8)
            confidence_scores.append(confidence)
        
        # Calculate percentages for difficulty distribution
        if total_cards > 0:
            for difficulty in difficulty_distribution:
                difficulty_distribution[difficulty] = round(
                    (difficulty_distribution[difficulty] / total_cards) * 100, 1
                )
        
        # Average confidence
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "total_generated": total_cards,
            "generation_time_seconds": round(generation_time, 2),
            "types_generated": list(flashcard_sets.keys()),
            "type_distribution": type_distribution,
            "difficulty_distribution": difficulty_distribution,
            "average_confidence": round(average_confidence, 3),
            "quality_score": self._calculate_quality_score(flashcards),
            "generation_method": "gemini_ai_enhanced",
            "api_available": self.is_available,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_quality_score(self, flashcards: List[Dict]) -> float:
        """Calculate overall quality score for the flashcard set"""
        if not flashcards:
            return 0.0
        
        total_score = 0.0
        for card in flashcards:
            card_score = card.get("confidence", 0.5)
            
            # Bonus for appropriate content length
            q_len = len(card.get("question", ""))
            a_len = len(card.get("answer", ""))
            
            if 20 <= q_len <= 150 and 30 <= a_len <= 300:
                card_score += 0.1
            
            # Bonus for good type diversity
            if card.get("type") in ["definition", "conceptual", "application"]:
                card_score += 0.05
            
            total_score += card_score
        
        return round(total_score / len(flashcards), 2)
    
    def _create_fallback_flashcards(self, text: str, key_phrases: List[str]) -> Dict:
        """Create basic flashcards when Gemini is unavailable"""
        logger.info("🔄 Creating fallback flashcards without Gemini AI...")
        
        try:
            # Basic text processing
            sentences = re.split(r'[.!?]+', text)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 25]
            
            fallback_cards = []
            
            # Create definition cards from key phrases
            for i, phrase in enumerate(key_phrases[:4]):
                context_sentence = None
                
                # Find the best sentence containing this phrase
                for sentence in meaningful_sentences:
                    if phrase.lower() in sentence.lower() and len(sentence) > 30:
                        context_sentence = sentence
                        break
                
                if context_sentence:
                    fallback_cards.append({
                        "question": f"What do you know about '{phrase}'?",
                        "answer": context_sentence.strip(),
                        "type": "definition",
                        "difficulty": "medium",
                        "concept": phrase,
                        "confidence": 0.6
                    })
            
            # Add a general comprehension question
            if meaningful_sentences:
                first_sentence = meaningful_sentences[0]
                if len(first_sentence) > 20:
                    fallback_cards.append({
                        "question": "What is the main topic discussed in this content?",
                        "answer": first_sentence,
                        "type": "conceptual",
                        "difficulty": "easy",
                        "concept": "main_topic",
                        "confidence": 0.7
                    })
            
            # Add a detail question if we have enough content
            if len(meaningful_sentences) > 2:
                detail_sentence = meaningful_sentences[1]
                if len(detail_sentence) > 25:
                    fallback_cards.append({
                        "question": "What specific information is mentioned about the main topic?",
                        "answer": detail_sentence,
                        "type": "detail",
                        "difficulty": "easy",
                        "concept": "details",
                        "confidence": 0.65
                    })
            
            # Organize cards by type
            organized_cards = self._organize_flashcards_by_type(fallback_cards)
            
            return {
                "flashcards": organized_cards,
                "generation_metadata": {
                    "total_generated": len(fallback_cards),
                    "generation_method": "fallback_basic",
                    "quality_score": 0.6,
                    "difficulty_distribution": {"easy": 50.0, "medium": 50.0, "hard": 0.0},
                    "average_confidence": 0.65,
                    "api_available": False,
                    "fallback_reason": "Gemini API unavailable"
                },
                "status": "fallback_success"
            }
            
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            return {
                "flashcards": {},
                "generation_metadata": {
                    "total_generated": 0,
                    "generation_method": "failed",
                    "error": str(e)
                },
                "status": "error",
                "error": f"Both AI and fallback generation failed: {str(e)}"
            }

# Create global instance
gemini_flashcard_generator = GeminiFlashcardGenerator()