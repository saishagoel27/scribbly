import streamlit as st
import logging
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import our components
from config import Config
from file_handler import file_handler
from azure_document import azure_document_processor
from azure_language import azure_language_processor
from flashcards import gemini_generator

logger = logging.getLogger(__name__)

class FlashcardApp:
    """Streamlit application"""
    
    def __init__(self):
        self.setup_page_config()
        self.init_session_state()
    
    def setup_page_config(self):
        """Page configuration with essential CSS"""
        st.set_page_config(
            page_title="🧠 Scribbly - AI Study Helper",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS - essential styles only
        st.markdown("""
        <style>
        /* Clean, modern styling without bloat */
        .main > div { padding-top: 1rem; }
        
        /* MAIN PAGE ACCESS BUTTON - PROMINENT */
        .main-access-button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white !important;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
            border: 3px solid #34d399;
        }
        .main-access-button h2 { 
            color: white !important; 
            margin-bottom: 1rem; 
            font-size: 1.8rem !important;
        }
        .main-access-button p { 
            color: #d1fae5 !important; 
            margin: 0; 
            font-size: 1.1rem;
        }
        
        /* Action buttons */
        .action-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .action-button h3 { color: white !important; margin-bottom: 0.5rem; }
        .action-button p { color: #e8eaff !important; margin: 0; }
        
        /* Results cards */
        .results-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: 2px solid #667eea;
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }
        .results-card h3 { color: #1e293b !important; margin-bottom: 1rem; }
        .results-card p { color: #475569 !important; margin-bottom: 1.5rem; }
        
        /* Flashcards */
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .flashcard-back {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Enhanced summary boxes */
        .summary-box {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            color: #2c3e50 !important;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #3498db;
            margin: 1.5rem 0;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.1);
        }
        .summary-box h3 { color: #1e3a8a !important; margin-bottom: 1rem; }
        .summary-box p { color: #374151 !important; margin: 0; line-height: 1.6; }
        
        /* Key concepts */
        .key-concept-tag {
            background: #4f46e5 !important;
            color: white !important;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9em;
            display: inline-block;
            margin: 0.3rem 0.2rem;
            font-weight: 600;
        }
        
        /* Navigation bar */
        .nav-bar {
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
            border: 1px solid #cbd5e1;
        }
        
        /* Progress styling */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Enhanced tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            padding: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px;
            color: #374151 !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = 1
        if 'processing_results' not in st.session_state:
            st.session_state.processing_results = {}
        if 'flashcards' not in st.session_state:
            st.session_state.flashcards = []
        if 'study_settings' not in st.session_state:
            st.session_state.study_settings = {
                'num_flashcards': 10,
                'difficulty': 'Mixed (Recommended)'
            }
        # Initialize flashcard study variables
        if 'current_card' not in st.session_state:
            st.session_state.current_card = 0
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False
        if 'study_stats' not in st.session_state:
            st.session_state.study_stats = {'correct': 0, 'incorrect': 0, 'total': 0}
    
    def run(self):
        """Main application runner - simplified flow"""
        # Sidebar
        self.render_sidebar()
        
        # Header
        st.markdown("# 🧠 Scribbly - AI Study Helper")
        st.markdown("Transform your notes into interactive flashcards with AI")
        
        # MAIN PAGE ACCESS BUTTON - PROMINENT DISPLAY
        self.render_main_access_button()
        
        # Progress indicator
        self.render_progress_indicator()
        
        # Main content based on stage
        if st.session_state.current_stage == 1:
            self.render_upload_stage()
        elif st.session_state.current_stage == 2:
            self.render_generation_options()
        elif st.session_state.current_stage == 3:
            self.render_processing_stage()
        elif st.session_state.current_stage == 4:
            self.render_study_mode()
    
    def render_main_access_button(self):
        """MAIN PAGE BUTTON - Shows prominently when content is generated"""
        
        # Only show if content has been generated
        if (st.session_state.processing_results and 
            (st.session_state.flashcards or 
             st.session_state.processing_results.get('language_result'))):
            
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            
            # Count what was generated
            flashcard_count = len(st.session_state.flashcards)
            language_result = st.session_state.processing_results.get('language_result', {})
            summary_data = language_result.get('summary', {})
            summary_count = len([k for k, v in summary_data.items() if v])
            
            # Create content description
            if generation_choice == "flashcards_only":
                content_desc = f"🃏 {flashcard_count} Interactive Flashcards"
            elif generation_choice == "summary_only":
                content_desc = f"📄 {summary_count} AI Summaries & Key Concepts"
            else:
                content_desc = f"🃏 {flashcard_count} Flashcards + 📄 {summary_count} AI Summaries"
            
            # PROMINENT ACCESS BUTTON
            st.markdown(f"""
            <div class="main-access-button">
                <h2>🎉 Your AI Study Materials are Ready!</h2>
                <p>{content_desc} generated and waiting for you</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Big access button
            if st.button("🚀 ACCESS YOUR STUDY MATERIALS", 
                        key="main_access_btn", 
                        type="primary", 
                        use_container_width=True):
                st.session_state.current_stage = 4
                st.session_state.view_mode = "summary" if generation_choice == "summary_only" else "browse"
                st.rerun()
            
            st.markdown("---")
    
    def render_sidebar(self):
        """SIMPLIFIED sidebar - REMOVED FOCUS MODE"""
        with st.sidebar:
            st.markdown("## ⚙️ Study Settings")
            
            # Service status
            services = Config.get_available_services()
            st.markdown("### 🔧 Services")
            for service, available in services.items():
                emoji = "✅" if available else "❌"
                name = service.replace('_', ' ').title()
                st.markdown(f"{emoji} {name}")
            
            st.divider()
            
            # Study configuration - SIMPLIFIED
            st.markdown("### 📚 Configuration")
            
            st.session_state.study_settings['num_flashcards'] = st.slider(
                "Number of Flashcards", 5, 20, 
                st.session_state.study_settings['num_flashcards']
            )
            
            st.session_state.study_settings['difficulty'] = st.selectbox(
                "Difficulty Focus",
                ["Mixed (Recommended)", "Basic Concepts", "Advanced Topics", "Application-Based"],
                index=0
            )
            
            # REMOVED FOCUS MODE BUTTON AS REQUESTED
            
            st.divider()
            
            if st.button("🔄 Start Over", key="sidebar_start_over", use_container_width=True):
                self.reset_session()
    
    def reset_session(self):
        """Reset session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    def render_progress_indicator(self):
        """Simple progress indicator"""
        steps = ["📁 Upload", "🎯 Choose", "🔍 Process", "📚 Study"]
        current = st.session_state.current_stage
        
        st.progress(current / len(steps))
        
        cols = st.columns(len(steps))
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                if i + 1 == current:
                    st.markdown(f"**{step}** ⭐")
                elif i + 1 < current:
                    st.markdown(f"~~{step}~~ ✅")
                else:
                    st.markdown(f"{step}")
    
    def render_upload_stage(self):
        """Simple file upload"""
        st.header("📁 Upload Your Study Material")
        st.markdown("Upload PDFs, images, or documents to create flashcards")
        
        uploaded_file_data = file_handler.create_upload_interface()
        
        if uploaded_file_data and not uploaded_file_data.get('error'):
            st.session_state.uploaded_file_data = uploaded_file_data
            st.success("✅ File uploaded successfully!")
            
            # Show file info
            metadata = uploaded_file_data.get('metadata', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📁 Size", f"{metadata.get('file_size_mb', 0):.1f} MB")
            with col2:
                st.metric("📄 Type", metadata.get('file_extension', 'Unknown').upper())
            with col3:
                st.metric("📋 Pages", metadata.get('estimated_pages', 1))
            
            if st.button("➡️ Choose What to Generate", key="upload_next", type="primary", use_container_width=True):
                st.session_state.current_stage = 2
                st.rerun()
        
        elif uploaded_file_data and uploaded_file_data.get('error'):
            st.error(f"❌ {uploaded_file_data['error']}")
    
    def render_generation_options(self):
        """Simple generation choice interface"""
        st.header("🎯 Choose What to Generate")
        
        if 'uploaded_file_data' in st.session_state:
            metadata = st.session_state.uploaded_file_data.get('metadata', {})
            st.info(f"📄 Ready to process: **{metadata.get('filename', 'Your file')}**")
        
        # Generation options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="action-button">
                <h3>🃏 Smart Flashcards</h3>
                <p>Generate interactive flashcards with Gemini AI</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Generate Flashcards Only", key="gen_flashcards", use_container_width=True, type="primary"):
                st.session_state.generation_choice = "flashcards_only"
                st.session_state.current_stage = 3
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="action-button">
                <h3>📄 AI Summary</h3>
                <p>Create summaries with Azure Language Services</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📝 Generate Summary Only", key="gen_summary", use_container_width=True):
                st.session_state.generation_choice = "summary_only"
                st.session_state.current_stage = 3
                st.rerun()
        
        # Combined option
        st.markdown("### 🌟 Recommended")
        st.markdown("""
        <div class="action-button">
            <h3>🎯 Complete Study Package</h3>
            <p>Generate both flashcards and summaries</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Generate Everything", key="gen_complete", use_container_width=True, type="primary"):
            st.session_state.generation_choice = "complete_package"
            st.session_state.current_stage = 3
            st.rerun()
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Upload", key="gen_back", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
    
    def render_processing_stage(self):
        """Simple processing stage"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        if generation_choice == "flashcards_only":
            st.header("🃏 Generating Flashcards")
        elif generation_choice == "summary_only":
            st.header("📄 Creating Summary")
        else:
            st.header("🔍 Creating Study Package")
        
        if not st.session_state.processing_results:
            self.execute_processing()
        else:
            self.show_results()
    
    def execute_processing(self):
        """Simple processing pipeline"""
        try:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            file_data = st.session_state.uploaded_file_data.get('file_data', {})
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(message: str, progress: float):
                status_text.text(message)
                progress_bar.progress(progress)
                time.sleep(0.3)
            
            # Step 1: Extract text
            update_progress("🔍 Extracting text...", 0.2)
            document_result = azure_document_processor.extract_text_with_handwriting(
                file_data.get('file_bytes'), 
                file_data.get('content_type'), 
                update_progress
            )
            
            if document_result.get('error'):
                st.error(f"❌ Text extraction failed: {document_result['error']}")
                return
            
            extracted_text = document_result.get('extracted_text', '')
            if len(extracted_text.strip()) < 50:
                st.error("❌ Not enough text extracted")
                return
            
            st.session_state.processing_results['document_result'] = document_result
            
            # Step 2: Language analysis
            language_result = None
            if generation_choice in ["summary_only", "complete_package"]:
                update_progress("🧠 Analyzing content...", 0.5)
                
                language_result = azure_language_processor.analyze_for_study_materials(
                    extracted_text, lambda msg: update_progress(msg, 0.6)
                )
                
                if language_result.get('error'):
                    language_result = azure_language_processor._create_fallback_analysis(extracted_text)
                
                st.session_state.processing_results['language_result'] = language_result
            
            # Step 3: Generate flashcards 
            if generation_choice in ["flashcards_only", "complete_package"]:
                update_progress("🃏 Creating flashcards...", 0.8)
                
                generation_params = {
                    'num_flashcards': st.session_state.study_settings['num_flashcards'],
                    'difficulty_focus': st.session_state.study_settings['difficulty'],
                    'key_phrases': language_result.get('key_phrases', {}).get('azure_key_phrases', []) if language_result else []
                }
                
                flashcards_result = gemini_generator.generate_enhanced_flashcards(
                    extracted_text, generation_params, 
                    lambda msg, prog: update_progress(msg, 0.8 + prog * 0.2)
                )
                
                if flashcards_result.get('error'):
                    flashcards_result = gemini_generator.generate_fallback_flashcards(extracted_text)
                
                st.session_state.flashcards = flashcards_result.get('flashcards', [])
                st.session_state.processing_results['flashcards_result'] = flashcards_result
            
            update_progress("✅ Complete!", 1.0)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            st.error(f"❌ Processing failed: {str(e)}")

    def show_results(self):
        """SIMPLIFIED results display - directs to main page button"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        st.success("✅ Generation completed!")
        
        # Show summary of what was created
        if generation_choice == "flashcards_only":
            st.markdown(f"### 🎉 Generated {len(st.session_state.flashcards)} flashcards!")
            st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to view your flashcards")
        
        elif generation_choice == "summary_only":
            language_result = st.session_state.processing_results.get('language_result', {})
            summary_data = language_result.get('summary', {})
            summary_count = len([k for k, v in summary_data.items() if v])
            st.markdown(f"### 📄 Generated {summary_count} AI summaries!")
            st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to view your summaries")
        
        else:  # complete_package
            language_result = st.session_state.processing_results.get('language_result', {})
            summary_data = language_result.get('summary', {})
            summary_count = len([k for k, v in summary_data.items() if v])
            
            st.markdown("### 🌟 Complete study package created!")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🃏 Flashcards", len(st.session_state.flashcards))
            with col2:
                st.metric("📄 AI Summaries", f"{summary_count} Types")
            
            st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to explore everything!")
        
        # Simple navigation
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Generate Something Else", key="result_back", use_container_width=True):
                st.session_state.processing_results = {}
                st.session_state.flashcards = []
                st.session_state.current_stage = 2
                st.rerun()
        with col2:
            if st.button("🔄 Start Over", key="result_restart", use_container_width=True):
                self.reset_session()
    
    def render_study_mode(self):
        """Enhanced study mode with proper navigation"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        view_mode = st.session_state.get('view_mode', 'study')
        
        # Always show navigation bar at top
        self.render_navigation_bar()
        
        # Handle different view modes
        if view_mode == "browse":
            self.render_flashcard_browser()
        elif view_mode == "summary":
            self.render_summary_viewer()
        elif view_mode == "concepts":
            self.render_concepts_viewer()
        else:
            # Default study interface
            if generation_choice == "summary_only":
                self.render_summary_study()
            else:
                self.render_flashcard_study()
    
    def render_navigation_bar(self):
        """Enhanced navigation bar for study mode"""
        generation_choice = st.session_state.get('generation_choice', 'complete_package')
        
        st.markdown("""
        <div class="nav-bar">
            <h4 style="margin: 0; color: #1e293b;">🧭 Navigation</h4>
            <p style="margin: 0.5rem 0 0 0; color: #64748b;">Switch between different views</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create dynamic navigation based on what's available
        nav_options = []
        
        if generation_choice in ["flashcards_only", "complete_package"]:
            nav_options.extend([
                ("🃏 Browse Flashcards", "browse"),
                ("🎯 Study Mode", "study")
            ])
        
        if generation_choice in ["summary_only", "complete_package"]:
            nav_options.extend([
                ("📖 AI Summary", "summary"),
                ("🔑 Key Concepts", "concepts")
            ])
        
        # Create columns for navigation
        if len(nav_options) > 0:
            cols = st.columns(len(nav_options))
            for i, (label, mode) in enumerate(nav_options):
                with cols[i]:
                    if st.button(label, key=f"nav_{mode}", use_container_width=True):
                        st.session_state.view_mode = mode
                        st.rerun()
        
        st.markdown("---")
    
    def render_flashcard_browser(self):
        """Enhanced flashcard browser"""
        st.header("🃏 Browse Your Flashcards")
        
        if not st.session_state.flashcards:
            st.warning("No flashcards available")
            return
        
        # Show total count
        st.info(f"📊 **{len(st.session_state.flashcards)} flashcards** generated from your content")
        
        # Display flashcards in a more organized way
        for i, card in enumerate(st.session_state.flashcards, 1):
            with st.expander(f"📚 Flashcard {i} - {card.get('concept', 'General')} ({card.get('difficulty', 'medium').title()})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="flashcard">
                        <h4>🤔 Question</h4>
                        <p>{card.get('question', 'No question')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="flashcard-back">
                        <h4>💡 Answer</h4>
                        <p>{card.get('answer', 'No answer')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Quick action buttons
        st.markdown("### 🚀 Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Start Studying Now", key="browser_study", type="primary", use_container_width=True):
                st.session_state.view_mode = "study"
                st.rerun()
        with col2:
            if st.button("⬅️ Back to Main", key="browser_back", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
    
    def render_summary_viewer(self):
        """ENHANCED summary viewer with better presentation"""
        st.header("📄 AI-Generated Summary")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("No summary available")
            return
        
        language_result = st.session_state.processing_results['language_result']
        summary_data = language_result.get('summary', {})
        
        # Display enhanced summary with tabs
        if summary_data:
            st.markdown("### 🎯 Choose Your Summary Style")
            
            # Create tabs for different summary types
            available_tabs = []
            tab_content = []
            
            if summary_data.get('best'):
                available_tabs.append("🌟 Best Summary")
                tab_content.append(('best', '🎯 AI-Optimized Summary', summary_data.get('best', '')))
            
            if summary_data.get('abstractive'):
                available_tabs.append("✨ AI Generated")
                tab_content.append(('abstractive', '✨ AI-Generated Summary', summary_data.get('abstractive', '')))
            
            if summary_data.get('extractive'):
                available_tabs.append("📋 Key Sentences")
                tab_content.append(('extractive', '📋 Key Sentences', summary_data.get('extractive', '')))
            
            if available_tabs:
                tabs = st.tabs(available_tabs)
                
                for tab, (key, title, content) in zip(tabs, tab_content):
                    with tab:
                        if content:
                            st.markdown(f"""
                            <div class="summary-box">
                                <h3>{title}</h3>
                                <p>{content}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info(f"No {title.lower()} available")
            else:
                st.warning("No summaries available")
        
        # Key concepts section
        key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
        if key_phrases:
            st.markdown("### 🔑 Key Concepts from Your Content")
            st.markdown("*These concepts were automatically identified by Azure AI*")
            
            # Display concepts in a nicer format
            concepts_html = ""
            for phrase in key_phrases[:20]:  # Show more concepts
                concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
            st.markdown(concepts_html, unsafe_allow_html=True)
        
        # Content analysis metrics
        st.markdown("### 📊 Content Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            word_count = language_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("📝 Total Words", f"{word_count:,}")
        
        with col2:
            st.metric("🔑 Key Concepts", len(key_phrases))
        
        with col3:
            quality = language_result.get('study_assessment', {}).get('overall_quality', 'good')
            st.metric("📚 Content Quality", quality.title())
        
        # Enhanced navigation
        st.markdown("### 🚀 What's Next?")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["flashcards_only", "complete_package"]:
                if st.button("🃏 View Flashcards", key="summary_flashcards", use_container_width=True):
                    st.session_state.view_mode = "browse"
                    st.rerun()
        
        with col2:
            if generation_choice in ["flashcards_only", "complete_package"]:
                if st.button("🎯 Start Studying", key="summary_study", type="primary", use_container_width=True):
                    st.session_state.view_mode = "study"
                    st.rerun()
        
        with col3:
            if st.button("⬅️ Back to Main", key="summary_back", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
    
    def render_concepts_viewer(self):
        """Enhanced concepts viewer"""
        st.header("🔑 Key Concepts Analysis")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("No concept analysis available")
            return
        
        language_result = st.session_state.processing_results['language_result']
        key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
        
        if key_phrases:
            st.markdown("### 🎯 Important Concepts Identified")
            st.markdown("*These concepts were automatically extracted using Azure AI Language Services*")
            
            # Display concepts in a nicer format
            concepts_html = ""
            for phrase in key_phrases:
                concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
            st.markdown(concepts_html, unsafe_allow_html=True)
        
        # Enhanced metrics
        st.markdown("### 📊 Content Analysis Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            word_count = language_result.get('text_complexity', {}).get('word_count', 0)
            st.metric("📝 Total Words", f"{word_count:,}")
        
        with col2:
            st.metric("🔑 Key Concepts", len(key_phrases))
        
        with col3:
            quality = language_result.get('study_assessment', {}).get('overall_quality', 'good')
            st.metric("📚 Content Quality", quality.title())
        
        # Navigation
        st.markdown("### 🚀 Continue Your Study Journey")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 View Full Summary", key="concepts_summary", type="primary", use_container_width=True):
                st.session_state.view_mode = "summary"
                st.rerun()
        with col2:
            if st.button("⬅️ Back to Main", key="concepts_back", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
    
    def render_summary_study(self):
        """Enhanced summary study mode"""
        st.header("📄 Study Your AI Summary")
        
        if 'language_result' not in st.session_state.processing_results:
            st.warning("No summary available")
            return
        
        # Use the enhanced summary viewer
        self.render_summary_viewer()
    
    def render_flashcard_study(self):
        """FIXED: Enhanced flashcard study interface"""
        st.header("🃏 Interactive Flashcard Study")
        
        if not st.session_state.flashcards:
            st.warning("No flashcards available")
            return
        
        total_cards = len(st.session_state.flashcards)
        current_idx = st.session_state.current_card
        current_card = st.session_state.flashcards[current_idx]
        
        # Enhanced progress display
        progress = (current_idx + 1) / total_cards
        st.progress(progress)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📊 Progress: {current_idx + 1} of {total_cards} cards**")
        with col2:
            if st.session_state.study_stats['total'] > 0:
                accuracy = (st.session_state.study_stats['correct'] / st.session_state.study_stats['total']) * 100
                st.markdown(f"**🎯 Accuracy: {accuracy:.1f}%**")
        
        # Card display
        if not st.session_state.show_answer:
            # Question
            st.markdown(f"""
            <div class="flashcard">
                <h3>🤔 Question {current_idx + 1}</h3>
                <p style="font-size: 1.2em; margin-top: 1rem;">{current_card.get('question', 'No question')}</p>
                <p style="margin-top: 1rem; font-size: 0.9em; opacity: 0.8;">
                    📚 Topic: {current_card.get('concept', 'General')} | 
                    📈 Difficulty: {current_card.get('difficulty', 'medium').title()}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Show Answer", key="btn_show_answer", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            with col2:
                if st.button("⏭️ Skip Card", key="btn_skip_card", use_container_width=True):
                    self.next_card()
        else:
            # Question and Answer
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="flashcard">
                    <h3>🤔 Question</h3>
                    <p>{current_card.get('question', 'No question')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="flashcard-back">
                    <h3>💡 Answer</h3>
                    <p>{current_card.get('answer', 'No answer')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Assessment
            st.markdown("### 🎯 How did you do?")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("❌ Incorrect", key="btn_incorrect", use_container_width=True):
                    self.record_answer(False)
            with col2:
                if st.button("✅ Correct", key="btn_correct", use_container_width=True):
                    self.record_answer(True)
            with col3:
                if st.button("➡️ Next Card", key="btn_next_card", use_container_width=True):
                    self.next_card()
        
        # Study controls
        st.markdown("---")
        st.markdown("### 🎮 Study Controls")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Restart", key="btn_restart_study", use_container_width=True):
                st.session_state.current_card = 0
                st.session_state.show_answer = False
                st.session_state.study_stats = {'correct': 0, 'incorrect': 0, 'total': 0}
                st.rerun()
        
        with col2:
            if st.button("🎲 Shuffle", key="btn_shuffle_cards", use_container_width=True):
                random.shuffle(st.session_state.flashcards)
                st.session_state.current_card = 0
                st.session_state.show_answer = False
                st.rerun()
        
        with col3:
            if st.button("📊 View Stats", key="btn_view_stats", use_container_width=True):
                self.show_detailed_stats()
        
        with col4:
            generation_choice = st.session_state.get('generation_choice', 'complete_package')
            if generation_choice in ["summary_only", "complete_package"]:
                if st.button("📖 View Summary", key="btn_study_to_summary", use_container_width=True):
                    st.session_state.view_mode = "summary"
                    st.rerun()
    
    def record_answer(self, correct: bool):
        """Record study answer"""
        stats = st.session_state.study_stats
        stats['total'] += 1
        if correct:
            stats['correct'] += 1
        else:
            stats['incorrect'] += 1
        self.next_card()
    
    def next_card(self):
        """Move to next card"""
        st.session_state.current_card = (st.session_state.current_card + 1) % len(st.session_state.flashcards)
        st.session_state.show_answer = False
        st.rerun()
    
    def show_detailed_stats(self):
        """Show detailed study statistics"""
        stats = st.session_state.study_stats
        
        st.markdown("### 📊 Study Session Statistics")
        
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Accuracy", f"{accuracy:.1f}%")
            with col2:
                st.metric("✅ Correct", stats['correct'])
            with col3:
                st.metric("❌ Incorrect", stats['incorrect'])
            with col4:
                st.metric("📝 Total Answered", stats['total'])
            
            # Progress bar for accuracy
            if accuracy >= 80:
                st.success(f"🎉 Excellent work! {accuracy:.1f}% accuracy")
            elif accuracy >= 60:
                st.info(f"👍 Good progress! {accuracy:.1f}% accuracy")
            else:
                st.warning(f"📚 Keep studying! {accuracy:.1f}% accuracy")
        else:
            st.info("📝 Start answering questions to see your statistics!")

# Run the application
if __name__ == "__main__":
    app = FlashcardApp()
    app.run()