import streamlit as st
import logging
import time
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
    Main Streamlit application class for AI-Powered Flashcard Generator
    
    This class orchestrates the entire workflow:
    1. File upload and validation
    2. Document processing (OCR/text extraction)
    3. Text analysis and enhancement
    4. AI-powered flashcard generation
    5. Interactive flashcard review
    """
    
    def __init__(self):
        """Initialize the application"""
        self.setup_page_config()
        self.setup_session_state()
        self.flashcard_generator = GeminiFlashcardGenerator()
        
        # Initialize application configuration
        if not hasattr(st.session_state, 'app_initialized'):
            self.initialize_app()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=Config.PAGE_TITLE,
            page_icon=Config.PAGE_ICON,
            layout=Config.LAYOUT,
            initial_sidebar_state=Config.INITIAL_SIDEBAR_STATE,
            menu_items={
                'Get Help': 'https://github.com/your-repo/flashcard-generator',
                'Report a bug': 'https://github.com/your-repo/flashcard-generator/issues',
                'About': "AI-Powered Flashcard Generator - Transform your study materials into interactive flashcards!"
            }
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stAlert > div {
            padding-top: 1rem;
        }
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .flashcard-back {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .status-success {
            color: #28a745;
            font-weight: bold;
        }
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .status-error {
            color: #dc3545;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def setup_session_state(self):
        """Initialize session state variables"""
        default_states = {
            'uploaded_file_data': None,
            'processing_results': None,
            'flashcards': None,
            'current_card_index': 0,
            'show_answer': False,
            'processing_stage': 'upload',
            'processing_progress': 0,
            'error_messages': [],
            'app_initialized': False,
            'cache_hits': 0,
            'total_processing_time': 0
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def initialize_app(self):
        """Initialize the application configuration"""
        try:
            with st.spinner("🚀 Initializing AI-Powered Flashcard Generator..."):
                # Initialize configuration
                init_success, init_message = Config.initialize_app()
                
                if init_success:
                    st.success("✅ Application initialized successfully!")
                    st.session_state.app_initialized = True
                    logger.info("Application initialized successfully")
                else:
                    st.error(f"❌ Application initialization failed: {init_message}")
                    st.stop()
                    
        except Exception as e:
            st.error(f"❌ Critical initialization error: {str(e)}")
            st.stop()
    
    def run(self):
        """Main application entry point"""
        try:
            # Header
            self.render_header()
            
            # Sidebar
            self.render_sidebar()
            
            # Main content area
            main_col1, main_col2 = st.columns([2, 1])
            
            with main_col1:
                self.render_main_content()
            
            with main_col2:
                self.render_status_panel()
            
            # Footer
            self.render_footer()
            
        except Exception as e:
            st.error(f"❌ Application error: {str(e)}")
            logger.error(f"Application error: {e}")
    
    def render_header(self):
        """Render application header"""
        st.title("🧠 AI-Powered Flashcard Generator")
        st.markdown("""
        Transform your study materials into interactive flashcards using advanced AI! 
        Upload documents, images, or text files and let our AI create personalized flashcards for optimal learning.
        """)
        
        # Progress indicator
        if st.session_state.processing_stage != 'upload':
            progress_stages = ['upload', 'processing', 'analysis', 'generation', 'complete']
            current_stage_index = progress_stages.index(st.session_state.processing_stage)
            progress_value = (current_stage_index + 1) / len(progress_stages)
            
            st.progress(progress_value)
            st.markdown(f"**Current Stage:** {st.session_state.processing_stage.title()}")
    
    def render_sidebar(self):
        """Render sidebar with configuration and status"""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Service status
            self.render_service_status()
            
            st.markdown("---")
            
            # Processing options
            st.subheader("🎛️ Processing Options")
            
            # Flashcard type selection
            st.multiselect(
                "Flashcard Types",
                Config.FLASHCARD_TYPES,
                default=["definition", "conceptual"],
                help="Select the types of flashcards to generate",
                key="selected_flashcard_types"
            )
            
            # Difficulty distribution
            st.selectbox(
                "Difficulty Level",
                ["Auto (Recommended)", "Easy Focus", "Medium Focus", "Hard Focus"],
                help="Choose the difficulty distribution for flashcards",
                key="difficulty_preference"
            )
            
            # Number of flashcards
            st.slider(
                "Number of Flashcards",
                min_value=3,
                max_value=Config.MAX_TOTAL_CARDS,
                value=10,
                help=f"Choose how many flashcards to generate (max: {Config.MAX_TOTAL_CARDS})",
                key="flashcard_count"
            )
            
            st.markdown("---")
            
            # Processing statistics
            if st.session_state.processing_results:
                self.render_processing_stats()
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("🚀 Quick Actions")
            
            if st.button("🗑️ Clear All Data"):
                self.reset_application()
                st.rerun()
            
            if st.button("📊 View Config Summary"):
                self.show_config_summary()
            
            if st.button("💾 Export Results"):
                self.export_results()
    
    def render_service_status(self):
        """Render service availability status"""
        st.subheader("🔌 Service Status")
        
        services = Config.get_available_services()
        
        for service, available in services.items():
            service_name = service.replace('_', ' ').title()
            if available:
                st.success(f"✅ {service_name}")
            else:
                st.error(f"❌ {service_name}")
        
        # Overall status
        available_count = sum(services.values())
        total_count = len(services)
        
        if available_count == total_count:
            st.success("🎉 All services operational!")
        elif available_count > 0:
            st.warning(f"⚠️ {available_count}/{total_count} services available")
        else:
            st.error("❌ No services available")
    
    def render_main_content(self):
        """Render main content area based on current stage"""
        if st.session_state.processing_stage == 'upload':
            self.render_upload_stage()
        elif st.session_state.processing_stage == 'processing':
            self.render_processing_stage()
        elif st.session_state.processing_stage == 'analysis':
            self.render_analysis_stage()
        elif st.session_state.processing_stage == 'generation':
            self.render_generation_stage()
        elif st.session_state.processing_stage == 'complete':
            self.render_flashcard_review_stage()
    
    def render_upload_stage(self):
        """Render file upload stage"""
        st.header("📁 Step 1: Upload Your Study Material")
        
        # File upload interface
        uploaded_file_data = file_handler.create_upload_interface()
        
        if uploaded_file_data and not uploaded_file_data.get('error'):
            st.session_state.uploaded_file_data = uploaded_file_data
            
            # Show file information
            st.success("✅ File uploaded successfully!")
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    self.start_processing()
            
            with col2:
                if st.button("🔄 Upload Different File", use_container_width=True):
                    st.session_state.uploaded_file_data = None
                    st.rerun()
        
        elif uploaded_file_data and uploaded_file_data.get('error'):
            st.error(f"❌ {uploaded_file_data['error']}")
    
    def render_processing_stage(self):
        """Render document processing stage"""
        st.header("🔍 Step 2: Processing Document")
        
        if st.session_state.uploaded_file_data:
            # Start processing
            self.process_document()
        else:
            st.error("❌ No file data available. Please upload a file first.")
            if st.button("← Go Back to Upload"):
                st.session_state.processing_stage = 'upload'
                st.rerun()
    
    def render_analysis_stage(self):
        """Render text analysis stage"""
        st.header("🧠 Step 3: Analyzing Content")
        
        if st.session_state.processing_results:
            # Start analysis
            self.analyze_content()
        else:
            st.error("❌ No processing results available.")
            if st.button("← Go Back"):
                st.session_state.processing_stage = 'upload'
                st.rerun()
    
    def render_generation_stage(self):
        """Render flashcard generation stage"""
        st.header("🎴 Step 4: Generating Flashcards")
        
        if st.session_state.processing_results:
            # Start flashcard generation
            self.generate_flashcards()
        else:
            st.error("❌ No analysis results available.")
            if st.button("← Go Back"):
                st.session_state.processing_stage = 'upload'
                st.rerun()
    
    def render_flashcard_review_stage(self):
        """Render flashcard review and interaction stage"""
        st.header("🎓 Step 5: Study Your Flashcards")
        
        if st.session_state.flashcards:
            self.render_flashcard_interface()
        else:
            st.error("❌ No flashcards available.")
            if st.button("← Generate Flashcards Again"):
                st.session_state.processing_stage = 'generation'
                st.rerun()
    
    def render_flashcard_interface(self):
        """Render interactive flashcard interface"""
        flashcards = st.session_state.flashcards
        
        if not flashcards or 'flashcards' not in flashcards:
            st.error("❌ No flashcards found in results.")
            return
        
        all_cards = []
        for card_type, cards in flashcards['flashcards'].items():
            if isinstance(cards, list):
                for card in cards:
                    card['type'] = card_type
                    all_cards.append(card)
        
        if not all_cards:
            st.warning("⚠️ No flashcards were generated. Try adjusting your settings and regenerating.")
            return
        
        # Flashcard navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("← Previous", disabled=st.session_state.current_card_index == 0):
                st.session_state.current_card_index = max(0, st.session_state.current_card_index - 1)
                st.session_state.show_answer = False
                st.rerun()
        
        with col2:
            st.markdown(f"**Card {st.session_state.current_card_index + 1} of {len(all_cards)}**")
            
            # Card type indicator
            current_card = all_cards[st.session_state.current_card_index]
            card_type = current_card.get('type', 'unknown').title()
            difficulty = current_card.get('difficulty', 'medium').title()
            
            st.markdown(f"*Type: {card_type} | Difficulty: {difficulty}*")
        
        with col3:
            if st.button("Next →", disabled=st.session_state.current_card_index >= len(all_cards) - 1):
                st.session_state.current_card_index = min(len(all_cards) - 1, st.session_state.current_card_index + 1)
                st.session_state.show_answer = False
                st.rerun()
        
        st.markdown("---")
        
        # Current flashcard
        current_card = all_cards[st.session_state.current_card_index]
        
        # Question side
        st.markdown(f"""
        <div class="flashcard">
            <h3>❓ Question</h3>
            <p style="font-size: 1.2em; line-height: 1.6;">{current_card.get('question', 'No question available')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show/Hide answer button
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if not st.session_state.show_answer:
                if st.button("👁️ Show Answer", type="primary", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                if st.button("🙈 Hide Answer", use_container_width=True):
                    st.session_state.show_answer = False
                    st.rerun()
        
        # Answer side (if shown)
        if st.session_state.show_answer:
            st.markdown(f"""
            <div class="flashcard-back">
                <h3>✅ Answer</h3>
                <p style="font-size: 1.2em; line-height: 1.6;">{current_card.get('answer', 'No answer available')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Confidence scoring
            st.markdown("### 📊 How well did you know this?")
            confidence_col1, confidence_col2, confidence_col3 = st.columns(3)
            
            with confidence_col1:
                if st.button("😔 Need to Review", use_container_width=True):
                    self.record_confidence("low")
            
            with confidence_col2:
                if st.button("🤔 Somewhat Familiar", use_container_width=True):
                    self.record_confidence("medium")
            
            with confidence_col3:
                if st.button("😊 Knew It Well", use_container_width=True):
                    self.record_confidence("high")
        
        st.markdown("---")
        
        # Study session controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Regenerate Flashcards"):
                st.session_state.processing_stage = 'generation'
                st.rerun()
        
        with col2:
            if st.button("📊 Study Statistics"):
                self.show_study_statistics(all_cards)
        
        with col3:
            if st.button("💾 Export Flashcards"):
                self.export_flashcards(all_cards)
    
    def render_status_panel(self):
        """Render status panel with progress and information"""
        st.subheader("📊 Status Panel")
        
        # Current stage info
        stage_info = {
            'upload': {'icon': '📁', 'description': 'Ready to upload files'},
            'processing': {'icon': '🔍', 'description': 'Extracting text content'},
            'analysis': {'icon': '🧠', 'description': 'Analyzing content quality'},
            'generation': {'icon': '🎴', 'description': 'Creating flashcards'},
            'complete': {'icon': '🎓', 'description': 'Ready for studying'}
        }
        
        current_stage = st.session_state.processing_stage
        stage_data = stage_info.get(current_stage, {'icon': '❓', 'description': 'Unknown stage'})
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>{stage_data['icon']} Current Stage</h4>
            <p><strong>{current_stage.title()}</strong></p>
            <p>{stage_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Processing metrics
        if st.session_state.processing_results:
            self.render_processing_metrics()
        
        # Error log
        if st.session_state.error_messages:
            st.subheader("⚠️ Issues & Warnings")
            for error in st.session_state.error_messages[-3:]:  # Show last 3 errors
                st.warning(error)
    
    def render_processing_metrics(self):
        """Render processing metrics and statistics"""
        results = st.session_state.processing_results
        
        st.subheader("📈 Processing Metrics")
        
        # Text extraction metrics
        if 'document_result' in results:
            doc_result = results['document_result']
            text_extraction = doc_result.get('text_extraction', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Text Extracted",
                    f"{len(text_extraction.get('extracted_text', ''))} chars"
                )
            
            with col2:
                confidence = text_extraction.get('processing_metadata', {}).get('overall_confidence', 0)
                st.metric("OCR Confidence", f"{confidence:.1%}")
        
        # Language analysis metrics
        if 'language_result' in results:
            lang_result = results['language_result']
            
            col1, col2 = st.columns(2)
            
            with col1:
                key_phrases = len(lang_result.get('key_phrases', {}).get('azure_key_phrases', []))
                st.metric("Key Phrases", key_phrases)
            
            with col2:
                quality = lang_result.get('study_assessment', {}).get('overall_quality', 'unknown')
                quality_color = {
                    'excellent': 'status-success',
                    'good': 'status-success',
                    'fair': 'status-warning',
                    'poor': 'status-error'
                }.get(quality, '')
                
                st.markdown(f'<p class="{quality_color}">Content Quality: {quality.title()}</p>', 
                           unsafe_allow_html=True)
    
    def render_processing_stats(self):
        """Render detailed processing statistics in sidebar"""
        st.subheader("📊 Processing Stats")
        
        results = st.session_state.processing_results
        
        # Cache statistics
        st.metric("Cache Hits", st.session_state.cache_hits)
        
        # Processing time
        if st.session_state.total_processing_time > 0:
            st.metric("Processing Time", f"{st.session_state.total_processing_time:.1f}s")
        
        # Content statistics
        if 'language_result' in results:
            lang_result = results['language_result']
            
            # Word count
            word_count = lang_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("Word Count", word_count)
            
            # Entities found
            entities = lang_result.get('entities', {}).get('unique_entities', 0)
            st.metric("Entities Found", entities)
    
    def start_processing(self):
        """Start the document processing workflow"""
        st.session_state.processing_stage = 'processing'
        st.session_state.processing_progress = 0
        st.rerun()
    
    def process_document(self):
        """Process uploaded document with progress tracking"""
        start_time = time.time()
        
        try:
            file_data = st.session_state.uploaded_file_data
            
            # Progress container
            progress_container = st.empty()
            status_container = st.empty()
            
            def update_progress(message: str):
                progress_container.progress(st.session_state.processing_progress)
                status_container.info(f"🔍 {message}")
                st.session_state.processing_progress = min(st.session_state.processing_progress + 0.1, 0.9)
            
            # Check cache first
            file_hash = file_data.get('file_hash')
            cached_result = file_handler._get_cached_result(file_hash) if file_hash else None
            
            if cached_result:
                st.session_state.cache_hits += 1
                st.session_state.processing_results = cached_result
                update_progress("Loading from cache...")
                time.sleep(1)  # Brief delay to show cache hit
                progress_container.progress(1.0)
                status_container.success("✅ Processing completed (cached)")
                st.session_state.processing_stage = 'analysis'
                time.sleep(2)
                st.rerun()
                return
            
            update_progress("Preparing document for processing...")
            
            # Process with Azure Document Intelligence
            document_result = azure_document_processor.extract_text_with_handwriting(
                file_data['file_data']['file_bytes'],
                file_data['file_data']['content_type'],
                update_progress
            )
            
            if document_result.get('status') == 'error':
                raise Exception(document_result.get('error', 'Document processing failed'))
            
            # Store results
            st.session_state.processing_results = {
                'document_result': document_result,
                'file_metadata': file_data['metadata']
            }
            
            # Cache the result
            if file_hash:
                file_handler.cache_result(file_hash, st.session_state.processing_results)
            
            # Record processing time
            st.session_state.total_processing_time = time.time() - start_time
            
            progress_container.progress(1.0)
            status_container.success("✅ Document processing completed!")
            
            # Advance to next stage
            st.session_state.processing_stage = 'analysis'
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            error_msg = f"Document processing error: {str(e)}"
            st.error(f"❌ {error_msg}")
            st.session_state.error_messages.append(error_msg)
            logger.error(error_msg)
    
    def analyze_content(self):
        """Analyze extracted content with Azure Language Services"""
        try:
            results = st.session_state.processing_results
            document_result = results['document_result']
            
            # Extract text for analysis
            extracted_text = document_result.get('text_extraction', {}).get('extracted_text', '')
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                st.error("❌ Insufficient text extracted for analysis")
                return
            
            # Progress tracking
            progress_container = st.empty()
            status_container = st.empty()
            
            def update_progress(message: str):
                progress_container.progress(st.session_state.processing_progress)
                status_container.info(f"🧠 {message}")
                st.session_state.processing_progress = min(st.session_state.processing_progress + 0.1, 0.9)
            
            update_progress("Starting content analysis...")
            
            # Analyze with Azure Language Services
            language_result = azure_language_processor.analyze_for_study_materials(
                extracted_text,
                update_progress
            )
            
            if language_result.get('status') == 'error':
                st.warning("⚠️ Language analysis encountered issues, using fallback processing")
                if 'fallback_analysis' in language_result:
                    language_result = language_result['fallback_analysis']
            
            # Update results
            st.session_state.processing_results['language_result'] = language_result
            
            progress_container.progress(1.0)
            status_container.success("✅ Content analysis completed!")
            
            # Show analysis summary
            self.show_analysis_summary(language_result)
            
            # Advance to flashcard generation
            st.session_state.processing_stage = 'generation'
            
            if st.button("🎴 Generate Flashcards", type="primary"):
                st.rerun()
            
        except Exception as e:
            error_msg = f"Content analysis error: {str(e)}"
            st.error(f"❌ {error_msg}")
            st.session_state.error_messages.append(error_msg)
            logger.error(error_msg)
    
    def generate_flashcards(self):
        """Generate flashcards using Gemini AI"""
        try:
            results = st.session_state.processing_results
            language_result = results['language_result']
            
            # Extract necessary data
            extracted_text = language_result.get('cleaned_text', '')
            summary_data = language_result.get('summary', {})
            key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
            
            if not extracted_text:
                st.error("❌ No text available for flashcard generation")
                return
            
            # Progress tracking
            progress_container = st.empty()
            status_container = st.empty()
            
            def update_progress(message: str):
                progress_container.progress(st.session_state.processing_progress)
                status_container.info(f"🎴 {message}")
                st.session_state.processing_progress = min(st.session_state.processing_progress + 0.1, 0.9)
            
            update_progress("Generating flashcards with AI...")
            
            # Generate flashcards
            flashcard_result = self.flashcard_generator.generate_comprehensive_flashcards(
                extracted_text,
                summary_data,
                key_phrases,
                update_progress
            )
            
            if flashcard_result.get('error'):
                raise Exception(flashcard_result['error'])
            
            # Store flashcards
            st.session_state.flashcards = flashcard_result
            
            progress_container.progress(1.0)
            status_container.success("✅ Flashcards generated successfully!")
            
            # Show generation summary
            self.show_generation_summary(flashcard_result)
            
            # Advance to review stage
            st.session_state.processing_stage = 'complete'
            st.session_state.current_card_index = 0
            st.session_state.show_answer = False
            
            if st.button("🎓 Start Studying", type="primary"):
                st.rerun()
            
        except Exception as e:
            error_msg = f"Flashcard generation error: {str(e)}"
            st.error(f"❌ {error_msg}")
            st.session_state.error_messages.append(error_msg)
            logger.error(error_msg)
    
    def show_analysis_summary(self, language_result: Dict):
        """Show summary of content analysis"""
        st.subheader("📊 Content Analysis Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            word_count = language_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("Words Analyzed", word_count)
        
        with col2:
            key_phrases_count = len(language_result.get('key_phrases', {}).get('azure_key_phrases', []))
            st.metric("Key Phrases Found", key_phrases_count)
        
        with col3:
            quality = language_result.get('study_assessment', {}).get('overall_quality', 'unknown')
            st.metric("Content Quality", quality.title())
        
        # Key phrases preview
        key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])[:5]
        if key_phrases:
            st.write("**Top Key Phrases:**", ", ".join(key_phrases))
        
        # Recommendations
        recommendations = language_result.get('study_assessment', {}).get('recommendations', [])
        if recommendations:
            st.write("**Recommendations:**")
            for rec in recommendations:
                st.write(f"• {rec}")
    
    def show_generation_summary(self, flashcard_result: Dict):
        """Show summary of flashcard generation"""
        st.subheader("🎴 Flashcard Generation Summary")
        
        flashcards = flashcard_result.get('flashcards', {})
        
        total_cards = 0
        for card_type, cards in flashcards.items():
            if isinstance(cards, list):
                count = len(cards)
                total_cards += count
                st.write(f"**{card_type.title()} Cards:** {count}")
        
        st.success(f"🎉 Generated {total_cards} flashcards total!")
        
        # Quality indicators
        generation_metadata = flashcard_result.get('generation_metadata', {})
        if generation_metadata:
            st.write("**Generation Quality:**")
            avg_confidence = generation_metadata.get('average_confidence', 0)
            st.write(f"• Average Confidence: {avg_confidence:.1%}")
    
    def record_confidence(self, level: str):
        """Record user confidence for spaced repetition"""
        # This would integrate with a spaced repetition system
        current_card = st.session_state.current_card_index
        st.success(f"✅ Recorded {level} confidence for card {current_card + 1}")
        
        # Auto-advance to next card
        if st.session_state.current_card_index < len(self.get_all_flashcards()) - 1:
            st.session_state.current_card_index += 1
            st.session_state.show_answer = False
            st.rerun()
    
    def get_all_flashcards(self) -> List[Dict]:
        """Get all flashcards as a flat list"""
        if not st.session_state.flashcards:
            return []
        
        all_cards = []
        flashcards = st.session_state.flashcards.get('flashcards', {})
        
        for card_type, cards in flashcards.items():
            if isinstance(cards, list):
                for card in cards:
                    card['type'] = card_type
                    all_cards.append(card)
        
        return all_cards
    
    def show_study_statistics(self, all_cards: List[Dict]):
        """Show study session statistics"""
        st.subheader("📊 Study Statistics")
        
        # Card type distribution
        type_counts = {}
        difficulty_counts = {}
        
        for card in all_cards:
            card_type = card.get('type', 'unknown')
            difficulty = card.get('difficulty', 'medium')
            
            type_counts[card_type] = type_counts.get(card_type, 0) + 1
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Cards by Type:**")
            for card_type, count in type_counts.items():
                st.write(f"• {card_type.title()}: {count}")
        
        with col2:
            st.write("**Cards by Difficulty:**")
            for difficulty, count in difficulty_counts.items():
                st.write(f"• {difficulty.title()}: {count}")
    
    def export_flashcards(self, all_cards: List[Dict]):
        """Export flashcards in various formats"""
        st.subheader("💾 Export Flashcards")
        
        export_format = st.selectbox(
            "Choose export format:",
            ["JSON", "CSV", "Text File", "Anki Deck"]
        )
        
        if st.button("Download Flashcards"):
            try:
                if export_format == "JSON":
                    export_data = json.dumps(all_cards, indent=2)
                    st.download_button(
                        "📥 Download JSON",
                        export_data,
                        f"flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
                
                elif export_format == "Text File":
                    text_data = self.format_flashcards_as_text(all_cards)
                    st.download_button(
                        "📥 Download Text",
                        text_data,
                        f"flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        "text/plain"
                    )
                
                # Add other format implementations as needed
                
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    def format_flashcards_as_text(self, all_cards: List[Dict]) -> str:
        """Format flashcards as plain text"""
        text_lines = ["AI-Generated Flashcards", "=" * 30, ""]
        
        for i, card in enumerate(all_cards, 1):
            text_lines.extend([
                f"Card {i} ({card.get('type', 'unknown').title()}) - {card.get('difficulty', 'medium').title()}",
                "-" * 40,
                f"Q: {card.get('question', 'No question')}",
                f"A: {card.get('answer', 'No answer')}",
                ""
            ])
        
        return "\n".join(text_lines)
    
    def reset_application(self):
        """Reset application to initial state"""
        keys_to_reset = [
            'uploaded_file_data', 'processing_results', 'flashcards',
            'current_card_index', 'show_answer', 'processing_progress',
            'error_messages'
        ]
        
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.processing_stage = 'upload'
        st.success("🔄 Application reset successfully!")
    
    def show_config_summary(self):
        """Show configuration summary"""
        st.subheader("⚙️ Configuration Summary")
        
        config_summary = Config.get_config_summary()
        
        for section, data in config_summary.items():
            st.write(f"**{section.replace('_', ' ').title()}:**")
            if isinstance(data, dict):
                for key, value in data.items():
                    st.write(f"  • {key}: {value}")
            else:
                st.write(f"  • {data}")
    
    def export_results(self):
        """Export all processing results"""
        if st.session_state.processing_results:
            export_data = {
                'processing_results': st.session_state.processing_results,
                'flashcards': st.session_state.flashcards,
                'export_timestamp': datetime.now().isoformat()
            }
            
            st.download_button(
                "📥 Download Results",
                json.dumps(export_data, indent=2),
                f"processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
        else:
            st.warning("⚠️ No results to export")
    
    def render_footer(self):
        """Render application footer"""
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9em;">
            🧠 AI-Powered Flashcard Generator | 
            Built with Streamlit, Azure AI, and Google Gemini | 
            © 2024
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    try:
        app = FlashcardApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Critical application error: {str(e)}")
        logger.error(f"Critical application error: {e}")

if __name__ == "__main__":
    main()