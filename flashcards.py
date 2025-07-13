import logging
import re
import json
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiFlashcardGenerator:
    """
    ENHANCED: Google Gemini AI flashcard generator with educational focus
    
    Generates comprehensive flashcards optimized for study materials
    """
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini AI client"""
        try:
            if Config.GEMINI_API_KEY:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
                self.is_available = True
                logger.info("Gemini AI client initialized successfully")
            else:
                logger.warning("Gemini API key not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.is_available = False
    
    def generate_enhanced_flashcards(self, 
                                   text: str, 
                                   generation_params: Dict, 
                                   progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict:
        """
        ENHANCED: Generate flashcards with educational parameters
        
        Args:
            text: Source text for flashcard generation
            generation_params: Dictionary with generation settings
            progress_callback: Optional progress callback (message, progress)
            
        Returns:
            Dict with flashcards and metadata
        """
        
        if not self.is_available:
            return self._create_error_response("Gemini AI not available")
        
        try:
            if progress_callback:
                progress_callback("🤖 Initializing Gemini AI for flashcard generation...", 0.1)
            
            # Extract parameters
            num_flashcards = generation_params.get('num_flashcards', 10)
            difficulty_focus = generation_params.get('difficulty_focus', 'Mixed (Recommended)')
            key_phrases = generation_params.get('key_phrases', [])
            educational_concepts = generation_params.get('educational_concepts', {})
            study_assessment = generation_params.get('study_assessment', {})
            
            if progress_callback:
                progress_callback("📝 Preparing educational content analysis...", 0.3)
            
            # Create enhanced prompt
            prompt = self._create_enhanced_educational_prompt(
                text, num_flashcards, difficulty_focus, key_phrases, educational_concepts
            )
            
            if progress_callback:
                progress_callback("🧠 Generating flashcards with Gemini AI...", 0.6)
            
            # Generate with Gemini
            response = self.client.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            if progress_callback:
                progress_callback("🔍 Processing and validating flashcards...", 0.8)
            
            # Parse and validate response
            flashcards = self._parse_gemini_flashcards(response.text)
            
            if not flashcards:
                return self._create_fallback_flashcards(text, key_phrases)
            
            if progress_callback:
                progress_callback("✅ Flashcard generation completed!", 1.0)
            
            # Create success response
            return {
                "status": "success",
                "flashcards": flashcards,
                "metadata": {
                    "total_generated": len(flashcards),
                    "avg_difficulty": difficulty_focus,
                    "topic_coverage": "Comprehensive",
                    "generation_method": "gemini_enhanced",
                    "key_concepts_used": len(key_phrases),
                    "educational_focus": True
                },
                "generation_metadata": {
                    "generation_method": "ai",
                    "quality_score": 0.9,
                    "source": "gemini_1.5_flash"
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced flashcard generation error: {e}")
            return self._create_fallback_flashcards(text, key_phrases)
    
    def generate_comprehensive_flashcards(self,
                                        text: str,
                                        summary_data: Dict,
                                        key_phrases: List[str],
                                        progress_callback: Optional[Callable[[str], None]] = None) -> Dict:
        """
        COMPREHENSIVE: Generate organized flashcards (legacy method for compatibility)
        
        Args:
            text: Source text
            summary_data: Summary information
            key_phrases: Key phrases for focus
            progress_callback: Progress callback (single parameter)
            
        Returns:
            Dict with organized flashcards
        """
        
        if not self.is_available:
            return self._create_fallback_flashcards(text, key_phrases)
        
        try:
            if progress_callback:
                progress_callback("🤖 Starting comprehensive flashcard generation...")
            
            # Create comprehensive prompt
            prompt = self._create_comprehensive_prompt(text, summary_data, key_phrases, 10)
            
            if progress_callback:
                progress_callback("🧠 Processing with Gemini AI...")
            
            # Generate with Gemini
            response = self.client.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            if progress_callback:
                progress_callback("🔍 Organizing flashcards by categories...")
            
            # Parse comprehensive response
            organized_flashcards = self._parse_comprehensive_flashcards(response.text)
            
            if not organized_flashcards:
                return self._create_fallback_flashcards(text, key_phrases)
            
            if progress_callback:
                progress_callback("✅ Comprehensive flashcard generation completed!")
            
            return {
                "status": "success",
                "flashcards": organized_flashcards,
                "generation_metadata": {
                    "generation_method": "ai",
                    "quality_score": 0.85,
                    "source": "gemini_comprehensive"
                }
            }
            
        except Exception as e:
            logger.error(f"Comprehensive flashcard generation error: {e}")
            return self._create_fallback_flashcards(text, key_phrases)
    
    def generate_fallback_flashcards(self, text: str) -> Dict:
        """
        FALLBACK: Generate basic flashcards (for app.py compatibility)
        
        Args:
            text: Source text
            
        Returns:
            Dict with basic flashcards
        """
        return self._create_fallback_flashcards(text, [])
    
    def _create_enhanced_educational_prompt(self, 
                                          text: str, 
                                          num_flashcards: int, 
                                          difficulty_focus: str, 
                                          key_phrases: List[str], 
                                          educational_concepts: Dict) -> str:
        """Create enhanced educational prompt for Gemini"""
        
        key_phrases_text = ", ".join(key_phrases[:10]) if key_phrases else "general concepts"
        
        difficulty_instruction = {
            "Basic Concepts": "Focus on fundamental definitions and simple explanations",
            "Advanced Topics": "Create challenging questions requiring deeper understanding",
            "Application-Based": "Focus on practical applications and real-world scenarios",
            "Mixed (Recommended)": "Include a variety of difficulty levels from basic to advanced"
        }.get(difficulty_focus, "Include a variety of difficulty levels")
        
        return f"""
You are an expert educational content creator specializing in study materials. Create {num_flashcards} high-quality flashcards from the following educational content.

**EDUCATIONAL CONTENT:**
{text[:4000]}

**KEY CONCEPTS TO FOCUS ON:**
{key_phrases_text}

**DIFFICULTY INSTRUCTIONS:**
{difficulty_instruction}

**FLASHCARD REQUIREMENTS:**
1. Create exactly {num_flashcards} flashcards
2. Each flashcard must have a clear, specific question and a comprehensive answer
3. Questions should test understanding, not just memorization
4. Answers should be educational and informative (2-4 sentences)
5. Cover the most important concepts from the content
6. Ensure variety in question types (definitions, explanations, applications, comparisons)
7. Make questions engaging and thought-provoking

**OUTPUT FORMAT:**
Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Clear, specific question here",
    "answer": "Comprehensive answer here",
    "concept": "Main concept being tested",
    "difficulty": "basic|medium|advanced"
  }}
]

**IMPORTANT:**
- Return ONLY the JSON array, no other text
- Ensure all JSON is properly formatted and valid
- Each question should be unique and meaningful
- Focus on educational value and learning outcomes

Generate the flashcards now:
"""
    
    def _create_comprehensive_prompt(self, 
                                   text: str, 
                                   summary_data: Dict, 
                                   key_phrases: List[str], 
                                   num_cards: int) -> str:
        """Create comprehensive prompt for organized flashcards"""
        
        summary_text = ""
        if isinstance(summary_data, dict):
            summary_text = summary_data.get('best', '') or summary_data.get('educational', '') or str(summary_data)
        else:
            summary_text = str(summary_data)
        
        key_phrases_text = ", ".join(key_phrases[:8]) if key_phrases else "main concepts"
        
        return f"""
You are an educational content expert. Create {num_cards} comprehensive flashcards organized by categories from this content.

**CONTENT:**
{text[:3000]}

**SUMMARY:**
{summary_text[:500]}

**KEY CONCEPTS:**
{key_phrases_text}

**REQUIREMENTS:**
1. Create exactly {num_cards} flashcards total
2. Organize into 2-3 relevant categories
3. Each flashcard needs question, answer, and concept
4. Focus on the most important educational content
5. Ensure variety in difficulty and question types

**OUTPUT FORMAT (JSON only):**
{{
  "fundamental_concepts": [
    {{
      "question": "Question here",
      "answer": "Answer here", 
      "concept": "Concept name"
    }}
  ],
  "advanced_topics": [
    {{
      "question": "Question here",
      "answer": "Answer here",
      "concept": "Concept name" 
    }}
  ]
}}

Generate the organized flashcards:
"""
    
    def _parse_gemini_flashcards(self, response_text: str) -> List[Dict]:
        """Parse Gemini response into flashcard list"""
        try:
            # Clean the response
            cleaned_text = self._clean_json_response(response_text)
            
            # Try to parse as JSON
            flashcards_data = json.loads(cleaned_text)
            
            if isinstance(flashcards_data, list):
                # Validate and clean flashcards
                valid_flashcards = []
                for card in flashcards_data:
                    if isinstance(card, dict) and 'question' in card and 'answer' in card:
                        valid_card = {
                            'question': str(card.get('question', '')).strip(),
                            'answer': str(card.get('answer', '')).strip(),
                            'concept': str(card.get('concept', 'General')).strip(),
                            'difficulty': str(card.get('difficulty', 'medium')).strip()
                        }
                        if valid_card['question'] and valid_card['answer']:
                            valid_flashcards.append(valid_card)
                
                return valid_flashcards
            
            return []
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            return self._extract_flashcards_from_text(response_text)
        except Exception as e:
            logger.error(f"Flashcard parsing error: {e}")
            return []
    
    def _parse_comprehensive_flashcards(self, response_text: str) -> Dict:
        """Parse comprehensive flashcards into organized structure"""
        try:
            # Clean the response
            cleaned_text = self._clean_json_response(response_text)
            
            # Try to parse as JSON
            organized_data = json.loads(cleaned_text)
            
            if isinstance(organized_data, dict):
                # Validate structure
                valid_organized = {}
                for category, cards in organized_data.items():
                    if isinstance(cards, list):
                        valid_cards = []
                        for card in cards:
                            if isinstance(card, dict) and 'question' in card and 'answer' in card:
                                valid_card = {
                                    'question': str(card.get('question', '')).strip(),
                                    'answer': str(card.get('answer', '')).strip(),
                                    'concept': str(card.get('concept', category)).strip()
                                }
                                if valid_card['question'] and valid_card['answer']:
                                    valid_cards.append(valid_card)
                        
                        if valid_cards:
                            valid_organized[category] = valid_cards
                
                return valid_organized
            
            return {}
            
        except json.JSONDecodeError as e:
            logger.warning(f"Comprehensive JSON parsing failed: {e}")
            # Fallback to simple list format
            simple_cards = self._extract_flashcards_from_text(response_text)
            if simple_cards:
                return {"general_concepts": simple_cards}
            return {}
        except Exception as e:
            logger.error(f"Comprehensive parsing error: {e}")
            return {}
    
    def _clean_json_response(self, text: str) -> str:
        """Clean Gemini response for JSON parsing"""
        # Remove code block markers
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Find JSON array or object
        json_match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text.strip()
    
    def _extract_flashcards_from_text(self, text: str) -> List[Dict]:
        """Extract flashcards from unstructured text"""
        flashcards = []
        
        # Look for Q&A patterns
        qa_patterns = [
            r'Q(?:uestion)?:\s*(.+?)\s*A(?:nswer)?:\s*(.+?)(?=Q(?:uestion)?:|$)',
            r'(\d+)\.\s*(.+?)\s*(?:Answer|A):\s*(.+?)(?=\d+\.|$)',
            r'Question:\s*(.+?)\s*Answer:\s*(.+?)(?=Question:|$)'
        ]
        
        for pattern in qa_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    question = match[-2].strip()
                    answer = match[-1].strip()
                    
                    if len(question) > 10 and len(answer) > 10:
                        flashcards.append({
                            'question': question,
                            'answer': answer,
                            'concept': 'General',
                            'difficulty': 'medium'
                        })
        
        return flashcards[:15]  # Limit extracted cards
    
    def _create_fallback_flashcards(self, text: str, key_phrases: List[str]) -> Dict:
        """Create fallback flashcards when AI generation fails"""
        
        # Simple rule-based flashcard generation
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        fallback_cards = []
        
        # Create basic definition cards from key phrases
        for phrase in key_phrases[:5]:
            # Find sentences containing the phrase
            relevant_sentences = [s for s in sentences if phrase.lower() in s.lower()]
            if relevant_sentences:
                context = relevant_sentences[0]
                fallback_cards.append({
                    'question': f"What is {phrase}?",
                    'answer': context,
                    'concept': phrase,
                    'difficulty': 'basic'
                })
        
        # Create general comprehension cards
        if len(sentences) >= 3:
            fallback_cards.append({
                'question': "What is the main topic of this content?",
                'answer': " ".join(sentences[:2]),
                'concept': 'Main Topic',
                'difficulty': 'basic'
            })
        
        # Ensure minimum number of cards
        while len(fallback_cards) < 5 and len(sentences) > len(fallback_cards):
            sentence = sentences[len(fallback_cards)]
            if len(sentence) > 30:
                fallback_cards.append({
                    'question': f"Explain the concept: {sentence[:50]}...",
                    'answer': sentence,
                    'concept': 'General Knowledge',
                    'difficulty': 'medium'
                })
        
        return {
            "status": "fallback",
            "flashcards": fallback_cards,
            "generation_metadata": {
                "generation_method": "fallback",
                "quality_score": 0.6,
                "source": "rule_based"
            }
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            "status": "error",
            "error": error_message,
            "flashcards": [],
            "generation_metadata": {
                "generation_method": "error",
                "quality_score": 0.0,
                "source": "none"
            }
        }
        
        #Create global instance
gemini_flashcard_generator = GeminiFlashcardGenerator()