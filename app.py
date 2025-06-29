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
    page_title="📚 Scribbly - Smart Document Analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI/UX
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
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    .status-ready {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .quality-excellent { color: #28a745; font-weight: bold; }
    .quality-good { color: #17a2b8; font-weight: bold; }
    .quality-fair { color: #ffc107; font-weight: bold; }
    .quality-poor { color: #dc3545; font-weight: bold; }
    
    .flashcard {
        background: white;
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .flashcard-question {
        font-size: 1.1rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    .flashcard-answer {
        font-size: 1rem;
        color: #333;
        line-height: 1.5;
    }
    
    .confidence-high { background-color: #d4edda; color: #155724; padding: 0.2rem 0.5rem; border-radius: 5px; }
    .confidence-medium { background-color: #fff3cd; color: #856404; padding: 0.2rem 0.5rem; border-radius: 5px; }
    .confidence-low { background-color: #f8d7da; color: #721c24; padding: 0.2rem 0.5rem; border-radius: 5px; }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .sentiment-positive { color: #28a745; }
    .sentiment-negative { color: #dc3545; }
    .sentiment-neutral { color: #6c757d; }
    
    .entity-tag {
        background-color: #e3f2fd;
        padding: 0.3rem 0.6rem;
        margin: 0.2rem;
        border-radius: 15px;
        display: inline-block;
        font-size: 0.9rem;
    }
    
    .key-phrase-tag {
        background-color: #f3e5f5;
        padding: 0.3rem 0.6rem;
        margin: 0.2rem;
        border-radius: 15px;
        display: inline-block;
        font-size: 0.9rem;
        border: 1px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Scribbly</h1>
        <p>AI-Powered Document Analysis & Study Tool</p>
        <p><em>Transform your handwritten notes into interactive study materials</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with system status
    display_sidebar()
    
    # Main content area
    display_main_content()

def display_sidebar():
    """Display sidebar with system status and information"""
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
        
        # App features
        st.markdown("## ✨ What Scribbly Can Do")
        
        features = [
            ("📝", "Extract text from handwritten notes"),
            ("🧠", "Generate intelligent summaries"),
            ("🔑", "Identify key concepts"),
            ("🎴", "Create study flashcards"),
            ("❓", "Generate Q&A pairs"),
            ("📊", "Analyze document structure"),
            ("😊", "Detect sentiment and opinions"),
            ("🏷️", "Recognize entities (people, places, etc.)")
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
        st.markdown("### 🎯 Quick Tips")
        st.markdown("• Upload clear, well-lit images")
        st.markdown("• Ensure handwriting is legible")
        st.markdown("• Higher quality = better results")
        st.markdown("• Try different file formats if needed")

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
            if st.button("🚀 Analyze Document", type="primary", use_container_width=True):
                analyze_document(uploaded_file)
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.processing_complete:
        display_analysis_results()

def analyze_document(uploaded_file):
    """Analyze the uploaded document using Azure services"""
    
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
        # Step 1: Document Intelligence Analysis (50% of progress)
        update_progress("🔍 Starting document analysis...", 0.1)
        
        document_results = azure_document_processor.comprehensive_document_analysis(
            file_bytes=file_bytes,
            content_type=content_type,
            file_info=file_info,
            progress_callback=lambda msg: update_progress(msg, 0.3)
        )
        
        update_progress("📝 Document analysis complete!", 0.5)
        
        # Step 2: Language Service Analysis (remaining 50%)
        extracted_text = document_results.get("text_extraction", {}).get("content", "")
        
        if extracted_text and len(extracted_text.strip()) > 10:
            update_progress("🧠 Starting language analysis...", 0.6)
            
            language_results = azure_language_processor.comprehensive_text_analysis(
                text=extracted_text,
                progress_callback=lambda msg: update_progress(msg, 0.8)
            )
            
            update_progress("✅ Analysis complete!", 1.0)
        else:
            language_results = {
                "error": "Insufficient text extracted for language analysis",
                "summary": {"status": "failed", "error": "Insufficient text"},
                "key_phrases": {"status": "failed", "phrases": []},
                "sentiment": {"status": "failed"},
                "entities": {"status": "failed", "entities": []},
                "qa_pairs": [],
                "flashcards": [],
                "language_detection": {"status": "failed"},
                "metadata": {"analysis_failed": True}
            }
            update_progress("⚠️ Limited text found for language analysis", 1.0)
        
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
        
        # ✅ FIXED: Changed from st.experimental_rerun() to st.rerun()
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Analysis failed: {str(e)}")
        
        # Log the error for debugging
        st.error("Please try again or contact support if the issue persists.")
        
        # Optionally show more details in an expander
        with st.expander("🔍 Error Details (for debugging)"):
            st.code(str(e))

def display_analysis_results():
    """Display comprehensive analysis results"""
    
    results = st.session_state.analysis_results
    document_analysis = results.get("document_analysis", {})
    language_analysis = results.get("language_analysis", {})
    
    st.markdown("## 📊 Analysis Results")
    
    # Quick stats summary
    display_quick_stats(document_analysis, language_analysis)
    
    # Create tabs for organized display
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Extracted Text", 
        "📋 Summary & Insights", 
        "🎴 Flashcards", 
        "❓ Q&A Pairs",
        "📊 Detailed Analysis", 
        "🔍 Quality Report"
    ])
    
    with tab1:
        display_extracted_text(document_analysis)
    
    with tab2:
        display_summary_insights(language_analysis)
    
    with tab3:
        display_flashcards(language_analysis)
    
    with tab4:
        display_qa_pairs(language_analysis)
    
    with tab5:
        display_detailed_analysis(document_analysis, language_analysis)
    
    with tab6:
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
    entities = language_analysis.get("entities", {}).get("entities", [])
    flashcards = language_analysis.get("flashcards", [])
    qa_pairs = language_analysis.get("qa_pairs", [])
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("📄 Pages", metadata.get("page_count", 0))
    
    with col2:
        st.metric("📝 Words", len(content.split()) if content else 0)
    
    with col3:
        st.metric("🔑 Key Phrases", len(key_phrases))
    
    with col4:
        st.metric("🏷️ Entities", len(entities))
    
    with col5:
        st.metric("🎴 Flashcards", len(flashcards))
    
    with col6:
        confidence = metadata.get("average_confidence", 0)
        st.metric("🎯 Confidence", f"{confidence:.1%}")

def display_extracted_text(document_analysis):
    """Display extracted text content"""
    text_extraction = document_analysis.get("text_extraction", {})
    content = text_extraction.get("content", "")
    
    if content:
        st.markdown("### 📄 Extracted Content")
        
        # Text statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Characters", len(content))
        with col2:
            st.metric("Words", len(content.split()))
        with col3:
            st.metric("Lines", len(text_extraction.get("lines", [])))
        with col4:
            confidence = text_extraction.get("metadata", {}).get("average_confidence", 0)
            st.metric("Avg Confidence", f"{confidence:.2%}")
        
        # Display content with copy functionality
        st.text_area(
            "Full Text Content",
            content,
            height=300,
            help="This is the complete text extracted from your document using Azure Document Intelligence"
        )
        
        # Content hierarchy if available
        content_hierarchy = text_extraction.get("content_hierarchy", [])
        if content_hierarchy:
            st.markdown("#### 📊 Important Content Sections")
            
            for i, item in enumerate(content_hierarchy[:5], 1):
                importance = item.get("importance", 0)
                confidence = item.get("confidence", 0)
                content_text = item.get("content", "")
                
                with st.expander(f"Section {i} - Importance: {importance:.1%}"):
                    st.write(content_text)
                    st.caption(f"Confidence: {confidence:.1%} | Page: {item.get('page', 'N/A')}")
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Extracted Text",
                data=content,
                file_name=f"extracted_text_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            if content_hierarchy:
                hierarchy_json = json.dumps(content_hierarchy, indent=2)
                st.download_button(
                    label="📊 Download Content Analysis",
                    data=hierarchy_json,
                    file_name=f"content_analysis_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )
    else:
        st.warning("⚠️ No text content was extracted from the document.")

def display_summary_insights(language_analysis):
    """Display summary and key insights"""
    
    # Summary
    summary_data = language_analysis.get("summary", {})
    if summary_data.get("text") and summary_data.get("status") == "success":
        st.markdown("### 📝 Intelligent Summary")
        st.markdown(f'<div class="feature-card">{summary_data["text"]}</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Method", summary_data.get("method", "Unknown"))
        with col2:
            st.metric("Confidence", f"{summary_data.get('confidence', 0):.1%}")
    elif summary_data.get("status") == "failed":
        st.info("📝 Summary generation was limited due to insufficient text content.")
    
    # Key Phrases
    key_phrases_data = language_analysis.get("key_phrases", {})
    phrases = key_phrases_data.get("phrases", [])
    
    if phrases and key_phrases_data.get("status") == "success":
        st.markdown("### 🔑 Key Concepts")
        
        # Display as styled tags
        phrase_html = ""
        for phrase in phrases[:15]:  # Show top 15
            phrase_html += f'<span class="key-phrase-tag">{phrase}</span>'
        
        st.markdown(phrase_html, unsafe_allow_html=True)
        
        # Show additional details
        if len(phrases) > 15:
            with st.expander(f"View all {len(phrases)} key phrases"):
                for phrase in phrases:
                    st.write(f"• {phrase}")
    
    # Sentiment Analysis
    sentiment_data = language_analysis.get("sentiment", {})
    if sentiment_data.get("overall_sentiment") and sentiment_data.get("status") == "success":
        st.markdown("### 😊 Sentiment Analysis")
        
        sentiment = sentiment_data["overall_sentiment"]
        confidence = sentiment_data.get("confidence", 0)
        
        # Sentiment visualization
        col1, col2, col3 = st.columns(3)
        
        with col1:
            emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(sentiment, "😐")
            sentiment_class = f"sentiment-{sentiment}"
            st.markdown(f'<div class="{sentiment_class}"><h3>{emoji} {sentiment.title()}</h3></div>', 
                       unsafe_allow_html=True)
        
        with col2:
            st.metric("Confidence", f"{confidence:.1%}")
        
        with col3:
            method = sentiment_data.get("method", "Azure Text Analytics")
            st.write(f"**Method:** {method}")
        
        # Detailed sentiment scores
        detailed_scores = sentiment_data.get("detailed_scores", {})
        if detailed_scores:
            st.markdown("**Detailed Sentiment Breakdown:**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("😊 Positive", f"{detailed_scores.get('positive', 0):.1%}")
            with col2:
                st.metric("😐 Neutral", f"{detailed_scores.get('neutral', 0):.1%}")
            with col3:
                st.metric("😞 Negative", f"{detailed_scores.get('negative', 0):.1%}")
    
    # Entities
    entities_data = language_analysis.get("entities", {})
    entities = entities_data.get("entities", [])
    
    if entities and entities_data.get("status") == "success":
        st.markdown("### 🏷️ Identified Entities")
        
        # Group by category
        by_category = entities_data.get("by_category", {})
        
        for category, entity_list in by_category.items():
            if entity_list:
                st.markdown(f"**{category}:**")
                
                # Display as tags
                entity_html = ""
                for entity in entity_list[:8]:  # Show top 8 per category
                    confidence = entity.get("confidence_score", 0)
                    conf_class = "confidence-high" if confidence >= 0.8 else "confidence-medium" if confidence >= 0.6 else "confidence-low"
                    entity_html += f'<span class="entity-tag {conf_class}">{entity["text"]} ({confidence:.1%})</span>'
                
                st.markdown(entity_html, unsafe_allow_html=True)
                
                if len(entity_list) > 8:
                    with st.expander(f"View all {len(entity_list)} {category} entities"):
                        for entity in entity_list:
                            st.write(f"• {entity['text']} (Confidence: {entity.get('confidence_score', 0):.1%})")
    
    # Language Detection
    language_detection = language_analysis.get("language_detection", {})
    if language_detection.get("status") == "success":
        st.markdown("### 🌍 Language Detection")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Detected Language", language_detection.get("language", "Unknown"))
        with col2:
            st.metric("Confidence", f"{language_detection.get('confidence_score', 0):.1%}")

def display_flashcards(language_analysis):
    """Display generated flashcards"""
    flashcards = language_analysis.get("flashcards", [])
    
    if not flashcards:
        st.info("📚 No flashcards were generated. This might happen if the extracted text is too short or doesn't contain suitable content for flashcard creation.")
        return
    
    st.markdown("### 🎴 Study Flashcards")
    st.markdown("*Click on cards to reveal answers and study information*")
    
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
    
    # Flashcard display with flip functionality
    for i, card in enumerate(filtered_cards):
        question = card.get("question", "No question")
        answer = card.get("answer", "No answer")
        card_type = card.get("type", "general")
        difficulty = card.get("difficulty", "medium")
        confidence = card.get("confidence", 0.5)
        source = card.get("source", "unknown")
        
        # Determine confidence class
        conf_class = "confidence-high" if confidence >= 0.8 else "confidence-medium" if confidence >= 0.6 else "confidence-low"
        
        with st.expander(f"🎴 Card {i+1}: {card_type.title()} - {difficulty.title()}", expanded=False):
            st.markdown(f'<div class="flashcard">', unsafe_allow_html=True)
            st.markdown(f'<div class="flashcard-question">❓ {question}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="flashcard-answer">💡 {answer}</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<span class="{conf_class}">Confidence: {confidence:.1%}</span>', unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Type:** {card_type}")
            with col3:
                st.markdown(f"**Source:** {source}")
            
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

def display_qa_pairs(language_analysis):
    """Display generated Q&A pairs"""
    qa_pairs = language_analysis.get("qa_pairs", [])
    
    if not qa_pairs:
        st.info("❓ No Q&A pairs were generated. This might happen if the extracted text is too short or doesn't contain suitable content for question generation.")
        return
    
    st.markdown("### ❓ Question & Answer Pairs")
    st.markdown("*These questions are automatically generated based on the document content*")
    
    for i, qa in enumerate(qa_pairs, 1):
        question = qa.get("question", "No question")
        answer = qa.get("answer", "No answer")
        confidence = qa.get("confidence", 0.5)
        qa_type = qa.get("type", "general")
        key_phrase = qa.get("key_phrase", "")
        
        with st.expander(f"Q{i}: {question}", expanded=False):
            st.markdown(f"**Answer:** {answer}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                conf_class = "confidence-high" if confidence >= 0.8 else "confidence-medium" if confidence >= 0.6 else "confidence-low"
                st.markdown(f'<span class="{conf_class}">Confidence: {confidence:.1%}</span>', unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Type:** {qa_type}")
            with col3:
                if key_phrase and key_phrase != "general":
                    st.markdown(f"**Key Phrase:** {key_phrase}")
    
    # Export Q&A pairs
    if st.button("📥 Export Q&A Pairs as JSON"):
        qa_json = json.dumps(qa_pairs, indent=2)
        st.download_button(
            label="Download Q&A Pairs",
            data=qa_json,
            file_name=f"qa_pairs_{int(time.time())}.json",
            mime="application/json"
        )

def display_detailed_analysis(document_analysis, language_analysis):
    """Display detailed analysis results"""
    
    st.markdown("### 📊 Comprehensive Analysis Details")
    
    # Document Structure
    layout_analysis = document_analysis.get("layout_analysis", {})
    if layout_analysis and layout_analysis.get("processing_successful", False):
        st.markdown("#### 📋 Document Structure Analysis")
        
        # Document statistics
        structure = layout_analysis.get("document_structure", {})
        if structure:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sections", structure.get("total_sections", 0))
            with col2:
                st.metric("Summary-Ready Sections", structure.get("summary_ready_sections", 0))
            with col3:
                structure_quality = structure.get("structure_quality", "unknown")
                st.metric("Structure Quality", structure_quality.title())
        
        # Summary sections
        summary_sections = layout_analysis.get("summary_sections", [])
        if summary_sections:
            st.markdown("**High-Priority Content Sections:**")
            for section in summary_sections[:5]:
                st.write(f"• **{section.get('role', 'content').title()}:** {section.get('content', '')[:100]}...")
    
    # Table Analysis
    table_extraction = document_analysis.get("table_extraction", {})
    tables = table_extraction.get("tables", [])
    
    if tables and table_extraction.get("processing_successful", False):
        st.markdown("#### 📊 Tables Analysis")
        
        for i, table in enumerate(tables):
            st.markdown(f"**Table {i+1}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", table.get('row_count', 0))
            with col2:
                st.metric("Columns", table.get('column_count', 0))
            with col3:
                relevance = table.get('summary_relevance', 0)
                st.metric("Summary Relevance", f"{relevance:.1%}")
            
            # Display sample table data
            cells = table.get("cells", [])
            if cells:
                st.markdown("**Sample Content:**")
                
                # Create a simple table display
                table_data = {}
                for cell in cells[:12]:  # Show first 12 cells
                    row = cell.get("row_index", 0)
                    col = cell.get("column_index", 0)
                    content = cell.get("content", "")
                    
                    if row not in table_data:
                        table_data[row] = {}
                    table_data[row][col] = content
                
                # Display first few rows
                for row_idx in sorted(table_data.keys())[:3]:
                    row_data = table_data[row_idx]
                    cells_content = [row_data.get(col_idx, "") for col_idx in sorted(row_data.keys())]
                    st.write(f"Row {row_idx}: {' | '.join(cells_content[:4])}")  # Show first 4 columns
            
            st.markdown("---")
    
    # Handwriting Analysis Details
    handwriting_analysis = document_analysis.get("handwriting_analysis", {})
    if handwriting_analysis.get("handwriting_detected"):
        st.markdown("#### ✍️ Handwriting Analysis Details")
        
        quality_score = handwriting_analysis.get("quality_score", 0)
        confidence_dist = handwriting_analysis.get("confidence_distribution", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Overall Quality", f"{quality_score:.1%}")
            
            summary_impact = handwriting_analysis.get("summary_impact", "unknown")
            impact_color = {"minimal": "🟢", "low": "🟡", "moderate": "🟠", "high": "🔴"}.get(summary_impact, "⚪")
            st.markdown(f"**Summary Impact:** {impact_color} {summary_impact.title()}")
        
        with col2:
            if confidence_dist:
                st.markdown("**Recognition Quality Distribution:**")
                st.write(f"High: {confidence_dist.get('high_confidence', 0):.1f}%")
                st.write(f"Medium: {confidence_dist.get('medium_confidence', 0):.1f}%")
                st.write(f"Low: {confidence_dist.get('low_confidence', 0):.1f}%")
    
    # Language Analysis Metadata
    lang_metadata = language_analysis.get("metadata", {})
    if lang_metadata and not lang_metadata.get("analysis_failed"):
        st.markdown("#### 🧠 Language Processing Statistics")
        
        text_stats = lang_metadata.get("text_statistics", {})
        analysis_results = lang_metadata.get("analysis_results", {})
        
        if text_stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Characters", text_stats.get("character_count", 0))
            with col2:
                st.metric("Words", text_stats.get("word_count", 0))
            with col3:
                st.metric("Sentences", text_stats.get("sentence_count", 0))
            with col4:
                st.metric("Paragraphs", text_stats.get("paragraph_count", 0))
        
        if analysis_results:
            st.markdown("**Analysis Success Rates:**")
            for analysis_type, success in analysis_results.items():
                if isinstance(success, bool):
                    status = "✅" if success else "❌"
                    st.write(f"{status} {analysis_type.replace('_', ' ').title()}")
                elif isinstance(success, int):
                    st.write(f"📊 {analysis_type.replace('_', ' ').title()}: {success}")

def display_quality_report(document_analysis, language_analysis):
    """Display quality assessment and recommendations"""
    
    st.markdown("### 🔍 Quality Assessment Report")
    
    # Overall Quality Summary
    quality_metrics = document_analysis.get("quality_metrics", {})
    
    if quality_metrics:
        st.markdown("#### 📊 Overall Quality Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_quality = quality_metrics.get("overall_quality", "Unknown")
            quality_class = f"quality-{overall_quality.lower()}"
            st.markdown(f'<div class="{quality_class}"><h3>Overall: {overall_quality}</h3></div>', 
                       unsafe_allow_html=True)
        
        with col2:
            text_quality = quality_metrics.get("text_extraction_quality", 0)
            st.metric("Text Extraction Quality", f"{text_quality:.1%}")
        
        with col3:
            optimization_score = quality_metrics.get("optimization_score", 0)
            st.metric("Summary Optimization", f"{optimization_score:.1%}")
        
        # Recommendations
        recommendations = quality_metrics.get("recommendations", [])
        if recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in recommendations:
                st.write(f"• {rec}")
    
    # Document Processing Details
    text_extraction = document_analysis.get("text_extraction", {})
    extraction_metadata = text_extraction.get("metadata", {})
    
    if extraction_metadata:
        st.markdown("#### 📄 Document Processing Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Processing Information:**")
            st.write(f"API Version: {extraction_metadata.get('api_version', 'Unknown')}")
            st.write(f"Region: {extraction_metadata.get('region', 'Unknown')}")
            st.write(f"Optimization Level: {extraction_metadata.get('optimization_level', 'Unknown')}")
            
            processing_successful = extraction_metadata.get("processing_successful", False)
            status_emoji = "✅" if processing_successful else "❌"
            st.write(f"Processing Status: {status_emoji}")
        
        with col2:
            st.markdown("**Content Statistics:**")
            st.write(f"Pages Processed: {extraction_metadata.get('page_count', 0)}")
            st.write(f"Total Lines: {extraction_metadata.get('total_lines', 0)}")
            st.write(f"Total Words: {extraction_metadata.get('total_words', 0)}")
            
            summary_readiness = extraction_metadata.get("summary_readiness", "unknown")
            readiness_emoji = {"excellent": "🌟", "good": "👍", "fair": "👌", "poor": "⚠️"}.get(summary_readiness, "❓")
            st.write(f"Summary Readiness: {readiness_emoji} {summary_readiness.title()}")
    
    # Quality Indicators
    st.markdown("#### 🎯 Quality Indicators")
    
    lang_metadata = language_analysis.get("metadata", {})
    quality_indicators = lang_metadata.get("quality_indicators", {})
    
    if quality_indicators:
        indicators = [
            ("Text Length Adequate", quality_indicators.get("text_length_adequate", False)),
            ("Has Structure", quality_indicators.get("has_structure", False)),
            ("Entity Richness", quality_indicators.get("entity_richness", False)),
            ("Concept Density", quality_indicators.get("concept_density", False))
        ]
        
        for indicator_name, indicator_value in indicators:
            status = "✅" if indicator_value else "❌"
            st.write(f"{status} {indicator_name}")
    
    # Processing Summary
    processing_info = lang_metadata.get("processing_info", {})
    if processing_info:
        st.markdown("#### ⚙️ Processing Summary")
        
        methods_used = processing_info.get("analysis_methods_used", [])
        if methods_used:
            st.markdown("**Analysis Methods Applied:**")
            for method in methods_used:
                st.write(f"• {method.replace('_', ' ').title()}")
        
        api_region = processing_info.get("api_region", "Unknown")
        service_name = processing_info.get("azure_language_service", "Unknown")
        st.write(f"**Service:** {service_name} ({api_region})")
    
    # Export Quality Report
    if st.button("📥 Export Quality Report"):
        quality_report = {
            "overall_assessment": quality_metrics,
            "document_processing": extraction_metadata,
            "language_analysis": lang_metadata,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        report_json = json.dumps(quality_report, indent=2)
        st.download_button(
            label="Download Quality Report",
            data=report_json,
            file_name=f"quality_report_{int(time.time())}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()