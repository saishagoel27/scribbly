import streamlit as st
import time
import logging
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

def execute_processing(app):
    """Main processing pipeline"""
    try:
        # Initialize processing results if not exists
        if PROCESSING_RESULTS not in st.session_state:
            st.session_state[PROCESSING_RESULTS] = {}
        
        generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
        file_data = st.session_state[UPLOADED_FILE_DATA].get('file_data', {})

        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(message: str, progress: float):
            status_text.text(message)
            progress_bar.progress(min(progress, 1.0))
            time.sleep(0.1)

        # Step 1: Extract text from document
        update_progress("🔍 Extracting text from your document...", 0.1)
        
        # Handle progress callback properly for Azure Document Intelligence
        def doc_progress_callback(msg, prog=None):
            if prog is not None:
                update_progress(msg, 0.1 + prog * 0.3)
            else:
                update_progress(msg, 0.25)
        
        document_result = AzureDocumentProcessor.extract_text_with_handwriting(
            file_data.get('file_bytes'),
            file_data.get('content_type'),
            doc_progress_callback
        )

        if document_result.get('error'):
            st.error(f"❌ Text extraction failed: {document_result['error']}")
            st.info("💡 Try a different file format or check your Azure credentials")
            return

        extracted_text = document_result.get('extracted_text', '')
        if len(extracted_text.strip()) < 50:
            st.error("❌ Not enough text extracted from document")
            st.info("💡 Try uploading a document with more content")
            return

        # Save document result
        st.session_state[PROCESSING_RESULTS]['document_result'] = document_result
        update_progress(f"✅ Extracted {len(extracted_text.split())} words", 0.4)

        # Step 2: Language analysis (only if summaries needed)
        language_result = None
        if generation_choice in ["summary_only", "complete_package"]:
            update_progress("🧠 Analyzing content with Azure AI...", 0.5)

            try:
                # Handle Azure Language callback properly
                def lang_progress_callback(msg):
                    update_progress(msg, 0.6)
                
                language_result = azure_language_processor.analyze_for_study_materials(
                    extracted_text, 
                    lang_progress_callback
                )
            except Exception as e:
                logger.warning(f"Azure Language processing failed: {e}")
                language_result = None

            # Create fallback if Azure fails
            if not language_result or language_result.get('error'):
                update_progress("🔄 Using backup summary generation...", 0.65)
                key_phrases = simple_key_extraction(extracted_text)
                summaries = {
                    'best': simple_extractive_summary(extracted_text),
                    'extractive': simple_extractive_summary(extracted_text),
                    'abstractive': f"Key topics: {', '.join(key_phrases[:5])}"
                }
                language_result = {
                    'summary': summaries,
                    'key_phrases': {'azure_key_phrases': key_phrases},
                    'text_complexity': {'word_count': len(extracted_text.split())},
                    'study_assessment': {'overall_quality': 'basic'},
                    'error': None
                }

            st.session_state[PROCESSING_RESULTS]['language_result'] = language_result
            update_progress("✅ Summary analysis complete", 0.7)

        # Step 3: Generate flashcards (only if flashcards needed)
        if generation_choice in ["flashcards_only", "complete_package"]:
            update_progress("🃏 Creating flashcards with AI...", 0.75)

            # Get flashcard count from sidebar settings
            generation_params = {
                'num_flashcards': st.session_state[STUDY_SETTINGS]['num_flashcards'],
                'difficulty_focus': st.session_state[STUDY_SETTINGS]['difficulty'],
                'key_phrases': language_result.get('key_phrases', {}).get('azure_key_phrases', []) if language_result else []
            }

            try:
                # Handle Gemini callback properly
                def flashcard_progress_callback(msg, prog):
                    update_progress(msg, 0.75 + prog * 0.2)
                
                flashcards_result = gemini_generator.generate_enhanced_flashcards(
                    extracted_text, 
                    generation_params,
                    flashcard_progress_callback
                )
            except Exception as e:
                logger.warning(f"Gemini flashcard generation failed: {e}")
                flashcards_result = None

            # Create fallback if Gemini fails
            if not flashcards_result or flashcards_result.get('error'):
                update_progress("🔄 Using backup flashcard generation...", 0.9)
                flashcards_result = create_basic_flashcards(
                    extracted_text, 
                    generation_params.get('num_flashcards', Config.DEFAULT_FLASHCARD_COUNT)
                )

            # Save flashcards
            st.session_state[FLASHCARDS] = flashcards_result.get('flashcards', [])
            st.session_state[PROCESSING_RESULTS]['flashcards_result'] = flashcards_result
            update_progress(f"✅ Created {len(st.session_state[FLASHCARDS])} flashcards", 0.95)

        # Complete processing
        update_progress("🎉 All done! Ready to study!", 1.0)
        time.sleep(0.5)
        
        # Clear progress display
        progress_bar.empty()
        status_text.empty()
        
        # Move to results stage (Stage 4 - Access Materials)
        st.session_state[CURRENT_STAGE] = 4
        st.rerun()

    except Exception as e:
        logger.error(f"Processing pipeline error: {e}")
        st.error(f"❌ Processing failed: {str(e)}")
        st.info("💡 Try uploading a different file or check your AI service credentials")