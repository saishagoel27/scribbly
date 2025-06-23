import os
import docx
import pdfplumber 
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
from dotenv import load_dotenv
import random
import logging
import streamlit as st
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Loading API keys from .env
load_dotenv()

# Text Analytics credentials (existing)
text_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
text_key = os.getenv("AZURE_LANGUAGE_KEY")

# Document Intelligence credentials (new)
doc_intel_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

# Validate environment variables
if not text_endpoint or not text_key:
    logger.error("Azure Text Analytics credentials not found in environment variables")
    st.error("⚠️ Azure Text Analytics credentials not configured. Please check your .env file.")

if not doc_intel_endpoint or not doc_intel_key:
    logger.warning("Azure Document Intelligence credentials not found. Image processing will be limited.")

# Setup Azure clients with error handling
try:
    text_client = TextAnalyticsClient(endpoint=text_endpoint, credential=AzureKeyCredential(text_key))
except Exception as e:
    logger.error(f"Failed to initialize Azure Text Analytics client: {e}")
    text_client = None

try:
    if doc_intel_endpoint and doc_intel_key:
        document_client = DocumentAnalysisClient(endpoint=doc_intel_endpoint, credential=AzureKeyCredential(doc_intel_key))
    else:
        document_client = None
except Exception as e:
    logger.error(f"Failed to initialize Azure Document Intelligence client: {e}")
    document_client = None

# ----- FILE READERS -----
def read_txt(file):
    """Extract text from TXT file"""
    try:
        return file.read().decode("utf-8")
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        file.seek(0)
        return file.read().decode("latin-1")
    except Exception as e:
        logger.error(f"Error reading TXT file: {e}")
        raise Exception(f"Failed to read TXT file: {str(e)}")

def read_docx(file):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        if not paragraphs:
            raise Exception("Document appears to be empty")
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error reading DOCX file: {e}")
        raise Exception(f"Failed to read DOCX file: {str(e)}")

def read_pdf(file):
    """Extract text from PDF file using pdfplumber"""
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            if len(pdf.pages) == 0:
                raise Exception("PDF appears to be empty")
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():  # Only add non-empty pages
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        
        if not text.strip():
            raise Exception("No readable text found in PDF")
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file: {e}")
        raise Exception(f"Failed to read PDF file: {str(e)}")

def read_image_with_document_intelligence(file):
    """Extract text from image using Azure Document Intelligence"""
    if not document_client:
        raise Exception("Azure Document Intelligence not configured. Please add AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY to your .env file.")
    
    try:
        # Reset file pointer
        file.seek(0)
        file_bytes = file.read()
        
        # Validate image
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception:
            raise Exception("Invalid image file")
        
        # Reset file pointer for Document Intelligence
        file.seek(0)
        
        # Use Document Intelligence to analyze the document
        poller = document_client.begin_analyze_document(
            "prebuilt-read", document=file_bytes
        )
        result = poller.result()
        
        # Extract text content
        text_content = []
        
        if result.content:
            return result.content
        
        # Fallback: extract from paragraphs
        for page in result.pages:
            for line in page.lines:
                text_content.append(line.content)
        
        extracted_text = "\n".join(text_content)
        
        if not extracted_text.strip():
            raise Exception("No text could be extracted from the image. Make sure the image contains clear, readable text.")
        
        return extracted_text
        
    except AzureError as e:
        logger.error(f"Azure Document Intelligence error: {e}")
        raise Exception(f"Document Intelligence error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise Exception(f"Image processing failed: {str(e)}")

def extract_text_from_file(file):
    """Extract text from uploaded file based on file extension"""
    try:
        filename = file.name.lower()
        
        # File size validation (max 10MB for regular files, 4MB for images)
        max_size = 4 * 1024 * 1024 if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']) else 10 * 1024 * 1024
        
        if file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise Exception(f"File size too large. Please upload files under {max_size_mb}MB.")
        
        # Handle different file types
        if filename.endswith(".txt"):
            return read_txt(file)
        elif filename.endswith(".docx"):
            return read_docx(file)
        elif filename.endswith(".pdf"):
            return read_pdf(file)
        elif any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
            return read_image_with_document_intelligence(file)
        else:
            raise Exception(f"Unsupported file type: {filename.split('.')[-1]}")
    
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        return None, str(e)

def validate_text_length(text, min_chars=50, max_chars=125000):
    """Validate text length for Azure API limits"""
    if len(text) < min_chars:
        raise Exception(f"Text too short (minimum {min_chars} characters required)")
    if len(text) > max_chars:
        raise Exception(f"Text too long (maximum {max_chars} characters allowed)")
    return True

# ----- AZURE AI LANGUAGE -----
def get_summary(text):
    """Generate summary using Azure Text Analytics key phrases and simple text processing"""
    if not text_client:
        raise Exception("Azure Text Analytics client not initialized")
    
    try:
        validate_text_length(text)
        
        # Split long text into chunks if needed
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        # Get key phrases first
        key_phrases_response = text_client.extract_key_phrases(documents=[text])
        
        if key_phrases_response[0].is_error:
            raise Exception(f"Azure API error: {key_phrases_response[0].error.message}")
        
        key_phrases = key_phrases_response[0].key_phrases[:8]  # Top 8 key phrases
        
        # Create summary from text structure
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        # Build intelligent summary
        summary_parts = []
        
        if key_phrases:
            summary_parts.append(f"Key topics: {', '.join(key_phrases[:5])}")
        
        # Add important sentences (those containing key phrases)
        important_sentences = []
        for sentence in sentences[:10]:  # Check first 10 sentences
            for phrase in key_phrases[:3]:  # Check against top 3 key phrases
                if phrase.lower() in sentence.lower():
                    important_sentences.append(sentence)
                    break
            if len(important_sentences) >= 2:  # Limit to 2 sentences
                break
        
        if important_sentences:
            summary_parts.extend(important_sentences)
        elif sentences:
            # Fallback to first 2 sentences if no key phrase matches
            summary_parts.extend(sentences[:2])
        
        summary = ". ".join(summary_parts)
        if summary and not summary.endswith('.'):
            summary += '.'
            
        return summary if summary else "Unable to generate summary from the provided text."
        
    except AzureError as e:
        logger.error(f"Azure API error in get_summary: {e}")
        raise Exception(f"Azure API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_summary: {e}")
        raise Exception(f"Summary generation failed: {str(e)}")

def get_key_phrases(text):
    """Extract key phrases using Azure Text Analytics"""
    if not text_client:
        raise Exception("Azure Text Analytics client not initialized")
    
    try:
        validate_text_length(text)
        
        # Split long text into chunks if needed
        if len(text) > 5000:
            text = text[:5000]
        
        response = text_client.extract_key_phrases(documents=[text])
        
        if response[0].is_error:
            raise Exception(f"Azure API error: {response[0].error.message}")
        
        key_phrases = response[0].key_phrases
        
        if not key_phrases:
            return ["No key phrases found - try uploading more detailed notes"]
        
        # Filter and deduplicate key phrases
        filtered_phrases = []
        for phrase in key_phrases:
            if len(phrase) > 2 and phrase.lower() not in [p.lower() for p in filtered_phrases]:
                filtered_phrases.append(phrase)
        
        return filtered_phrases[:15]  # Limit to top 15 phrases
        
    except AzureError as e:
        logger.error(f"Azure API error in get_key_phrases: {e}")
        raise Exception(f"Azure API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_key_phrases: {e}")
        raise Exception(f"Key phrase extraction failed: {str(e)}")

# ----- FLASHCARD GENERATOR -----
def generate_flashcards(text, key_phrases, max_cards=8):
    """Generate flashcards from text and key phrases"""
    try:
        if not text or not key_phrases:
            return [("Sample Question", "No content available for flashcard generation")]
        
        flashcards = []
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        
        if not sentences:
            return [("Sample Question", "Text content too short for flashcard generation")]
        
        # Shuffle for variety
        random.shuffle(sentences)
        
        # Generate different types of questions
        question_templates = [
            "What is {}?",
            "Define: {}",
            "Explain the concept of {}",
            "What do you know about {}?",
            "Describe {}"
        ]
        
        used_phrases = set()
        
        for phrase in key_phrases:
            if len(flashcards) >= max_cards:
                break
                
            if phrase.lower() in used_phrases:
                continue
                
            # Find best sentence containing the phrase
            best_sentence = None
            for sentence in sentences:
                if phrase.lower() in sentence.lower() and len(sentence) > 30:
                    best_sentence = sentence
                    break
            
            if best_sentence:
                question_template = random.choice(question_templates)
                question = question_template.format(phrase)
                answer = best_sentence.strip()
                
                # Clean up the answer
                if not answer.endswith('.'):
                    answer += '.'
                
                flashcards.append((question, answer))
                used_phrases.add(phrase.lower())
        
        # If we don't have enough flashcards, create some general ones
        while len(flashcards) < min(3, max_cards) and len(sentences) > len(flashcards):
            sentence = sentences[len(flashcards)]
            # Create a fill-in-the-blank style question
            words = sentence.split()
            if len(words) > 5:
                # Pick a meaningful word to blank out
                important_words = [w for w in words if len(w) > 4 and w.isalpha()]
                if important_words:
                    blank_word = random.choice(important_words)
                    question_sentence = sentence.replace(blank_word, "______", 1)
                    question = f"Fill in the blank: {question_sentence}"
                    answer = blank_word
                    flashcards.append((question, answer))
        
        return flashcards if flashcards else [("General Question", "Please upload more detailed notes for better flashcard generation")]
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return [("Error", f"Flashcard generation failed: {str(e)}")]

def get_file_info(file):
    """Get basic information about uploaded file"""
    return {
        "filename": file.name,
        "filetype": file.type,
        "filesize": f"{file.size / 1024:.1f} KB"
    }

def get_document_intelligence_status():
    """Check if Document Intelligence is properly configured"""
    return document_client is not None