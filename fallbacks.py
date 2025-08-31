import re
import logging
from typing import List, Dict
from collections import Counter
from config import Config

logger = logging.getLogger(__name__)

def simple_key_extraction(text: str) -> List[str]:
    """Enhanced keyword extraction fallback with improved algorithm"""
    try:
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for key extraction")
            return []
        
        logger.info("Using fallback key extraction method")
        
        # Convert to lowercase and split
        words = text.lower().split()
        
        # Enhanced stop words list for better filtering
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'it', 'they', 'them', 'their', 'there', 'then', 'than', 'when', 'where',
            'why', 'how', 'what', 'who', 'which', 'said', 'say', 'says', 'get', 'got', 'go', 'goes',
            'went', 'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'take', 'took',
            'make', 'made', 'give', 'gave', 'find', 'found', 'use', 'used', 'work', 'works', 'worked'
        }
        
        # Clean and filter words
        cleaned_words = []
        for word in words:
            # Remove punctuation and convert to lowercase
            cleaned_word = re.sub(r'[^\w]', '', word).lower()
            
            # Filter criteria: length > 3, not a stop word, contains letters
            if (len(cleaned_word) > 3 and 
                cleaned_word not in stop_words and 
                re.search(r'[a-zA-Z]', cleaned_word) and
                not cleaned_word.isdigit()):
                cleaned_words.append(cleaned_word)
        
        # Count word frequencies using Counter for better performance
        word_freq = Counter(cleaned_words)
        
        # Get top words, using the correct config reference
        max_phrases = Config.MAX_KEY_PHRASES
        top_words = [word for word, freq in word_freq.most_common(max_phrases)]
        
        logger.info(f"Extracted {len(top_words)} key phrases using fallback method")
        return top_words
        
    except Exception as e:
        logger.error(f"Key extraction fallback failed: {e}")
        return []

def simple_extractive_summary(text: str) -> str:
    """Enhanced fallback summary with intelligent sentence selection"""
    try:
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for meaningful summary")
            return text.strip() if text else "No content available for summary."
        
        logger.info("Using fallback extractive summary method")
        
        # Split into sentences more intelligently
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]  # Filter very short sentences
        
        if len(sentences) <= 2:
            # If very few sentences, return as-is
            return ". ".join(sentences).strip() + "."
        
        # Score sentences based on multiple factors
        scored_sentences = []
        total_words = len(text.split())
        
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_words = sentence.lower().split()
            
            # Factor 1: Position scoring (first and last sentences often important)
            if i == 0:  # First sentence
                score += 3
            elif i == len(sentences) - 1:  # Last sentence
                score += 2
            elif i < len(sentences) * 0.3:  # Early sentences
                score += 1
            
            # Factor 2: Length scoring (not too short, not too long)
            word_count = len(sentence_words)
            if 10 <= word_count <= 25:  # Optimal length
                score += 2
            elif 6 <= word_count <= 35:  # Acceptable length
                score += 1
            
            # Factor 3: Important word indicators
            important_indicators = [
                'important', 'key', 'main', 'primary', 'essential', 'crucial', 
                'significant', 'major', 'fundamental', 'critical', 'vital',
                'conclusion', 'result', 'therefore', 'thus', 'summary',
                'in summary', 'to conclude', 'overall'
            ]
            
            for indicator in important_indicators:
                if indicator in sentence.lower():
                    score += 2
                    break
            
            # Factor 4: Avoid sentences that are too generic
            generic_patterns = ['this is', 'there are', 'it is', 'we can see']
            is_generic = any(pattern in sentence.lower() for pattern in generic_patterns)
            if is_generic:
                score -= 1
            
            scored_sentences.append((sentence, score, i))
        
        # Sort by score (descending) and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select sentences based on document length
        if len(sentences) > 10:
            num_sentences = min(4, len(scored_sentences))
        elif len(sentences) > 6:
            num_sentences = min(3, len(scored_sentences))
        else:
            num_sentences = min(2, len(scored_sentences))
        
        # Get top sentences and sort them back to original order
        selected_sentences = sorted(
            scored_sentences[:num_sentences], 
            key=lambda x: x[2]  # Sort by original position
        )
        
        summary = ". ".join([s[0] for s in selected_sentences]) + "."
        
        # Clean up the summary
        summary = re.sub(r'\s+', ' ', summary)  # Multiple spaces
        summary = re.sub(r'\.+', '.', summary)  # Multiple dots
        
        logger.info(f"Created fallback summary from {len(sentences)} sentences -> {len(selected_sentences)} sentences")
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Summary fallback failed: {e}")
        # Return first few sentences as emergency fallback
        emergency_sentences = text.split('.')[:2]
        return ". ".join([s.strip() for s in emergency_sentences if s.strip()]) + "."

def create_basic_flashcards(text: str, num_cards: int = None) -> Dict:
    """Enhanced fallback flashcard creation with improved algorithms"""
    try:
        if num_cards is None:
            num_cards = Config.DEFAULT_FLASHCARD_COUNT
        
        if not text or len(text.strip()) < 30:
            logger.warning("Text too short for flashcard generation")
            return _create_emergency_flashcard(text)
        
        logger.info(f"Using fallback flashcard generation for {num_cards} cards")
        
        # Split into sentences more intelligently
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 25]  # Minimum viable sentence length
        
        if not sentences:
            return _create_emergency_flashcard(text)
        
        fallback_flashcards = []
        used_concepts = set()  # Avoid duplicate concepts
        
        for i, sentence in enumerate(sentences[:num_cards * 2]):  # Process more sentences for better selection
            if len(fallback_flashcards) >= num_cards:
                break
                
            card = _create_flashcard_from_sentence(sentence, i, used_concepts)
            if card:
                fallback_flashcards.append(card)
                used_concepts.add(card['concept'])
        
        # If we don't have enough cards, create additional ones with different strategies
        while len(fallback_flashcards) < min(num_cards, len(sentences)):
            remaining_sentences = sentences[len(fallback_flashcards):]
            if not remaining_sentences:
                break
                
            # Use definition-style questions for remaining sentences
            sentence = remaining_sentences[0]
            card = _create_definition_card(sentence, len(fallback_flashcards))
            if card and card['concept'] not in used_concepts:
                fallback_flashcards.append(card)
                used_concepts.add(card['concept'])
            else:
                break
        
        # Ensure we have at least one card
        if not fallback_flashcards:
            fallback_flashcards = [_create_emergency_flashcard(text)['flashcards'][0]]
        
        # Calculate quality score based on card characteristics
        quality_score = _calculate_fallback_quality_score(fallback_flashcards)
        
        logger.info(f"Generated {len(fallback_flashcards)} fallback flashcards with quality score {quality_score}")
        
        return {
            "flashcards": fallback_flashcards,
            "generation_metadata": {
                "total_generated": len(fallback_flashcards),
                "method": "enhanced_fallback_generation",
                "quality_score": quality_score,
                "source_sentences": len(sentences),
                "strategies_used": _get_strategies_used(fallback_flashcards)
            },
            "success": True,
            "fallback_used": True
        }
        
    except Exception as e:
        logger.error(f"Enhanced flashcard fallback failed: {e}")
        return _create_emergency_flashcard(text)

def _create_flashcard_from_sentence(sentence: str, index: int, used_concepts: set) -> Dict:
    """Create a flashcard from a single sentence using multiple strategies"""
    
    words = sentence.split()
    if len(words) < 4:
        return None
    
    # Strategy 1: Find proper nouns (capitalized words that aren't at sentence start)
    capitalized_terms = []
    for i, word in enumerate(words):
        if (i > 0 and word[0].isupper() and len(word) > 3 and 
            not word.isupper() and word.isalpha()):
            capitalized_terms.append(word)
    
    if capitalized_terms:
        term = capitalized_terms[0]
        if term.lower() not in used_concepts:
            return {
                'question': f"What is {term} according to this material?",
                'answer': sentence.strip(),
                'concept': term,
                'difficulty': 'basic',
                'strategy': 'proper_noun'
            }
    
    # Strategy 2: Look for definition patterns
    definition_patterns = [
        r'(.+?)\s+is\s+(.+)',
        r'(.+?)\s+are\s+(.+)',
        r'(.+?)\s+means\s+(.+)',
        r'(.+?)\s+refers to\s+(.+)',
        r'(.+?):\s*(.+)'  # Colon definitions
    ]
    
    for pattern in definition_patterns:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            
            if (len(term.split()) <= 4 and len(definition.split()) >= 3 and
                term.lower() not in used_concepts):
                return {
                    'question': f"Define: {term}",
                    'answer': definition,
                    'concept': term.title(),
                    'difficulty': 'intermediate',
                    'strategy': 'definition_pattern'
                }
    
    # Strategy 3: Fill-in-the-blank for important words
    important_words = []
    for word in words:
        if (len(word) > 5 and word.lower() not in ['because', 'through', 'however', 'therefore'] and
            not word.lower() in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'was', 'one']):
            important_words.append(word)
    
    if important_words and len(words) > 8:
        # Choose a word from the middle portion of the sentence
        middle_words = important_words[len(important_words)//4:3*len(important_words)//4]
        if middle_words:
            blank_word = middle_words[0]
            concept_name = blank_word if len(blank_word) > 3 else f"Concept {index + 1}"
            
            if concept_name.lower() not in used_concepts:
                sentence_with_blank = sentence.replace(blank_word, "______", 1)
                return {
                    'question': f"Fill in the blank: {sentence_with_blank}",
                    'answer': f"The missing word is: **{blank_word}**. Complete sentence: {sentence}",
                    'concept': concept_name.title(),
                    'difficulty': 'intermediate',
                    'strategy': 'fill_blank'
                }
    
    # Strategy 4: Concept explanation for complex sentences
    if len(words) >= 12:
        concept_name = f"Concept {index + 1}"
        if concept_name not in used_concepts:
            return {
                'question': f"Explain this key concept: {sentence[:60]}...",
                'answer': sentence.strip(),
                'concept': concept_name,
                'difficulty': 'advanced',
                'strategy': 'concept_explanation'
            }
    
    return None

def _create_definition_card(sentence: str, index: int) -> Dict:
    """Create a definition-style card from any sentence"""
    words = sentence.split()
    if len(words) < 6:
        return None
        
    # Extract potential key terms (longer words, not common words)
    potential_terms = [
        word.strip('.,!?;:"()[]') for word in words 
        if len(word) > 5 and word.lower() not in [
            'because', 'however', 'therefore', 'through', 'without', 'between', 
            'during', 'before', 'after', 'within', 'around', 'should', 'could', 'would'
        ]
    ]
    
    if potential_terms:
        term = potential_terms[0]
        return {
            'question': f"What can you tell me about {term.lower()}?",
            'answer': sentence.strip(),
            'concept': term.title(),
            'difficulty': 'basic',
            'strategy': 'general_definition'
        }
    
    return {
        'question': f"Explain this concept from the material:",
        'answer': sentence.strip(),
        'concept': f"General Concept {index + 1}",
        'difficulty': 'basic',
        'strategy': 'general_explanation'
    }

def _create_emergency_flashcard(text: str) -> Dict:
    """Create minimal flashcard when all else fails"""
    logger.warning("Creating emergency fallback flashcard")
    
    preview = text[:150] + "..." if len(text) > 150 else text
    
    return {
        "flashcards": [{
            'question': 'What is the main topic of this study material?',
            'answer': preview,
            'concept': 'Main Topic',
            'difficulty': 'basic',
            'strategy': 'emergency_fallback'
        }],
        "generation_metadata": {
            "total_generated": 1,
            "method": "emergency_fallback",
            "quality_score": 0.3
        },
        "success": True,
        "fallback_used": True
    }

def _calculate_fallback_quality_score(flashcards: List[Dict]) -> float:
    """Calculate quality score for fallback flashcards"""
    if not flashcards:
        return 0.0
    
    total_score = 0
    for card in flashcards:
        score = 0.4  # Base score for fallback
        
        # Question quality factors
        if len(card['question'].split()) >= 5:
            score += 0.1
        if any(word in card['question'].lower() for word in ['what', 'how', 'why', 'explain', 'define']):
            score += 0.1
        
        # Answer quality factors  
        if len(card['answer'].split()) >= 8:
            score += 0.2
        if len(card['answer'].split()) <= 50:  # Not too long
            score += 0.1
        
        # Strategy bonus
        strategy_bonus = {
            'definition_pattern': 0.2,
            'proper_noun': 0.15,
            'fill_blank': 0.1,
            'concept_explanation': 0.05,
            'general_definition': 0.0,
            'emergency_fallback': -0.1
        }
        score += strategy_bonus.get(card.get('strategy', ''), 0)
        
        total_score += min(score, 1.0)
    
    return round(total_score / len(flashcards), 2)

def _get_strategies_used(flashcards: List[Dict]) -> List[str]:
    """Get list of strategies used in flashcard generation"""
    strategies = []
    for card in flashcards:
        strategy = card.get('strategy', 'unknown')
        if strategy not in strategies:
            strategies.append(strategy)
    return strategies