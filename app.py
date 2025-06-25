import streamlit as st
from utils import extract_text_from_file, get_summary, get_key_phrases, generate_flashcards, get_file_info, get_document_intelligence_status
import time

# Page configuration
st.set_page_config(
    page_title="Scribbly - AI Note Summarizer", 
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for better styling and dark mode compatibility
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header h3 {
        font-size: 1.5rem;
        font-weight: 300;
        margin-bottom: 1rem;
        opacity: 0.9;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.8;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Enhanced Flashcard Styling */
    .flashcard-container {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .flashcard-container::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 5px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .flashcard-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .flashcard-question {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .flashcard-question h4 {
        color: white !important;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    
    .flashcard-question p {
        color: white !important;
        margin: 0;
        font-size: 1.1rem;
        line-height: 1.4;
    }
    
    .flashcard-answer {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .flashcard-answer h4 {
        color: white !important;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    
    .flashcard-answer p {
        color: white !important;
        margin: 0;
        font-size: 1.1rem;
        line-height: 1.4;
    }
    
    /* Key Phrases Tags */
    .key-phrase-tag {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 0.75rem 1.25rem;
        margin: 0.25rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: 500;
        font-size: 0.9rem;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
        border: none;
    }
    
    .key-phrase-tag:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* Status Indicators */
    .doc-intel-status {
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .doc-intel-enabled {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #065f46;
        border: 2px solid #10b981;
    }
    
    .doc-intel-disabled {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #991b1b;
        border: 2px solid #ef4444;
    }
    
    /* Metrics */
    .metric-container {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* File Upload Area */
    .uploadedFile {
        border-radius: 12px;
        border: 2px dashed #667eea;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Summary Box */
    .summary-container {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
        border: 2px solid #8b5cf6;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #4c1d95;
    }
    
    .summary-container .stMarkdown {
        color: #4c1d95 !important;
    }
    
    /* Export Buttons */
    .export-button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-animation {
        animation: pulse 2s infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .main-header {
            padding: 2rem 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header with enhanced styling
st.markdown("""
<div class="main-header">
    <h1>✍️ Scribbly</h1>
    <h3><em>From chaos to clarity.</em></h3>
    <p>Transform your handwritten notes into organized summaries and flashcards with the power of AI</p>
</div>
""", unsafe_allow_html=True)

# Check Document Intelligence status
doc_intel_enabled = get_document_intelligence_status()

# Enhanced sidebar with better organization
with st.sidebar:
    st.markdown("### 🚀 How to Use Scribbly")
    st.markdown("""
    **Step 1:** 📤 Upload your notes (text files or images)  
    **Step 2:** 👀 Preview the extracted content  
    **Step 3:** 🧠 Analyze with Azure AI  
    **Step 4:** 📊 Review summaries, key concepts & flashcards  
    **Step 5:** 📚 Study with generated materials  
    """)
    
    st.markdown("---")
    st.markdown("### 📄 Supported Formats")
    
    # Dynamic format list based on capabilities
    formats_html = """
    <div style="margin: 0.5rem 0;">
        <span style="color: #059669; font-weight: 600;">✓ TXT</span> - Plain text files<br>
        <span style="color: #059669; font-weight: 600;">✓ DOCX</span> - Microsoft Word documents<br>
        <span style="color: #059669; font-weight: 600;">✓ PDF</span> - Portable Document Format
    """
    
    if doc_intel_enabled:
        formats_html += """<br>
        <span style="color: #059669; font-weight: 600;">✓ JPG/PNG</span> - Image files with text<br>
        <span style="color: #059669; font-weight: 600;">✓ BMP/TIFF</span> - Other image formats
        """
    
    formats_html += "</div>"
    st.markdown(formats_html, unsafe_allow_html=True)
    
    st.markdown("---")
    # Enhanced Document Intelligence status
    st.markdown("### 🔍 OCR Capabilities")
    if doc_intel_enabled:
        st.markdown("""
        <div class="doc-intel-status doc-intel-enabled">
            <strong>✅ Document Intelligence: Active</strong><br>
            📸 Upload images of handwritten notes!<br>
            🔍 Advanced OCR text extraction enabled
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="doc-intel-status doc-intel-disabled">
            <strong>⚠️ Document Intelligence: Not Configured</strong><br>
            📝 Text files only<br>
            🔧 Configure Azure credentials for image support
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💡 Pro Tips")
    tips_html = """
    <div style="font-size: 0.9rem; line-height: 1.4;">
        <strong>📝 Content:</strong> Upload detailed notes (500+ words)<br>
        <strong>📏 Size:</strong> Keep files under 10MB<br>
        <strong>🎯 Quality:</strong> Well-structured notes = better results
    """
    
    if doc_intel_enabled:
        tips_html += """<br><strong>📸 Images:</strong> Clear, well-lit photos work best<br>
        <strong>🔍 OCR:</strong> Ensure text is readable and not blurry"""
    
    tips_html += "</div>"
    st.markdown(tips_html, unsafe_allow_html=True)

# Main content area with improved layout
col1, col2 = st.columns([3, 1])

with col1:
    # Enhanced file upload section
    st.markdown("### 📤 Upload Your Notes")
    
    # Determine file types and help text
    if doc_intel_enabled:
        file_types = ["txt", "docx", "pdf", "jpg", "jpeg", "png", "bmp", "tiff"]
        help_text = "📁 Upload text files (TXT, DOCX, PDF) or 📸 images (JPG, PNG, etc.) with handwritten/printed text"
    else:
        file_types = ["txt", "docx", "pdf"]
        help_text = "📁 Upload your typed notes in TXT, DOCX, or PDF format"
    
    uploaded_file = st.file_uploader(
        "Choose your notes file",
        type=file_types,
        help=help_text
    )

# File processing with enhanced UI
if uploaded_file:
    # Enhanced file information display
    with col2:
        st.markdown("### 📊 File Information")
        file_info = get_file_info(uploaded_file)
        
        # Enhanced file type detection
        filename = uploaded_file.name.lower()
        if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
            file_info["processing_type"] = "🔍 OCR Processing"
            file_info["ai_service"] = "Document Intelligence"
        else:
            file_info["processing_type"] = "📄 Text Extraction"
            file_info["ai_service"] = "Direct Reading"
        
        # Display file info in a nice format
        info_html = f"""
        <div style="background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
                    border-radius: 12px; padding: 1rem; border: 1px solid #cbd5e1;">
            <strong>📄 Name:</strong> {file_info['filename']}<br>
            <strong>📊 Size:</strong> {file_info['filesize']}<br>
            <strong>🔧 Type:</strong> {file_info['processing_type']}<br>
            <strong>🤖 Service:</strong> {file_info['ai_service']}
        </div>
        """
        st.markdown(info_html, unsafe_allow_html=True)
    
    # Enhanced processing indicators
    filename = uploaded_file.name.lower()
    is_image = any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'])
    
    if is_image:
        processing_message = "🔍 Extracting text from image using AI..."
        if not doc_intel_enabled:
            st.error("❌ Image processing requires Azure Document Intelligence configuration")
            st.info("💡 Add your Azure Document Intelligence credentials to enable image processing")
            st.stop()
    else:
        processing_message = "📄 Reading your document..."
    
    # Extract text with enhanced progress
    with st.spinner(processing_message):
        result = extract_text_from_file(uploaded_file)
        
        if isinstance(result, tuple):  # Error case
            text, error = result
            st.error(f"❌ {error}")
            if is_image and "Document Intelligence not configured" in error:
                st.info("💡 Configure Azure Document Intelligence to process images")
            st.stop()
        else:
            text = result
    
    # Enhanced success messages
    if is_image:
        st.success(f"✅ Successfully extracted text from image: **{uploaded_file.name}**")
        st.info("🔍 Powered by Azure Document Intelligence OCR")
    else:
        st.success(f"✅ Successfully processed document: **{uploaded_file.name}**")
    
    # Enhanced content preview section
    st.markdown("### 👀 Content Preview")
    
    # Enhanced statistics display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Characters", f"{len(text):,}")
    with col2:
        st.metric("📖 Words", f"{len(text.split()):,}")
    with col3:
        st.metric("📄 Lines", f"{len(text.split(chr(10))):,}")
    with col4:
        reading_time = max(1, len(text.split()) // 200)  # Average reading speed
        st.metric("⏱️ Read Time", f"{reading_time} min")
    
    # Enhanced text preview
    with st.expander("📄 View Extracted Text", expanded=False):
        if len(text) > 1000:
            show_full = st.checkbox("📖 Show full content", help="Toggle to view the complete extracted text")
            if show_full:
                st.text_area("Full Text Content", text, height=400, disabled=True)
            else:
                preview_text = text[:1000] + "..." if len(text) > 1000 else text
                st.text_area("Preview (First 1000 characters)", preview_text, height=200, disabled=True)
                st.info(f"💡 Showing first 1000 of {len(text)} characters. Check 'Show full content' to see more.")
        else:
            st.text_area("Full Text Content", text, height=300, disabled=True)
    
    # Enhanced analysis section
    st.markdown("### 🧠 AI Analysis")
    st.markdown("Transform your notes into organized study materials using Azure AI")
    
    # Enhanced analysis button
    if st.button("🚀 Analyze with Azure AI", type="primary", help="Generate summary, key concepts, and flashcards"):
        
        # Enhanced progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Generate summary
                status_text.markdown("**📝 Generating AI summary...**")
                progress_bar.progress(25)
                time.sleep(0.5)  # Small delay for better UX
                summary = get_summary(text)
                
                # Step 2: Extract key phrases
                status_text.markdown("**🔑 Extracting key concepts...**")
                progress_bar.progress(50)
                time.sleep(0.5)
                key_phrases = get_key_phrases(text)
                
                # Step 3: Generate flashcards
                status_text.markdown("**📇 Creating study flashcards...**")
                progress_bar.progress(75)
                time.sleep(0.5)
                flashcards = generate_flashcards(text, key_phrases)
                
                # Complete
                progress_bar.progress(100)
                status_text.markdown("**✅ Analysis complete! Scroll down to see results.**")
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
                # Enhanced results section
                st.markdown("---")
                st.markdown("## 📊 Your Study Materials")
                
                # Enhanced summary section
                st.markdown("### 📝 AI-Generated Summary")
                st.markdown(f"""
                <div class="summary-container">
                    <p style="font-size: 1.1rem; line-height: 1.6; margin: 0;">{summary}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced key concepts section
                st.markdown("### 🔑 Key Concepts")
                if key_phrases:
                    st.markdown("**Important topics identified in your notes:**")
                    
                    # Create a more organized tag display
                    tags_html = "<div style='margin: 1rem 0;'>"
                    for phrase in key_phrases:
                        tags_html += f"""
                        <span class="key-phrase-tag">{phrase}</span>
                        """
                    tags_html += "</div>"
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    st.info(f"💡 Found {len(key_phrases)} key concepts to focus your studies on")
                else:
                    st.warning("🤔 No key phrases extracted. Try uploading more detailed notes for better results.")
                
                # Enhanced flashcards section
                st.markdown("### 📇 Study Flashcards")
                if flashcards and len(flashcards) > 0:
                    
                    # Flashcard controls
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if len(flashcards) > 1:
                            card_index = st.selectbox(
                                "📇 Select Flashcard", 
                                range(1, len(flashcards) + 1), 
                                format_func=lambda x: f"Flashcard {x} of {len(flashcards)}",
                                help="Navigate through your generated flashcards"
                            )
                            card_index -= 1
                        else:
                            card_index = 0
                            st.info("📇 **Flashcard 1 of 1**")
                    
                    # Display flashcard with enhanced styling
                    question, answer = flashcards[card_index]
                    
                    # Question card
                    st.markdown(f"""
                    <div class="flashcard-container">
                        <div class="flashcard-question">
                            <h4>🤔 Question</h4>
                            <p>{question}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Answer reveal with session state
                    reveal_key = f"reveal_{card_index}_{len(flashcards)}"
                    if reveal_key not in st.session_state:
                        st.session_state[reveal_key] = False
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button("💡 Reveal Answer", key=reveal_key, help="Click to see the answer"):
                            st.session_state[reveal_key] = True
                    
                    # Show answer if revealed
                    if st.session_state[reveal_key]:
                        st.markdown(f"""
                        <div class="flashcard-container">
                            <div class="flashcard-answer">
                                <h4>✅ Answer</h4>
                                <p>{answer}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Reset button
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            if st.button("🔄 Hide Answer", key=f"hide_{reveal_key}"):
                                st.session_state[reveal_key] = False
                                st.rerun()
                    
                    # Enhanced flashcard statistics
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📇 Total Cards", len(flashcards))
                    with col2:
                        st.metric("📍 Current", f"{card_index + 1}")
                    with col3:
                        progress_pct = round(((card_index + 1) / len(flashcards)) * 100)
                        st.metric("📊 Progress", f"{progress_pct}%")
                    
                else:
                    st.warning("🤔 No flashcards generated. Try uploading more detailed notes with specific concepts.")
                
                # Enhanced export options
                st.markdown("---")
                st.markdown("### 📥 Export Your Study Materials")
                st.markdown("Save your generated content for offline study")
                
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    # Enhanced summary download
                    summary_content = f"""SCRIBBLY STUDY MATERIALS
============================

📝 AI SUMMARY:
{summary}

🔑 KEY CONCEPTS:
{chr(10).join([f"• {phrase}" for phrase in key_phrases])}

📊 STATISTICS:
• Original text: {len(text)} characters
• Words: {len(text.split())} words
• Key concepts: {len(key_phrases)} identified
• Flashcards: {len(flashcards)} generated

Generated by Scribbly AI Note Summarizer
"""
                    st.download_button(
                        label="📄 Download Summary & Concepts",
                        data=summary_content,
                        file_name=f"scribbly_summary_{uploaded_file.name.split('.')[0]}.txt",
                        mime="text/plain",
                        help="Download summary and key concepts as a text file"
                    )
                
                with export_col2:
                    # Enhanced flashcards download
                    flashcard_content = f"""SCRIBBLY FLASHCARDS
===================

Generated from: {uploaded_file.name}
Total cards: {len(flashcards)}

{chr(10).join([f"CARD {i+1}:{chr(10)}Q: {q}{chr(10)}A: {a}{chr(10)}{'-'*50}{chr(10)}" for i, (q, a) in enumerate(flashcards)])}

Study Tips:
• Review cards multiple times
• Focus on difficult concepts
• Use spaced repetition for better retention

Generated by Scribbly AI Note Summarizer
"""
                    st.download_button(
                        label="📇 Download Flashcards",
                        data=flashcard_content,
                        file_name=f"scribbly_flashcards_{uploaded_file.name.split('.')[0]}.txt",
                        mime="text/plain",
                        help="Download flashcards as a text file for study"
                    )
                    
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Analysis failed: {str(e)}")
                st.info("💡 **Troubleshooting tips:**")
                st.markdown("""
                - Ensure your file contains readable text
                - Check your internet connection
                - Try uploading a different file
                - Verify Azure AI services are configured
                """)

# Enhanced footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #64748b; padding: 3rem 1rem; 
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
            border-radius: 16px; margin-top: 2rem;">
    <h4 style="color: #334155; margin-bottom: 1rem;">Made with ❤️ for Students</h4>
    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
        <strong>Scribbly</strong> - Powered by Azure AI & Streamlit
    </p>
    <p style="margin-bottom: 1rem;">
        Transform your handwritten notes into organized study materials instantly
    </p>
    <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
        <span style="color: #059669;">✅ AI Summarization</span>
        <span style="color: #059669;">✅ Key Concept Extraction</span>
        <span style="color: #059669;">✅ Smart Flashcards</span>
        <span style="color: {'#059669' if doc_intel_enabled else '#ef4444'};">
            {'✅' if doc_intel_enabled else '⚠️'} Image OCR
        </span>
    </div>
</div>
""", unsafe_allow_html=True)