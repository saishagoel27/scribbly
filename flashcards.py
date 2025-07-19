import logging
import json
import re
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiFlashcardGenerator:
    """Simplified Gemini AI flashcard generator - no over-engineering"""
    
    def __init__(self):
        """Initialize Gemini AI client"""
        self.model = None
        self.available = False
        
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                
                # Simple model configuration
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4096,
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
                
                self.available = True
                logger.info("Gemini AI initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            logger.warning("Gemini API key not found")
    
    def generate_enhanced_flashcards(self, text: str, generation_params: Dict, 
                                   progress_callback: Optional[Callable] = None) -> Dict:
        """Main flashcard generation method - simplified but effective"""
        
        if not self.available:
            return self._create_fallback_flashcards(text, generation_params)
        
        try:
            if progress_callback:
                progress_callback("🧠 Analyzing content for flashcard generation...", 0.1)
            
            # Clean and prepare text
            cleaned_text = self._clean_text_for_processing(text)
            
            if len(cleaned_text.split()) < 50:
                return {"error": "Text too short for meaningful flashcards"}
            
            if progress_callback:
                progress_callback("📝 Creating optimized prompt...", 0.3)
            
            # Create single, effective prompt
            prompt = self._create_flashcard_prompt(cleaned_text, generation_params)
            
            if progress_callback:
                progress_callback("🤖 Generating flashcards with Gemini AI...", 0.5)
            
            # Generate with Gemini
            response = self.model.generate_content(prompt)
            
            if progress_callback:
                progress_callback("📋 Processing flashcard data...", 0.8)
            
            # Parse response
            flashcards = self._parse_flashcard_response(response.text)
            
            if not flashcards:
                logger.warning("No flashcards parsed, using fallback")
                return self._create_fallback_flashcards(text, generation_params)
            
            if progress_callback:
                progress_callback("✅ Flashcards generated successfully!", 1.0)
            
            return {
                "flashcards": flashcards,
                "generation_metadata": {
                    "total_generated": len(flashcards),
                    "method": "gemini_ai",
                    "quality_score": 0.9,  # Simple default
                    "timestamp": datetime.now().isoformat()
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Gemini flashcard generation error: {e}")
            return self._create_fallback_flashcards(text, generation_params)
    
    def _clean_text_for_processing(self, text: str) -> str:
        """Simple text cleaning for flashcard generation"""
        # Remove excessive whitespace and clean formatting
        cleaned = re.sub(r'\s+', ' ', text)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Limit text length for Gemini (keep most important parts)
        max_words = 1000
        words = cleaned.split()
        if len(words) > max_words:
            # Take first 70% and last 30% to preserve context
            first_part = words[:int(max_words * 0.7)]
            last_part = words[-int(max_words * 0.3):]
            cleaned = ' '.join(first_part + ['...'] + last_part)
        
        return cleaned
    
    def _create_flashcard_prompt(self, text: str, params: Dict) -> str:
        """Create effective prompt for Gemini AI"""
        
        num_cards = params.get('num_flashcards', 10)
        difficulty = params.get('difficulty_focus', 'Mixed (Recommended)')
        key_phrases = params.get('key_phrases', [])
        
        # Map difficulty to instruction
        difficulty_instructions = {
            'Basic Concepts': 'Focus on fundamental concepts and definitions. Keep questions simple and clear.',
            'Advanced Topics': 'Create challenging questions that test deep understanding and application.',
            'Application-Based': 'Focus on practical applications and real-world scenarios.',
            'Mixed (Recommended)': 'Mix basic concepts, intermediate understanding, and some application questions.'
        }
        
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions['Mixed (Recommended)'])
        
        # Include key phrases if available
        key_phrases_text = ""
        if key_phrases:
            key_phrases_text = f"\n\nKey concepts to focus on: {', '.join(key_phrases[:10])}"
        
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
        """Parse Gemini response into flashcard list"""
        try:
            # Clean the response text
            cleaned_response = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in cleaned_response:
                cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
                cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
            elif '```' in cleaned_response:
                cleaned_response = re.sub(r'```\s*', '', cleaned_response)
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                json_text = cleaned_response
            
            # Parse JSON
            parsed_data = json.loads(json_text)
            
            # Extract flashcards
            if isinstance(parsed_data, dict):
                flashcards = parsed_data.get('flashcards', [])
            elif isinstance(parsed_data, list):
                flashcards = parsed_data
            else:
                return []
            
            # Validate and clean flashcards
            valid_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    # Clean and validate required fields
                    cleaned_card = {
                        'question': str(card.get('question', '')).strip(),
                        'answer': str(card.get('answer', '')).strip(),
                        'concept': str(card.get('concept', 'General')).strip(),
                        'difficulty': str(card.get('difficulty', 'intermediate')).strip().lower()
                    }
                    
                    # Only include cards with meaningful content
                    if (len(cleaned_card['question']) > 10 and 
                        len(cleaned_card['answer']) > 10):
                        valid_flashcards.append(cleaned_card)
            
            logger.info(f"Successfully parsed {len(valid_flashcards)} flashcards")
            return valid_flashcards
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._extract_flashcards_from_text(response_text)
        
        except Exception as e:
            logger.error(f"Flashcard parsing error: {e}")
            return self._extract_flashcards_from_text(response_text)
    
    def _extract_flashcards_from_text(self, response_text: str) -> List[Dict]:
        """Fallback: extract flashcards from unstructured text"""
        try:
            flashcards = []
            
            # Look for Q: and A: patterns
            qa_pattern = r'(?:Q:|Question:|question:)\s*(.+?)(?:A:|Answer:|answer:)\s*(.+?)(?=(?:Q:|Question:|question:)|$)'
            matches = re.findall(qa_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
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
                logger.info(f"Extracted {len(flashcards)} flashcards from text fallback")
                return flashcards
            
            return []
            
        except Exception as e:
            logger.error(f"Text extraction fallback error: {e}")
            return []
    
    def _create_fallback_flashcards(self, text: str, params: Dict) -> Dict:
        """Create simple flashcards when Gemini is unavailable"""
        try:
            num_cards = min(params.get('num_flashcards', 10), 8)  # Limit for fallback
            
            # Split text into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
            
            fallback_flashcards = []
            
            # Create simple definition-style flashcards
            for i, sentence in enumerate(sentences[:num_cards]):
                # Extract potential key terms (simple heuristic)
                words = sentence.split()
                
                # Look for capitalized words or phrases that might be important
                key_terms = [word for word in words if word[0].isupper() and len(word) > 3]
                
                if key_terms:
                    term = key_terms[0]
                    question = f"What is {term}?"
                    answer = sentence.strip()
                else:
                    # Create a fill-in-the-blank style question
                    if len(words) > 8:
                        # Remove a key word from the middle
                        blank_index = len(words) // 2
                        blank_word = words[blank_index]
                        question_words = words.copy()
                        question_words[blank_index] = "______"
                        question = f"Fill in the blank: {' '.join(question_words)}"
                        answer = f"The missing word is: {blank_word}. Complete sentence: {sentence}"
                    else:
                        question = f"Explain this concept: {sentence[:50]}..."
                        answer = sentence.strip()
                
                fallback_flashcards.append({
                    'question': question,
                    'answer': answer,
                    'concept': f'Concept {i+1}',
                    'difficulty': 'basic'
                })
            
            if not fallback_flashcards:
                # Ultimate fallback - create basic questions
                fallback_flashcards = [
                    {
                        'question': 'What is the main topic of this material?',
                        'answer': text[:200] + "..." if len(text) > 200 else text,
                        'concept': 'Main Topic',
                        'difficulty': 'basic'
                    }
                ]
            
            return {
                "flashcards": fallback_flashcards,
                "generation_metadata": {
                    "total_generated": len(fallback_flashcards),
                    "method": "fallback_generation",
                    "quality_score": 0.6,
                    "timestamp": datetime.now().isoformat()
                },
                "success": True,
                "fallback_used": True
            }
            
        except Exception as e:
            logger.error(f"Fallback flashcard creation error: {e}")
            return {
                "error": "Failed to create flashcards",
                "fallback_used": True
            }
    
    def generate_fallback_flashcards(self, text: str) -> Dict:
        """Simple public fallback method for external use"""
        return self._create_fallback_flashcards(text, {'num_flashcards': 5})

# Create global instance
gemini_generator = GeminiFlashcardGenerator()