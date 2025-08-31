import logging
import json
import re
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass, field

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import Config
from fallbacks import create_basic_flashcards  

logger = logging.getLogger(__name__)

@dataclass
class GeminiRateLimiter:
    """Simple rate limiter for Gemini API calls"""
    requests_per_minute: int = 60
    request_timestamps: List[float] = field(default_factory=list)
    
    def can_make_request(self) -> bool:
        now = time.time()
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
        return len(self.request_timestamps) < self.requests_per_minute
    
    def record_request(self) -> None:
        self.request_timestamps.append(time.time())
    
    def wait_if_needed(self) -> float:
        if self.can_make_request():
            return 0.0
        
        if self.request_timestamps:
            wait_time = 60 - (time.time() - self.request_timestamps[0]) + 1
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                return wait_time
        return 0.0

class GeminiFlashcardGenerator:
    """Enhanced Gemini AI flashcard generator with rate limiting and resilience"""
    
    def __init__(self):
        self.model = None
        self.available = False
        self.rate_limiter = GeminiRateLimiter()
        self.initialization_error = None
        
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4096,
                    "response_mime_type": "text/plain"
                }
                
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
                
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                test_response = self.model.generate_content("Hello")
                if test_response and test_response.text:
                    self.available = True
                    logger.info("Gemini AI initialized and tested successfully")
                else:
                    raise Exception("Model test failed")
                
            except Exception as e:
                self.initialization_error = str(e)
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            self.initialization_error = "No API key provided"
            logger.warning("Gemini API key not found")
    
    def generate_enhanced_flashcards(self, text: str, generation_params: Dict, 
                                   progress_callback: Optional[Callable] = None) -> Dict:
        """Enhanced flashcard generation with rate limiting and resilience"""
        
        if not self.available:
            logger.warning(f"Gemini unavailable: {self.initialization_error}")
            return self._create_fallback_flashcards(text, generation_params)
        
        try:
            if progress_callback:
                progress_callback("🧠 Analyzing content for flashcard generation...", 0.1)
            
            cleaned_text = self._clean_text_for_processing(text)
            
            if len(cleaned_text.split()) < 50:
                return {"error": "Text too short for meaningful flashcards"}
            
            if progress_callback:
                progress_callback("📝 Creating optimized prompt...", 0.3)
            
            prompt = self._create_flashcard_prompt(cleaned_text, generation_params)
            
            wait_time = self.rate_limiter.wait_if_needed()
            if wait_time > 0 and progress_callback:
                progress_callback(f"⏳ Waiting {wait_time:.1f}s for API rate limit...", 0.4)
            
            if progress_callback:
                progress_callback("🤖 Generating flashcards with Gemini AI...", 0.5)
            
            start_time = time.time()
            self.rate_limiter.record_request()
            response = self.model.generate_content(prompt)
            generation_time = time.time() - start_time
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return self._create_fallback_flashcards(text, generation_params)
            
            if progress_callback:
                progress_callback("📋 Processing flashcard data...", 0.8)
            
            flashcards = self._parse_flashcard_response(response.text)
            
            if not flashcards:
                logger.warning("No valid flashcards parsed, using fallback")
                return self._create_fallback_flashcards(text, generation_params)
            
            if progress_callback:
                progress_callback("✅ Flashcards generated successfully!", 1.0)
            
            return {
                "flashcards": flashcards,
                "generation_metadata": {
                    "total_generated": len(flashcards),
                    "method": "gemini_ai_enhanced",
                    "generation_time_seconds": round(generation_time, 2),
                    "quality_score": self._calculate_quality_score(flashcards),
                    "timestamp": datetime.now().isoformat(),
                    "rate_limited": wait_time > 0
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Enhanced Gemini flashcard generation error: {e}")
            return self._create_fallback_flashcards(text, generation_params)
    
    def _clean_text_for_processing(self, text: str) -> str:
        """Clean and limit text for Gemini processing"""
        cleaned = re.sub(r'\s+', ' ', text)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        max_words = Config.ProcessingLimits.FLASHCARD_INPUT_MAX_WORDS
        words = cleaned.split()
        if len(words) > max_words:
            first_part = words[:int(max_words * 0.7)]
            last_part = words[-int(max_words * 0.3):]
            cleaned = ' '.join(first_part + ['...'] + last_part)
            logger.info(f"Text truncated from {len(words)} to {len(cleaned.split())} words")
        
        return cleaned
    
    def _create_flashcard_prompt(self, text: str, params: Dict) -> str:
        """Create effective prompt for Gemini AI"""
        num_cards = params.get('num_flashcards', Config.DEFAULT_FLASHCARD_COUNT)
        difficulty = params.get('difficulty_focus', 'Mixed (Recommended)')
        key_phrases = params.get('key_phrases', [])
        
        difficulty_instructions = {
            'Basic Concepts': 'Focus on fundamental concepts and definitions. Keep questions simple and clear.',
            'Advanced Topics': 'Create challenging questions that test deep understanding and application.',
            'Application-Based': 'Focus on practical applications and real-world scenarios.',
            'Mixed (Recommended)': 'Mix basic concepts, intermediate understanding, and some application questions.'
        }
        
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions['Mixed (Recommended)'])
        
        key_phrases_text = ""
        if key_phrases:
            key_phrases_text = f"\n\nKey concepts to focus on: {', '.join(key_phrases[:Config.MAX_KEY_PHRASES])}"
        
        prompt = f"""
You are an expert educational content creator. Create {num_cards} high-quality flashcards from the following study material.

REQUIREMENTS:
- {difficulty_instruction}
- Questions should test understanding, not just memorization
- Answers should be clear, concise, and educational
- Include important details and context in answers
- Make questions specific and well-focused
- Return ONLY valid JSON format

{key_phrases_text}

STUDY MATERIAL:
{text}

Return the flashcards in this EXACT JSON format:
{{
  "flashcards": [
    {{
      "question": "Clear, specific question here",
      "answer": "Complete, educational answer here",
      "concept": "Main topic/concept being tested",
      "difficulty": "basic/intermediate/advanced"
    }}
  ]
}}

Generate exactly {num_cards} flashcards now:
"""
        return prompt
    
    def _parse_flashcard_response(self, response_text: str) -> List[Dict]:
        """Enhanced JSON parsing with multiple fallback strategies"""
        
        flashcards = self._parse_json_strategy(response_text)
        if flashcards:
            return flashcards
        
        flashcards = self._parse_code_block_strategy(response_text)
        if flashcards:
            return flashcards
        
        flashcards = self._parse_qa_pattern_strategy(response_text)
        if flashcards:
            return flashcards
        
        flashcards = self._parse_line_strategy(response_text)
        if flashcards:
            return flashcards
        
        logger.warning("All parsing strategies failed")
        return []
    
    def _parse_json_strategy(self, response_text: str) -> List[Dict]:
        """Strategy 1: Clean JSON parsing"""
        try:
            cleaned_response = response_text.strip()
            
            if '```json' in cleaned_response:
                cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
                cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
            elif '```' in cleaned_response:
                cleaned_response = re.sub(r'```\s*', '', cleaned_response)
            
            json_start = cleaned_response.find('{')
            if json_start > 0:
                cleaned_response = cleaned_response[json_start:]
            
            json_end = cleaned_response.rfind('}')
            if json_end > 0:
                cleaned_response = cleaned_response[:json_end + 1]
            
            parsed_data = json.loads(cleaned_response)
            
            if isinstance(parsed_data, dict):
                flashcards = parsed_data.get('flashcards', [])
            elif isinstance(parsed_data, list):
                flashcards = parsed_data
            else:
                return []
            
            return self._validate_flashcards(flashcards)
            
        except json.JSONDecodeError as e:
            logger.debug(f"JSON strategy failed: {e}")
            return []
        except Exception as e:
            logger.debug(f"JSON strategy error: {e}")
            return []
    
    def _parse_code_block_strategy(self, response_text: str) -> List[Dict]:
        """Strategy 2: Extract from any code block"""
        try:
            code_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            
            for block in code_blocks:
                try:
                    parsed_data = json.loads(block)
                    if isinstance(parsed_data, dict) and 'flashcards' in parsed_data:
                        flashcards = self._validate_flashcards(parsed_data['flashcards'])
                        if flashcards:
                            logger.info("Successfully parsed from code block")
                            return flashcards
                except json.JSONDecodeError:
                    continue
            
            return []
            
        except Exception as e:
            logger.debug(f"Code block strategy error: {e}")
            return []
    
    def _parse_qa_pattern_strategy(self, response_text: str) -> List[Dict]:
        """Strategy 3: Extract Q&A patterns"""
        try:
            flashcards = []
            
            patterns = [
                r'(?:Q:|Question:|question:)\s*(.+?)(?:A:|Answer:|answer:)\s*(.+?)(?=(?:Q:|Question:|question:)|$)',
                r'(?:\d+\.)\s*(.+?)\s*(?:Answer:|A:)\s*(.+?)(?=(?:\d+\.)|$)',
                r'(?:Question\s*\d+:)\s*(.+?)(?:Answer\s*\d+:)\s*(.+?)(?=(?:Question\s*\d+:)|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
                
                for i, (question, answer) in enumerate(matches):
                    question = question.strip().replace('\n', ' ')
                    answer = answer.strip().replace('\n', ' ')
                    
                    if len(question) > 10 and len(answer) > 10:
                        flashcards.append({
                            'question': question,
                            'answer': answer,
                            'concept': f'Concept {i+1}',
                            'difficulty': 'intermediate'
                        })
                
                if len(flashcards) >= 3:
                    logger.info(f"Extracted {len(flashcards)} flashcards using pattern strategy")
                    return flashcards
            
            return []
            
        except Exception as e:
            logger.debug(f"QA pattern strategy error: {e}")
            return []
    
    def _parse_line_strategy(self, response_text: str) -> List[Dict]:
        """Strategy 4: Line-by-line extraction for edge cases"""
        try:
            lines = response_text.split('\n')
            flashcards = []
            current_card = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if any(indicator in line.lower() for indicator in ['question:', 'q:', 'what', 'how', 'why', 'when', 'where']):
                    if current_card and 'question' in current_card and 'answer' in current_card:
                        flashcards.append(current_card)
                    current_card = {'question': line}
                
                elif any(indicator in line.lower() for indicator in ['answer:', 'a:']):
                    if 'question' in current_card:
                        current_card['answer'] = line
                        current_card['concept'] = 'General'
                        current_card['difficulty'] = 'intermediate'
            
            if current_card and 'question' in current_card and 'answer' in current_card:
                flashcards.append(current_card)
            
            validated = self._validate_flashcards(flashcards)
            if validated:
                logger.info(f"Extracted {len(validated)} flashcards using line strategy")
            
            return validated
            
        except Exception as e:
            logger.debug(f"Line strategy error: {e}")
            return []
    
    def _validate_flashcards(self, flashcards: List[Any]) -> List[Dict]:
        """Validate and clean flashcard data"""
        valid_flashcards = []
        
        for card in flashcards:
            if not isinstance(card, dict):
                continue
            
            if 'question' not in card or 'answer' not in card:
                continue
            
            cleaned_card = {
                'question': str(card.get('question', '')).strip(),
                'answer': str(card.get('answer', '')).strip(),
                'concept': str(card.get('concept', 'General')).strip(),
                'difficulty': str(card.get('difficulty', 'intermediate')).strip().lower()
            }
            
            if (len(cleaned_card['question']) > 10 and 
                len(cleaned_card['answer']) > 10 and
                len(cleaned_card['question']) < 300 and
                len(cleaned_card['answer']) < 500):
                valid_flashcards.append(cleaned_card)
        
        logger.info(f"Validated {len(valid_flashcards)} flashcards")
        return valid_flashcards
    
    def _calculate_quality_score(self, flashcards: List[Dict]) -> float:
        """Calculate quality score based on flashcard characteristics"""
        if not flashcards:
            return 0.0
        
        total_score = 0
        for card in flashcards:
            score = 0.5
            
            if len(card['question'].split()) >= 5:
                score += 0.2
            if '?' in card['question']:
                score += 0.1
            
            if len(card['answer'].split()) >= 8:
                score += 0.2
            
            total_score += min(score, 1.0)
        
        return round(total_score / len(flashcards), 2)
    
    def _create_fallback_flashcards(self, text: str, params: Dict) -> Dict:
        """Create simple flashcards when Gemini is unavailable"""
        try:
            num_cards = min(params.get('num_flashcards', Config.DEFAULT_FLASHCARD_COUNT), 8)
            return create_basic_flashcards(text, num_cards)
        except Exception as e:
            logger.error(f"Fallback flashcard creation error: {e}")
            return {
                "error": "Failed to create flashcards",
                "fallback_used": True
            }

def create_gemini_flashcard_generator() -> GeminiFlashcardGenerator:
    """Factory function to create Gemini flashcard generator"""
    return GeminiFlashcardGenerator()

def get_gemini_generator() -> GeminiFlashcardGenerator:
    """Get global instance for backward compatibility"""
    global _global_gemini_generator
    if '_global_gemini_generator' not in globals():
        _global_gemini_generator = GeminiFlashcardGenerator()
    return _global_gemini_generator

# Global Instance
gemini_generator = get_gemini_generator()