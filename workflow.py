import streamlit as st
import time
import logging
from typing import Dict, Any, Optional, Callable, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass

from azure_document import AzureDocumentProcessor
from azure_language import azure_language_processor
from flashcards import gemini_generator
from session_keys import (
    PROCESSING_RESULTS, FLASHCARDS, STUDY_SETTINGS,
    UPLOADED_FILE_DATA, GENERATION_CHOICE, CURRENT_STAGE
)
from fallbacks import create_basic_flashcards, simple_key_extraction, simple_extractive_summary
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ProcessingContext:
    """Context object to pass data between processing steps"""
    file_data: Dict[str, Any]
    generation_choice: str
    study_settings: Dict[str, Any]
    extracted_text: Optional[str] = None
    document_result: Optional[Dict[str, Any]] = None
    language_result: Optional[Dict[str, Any]] = None
    flashcards_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ProgressReporter(Protocol):
    """Interface for progress reporting"""
    def report(self, message: str, progress: float) -> None: ...

class ProcessingCommand(ABC):
    """Base class for processing commands"""
    
    @abstractmethod
    def execute(self, context: ProcessingContext, progress: ProgressReporter) -> bool: pass
    
    @abstractmethod  
    def get_command_name(self) -> str: pass

class DocumentExtractionCommand(ProcessingCommand):
    """Extract text from uploaded document"""
    
    def get_command_name(self) -> str:
        return "Document Text Extraction"
    
    def execute(self, context: ProcessingContext, progress: ProgressReporter) -> bool:
        try:
            progress.report("🔍 Extracting text from your document...", 0.1)
            
            def doc_progress_callback(msg: str, prog: Optional[float] = None):
                if prog is not None:
                    progress.report(msg, 0.1 + prog * 0.3)
                else:
                    progress.report(msg, 0.25)
            
            document_result = AzureDocumentProcessor.extract_text_with_handwriting(
                context.file_data.get('file_bytes'),
                context.file_data.get('content_type'),
                doc_progress_callback
            )
            
            if document_result.get('error'):
                context.error = f"Text extraction failed: {document_result['error']}"
                return False
            
            extracted_text = document_result.get('extracted_text', '')
            if len(extracted_text.strip()) < 50:
                context.error = "Not enough text extracted from document"
                return False
            
            context.document_result = document_result
            context.extracted_text = extracted_text
            
            progress.report(f"✅ Extracted {len(extracted_text.split())} words", 0.4)
            return True
            
        except Exception as e:
            logger.error(f"Document extraction error: {e}")
            context.error = f"Document processing failed: {str(e)}"
            return False

class LanguageAnalysisCommand(ProcessingCommand):
    """Analyze text and create summaries"""
    
    def get_command_name(self) -> str:
        return "Language Analysis & Summarization"
    
    def execute(self, context: ProcessingContext, progress: ProgressReporter) -> bool:
        if context.generation_choice not in ["summary_only", "complete_package"]:
            return True
        
        try:
            progress.report("🧠 Analyzing content with Azure AI...", 0.5)
            
            language_result = None
            try:
                def lang_progress_callback(msg: str):
                    progress.report(msg, 0.6)
                
                language_result = azure_language_processor.analyze_for_study_materials(
                    context.extracted_text, 
                    lang_progress_callback
                )
            except Exception as e:
                logger.warning(f"Azure Language processing failed: {e}")
            
            if not language_result or language_result.get('error'):
                progress.report("🔄 Using backup summary generation...", 0.65)
                language_result = self._create_fallback_analysis(context.extracted_text)
            
            context.language_result = language_result
            progress.report("✅ Summary analysis complete", 0.7)
            return True
            
        except Exception as e:
            logger.error(f"Language analysis error: {e}")
            context.error = f"Language analysis failed: {str(e)}"
            return False
    
    def _create_fallback_analysis(self, text: str) -> Dict[str, Any]:
        key_phrases = simple_key_extraction(text)
        summaries = {
            'best': simple_extractive_summary(text),
            'extractive': simple_extractive_summary(text),
            'abstractive': f"Key topics: {', '.join(key_phrases[:5])}"
        }
        return {
            'summary': summaries,
            'key_phrases': {'azure_key_phrases': key_phrases},
            'text_complexity': {'word_count': len(text.split())},
            'study_assessment': {'overall_quality': 'basic'},
            'error': None
        }

class FlashcardGenerationCommand(ProcessingCommand):
    """Generate flashcards using AI"""
    
    def get_command_name(self) -> str:
        return "AI Flashcard Generation"
    
    def execute(self, context: ProcessingContext, progress: ProgressReporter) -> bool:
        if context.generation_choice not in ["flashcards_only", "complete_package"]:
            return True
        
        try:
            progress.report("🃏 Creating flashcards with AI...", 0.75)
            
            generation_params = {
                'num_flashcards': context.study_settings['num_flashcards'],
                'difficulty_focus': context.study_settings['difficulty'],
                'key_phrases': self._get_key_phrases_from_context(context)
            }
            
            flashcards_result = None
            try:
                def flashcard_progress_callback(msg: str, prog: float):
                    progress.report(msg, 0.75 + prog * 0.2)
                
                flashcards_result = gemini_generator.generate_enhanced_flashcards(
                    context.extracted_text, 
                    generation_params,
                    flashcard_progress_callback
                )
            except Exception as e:
                logger.warning(f"Gemini flashcard generation failed: {e}")
            
            if not flashcards_result or flashcards_result.get('error'):
                progress.report("🔄 Using backup flashcard generation...", 0.9)
                flashcards_result = create_basic_flashcards(
                    context.extracted_text, 
                    generation_params.get('num_flashcards', Config.DEFAULT_FLASHCARD_COUNT)
                )
            
            context.flashcards_result = flashcards_result
            flashcards = flashcards_result.get('flashcards', [])
            progress.report(f"✅ Created {len(flashcards)} flashcards", 0.95)
            return True
            
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            context.error = f"Flashcard generation failed: {str(e)}"
            return False
    
    def _get_key_phrases_from_context(self, context: ProcessingContext) -> list:
        if context.language_result:
            return context.language_result.get('key_phrases', {}).get('azure_key_phrases', [])
        return []

class ProcessingPipeline:
    """Manages the processing pipeline"""
    
    def __init__(self):
        self.commands = [
            DocumentExtractionCommand(),
            LanguageAnalysisCommand(),
            FlashcardGenerationCommand()
        ]
    
    def execute(self, context: ProcessingContext, progress: ProgressReporter) -> bool:
        for command in self.commands:
            logger.info(f"Executing: {command.get_command_name()}")
            
            if not command.execute(context, progress):
                logger.error(f"Command failed: {command.get_command_name()}")
                return False
        
        return True

class StreamlitProgressReporter:
    """Progress reporter for Streamlit UI"""
    
    def __init__(self):
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def report(self, message: str, progress: float) -> None:
        self.status_text.text(message)
        self.progress_bar.progress(min(progress, 1.0))
        time.sleep(0.1)
    
    def clear(self) -> None:
        self.progress_bar.empty()
        self.status_text.empty()

def execute_processing(app):
    """Main processing entry point - clean and focused"""
    
    try:
        if PROCESSING_RESULTS not in st.session_state:
            st.session_state[PROCESSING_RESULTS] = {}
        
        context = ProcessingContext(
            file_data=st.session_state[UPLOADED_FILE_DATA].get('file_data', {}),
            generation_choice=st.session_state.get(GENERATION_CHOICE, 'complete_package'),
            study_settings=st.session_state[STUDY_SETTINGS]
        )
        
        progress_reporter = StreamlitProgressReporter()
        pipeline = ProcessingPipeline()
        
        success = pipeline.execute(context, progress_reporter)
        
        if success:
            _save_results_to_session(context)
            progress_reporter.report("🎉 All done! Ready to study!", 1.0)
            time.sleep(0.5)
            progress_reporter.clear()
            st.session_state[CURRENT_STAGE] = 4
            st.rerun()
        else:
            progress_reporter.clear()
            st.error(f"❌ Processing failed: {context.error}")
            st.info("💡 Try uploading a different file or check your AI service credentials")
            
    except Exception as e:
        logger.error(f"Processing pipeline error: {e}")
        st.error(f"❌ Processing failed: {str(e)}")

def _save_results_to_session(context: ProcessingContext) -> None:
    """Save processing results to session state"""
    
    if context.document_result:
        st.session_state[PROCESSING_RESULTS]['document_result'] = context.document_result
    
    if context.language_result:
        st.session_state[PROCESSING_RESULTS]['language_result'] = context.language_result
    
    if context.flashcards_result:
        st.session_state[PROCESSING_RESULTS]['flashcards_result'] = context.flashcards_result
        st.session_state[FLASHCARDS] = context.flashcards_result.get('flashcards', [])