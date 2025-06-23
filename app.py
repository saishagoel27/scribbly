import streamlit as st
from utils import extract_text_from_file, get_summary, get_key_phrases, generate_flashcards, get_file_info
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

# Sidebar with instructions
with st.sidebar:
    st.markdown("### 📋 How to Use Scribbly")
    st.markdown("""
    1. **Upload** your typed notes (.txt, .docx, .pdf)
    2. **Preview** the extracted content
    3. **Analyze** with Azure AI
    4. **Review** summaries, key concepts & flashcards
    5. **Study** with generated materials
    """)
    
    st.markdown("### 📄 Supported Formats")
    st.markdown("""
    - **TXT**: Plain text files
    - **DOCX**: Microsoft Word documents  
    - **PDF**: Portable Document Format
    """)
    
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Upload detailed notes (50+ characters)
    - Keep files under 10MB
    - Well-structured notes produce better results
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # File upload section
    st.markdown("### 📤 Upload Your Notes")
    uploaded_file = st.file_uploader(
        "Choose your handwritten (typed-up) notes file",
        type=["txt", "docx", "pdf"],
        help="Upload your typed notes in TXT, DOCX, or PDF format"
    )

# File processing
if uploaded_file:
    # Show file information
    with col2:
        st.markdown("### 📊 File Information")
        file_info = get_file_info(uploaded_file)
        st.json(file_info)
    
    # Extract text with progress indicator
    with st.spinner("🔍 Reading your file..."):
        result = extract_text_from_file(uploaded_file)
        
        # Handle extraction results
        if isinstance(result, tuple):  # Error case
            text, error = result
            st.error(f"❌ {error}")
            st.stop()
        else:
            text = result
    
    # Show success message
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
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Made with ❤️ using Streamlit and Azure AI</p>
    <p><small>Scribbly helps students transform their handwritten notes into organized study materials</small></p>
</div>
""", unsafe_allow_html=True)