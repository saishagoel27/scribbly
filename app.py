import streamlit as st
import time
from pathlib import Path
import json

# Import our custom modules
from config import config
from file_handler import file_handler
from azure_document import azure_document_processor
from azure_language import azure_language_processor

# Page configuration
st.set_page_config(
    page_title="📚 Scribbly - Smart Note Analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with better color schemes and visibility
st.markdown("""
<style>
    /* Main app styling - respecting user's theme preference */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1, .main-header p, .main-header em {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Feature cards with better contrast */
    .feature-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        color: #212529 !important;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    }
    
    /* Status cards with vibrant colors */
    .status-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .status-ready {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        color: #155724 !important;
        border: 2px solid #28a745;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        color: #721c24 !important;
        border: 2px solid #dc3545;
    }
    
    /* Flashcard styling with better visual appeal */
    .flashcard {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
        border: 3px solid #667eea;
        border-radius: 15px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
        color: #212529 !important;
        transition: all 0.3s ease;
    }
    
    .flashcard:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .flashcard-question {
        font-size: 1.2rem;
        font-weight: bold;
        color: #667eea !important;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .flashcard-answer {
        font-size: 1rem;
        color: #495057 !important;
        line-height: 1.6;
        background: rgba(102, 126, 234, 0.05);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    /* Confidence indicators with better colors */
    .confidence-high { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important; 
        color: #155724 !important; 
        padding: 0.3rem 0.8rem; 
        border-radius: 20px; 
        display: inline-block;
        font-weight: bold;
        border: 2px solid #28a745;
        box-shadow: 0 2px 5px rgba(40, 167, 69, 0.3);
    }
    .confidence-medium { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%) !important; 
        color: #856404 !important; 
        padding: 0.3rem 0.8rem; 
        border-radius: 20px; 
        display: inline-block;
        font-weight: bold;
        border: 2px solid #ffc107;
        box-shadow: 0 2px 5px rgba(255, 193, 7, 0.3);
    }
    .confidence-low { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important; 
        color: #721c24 !important; 
        padding: 0.3rem 0.8rem; 
        border-radius: 20px; 
        display: inline-block;
        font-weight: bold;
        border: 2px solid #dc3545;
        box-shadow: 0 2px 5px rgba(220, 53, 69, 0.3);
    }
    
    /* Key phrase tags with vibrant styling */
    .key-phrase-tag {
        background: linear-gradient(135deg, #e1bee7 0%, #f3e5f5 100%) !important;
        color: #4a148c !important;
        padding: 0.4rem 0.8rem;
        margin: 0.3rem;
        border-radius: 25px;
        display: inline-block;
        font-size: 0.9rem;
        font-weight: 600;
        border: 2px solid #9c27b0;
        box-shadow: 0 2px 8px rgba(156, 39, 176, 0.2);
        transition: all 0.2s ease;
    }
    
    .key-phrase-tag:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(156, 39, 176, 0.3);
    }
    
    /* Enhanced text input areas */
    .stTextArea textarea {
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        transition: border-color 0.2s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
    }
    
    .stTextInput input {
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        transition: border-color 0.2s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
    }
    
    /* Enhanced button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Download button with different color */
    .stDownloadButton button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3) !important;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4) !important;
    }
    
    /* Enhanced progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px !important;
    }
    
    /* Tab styling with better contrast */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Metric styling improvements */
    [data-testid="metric-container"] {
        background: rgba(102, 126, 234, 0.05);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Expander improvements */
    .streamlit-expanderHeader {
        border-radius: 10px;
        background: rgba(102, 126, 234, 0.1) !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(102, 126, 234, 0.15) !important;
        border-color: rgba(102, 126, 234, 0.3) !important;
    }
    
    .streamlit-expanderContent {
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        background: rgba(102, 126, 234, 0.02) !important;
    }
    
    /* Sidebar enhancements */
    div[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 3px solid #667eea;
    }
    
    /* Alert styling improvements */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        border: 2px solid #28a745 !important;
        border-radius: 10px !important;
        color: #155724 !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        border: 2px solid #dc3545 !important;
        border-radius: 10px !important;
        color: #721c24 !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%) !important;
        border: 2px solid #ffc107 !important;
        border-radius: 10px !important;
        color: #856404 !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%) !important;
        border: 2px solid #17a2b8 !important;
        border-radius: 10px !important;
        color: #0c5460 !important;
    }
    
    /* Enhanced headers */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Code blocks */
    .stCode {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        color: #495057 !important;
    }
    
    /* General text improvements */
    p {
        line-height: 1.6 !important;
        color: #495057 !important;
    }
    
    /* Strong and emphasis styling */
    strong {
        color: #2c3e50 !important;
        font-weight: 700 !important;
    }
    
    em {
        color: #6c757d !important;
        font-style: italic !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Scribbly</h1>
        <p>AI-Powered Note Analyzer for Students</p>
        <p><em>Transform your handwritten notes into summaries and flashcards</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    display_sidebar()
    
    # Main content area
    display_main_content()

def display_sidebar():
    """Display streamlined sidebar"""
    with st.sidebar:
        st.markdown("## 🔧 System Status")
        
        # Check Azure services status
        status = config.get_status()
        
        for service, status_text in status.items():
            service_name = service.replace("_", " ").title()
            if "✅" in status_text:
                st.markdown(f'<div class="status-card status-ready">{service_name}<br>{status_text}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-card status-error">{service_name}<br>{status_text}</div>', 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Core features
        st.markdown("## ✨ What Scribbly Does")
        
        features = [
            ("📝", "Extract text from handwritten notes"),
            ("🧠", "Generate intelligent summaries"),
            ("🔑", "Identify key concepts"),
            ("🎴", "Create study flashcards")
        ]
        
        for icon, description in features:
            st.markdown(f"**{icon}** {description}")
        
        st.markdown("---")
        st.markdown("### 📋 Supported Formats")
        st.markdown("• **Images**: PNG, JPG, JPEG")
        st.markdown("• **Documents**: PDF, DOCX")
        st.markdown("• **Text**: TXT files")
        st.markdown(f"• **Max Size**: {config.max_file_size_mb} MB")
        
        st.markdown("---")
        st.markdown("### 🎯 Tips for Best Results")
        st.markdown("• Upload clear, well-lit images")
        st.markdown("• Ensure handwriting is legible")
        st.markdown("• Include definitions and key concepts")
        st.markdown("• Try PDF format for best results")

def display_main_content():
    """Display main content area"""
    
    # Check if services are available
    if not config.has_document_intelligence() or not config.has_language_service():
        st.error("⚠️ Azure services not properly configured. Please check your .env file.")
        st.markdown("""
        **Required Environment Variables:**
        - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
        - `AZURE_DOCUMENT_INTELLIGENCE_KEY`
        - `AZURE_LANGUAGE_ENDPOINT`
        - `AZURE_LANGUAGE_KEY`
        """)
        return
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'uploaded_file_info' not in st.session_state:
        st.session_state.uploaded_file_info = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # File upload section
    uploaded_file = file_handler.create_upload_interface()
    
    if uploaded_file is not None:
        # Validate file
        is_valid, message = file_handler.validate_file(uploaded_file)
        
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        # Display file info
        st.success(f"✅ {message}")
        file_handler.display_file_info(uploaded_file)
        
        # Store file info
        st.session_state.uploaded_file_info = file_handler.get_file_info(uploaded_file)
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Analyze Notes", type="primary", use_container_width=True):
                analyze_document(uploaded_file)
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.processing_complete:
        display_analysis_results()

def analyze_document(uploaded_file):
    """Analyze the uploaded document"""
    
    # Prepare file for Azure
    file_bytes, content_type = file_handler.prepare_file_for_azure(uploaded_file)
    file_info = st.session_state.uploaded_file_info
    
    # Reset processing state
    st.session_state.processing_complete = False
    
    # Progress tracking
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    def update_progress(message, progress_value=None):
        status_text.text(message)
        if progress_value is not None:
            progress_bar.progress(progress_value)
    
    try:
        # Step 1: Document Intelligence Analysis
        update_progress("🔍 Extracting text from document...", 0.1)
        
        document_results = azure_document_processor.comprehensive_document_analysis(
            file_bytes=file_bytes,
            content_type=content_type,
            file_info=file_info,
            progress_callback=lambda msg: update_progress(msg, 0.4)
        )
        
        update_progress("📝 Text extraction complete!", 0.5)
        
        # Step 2: Language Service Analysis
        extracted_text = document_results.get("text_extraction", {}).get("content", "")
        
        if extracted_text and len(extracted_text.strip()) > 10:
            update_progress("🧠 Generating study materials...", 0.6)
            
            # Use streamlined analysis method
            language_results = azure_language_processor.analyze_for_study_materials(
                text=extracted_text,
                progress_callback=lambda msg: update_progress(msg, 0.9)
            )
            
            update_progress("✅ Analysis complete!", 1.0)
        else:
            language_results = {
                "error": "Insufficient text extracted for analysis",
                "summary": {"status": "failed", "error": "Insufficient text"},
                "key_phrases": {"status": "failed", "phrases": []},
                "flashcards": [],
                "metadata": {"analysis_failed": True}
            }
            update_progress("⚠️ Limited text found for analysis", 1.0)
        
        # Store results
        st.session_state.analysis_results = {
            "document_analysis": document_results,
            "language_analysis": language_results,
            "file_info": file_info
        }
        
        # Mark processing as complete
        st.session_state.processing_complete = True
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success("🎉 Analysis completed successfully!")
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Analysis failed: {str(e)}")
        
        with st.expander("🔍 Error Details (for debugging)"):
            st.code(str(e))

def display_analysis_results():
    """Display streamlined analysis results"""
    
    results = st.session_state.analysis_results
    document_analysis = results.get("document_analysis", {})
    language_analysis = results.get("language_analysis", {})
    
    st.markdown("## 📊 Analysis Results")
    
    # Quick stats
    display_quick_stats(document_analysis, language_analysis)
    
    # Streamlined tabs - only core features
    tab1, tab2, tab3 = st.tabs([
        "📝 Extracted Text & Summary", 
        "🎴 Study Flashcards",
        "🔍 Quality Report"
    ])
    
    with tab1:
        display_text_and_summary(document_analysis, language_analysis)
    
    with tab2:
        display_flashcards(language_analysis)
    
    with tab3:
        display_quality_report(document_analysis, language_analysis)

def display_quick_stats(document_analysis, language_analysis):
    """Display quick statistics overview"""
    
    st.markdown("### 📈 Quick Overview")
    
    # Extract key metrics
    text_extraction = document_analysis.get("text_extraction", {})
    content = text_extraction.get("content", "")
    metadata = text_extraction.get("metadata", {})
    
    # Language analysis metrics
    key_phrases = language_analysis.get("key_phrases", {}).get("phrases", [])
    flashcards = language_analysis.get("flashcards", [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Pages", metadata.get("page_count", 0))
    
    with col2:
        st.metric("📝 Words", len(content.split()) if content else 0)
    
    with col3:
        st.metric("🔑 Key Concepts", len(key_phrases))
    
    with col4:
        st.metric("🎴 Flashcards", len(flashcards))

def display_text_and_summary(document_analysis, language_analysis):
    """Display extracted text and summary together"""
    
    text_extraction = document_analysis.get("text_extraction", {})
    content = text_extraction.get("content", "")
    
    # Summary Section
    summary_data = language_analysis.get("summary", {})
    if summary_data.get("text") and summary_data.get("status") == "success":
        st.markdown("### 📝 Intelligent Summary")
        st.markdown(f'<div class="feature-card">{summary_data["text"]}</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Method", summary_data.get("method", "Unknown").replace("_", " ").title())
        with col2:
            st.metric("Confidence", f"{summary_data.get('confidence', 0):.1%}")
    else:
        st.info("📝 Summary generation was limited due to insufficient text content.")
    
    st.markdown("---")
    
    # Key Concepts Section
    key_phrases_data = language_analysis.get("key_phrases", {})
    phrases = key_phrases_data.get("phrases", [])
    
    if phrases and key_phrases_data.get("status") == "success":
        st.markdown("### 🔑 Key Concepts Identified")
        
        # Display as styled tags
        phrase_html = ""
        for phrase in phrases:
            phrase_html += f'<span class="key-phrase-tag">{phrase}</span>'
        
        st.markdown(phrase_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Extracted Text Section
    if content:
        st.markdown("### 📄 Extracted Text")
        
        # Text statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Characters", len(content))
        with col2:
            st.metric("Words", len(content.split()))
        with col3:
            confidence = text_extraction.get("metadata", {}).get("average_confidence", 0)
            st.metric("OCR Confidence", f"{confidence:.1%}")
        
        # Display content
        st.text_area(
            "Full Text Content",
            content,
            height=300,
            help="Complete text extracted from your document"
        )
        
        # Download option
        st.download_button(
            label="📥 Download Extracted Text",
            data=content,
            file_name=f"extracted_text_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("⚠️ No text content was extracted from the document.")

def display_flashcards(language_analysis):
    """Display study flashcards"""
    flashcards = language_analysis.get("flashcards", [])
    
    if not flashcards:
        st.info("📚 No flashcards were generated. Try uploading notes with more definitions and key concepts.")
        return
    
    st.markdown("### 🎴 Study Flashcards")
    st.markdown("*Click on cards to reveal answers*")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        card_types = list(set([card.get("type", "general") for card in flashcards]))
        selected_type = st.selectbox("Filter by Type", ["All"] + card_types)
    
    with col2:
        difficulties = list(set([card.get("difficulty", "medium") for card in flashcards]))
        selected_difficulty = st.selectbox("Filter by Difficulty", ["All"] + difficulties)
    
    # Filter flashcards
    filtered_cards = flashcards
    if selected_type != "All":
        filtered_cards = [card for card in filtered_cards if card.get("type") == selected_type]
    if selected_difficulty != "All":
        filtered_cards = [card for card in filtered_cards if card.get("difficulty") == selected_difficulty]
    
    if not filtered_cards:
        st.warning("No flashcards match the selected filters.")
        return
    
    # Display flashcards
    for i, card in enumerate(filtered_cards):
        question = card.get("question", "No question")
        answer = card.get("answer", "No answer")
        card_type = card.get("type", "general")
        difficulty = card.get("difficulty", "medium")
        confidence = card.get("confidence", 0.5)
        
        # Determine confidence class
        conf_class = "confidence-high" if confidence >= 0.8 else "confidence-medium" if confidence >= 0.6 else "confidence-low"
        
        with st.expander(f"🎴 Card {i+1}: {question}", expanded=False):
            st.markdown(f'<div class="flashcard">', unsafe_allow_html=True)
            st.markdown(f'<div class="flashcard-answer">💡 {answer}</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<span class="{conf_class}">Confidence: {confidence:.1%}</span>', unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Type:** {card_type.title()}")
            with col3:
                st.markdown(f"**Difficulty:** {difficulty.title()}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Export flashcards
    if st.button("📥 Export Flashcards as JSON"):
        flashcard_json = json.dumps(filtered_cards, indent=2)
        st.download_button(
            label="Download Flashcards",
            data=flashcard_json,
            file_name=f"flashcards_{int(time.time())}.json",
            mime="application/json"
        )

def display_quality_report(document_analysis, language_analysis):
    """Display simplified quality report"""
    
    st.markdown("### 🔍 Quality Assessment")
    
    # Overall Quality Summary
    quality_metrics = document_analysis.get("quality_metrics", {})
    
    if quality_metrics:
        col1, col2 = st.columns(2)
        
        with col1:
            overall_quality = quality_metrics.get("overall_quality", "Unknown")
            st.metric("Overall Quality", overall_quality)
        
        with col2:
            text_quality = quality_metrics.get("text_extraction_quality", 0)
            st.metric("Text Extraction Quality", f"{text_quality:.1%}")
        
        # Recommendations
        recommendations = quality_metrics.get("recommendations", [])
        if recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in recommendations:
                st.write(f"• {rec}")
    
    # Processing Details
    text_extraction = document_analysis.get("text_extraction", {})
    extraction_metadata = text_extraction.get("metadata", {})
    
    if extraction_metadata:
        st.markdown("#### 📄 Processing Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Pages Processed:** {extraction_metadata.get('page_count', 0)}")
            st.write(f"**OCR Confidence:** {extraction_metadata.get('average_confidence', 0):.1%}")
            
        with col2:
            summary_readiness = extraction_metadata.get("summary_readiness", "unknown")
            st.write(f"**Summary Readiness:** {summary_readiness.title()}")
            
            processing_successful = extraction_metadata.get("processing_successful", False)
            status = "✅ Success" if processing_successful else "❌ Failed"
            st.write(f"**Processing Status:** {status}")
    
    # Language Analysis Summary
    lang_metadata = language_analysis.get("metadata", {})
    if lang_metadata and not lang_metadata.get("analysis_failed"):
        st.markdown("#### 🧠 Analysis Summary")
        
        analysis_results = lang_metadata.get("analysis_results", {})
        if analysis_results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Key Phrases Found:** {analysis_results.get('key_phrases_extracted', 0)}")
                
            with col2:
                st.write(f"**Flashcards Created:** {analysis_results.get('flashcards_created', 0)}")
            
            summary_status = "✅ Generated" if analysis_results.get('summary_generated', False) else "❌ Failed"
            st.write(f"**Summary Status:** {summary_status}")

if __name__ == "__main__":
    main()