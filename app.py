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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #667eea;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #5a67d8;
        transform: translateY(-2px);
        transition: all 0.3s;
    }
    .flashcard-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .doc-intel-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .doc-intel-enabled {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .doc-intel-disabled {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>✍️ Scribbly</h1>
    <h3><em>From chaos to clarity.</em></h3>
    <p>Transform your handwritten notes into organized summaries and flashcards</p>
</div>
""", unsafe_allow_html=True)

# Check Document Intelligence status
doc_intel_enabled = get_document_intelligence_status()

# Sidebar with instructions
with st.sidebar:
    st.markdown("### 📋 How to Use Scribbly")
    st.markdown("""
    1. **Upload** your notes (text files or images)
    2. **Preview** the extracted content
    3. **Analyze** with Azure AI
    4. **Review** summaries, key concepts & flashcards
    5. **Study** with generated materials
    """)
    
    st.markdown("### 📄 Supported Formats")
    supported_formats = [
        "- **TXT**: Plain text files",
        "- **DOCX**: Microsoft Word documents",
        "- **PDF**: Portable Document Format"
    ]
    
    if doc_intel_enabled:
        supported_formats.extend([
            "- **JPG/JPEG**: Image files with handwritten/printed text",
            "- **PNG**: Image files with handwritten/printed text",
            "- **BMP/TIFF**: Image files with handwritten/printed text"
        ])
    
    st.markdown("\n".join(supported_formats))
    
    # Document Intelligence status
    st.markdown("### 🔍 OCR Status")
    if doc_intel_enabled:
        st.markdown("""
        <div class="doc-intel-status doc-intel-enabled">
            ✅ Document Intelligence: <strong>Enabled</strong><br>
            📸 You can upload images of handwritten notes!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="doc-intel-status doc-intel-disabled">
            ⚠️ Document Intelligence: <strong>Not Configured</strong><br>
            📝 Only text files supported currently
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 💡 Tips")
    tips = [
        "- Upload detailed notes (50+ characters)",
        "- Keep text files under 10MB",
        "- Well-structured notes produce better results"
    ]
    
    if doc_intel_enabled:
        tips.extend([
            "- For images: Use clear, well-lit photos",
            "- Keep image files under 4MB",
            "- Ensure text is readable and not blurry"
        ])
    
    st.markdown("\n".join(tips))

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # File upload section
    st.markdown("### 📤 Upload Your Notes")
    
    # Determine allowed file types based on Document Intelligence availability
    if doc_intel_enabled:
        file_types = ["txt", "docx", "pdf", "jpg", "jpeg", "png", "bmp", "tiff"]
        help_text = "Upload your notes as text files (TXT, DOCX, PDF) or images (JPG, PNG, etc.) of handwritten/printed text"
    else:
        file_types = ["txt", "docx", "pdf"]
        help_text = "Upload your typed notes in TXT, DOCX, or PDF format"
    
    uploaded_file = st.file_uploader(
        "Choose your notes file",
        type=file_types,
        help=help_text
    )

# File processing
if uploaded_file:
    # Show file information
    with col2:
        st.markdown("### 📊 File Information")
        file_info = get_file_info(uploaded_file)
        
        # Add file type indicator
        filename = uploaded_file.name.lower()
        if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
            file_info["processing_type"] = "🔍 OCR (Image to Text)"
        else:
            file_info["processing_type"] = "📄 Direct Text Extraction"
        
        st.json(file_info)
    
    # Show processing indicator based on file type
    filename = uploaded_file.name.lower()
    is_image = any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'])
    
    if is_image:
        processing_message = "🔍 Processing image with OCR..."
        if not doc_intel_enabled:
            st.error("❌ Image processing requires Azure Document Intelligence configuration")
            st.stop()
    else:
        processing_message = "📄 Reading your file..."
    
    # Extract text with progress indicator
    with st.spinner(processing_message):
        result = extract_text_from_file(uploaded_file)
        
        # Handle extraction results
        if isinstance(result, tuple):  # Error case
            text, error = result
            st.error(f"❌ {error}")
            if is_image and "Document Intelligence not configured" in error:
                st.info("💡 To process images, add your Azure Document Intelligence credentials to the .env file")
            st.stop()
        else:
            text = result
    
    # Show success message with different text for images
    if is_image:
        st.success(f"✅ Successfully extracted text from image: {uploaded_file.name}")
        st.info("🔍 Text was extracted using Azure Document Intelligence OCR")
    else:
        st.success(f"✅ Successfully processed: {uploaded_file.name}")
    
    # Text preview section
    st.markdown("### 👀 Content Preview")
    
    # Show text statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Characters", len(text))
    with col2:
        st.metric("Words", len(text.split()))
    with col3:
        st.metric("Lines", len(text.split('\n')))
    
    # Text preview with option to show full content
    with st.expander("📄 View Extracted Text", expanded=False):
        if len(text) > 1000:
            show_full = st.checkbox("Show full content")
            if show_full:
                st.text_area("Full Text", text, height=400, disabled=True)
            else:
                st.text_area("Preview (first 1000 characters)", text[:1000] + "..." if len(text) > 1000 else text, height=200, disabled=True)
        else:
            st.text_area("Full Text", text, height=300, disabled=True)
    
    # Analysis section
    st.markdown("### 🧠 AI Analysis")
    
    # Analysis button with loading state
    if st.button("🚀 Analyze with Azure AI", type="primary"):
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Generate summary
            status_text.text("📝 Generating summary...")
            progress_bar.progress(25)
            summary = get_summary(text)
            
            # Step 2: Extract key phrases
            status_text.text("🔑 Extracting key concepts...")
            progress_bar.progress(50)
            key_phrases = get_key_phrases(text)
            
            # Step 3: Generate flashcards
            status_text.text("📇 Creating flashcards...")
            progress_bar.progress(75)
            flashcards = generate_flashcards(text, key_phrases)
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            # Results section
            st.markdown("---")
            st.markdown("## 📊 Analysis Results")
            
            # Summary section
            st.markdown("### 📝 AI Summary")
            st.info(summary)
            
            # Key concepts section
            st.markdown("### 🔑 Key Concepts")
            if key_phrases:
                # Display as tags
                phrase_container = st.container()
                with phrase_container:
                    cols = st.columns(3)
                    for i, phrase in enumerate(key_phrases):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div style="background-color: #e3f2fd; padding: 0.5rem; margin: 0.2rem; 
                                        border-radius: 15px; text-align: center; border: 2px solid #2196f3;">
                                <strong>{phrase}</strong>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("No key phrases extracted. Try uploading more detailed notes.")
            
            # Flashcards section
            st.markdown("### 📇 Study Flashcards")
            if flashcards and len(flashcards) > 0:
                
                # Flashcard navigation
                if len(flashcards) > 1:
                    card_index = st.selectbox("Select Flashcard", 
                                            range(1, len(flashcards) + 1), 
                                            format_func=lambda x: f"Card {x}")
                    card_index -= 1  # Convert to 0-based index
                else:
                    card_index = 0
                
                # Display selected flashcard
                question, answer = flashcards[card_index]
                
                st.markdown(f"""
                <div class="flashcard-container">
                    <h4>🤔 Question:</h4>
                    <p style="font-size: 1.1em; margin: 1rem 0;"><strong>{question}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show answer button
                if st.button("💡 Reveal Answer", key=f"reveal_{card_index}"):
                    st.markdown(f"""
                    <div class="flashcard-container" style="background-color: #e8f5e8; border-left-color: #4caf50;">
                        <h4>✅ Answer:</h4>
                        <p style="font-size: 1.1em; margin: 1rem 0;">{answer}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Flashcard statistics
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Flashcards", len(flashcards))
                with col2:
                    st.metric("Current Card", f"{card_index + 1}/{len(flashcards)}")
                
            else:
                st.warning("No flashcards generated. Try uploading more detailed notes.")
            
            # Export options
            st.markdown("### 📥 Export Options")
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                # Download summary as text
                summary_download = f"SUMMARY:\n{summary}\n\nKEY CONCEPTS:\n" + "\n".join([f"• {phrase}" for phrase in key_phrases])
                st.download_button(
                    label="📄 Download Summary",
                    data=summary_download,
                    file_name="scribbly_summary.txt",
                    mime="text/plain"
                )
            
            with export_col2:
                # Download flashcards as text
                flashcard_download = "\n".join([f"Q: {q}\nA: {a}\n---" for q, a in flashcards])
                st.download_button(
                    label="📇 Download Flashcards",
                    data=flashcard_download,
                    file_name="scribbly_flashcards.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("💡 Try uploading a different file or check your Azure connection")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Made with ❤️ using Streamlit and Azure AI</p>
    <p><small>Scribbly helps students transform their notes into organized study materials</small></p>
    <p><small>Document Intelligence: {'✅ Enabled' if doc_intel_enabled else '❌ Not Configured'}</small></p>
</div>
""", unsafe_allow_html=True)