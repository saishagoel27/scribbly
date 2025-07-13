import streamlit as st
import logging
import time
import io
import re
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# Import our enhanced components
from config import Config
from file_handler import file_handler
from azure_document import azure_document_processor
from azure_language import azure_language_processor
from flashcards import GeminiFlashcardGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlashcardApp:
    """
    Streamlit application class 
    """
    
    def __init__(self):
        """Initialize the application"""
        self.setup_page_config()
        self.gemini_generator = GeminiFlashcardGenerator()
        
        # Initialize session state
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = 1
        if 'processing_results' not in st.session_state:
            st.session_state.processing_results = {}
        if 'flashcards' not in st.session_state:
            st.session_state.flashcards = []
        if 'study_settings' not in st.session_state:
            st.session_state.study_settings = {
                'num_flashcards': 10,
                'difficulty': 'Mixed (Recommended)',
                'focus_mode': False
            }

    def setup_page_config(self):
        """Configure Streamlit page settings with enhanced CSS and fixed UI issues"""
        st.set_page_config(
            page_title="🧠 Scribbly - AI Study Helper",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # FIXED CSS with improved tab visibility and summary styling
        st.markdown("""
        <style>
        .main > div {
            padding-top: 1rem;
        }
        
        /* FIXED: Enhanced action button styling */
        .action-button-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        .action-button-container h3 {
            color: white !important;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .action-button-container p {
            color: #e8eaff !important;
            margin-bottom: 1.5rem;
            font-size: 1.1em;
        }
        
        /* Generation options styling */
        .generation-options {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 2rem;
            margin: 1.5rem 0;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }
        .generation-options h3 {
            color: #2c3e50 !important;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .generation-options p {
            color: #495057 !important;
            margin: 0;
            font-size: 1.05em;
            line-height: 1.6;
        }
        
        /* NEW: Flashcard styling for viewing modes */
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .flashcard-back {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .key-concept-tag {
            display: inline-block;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 0.3rem 0.8rem;
            margin: 0.2rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .concept-category {
            background: #f8f9fa;
            padding: 0.8rem;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
            border-radius: 5px;
        }
        }
        
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        }
        .flashcard:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        .flashcard-back {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        }
        .flashcard-back:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        
        /* FIXED: Improved summary box styles with better contrast */
        .summary-box {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            color: #2c3e50 !important;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #3498db;
            margin: 1.5rem 0;
            font-size: 1.1em;
            line-height: 1.7;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.1);
        }
        .summary-box h3 {
            color: #1e3a8a !important;
            margin-bottom: 1.5rem;
            font-weight: 700;
            font-size: 1.3em;
        }
        .summary-box p {
            color: #374151 !important;
            margin: 0;
            font-weight: 400;
            text-align: justify;
        }
        
        /* FIXED: Educational summary style with better readability */
        .educational-summary {
            background: linear-gradient(135deg, #ffffff 0%, #fef7ff 100%);
            color: #2d1b69 !important;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #8b5cf6;
            margin: 1.5rem 0;
            font-size: 1.1em;
            line-height: 1.7;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.1);
        }
        .educational-summary h3 {
            color: #5b21b6 !important;
            margin-bottom: 1.5rem;
            font-weight: 700;
            font-size: 1.3em;
        }
        .educational-summary p {
            color: #4c1d95 !important;
            margin: 0;
            font-weight: 400;
            text-align: justify;
        }
        
        /* FIXED: Azure extractive summary style with dark text */
        .extractive-summary {
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
            color: #14532d !important;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #10b981;
            margin: 1.5rem 0;
            font-size: 1.1em;
            line-height: 1.7;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
        }
        .extractive-summary h3 {
            color: #065f46 !important;
            margin-bottom: 1.5rem;
            font-weight: 700;
            font-size: 1.3em;
        }
        .extractive-summary p {
            color: #166534 !important;
            margin: 0;
            font-weight: 400;
            text-align: justify;
        }
        
        /* FIXED: Azure abstractive summary style with better contrast */
        .abstractive-summary {
            background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
            color: #92400e !important;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #f59e0b;
            margin: 1.5rem 0;
            font-size: 1.1em;
            line-height: 1.7;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.1);
        }
        .abstractive-summary h3 {
            color: #78350f !important;
            margin-bottom: 1.5rem;
            font-weight: 700;
            font-size: 1.3em;
        }
        .abstractive-summary p {
            color: #a16207 !important;
            margin: 0;
            font-weight: 400;
            text-align: justify;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 3px solid #667eea;
        }
        .error-box {
            background: #ffebee;
            border: 1px solid #f44336;
            color: #c62828 !important;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* FIXED: Better key concept tags */
        .key-concept-tag {
            background: #4f46e5 !important;
            color: white !important;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9em;
            display: inline-block;
            margin: 0.3rem 0.2rem;
            font-weight: 600;
            box-shadow: 0 2px 6px rgba(79, 70, 229, 0.3);
            transition: transform 0.2s;
        }
        .key-concept-tag:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(79, 70, 229, 0.4);
        }
        
        /* FIXED: Educational concept categories */
        .concept-category {
            margin: 1.5rem 0;
            padding: 1.5rem;
            border-radius: 12px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-left: 4px solid #6366f1;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .concept-category h4 {
            color: #1e293b !important;
            margin-bottom: 1rem;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        /* FIXED: Progress bar styling */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* FIXED: Enhanced tab styling with better visibility */
        .stTabs [data-baseweb="tab-list"] {
            gap: 32px;
            padding: 0 16px;
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            margin: 16px 0;
        }
        .stTabs [data-baseweb="tab"] {
            height: 56px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            color: #374151 !important;
            font-weight: 600 !important;
            font-size: 1.05em !important;
            padding: 12px 24px !important;
            border: none !important;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(102, 126, 234, 0.1);
            color: #4f46e5 !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            transform: translateY(-2px);
        }
        
        /* FIXED: Ensure all text in containers is readable */
        .stMarkdown {
            color: inherit;
        }
        
        /* FIXED: File info styling to prevent duplication */
        .file-info-container {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #10b981;
        }
        </style>
        """, unsafe_allow_html=True)

    def run(self):
        """Main application runner with enhanced workflow"""
        # Sidebar with enhanced settings
        self.render_sidebar()
        
        # Main header
        st.markdown("# 🧠 Scribbly - AI Study Helper")
        st.markdown("Transform your notes into interactive flashcards with AI")
        
        # Progress indicator
        self.render_progress_indicator()
        
        # Main content area based on current stage
        if st.session_state.current_stage == 1:
            self.render_upload_stage()
        elif st.session_state.current_stage == 2:
            self.render_generation_options_stage()
        elif st.session_state.current_stage == 3:
            self.render_processing_stage()
        elif st.session_state.current_stage == 4:
            self.render_study_mode()
        else:
            st.error("Invalid application stage")

    def render_sidebar(self):
        """Enhanced sidebar with Azure service status and study settings"""
        with st.sidebar:
            st.markdown("## ⚙️ Study Settings")
            
            # Service status
            st.markdown("### 🔧 Azure Services")
            services = Config.get_available_services()
            
            for service, available in services.items():
                emoji = "✅" if available else "❌"
                service_name = service.replace('_', ' ').title()
                st.markdown(f"{emoji} {service_name}")
            
            st.divider()
            
            # Study settings
            st.markdown("### 📚 Study Configuration")
            
            st.session_state.study_settings['num_flashcards'] = st.slider(
                "Number of Flashcards",
                min_value=5,
                max_value=20,
                value=st.session_state.study_settings['num_flashcards'],
                step=1
            )
            
            st.session_state.study_settings['difficulty'] = st.selectbox(
                "Difficulty Focus",
                ["Mixed (Recommended)", "Basic Concepts", "Advanced Topics", "Application-Based"],
                index=0 if st.session_state.study_settings['difficulty'] == "Mixed (Recommended)" else 0
            )
            
            st.session_state.study_settings['focus_mode'] = st.checkbox(
                "🎯 Study Mode",
                value=st.session_state.study_settings['focus_mode'],
                help="Removes distractions during study sessions"
            )
            
            st.divider()
            
            # Reset and help
            if st.button("🔄 Start Over", use_container_width=True):
                self.reset_session()
            
            with st.expander("ℹ️ How it works"):
                st.markdown("""
                **Step 1:** Upload your study material (PDF, images, text)
                
                **Step 2:** Choose what to generate (flashcards, summary, or both)
                
                **Step 3:** AI processes and analyzes your content
                
                **Step 4:** Study with interactive flashcard interface
                
                **Powered by:** Azure Document Intelligence, Azure Language Services, Google Gemini AI
                """)

    def reset_session(self):
        """Reset all session state variables"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    def render_progress_indicator(self):
        """Enhanced progress indicator with new stage"""
        progress_steps = [
            "📁 Upload Material",
            "🎯 Choose Actions",
            "🔍 AI Processing", 
            "📚 Study Mode"
        ]
        
        current_step = st.session_state.current_stage
        progress_percentage = (current_step / len(progress_steps))
        
        st.progress(progress_percentage)
        
        # Step indicator
        cols = st.columns(len(progress_steps))
        for i, (col, step) in enumerate(zip(cols, progress_steps)):
            with col:
                if i + 1 == current_step:
                    st.markdown(f"**{step}** ⭐")
                elif i + 1 < current_step:
                    st.markdown(f"~~{step}~~ ✅")
                else:
                    st.markdown(f"{step}")

    def render_upload_stage(self):
        """FIXED: Enhanced file upload stage without duplicate file info"""
        st.header("📁 Upload Your Study Material")
        st.markdown("Upload notes, PDFs, images, or documents to create flashcards")
        
        # File upload interface
        uploaded_file_data = file_handler.create_upload_interface()
        
        if uploaded_file_data and not uploaded_file_data.get('error'):
            st.session_state.uploaded_file_data = uploaded_file_data
            
            st.success("✅ File uploaded successfully!")
            
            # FIXED: Show file info only once in a styled container
            metadata = uploaded_file_data.get('metadata', {})
            
            st.markdown(f"""
            <div class="file-info-container">
                <h4 style="color: #065f46; margin-bottom: 1rem;">📄 File Information</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    <div style="text-align: center;">
                        <strong style="color: #374151;">📁 Size</strong><br>
                        <span style="color: #6b7280; font-size: 1.1em;">{metadata.get('file_size_mb', 0):.1f} MB</span>
                    </div>
                    <div style="text-align: center;">
                        <strong style="color: #374151;">📄 Type</strong><br>
                        <span style="color: #6b7280; font-size: 1.1em;">{metadata.get('file_extension', 'Unknown').upper()}</span>
                    </div>
                    <div style="text-align: center;">
                        <strong style="color: #374151;">📋 Pages</strong><br>
                        <span style="color: #6b7280; font-size: 1.1em;">{metadata.get('estimated_pages', 1)}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ENHANCED: Clear next step button
            if st.button("➡️ Choose What to Generate", type="primary", use_container_width=True):
                st.session_state.current_stage = 2
                st.rerun()
        
        elif uploaded_file_data and uploaded_file_data.get('error'):
            st.error(f"❌ {uploaded_file_data['error']}")

    def render_generation_options_stage(self):
        """NEW: Stage for choosing what to generate with explicit buttons"""
        st.header("🎯 Choose What to Generate")
        st.markdown("Select what you'd like to create from your uploaded material")
        
        # Display uploaded file info
        if 'uploaded_file_data' in st.session_state:
            metadata = st.session_state.uploaded_file_data.get('metadata', {})
            st.info(f"📄 Ready to process: **{metadata.get('filename', 'Your file')}** ({metadata.get('file_size_mb', 0):.1f} MB)")
        
        # ENHANCED: Generation options with beautiful UI
        st.markdown("""
        <div class="generation-options">
            <h3>🤖 AI Generation Options</h3>
            <p>Choose what you want to create from your study material. You can generate items individually or all at once.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Generation buttons in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="action-button-container">
                <h3>🃏 Smart Flashcards</h3>
                <p>Generate interactive flashcards optimized for study and retention using Gemini AI</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Generate Flashcards Only", use_container_width=True, type="primary"):
                st.session_state.generation_choice = "flashcards_only"
                self.start_processing()
        
        with col2:
            st.markdown("""
            <div class="action-button-container">
                <h3>📄 AI Summary</h3>
                <p>Create comprehensive summaries with key concepts using Azure Language Services</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📝 Generate Summary Only", use_container_width=True, type="secondary"):
                st.session_state.generation_choice = "summary_only"
                self.start_processing()
        
        # Combined option
        st.markdown("### 🌟 Recommended Option")
        
        st.markdown("""
        <div class="action-button-container">
            <h3>🎯 Complete Study Package</h3>
            <p>Generate both flashcards and comprehensive summaries for the ultimate study experience</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Generate Everything (Recommended)", use_container_width=True, type="primary"):
            st.session_state.generation_choice = "complete_package"
            self.start_processing()
        
        # Additional options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Go Back to Upload", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
        
        with col2:
            # Show current settings
            with st.expander("⚙️ Current Settings"):
                settings = st.session_state.study_settings
                st.write(f"**Flashcards:** {settings['num_flashcards']}")
                st.write(f"**Difficulty:** {settings['difficulty']}")
                st.write(f"**Focus Mode:** {'On' if settings['focus_mode'] else 'Off'}")

    def start_processing(self):
        """Enhanced processing initiation with generation choice"""
        if 'uploaded_file_data' in st.session_state:
            st.session_state.current_stage = 3
            st.rerun()
        else:
            st.error("No file uploaded")

    def render_processing_stage(self):
        """Enhanced processing stage with generation choice awareness"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        # Dynamic header based on choice
        if generation_choice == "flashcards_only":
            st.header("🃏 Generating Your Flashcards")
            st.markdown("Creating smart flashcards with AI...")
        elif generation_choice == "summary_only":
            st.header("📄 Creating Your Summary")
            st.markdown("Analyzing and summarizing your content...")
        else:
            st.header("🔍 Creating Your Complete Study Package")
            st.markdown("Generating flashcards and summaries with AI...")
        
        # Processing container
        processing_container = st.container()
        
        if not st.session_state.processing_results:
            with processing_container:
                self.execute_processing_pipeline()
        else:
            self.display_processing_results()

    def execute_processing_pipeline(self):
        """Enhanced processing pipeline with generation choice support"""
        try:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            
            file_data = st.session_state.uploaded_file_data.get('file_data', {})
            file_bytes = file_data.get('file_bytes')
            content_type = file_data.get('content_type')
            
            if not file_bytes:
                st.error("❌ File data not available")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(message: str, progress: float):
                """Progress callback for Azure services"""
                status_text.text(message)
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            # Step 1: Azure Document Intelligence (always needed)
            update_progress("🔍 Extracting text with Azure Document Intelligence...", 0.2)
            
            document_result = azure_document_processor.extract_text_with_handwriting(
                file_bytes, content_type, update_progress
            )
            
            if document_result.get('error'):
                st.error(f"❌ Document processing failed: {document_result['error']}")
                return
            
            extracted_text = document_result.get('extracted_text', '')
            if not extracted_text or len(extracted_text.strip()) < 50:
                st.error("❌ Insufficient text extracted from document")
                return
            
            st.session_state.processing_results['document_result'] = document_result
            
            # Step 2: Azure Language Services (for summary or complete package)
            language_result = None
            if generation_choice in ["summary_only", "complete_package"]:
                update_progress("🧠 Analyzing content with Azure Language Services...", 0.4)
                
                def language_progress_callback(message: str):
                    progress_map = {
                        "🧠 Starting advanced content analysis...": 0.41,
                        "🧹 Preparing text for Azure analysis...": 0.45,
                        "📝 Creating AI-powered summaries...": 0.55,
                        "🔍 Extracting key educational concepts...": 0.65,
                        "🏷️ Identifying educational entities...": 0.70,
                        "😊 Analyzing educational tone...": 0.75,
                        "📊 Assessing educational value...": 0.80,
                        "✅ Advanced analysis completed!": 0.85
                    }
                    progress_value = progress_map.get(message, 0.6)
                    update_progress(message, progress_value)
                
                language_result = azure_language_processor.analyze_for_study_materials(
                    extracted_text, language_progress_callback
                )
                
                if language_result.get('error'):
                    st.warning(f"⚠️ Language analysis had issues: {language_result['error']}")
                    language_result = azure_language_processor._create_fallback_analysis(extracted_text)
                
                st.session_state.processing_results['language_result'] = language_result
            
            # Step 3: Flashcard generation (for flashcards or complete package)
            if generation_choice in ["flashcards_only", "complete_package"]:
                update_progress("🃏 Generating flashcards with Gemini AI...", 0.9)
                
                # Use language result if available, otherwise use document result
                text_for_flashcards = extracted_text
                if language_result:
                    text_for_flashcards = language_result.get('cleaned_text', extracted_text)
                
                generation_params = {
                    'num_flashcards': st.session_state.study_settings['num_flashcards'],
                    'difficulty_focus': st.session_state.study_settings['difficulty'],
                    'key_phrases': language_result.get('key_phrases', {}).get('azure_key_phrases', []) if language_result else [],
                    'educational_concepts': language_result.get('key_phrases', {}).get('educational_concepts', {}) if language_result else {},
                    'study_assessment': language_result.get('study_assessment', {}) if language_result else {}
                }
                
                def flashcard_progress_callback(message: str, progress: float):
                    # Adjust progress to final range
                    adjusted_progress = 0.9 + (progress * 0.1)
                    update_progress(message, adjusted_progress)
                
                flashcards_result = self.gemini_generator.generate_enhanced_flashcards(
                    text_for_flashcards, generation_params, flashcard_progress_callback
                )
                
                if flashcards_result.get('error'):
                    st.warning(f"⚠️ Flashcard generation had issues: {flashcards_result['error']}")
                    flashcards_result = self.gemini_generator.generate_fallback_flashcards(text_for_flashcards)
                
                # Extract flashcards properly
                flashcards = flashcards_result.get('flashcards', [])
                if isinstance(flashcards, dict):
                    flat_flashcards = []
                    for category, cards in flashcards.items():
                        if isinstance(cards, list):
                            flat_flashcards.extend(cards)
                    flashcards = flat_flashcards
                
                st.session_state.flashcards = flashcards
                st.session_state.processing_results['flashcards_result'] = flashcards_result
            
            # Step 4: Cache results
            update_progress("💾 Caching results for faster future access...", 0.98)
            
            file_hash = st.session_state.uploaded_file_data.get('file_hash')
            if file_hash:
                cache_data = {
                    'document_result': document_result,
                    'language_result': language_result,
                    'generation_choice': generation_choice,
                    'timestamp': datetime.now().isoformat()
                }
                file_handler.cache_result(file_hash, cache_data)
            
            update_progress("✅ Generation completed successfully!", 1.0)
            
            # Show processing summary
            self.display_processing_summary()
            
        except Exception as e:
            logger.error(f"Processing pipeline error: {e}")
            st.error(f"❌ Processing failed: {str(e)}")

    def display_processing_results(self):
        """Display the results after processing is complete."""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        st.success("✅ Generation completed successfully!")
        
        # Show what was generated with explicit viewing options
        if generation_choice == "flashcards_only":
            st.markdown(f"### 🎉 Generated {len(st.session_state.flashcards)} flashcards!")
            
            # Preview a flashcard
            if st.session_state.flashcards:
                preview_card = st.session_state.flashcards[0]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="flashcard">
                        <h4>Question Preview:</h4>
                        <p>{preview_card.get('question', 'No question')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="flashcard-back">
                        <h4>Answer Preview:</h4>
                        <p>{preview_card.get('answer', 'No answer')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # ENHANCED: Explicit viewing options
            st.markdown("### 🎯 What would you like to do?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📖 View All Flashcards", type="secondary", use_container_width=True):
                    st.session_state.viewing_mode = "flashcards_preview"
                    st.session_state.current_stage = 4
                    st.rerun()
            
            with col2:
                if st.button("🎯 Start Studying", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "study_mode"
                    st.session_state.current_stage = 4
                    st.rerun()
                
        elif generation_choice == "summary_only":
            st.markdown("### 📄 Summary Generated!")
            
            # Show summary preview
            if 'language_result' in st.session_state.processing_results:
                language_result = st.session_state.processing_results['language_result']
                summary_data = language_result.get('summary', {})
                best_summary = summary_data.get('best', '')
                
                if best_summary:
                    st.markdown(f"""
                    <div class="summary-box">
                        <h3>📋 Summary Preview</h3>
                        <p>{best_summary[:200]}{'...' if len(best_summary) > 200 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # ENHANCED: Explicit viewing options
            st.markdown("### 🎯 What would you like to do?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📖 View Complete Summary", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "summary_view"
                    st.session_state.current_stage = 4
                    st.rerun()
            
            with col2:
                if st.button("🔍 View Key Concepts", type="secondary", use_container_width=True):
                    st.session_state.viewing_mode = "concepts_view"
                    st.session_state.current_stage = 4
                    st.rerun()
                
        else:  # complete_package
            st.markdown("### 🌟 Complete Study Package Generated!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🃏 Flashcards", len(st.session_state.flashcards))
            with col2:
                st.metric("📄 Summary Types", "3" if 'language_result' in st.session_state.processing_results else "1")
            
            # ENHANCED: Multiple explicit viewing options
            st.markdown("### 🎯 What would you like to explore first?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📖 View Complete Summary", use_container_width=True):
                    st.session_state.viewing_mode = "summary_view"
                    st.session_state.current_stage = 4
                    st.rerun()
            
            with col2:
                if st.button("🃏 Browse All Flashcards", use_container_width=True):
                    st.session_state.viewing_mode = "flashcards_preview"
                    st.session_state.current_stage = 4
                    st.rerun()
            
            with col3:
                if st.button("🚀 Start Studying", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "study_mode"
                    st.session_state.current_stage = 4
                    st.rerun()
        
        # Additional options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Generate Something Else", use_container_width=True):
                # Clear results and go back to options
                st.session_state.processing_results = {}
                st.session_state.flashcards = []
                st.session_state.current_stage = 2
                st.rerun()
        
        with col2:
            if st.button("🔄 Start Over", use_container_width=True):
                self.reset_session()

    def display_processing_summary(self):
        """Enhanced processing summary with generation choice awareness"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        st.markdown("### 📊 Generation Summary")
        
        # Dynamic metrics based on what was generated
        if generation_choice == "flashcards_only":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🃏 Flashcards Generated", len(st.session_state.flashcards))
            with col2:
                difficulty = st.session_state.study_settings['difficulty']
                st.metric("🎯 Difficulty Level", difficulty)
            with col3:
                quality_score = st.session_state.processing_results.get('flashcards_result', {}).get('generation_metadata', {}).get('quality_score', 0.8)
                st.metric("⭐ Quality Score", f"{quality_score:.1%}")
                
        elif generation_choice == "summary_only":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                language_result = st.session_state.processing_results.get('language_result', {})
                key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
                st.metric("🔑 Key Concepts", len(key_phrases))
            with col2:
                quality = language_result.get('study_assessment', {}).get('overall_quality', 'unknown')
                st.metric("📚 Content Quality", quality.title())
            with col3:
                summary_types = len([k for k, v in language_result.get('summary', {}).items() if v])
                st.metric("📄 Summary Types", summary_types)
                
        else:  # complete_package
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🃏 Flashcards", len(st.session_state.flashcards))
            with col2:
                language_result = st.session_state.processing_results.get('language_result', {})
                key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
                st.metric("🔑 Key Concepts", len(key_phrases))
            with col3:
                quality = language_result.get('study_assessment', {}).get('overall_quality', 'unknown')
                st.metric("📚 Content Quality", quality.title())
            with col4:
                summary_types = len([k for k, v in language_result.get('summary', {}).items() if v])
                st.metric("📄 Summary Types", summary_types)

    def render_study_mode(self):
        """ENHANCED: Study mode with explicit viewing modes and generation choice awareness"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        viewing_mode = st.session_state.get('viewing_mode', 'study_mode')
        
        # Handle specific viewing modes first
        if viewing_mode == "flashcards_preview":
            self.render_flashcards_preview()
            return
        elif viewing_mode == "summary_view":
            self.render_summary_view()
            return
        elif viewing_mode == "concepts_view":
            self.render_concepts_view()
            return
        
        # Default study mode based on generation choice
        if generation_choice == "flashcards_only":
            st.header("🃏 Study Your Flashcards")
            tab1 = st.tabs(["🃏 Study Flashcards"])
            with tab1[0]:
                self.render_flashcard_study_interface()
                
        elif generation_choice == "summary_only":
            st.header("📄 Review Your Summary")
            tab1 = st.tabs(["📄 Summary Review"])
            with tab1[0]:
                self.render_enhanced_summary_tab()
                
        else:  # complete_package
            st.header("📚 Study Mode")
            # FIXED: Better tab labels with clearer text
            tab1, tab2, tab3 = st.tabs(["🃏 Study Flashcards", "📄 Summary Review", "📊 Progress Analytics"])
            
            with tab1:
                self.render_flashcard_study_interface()
            with tab2:
                self.render_enhanced_summary_tab()
            with tab3:
                self.render_progress_tab()

    def render_flashcard_study_interface(self):
        """Enhanced flashcard study interface"""
        if not st.session_state.flashcards:
            st.warning("⚠️ No flashcards available. Generate flashcards first!")
            if st.button("🔙 Go Back to Generation Options"):
                st.session_state.current_stage = 2
                st.rerun()
            return
            
        if 'current_card_index' not in st.session_state:
            st.session_state.current_card_index = 0
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False
        if 'study_stats' not in st.session_state:
            st.session_state.study_stats = {'correct': 0, 'incorrect': 0, 'total_answered': 0}
        
        total_cards = len(st.session_state.flashcards)
        current_index = st.session_state.current_card_index
        current_card = st.session_state.flashcards[current_index]
        
        # Card counter and progress
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"**Card {current_index + 1} of {total_cards}**")
            st.progress((current_index + 1) / total_cards)
        
        # Flashcard display
        if not st.session_state.show_answer:
            # Question side
            st.markdown(f"""
            <div class="flashcard">
                <h3>🤔 Question</h3>
                <p style="font-size: 1.2em; margin-top: 1rem;">{current_card.get('question', 'No question available')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Show Answer", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            with col2:
                if st.button("⏭️ Skip Card", use_container_width=True):
                    self.next_card()
        else:
            # Answer side
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="flashcard">
                    <h3>🤔 Question</h3>
                    <p style="font-size: 1.1em;">{current_card.get('question', 'No question available')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="flashcard-back">
                    <h3>💡 Answer</h3>
                    <p style="font-size: 1.1em;">{current_card.get('answer', 'No answer available')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Self-assessment buttons
            st.markdown("### 🎯 How did you do?")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("❌ Incorrect", use_container_width=True):
                    self.record_answer(False)
            with col2:
                if st.button("✅ Correct", use_container_width=True):
                    self.record_answer(True)
            with col3:
                if st.button("➡️ Next Card", use_container_width=True):
                    self.next_card()
        
        # Study controls
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Restart Study Session", use_container_width=True):
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.session_state.study_stats = {'correct': 0, 'incorrect': 0, 'total_answered': 0}
                st.rerun()
        
        with col2:
            if st.button("🎲 Shuffle Cards", use_container_width=True):
                random.shuffle(st.session_state.flashcards)
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.rerun()
        
        with col3:
            if st.button("📊 View Stats", use_container_width=True):
                self.show_study_stats()

    def record_answer(self, correct: bool):
        """Record study performance"""
        stats = st.session_state.study_stats
        stats['total_answered'] += 1
        if correct:
            stats['correct'] += 1
        else:
            stats['incorrect'] += 1
        
        self.next_card()

    def next_card(self):
        """Move to next flashcard"""
        st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(st.session_state.flashcards)
        st.session_state.show_answer = False
        st.rerun()

    def show_study_stats(self):
        """Display study statistics"""
        stats = st.session_state.study_stats
        
        if stats['total_answered'] > 0:
            accuracy = (stats['correct'] / stats['total_answered']) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Accuracy", f"{accuracy:.1f}%")
            with col2:
                st.metric("✅ Correct", stats['correct'])
            with col3:
                st.metric("❌ Incorrect", stats['incorrect'])
        else:
            st.info("📈 Start answering questions to see your progress!")

    def render_enhanced_summary_tab(self):
        """FIXED: Enhanced summary display with better styling and contrast"""
        st.header("📄 Content Summary")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("⚠️ No summary available. Generate summary first!")
            if st.button("🔙 Go Back to Generation Options"):
                st.session_state.current_stage = 2
                st.rerun()
            return
        
        language_result = st.session_state.processing_results['language_result']
        summary_data = language_result.get('summary', {})
        
        if isinstance(summary_data, dict) and summary_data:
            # Best Summary (Primary)
            best_summary = summary_data.get('best', '')
            if best_summary and len(best_summary.strip()) > 50:
                st.markdown(f"""
                <div class="summary-box">
                    <h3>🎯 AI-Powered Summary</h3>
                    <p>{best_summary}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # FIXED: Summary type tabs with better labels and styling
            summary_tabs = st.tabs(["🎓 Educational Focus", "📋 Key Sentences", "✨ AI Generated"])
            
            with summary_tabs[0]:
                educational_summary = summary_data.get('educational', '')
                if educational_summary and len(educational_summary.strip()) > 30:
                    st.markdown(f"""
                    <div class="educational-summary">
                        <h3>🎓 Educational Focus Summary</h3>
                        <p>{educational_summary}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("🎯 Optimized for study materials and educational content")
                else:
                    st.info("📚 Educational summary not available")
            
            with summary_tabs[1]:
                extractive_summary = summary_data.get('extractive', '')
                if extractive_summary and len(extractive_summary.strip()) > 30:
                    st.markdown(f"""
                    <div class="extractive-summary">
                        <h3>📋 Key Sentences from Original Text</h3>
                        <p>{extractive_summary}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("💡 Important sentences selected by Azure AI from your original text")
                else:
                    st.info("📋 Key sentences summary not available")
            
            with summary_tabs[2]:
                abstractive_summary = summary_data.get('abstractive', '')
                if abstractive_summary and len(abstractive_summary.strip()) > 30:
                    st.markdown(f"""
                    <div class="abstractive-summary">
                        <h3>✨ AI Generated Summary</h3>
                        <p>{abstractive_summary}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("🤖 New summary text generated by Azure AI based on your content")
                else:
                    st.info("✨ AI generated summary not available")
        
        # Key concepts display
        key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
        
        if key_phrases:
            st.subheader("🔑 Key Concepts")
            key_concepts_html = ""
            for phrase in key_phrases[:15]:
                key_concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
            
            st.markdown(f"""
            <div style="margin: 1.5rem 0;">
                {key_concepts_html}
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced content metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            word_count = language_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("📝 Word Count", f"{word_count:,}")
        
        with col2:
            st.metric("🔑 Key Concepts", len(key_phrases))
        
        with col3:
            quality = language_result.get('study_assessment', {}).get('overall_quality', 'unknown')
            st.metric("📚 Content Quality", quality.title())
        
        with col4:
            complexity = language_result.get('text_complexity', {}).get('complexity_level', 'unknown')
            st.metric("🎓 Complexity", complexity.title())

    def render_flashcards_preview(self):
        """NEW: Preview all flashcards before studying"""
        st.header("🃏 Your Generated Flashcards")
        st.markdown(f"Browse through all **{len(st.session_state.flashcards)}** flashcards before you start studying")
        
        if not st.session_state.flashcards:
            st.warning("⚠️ No flashcards available.")
            return
        
        # Navigation controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Start Studying Now", type="primary", use_container_width=True):
                st.session_state.viewing_mode = "study_mode"
                st.rerun()
        
        st.markdown("---")
        
        # Display all flashcards in an organized way
        for i, card in enumerate(st.session_state.flashcards, 1):
            with st.expander(f"**Flashcard {i}** - {card.get('concept', 'General')}", expanded=i <= 3):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="flashcard">
                        <h4>🤔 Question</h4>
                        <p>{card.get('question', 'No question available')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="flashcard-back">
                        <h4>💡 Answer</h4>
                        <p>{card.get('answer', 'No answer available')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show difficulty and concept if available
                if card.get('difficulty') or card.get('concept'):
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        if card.get('difficulty'):
                            st.caption(f"🎯 **Difficulty:** {card['difficulty'].title()}")
                    with info_col2:
                        if card.get('concept'):
                            st.caption(f"📚 **Topic:** {card['concept']}")
        
        # Action buttons at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Results", use_container_width=True):
                st.session_state.current_stage = 3
                st.rerun()
        
        with col2:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["summary_only", "complete_package"]:
                if st.button("📄 View Summary", use_container_width=True):
                    st.session_state.viewing_mode = "summary_view"
                    st.rerun()
        
        with col3:
            if st.button("🎯 Start Studying", type="primary", use_container_width=True):
                st.session_state.viewing_mode = "study_mode"
                st.rerun()

    def render_summary_view(self):
        """NEW: Dedicated summary viewing mode"""
        st.header("📄 Complete Summary View")
        st.markdown("Review your AI-generated content summaries and key concepts")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("⚠️ No summary available.")
            return
        
        # Navigation controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["flashcards_only", "complete_package"]:
                if st.button("🃏 View Flashcards", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "flashcards_preview"
                    st.rerun()
            else:
                if st.button("🔍 View Key Concepts", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "concepts_view"
                    st.rerun()
        
        st.markdown("---")
        
        # Use the existing enhanced summary tab logic
        self.render_enhanced_summary_tab()
        
        # Action buttons at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Results", use_container_width=True):
                st.session_state.current_stage = 3
                st.rerun()
        
        with col2:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["flashcards_only", "complete_package"]:
                if st.button("🃏 Browse Flashcards", use_container_width=True):
                    st.session_state.viewing_mode = "flashcards_preview"
                    st.rerun()
        
        with col3:
            if generation_choice != "summary_only":
                if st.button("🎯 Start Studying", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "study_mode"
                    st.rerun()

    def render_concepts_view(self):
        """NEW: Dedicated key concepts viewing mode"""
        st.header("🔑 Key Concepts & Analysis")
        st.markdown("Explore the educational concepts and analysis extracted from your content")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("⚠️ No concept analysis available.")
            return
        
        language_result = st.session_state.processing_results['language_result']
        
        # Navigation controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📄 View Complete Summary", type="primary", use_container_width=True):
                st.session_state.viewing_mode = "summary_view"
                st.rerun()
        
        st.markdown("---")
        
        # Key concepts display
        key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
        educational_concepts = language_result.get('key_phrases', {}).get('educational_concepts', {})
        
        if key_phrases:
            st.subheader("🔑 Key Concepts")
            key_concepts_html = ""
            for phrase in key_phrases:
                key_concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
            
            st.markdown(f"""
            <div style="margin: 1.5rem 0;">
                {key_concepts_html}
            </div>
            """, unsafe_allow_html=True)
        
        # Educational concept categories
        if educational_concepts and isinstance(educational_concepts, dict):
            st.subheader("📚 Educational Concept Categories")
            
            for category, concepts in educational_concepts.items():
                if concepts:
                    st.markdown(f"""
                    <div class="concept-category">
                        <h4>{category.replace('_', ' ').title()}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    concepts_html = ""
                    for concept in concepts[:8]:  # Limit display
                        concepts_html += f'<span class="key-concept-tag">{concept}</span> '
                    
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0 1.5rem 0;">
                        {concepts_html}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Content analysis metrics
        st.subheader("📊 Content Analysis")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            word_count = language_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("📝 Word Count", f"{word_count:,}")
        
        with col2:
            st.metric("🔑 Key Phrases", len(key_phrases))
        
        with col3:
            quality = language_result.get('study_assessment', {}).get('overall_quality', 'unknown')
            st.metric("📚 Content Quality", quality.title())
        
        with col4:
            complexity = language_result.get('text_complexity', {}).get('complexity_level', 'unknown')
            st.metric("🎓 Complexity", complexity.title())
        
        # Educational analysis
        sentiment = language_result.get('sentiment', {})
        if sentiment and isinstance(sentiment, dict):
            st.subheader("🧠 Educational Analysis")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                educational_tone = sentiment.get('educational_tone', 'informational')
                st.metric("📚 Educational Tone", educational_tone.title())
            
            with col2:
                learning_difficulty = sentiment.get('learning_difficulty', 'moderate')
                st.metric("🎯 Learning Difficulty", learning_difficulty.title())
            
            with col3:
                engagement_level = sentiment.get('engagement_level', 'neutral')
                st.metric("⚡ Engagement Level", engagement_level.title())
        
        # Action buttons at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Results", use_container_width=True):
                st.session_state.current_stage = 3
                st.rerun()
        
        with col2:
            if st.button("📄 View Summary", use_container_width=True):
                st.session_state.viewing_mode = "summary_view"
                st.rerun()
        
        with col3:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["flashcards_only", "complete_package"]:
                if st.button("🃏 Browse Flashcards", type="primary", use_container_width=True):
                    st.session_state.viewing_mode = "flashcards_preview"
                    st.rerun()

    def render_progress_tab(self):
        """Enhanced progress tab with study analytics"""
        st.header("📊 Study Progress Analytics")
        
        if 'study_stats' in st.session_state:
            stats = st.session_state.study_stats
            
            if stats['total_answered'] > 0:
                accuracy = (stats['correct'] / stats['total_answered']) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Accuracy", f"{accuracy:.1f}%")
                with col2:
                    st.metric("✅ Correct", stats['correct'])
                with col3:
                    st.metric("❌ Incorrect", stats['incorrect'])
                with col4:
                    st.metric("📝 Total Answered", stats['total_answered'])
                
                # Progress visualization
                if stats['total_answered'] > 0:
                    st.subheader("📈 Performance Overview")
                    
                    # Create a simple chart
                    chart_data = {
                        'Category': ['Correct', 'Incorrect'],
                        'Count': [stats['correct'], stats['incorrect']]
                    }
                    st.bar_chart(chart_data)
                
                # Study recommendations
                st.subheader("💡 Study Recommendations")
                
                if accuracy >= 90:
                    st.success("🌟 Excellent work! You've mastered this material. Consider reviewing new topics or advanced concepts.")
                elif accuracy >= 80:
                    st.info("👍 Great progress! Review the cards you missed and try again to reach mastery.")
                elif accuracy >= 70:
                    st.warning("📚 Good start! Focus on understanding the concepts you found challenging.")
                else:
                    st.error("💪 Keep practicing! Consider reviewing the source material and trying again.")
            
            else:
                st.info("📚 Start studying to see your progress!")
                
                # Show study tips
                st.subheader("💡 Study Tips")
                st.markdown("""
                - **Active Recall**: Try to answer before revealing the answer
                - **Spaced Repetition**: Review cards you got wrong more frequently
                - **Understanding**: Focus on why the answer is correct, not just memorizing
                - **Regular Practice**: Short, frequent study sessions are more effective
                """)
        
        else:
            st.info("📈 No study data available yet.")
            st.markdown("Start studying flashcards to track your progress here!")

# Main application runner
if __name__ == "__main__":
    app = FlashcardApp()
    app.run()