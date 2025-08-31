import re
from typing import List, Dict
from config import Config

def simple_key_extraction(text: str) -> List[str]:
    """Basic keyword extraction fallback."""
    words = text.lower().split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
    word_freq = {}
    for word in words:
        word = word.strip('.,!?;:"()[]').lower()
        if len(word) > 3 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word[0] for word in sorted_words[:Config.MAX_KEY_PHRASES if hasattr(Config, "MAX_KEY_PHRASES") else 15]]

def simple_extractive_summary(text: str) -> str:
    """Simple fallback summary."""
    sentences = text.split('.')
    if len(sentences) > 6:
        summary_sentences = sentences[:3] + sentences[-2:]
    else:
        summary_sentences = sentences[:min(4, len(sentences))]
    return ". ".join([s.strip() for s in summary_sentences if len(s.strip()) > 10])

def create_basic_flashcards(text: str, num_cards: int = None) -> Dict:
    """Create simple definition-style flashcards as fallback."""
    if num_cards is None:
        num_cards = Config.DEFAULT_FLASHCARD_COUNT if hasattr(Config, "DEFAULT_FLASHCARD_COUNT") else 5
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    fallback_flashcards = []
    for i, sentence in enumerate(sentences[:num_cards]):
        words = sentence.split()
        key_terms = [word for word in words if word[0].isupper() and len(word) > 3]
        if key_terms:
            term = key_terms[0]
            question = f"What is {term}?"
            answer = sentence.strip()
        else:
            if len(words) > 8:
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
            "quality_score": 0.6
        },
        "success": True,
        "fallback_used": True
    }