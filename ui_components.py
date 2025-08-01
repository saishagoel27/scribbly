import streamlit as st
import random
from config import Config
from file_handler import file_handler
from session_keys import (
    CURRENT_STAGE, PROCESSING_RESULTS, FLASHCARDS, STUDY_SETTINGS,
    CURRENT_CARD, SHOW_ANSWER, STUDY_STATS, UPLOADED_FILE_DATA,
    GENERATION_CHOICE, VIEW_MODE
)

def render_main_access_button(app):
    if (st.session_state[PROCESSING_RESULTS] and 
        (st.session_state[FLASHCARDS] or 
         st.session_state[PROCESSING_RESULTS].get('language_result'))):

        generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
        flashcard_count = len(st.session_state[FLASHCARDS])
        language_result = st.session_state[PROCESSING_RESULTS].get('language_result', {})
        summary_data = language_result.get('summary', {})
        summary_count = len([k for k, v in summary_data.items() if v])

        if generation_choice == "flashcards_only":
            content_desc = f"🃏 {flashcard_count} Interactive Flashcards"
        elif generation_choice == "summary_only":
            content_desc = f"📄 {summary_count} AI Summaries & Key Concepts"
        else:
            content_desc = f"🃏 {flashcard_count} Flashcards + 📄 {summary_count} AI Summaries"

        st.markdown(f"""
        <div class="main-access-button">
            <h2>🎉 Your AI Study Materials are Ready!</h2>
            <p>{content_desc} generated and waiting for you</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 ACCESS YOUR STUDY MATERIALS", 
                    key="main_access_btn", 
                    type="primary", 
                    use_container_width=True):
            st.session_state[CURRENT_STAGE] = 4
            st.session_state[VIEW_MODE] = "summary" if generation_choice == "summary_only" else "browse"
            st.rerun()
        st.markdown("---")

def render_sidebar(app):
    with st.sidebar:
        st.markdown("## ⚙️ Study Settings")
        services = Config.get_available_services()
        st.markdown("### 🔧 Services")
        for service, available in services.items():
            emoji = "✅" if available else "❌"
            name = service.replace('_', ' ').title()
            st.markdown(f"{emoji} {name}")
        st.divider()
        st.markdown("### 📚 Configuration")
        st.session_state[STUDY_SETTINGS]['num_flashcards'] = st.slider(
            "Number of Flashcards", 5, 20, 
            st.session_state[STUDY_SETTINGS]['num_flashcards']
        )
        st.session_state[STUDY_SETTINGS]['difficulty'] = st.selectbox(
            "Difficulty Focus",
            ["Mixed (Recommended)", "Basic Concepts", "Advanced Topics", "Application-Based"],
            index=0
        )
        st.divider()
        if st.button("🔄 Start Over", key="sidebar_start_over", use_container_width=True):
            app.reset_session()

def render_progress_indicator(app):
    steps = ["📁 Upload", "🎯 Choose", "🔍 Process", "📚 Study"]
    current = st.session_state[CURRENT_STAGE]
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

def render_upload_stage(app):
    st.header("📁 Upload Your Study Material")
    st.markdown("Upload PDFs, images, or documents to create flashcards")
    uploaded_file_data = file_handler.create_upload_interface()
    if uploaded_file_data and not uploaded_file_data.get('error'):
        st.session_state[UPLOADED_FILE_DATA] = uploaded_file_data
        st.success("✅ File uploaded successfully!")
        metadata = uploaded_file_data.get('metadata', {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Size", f"{metadata.get('file_size_mb', 0):.1f} MB")
        with col2:
            st.metric("📄 Type", metadata.get('file_extension', 'Unknown').upper())
        with col3:
            st.metric("📋 Pages", metadata.get('estimated_pages', 1))
        if st.button("➡️ Choose What to Generate", key="upload_next", type="primary", use_container_width=True):
            st.session_state[CURRENT_STAGE] = 2
            st.rerun()
    elif uploaded_file_data and uploaded_file_data.get('error'):
        st.error(f"❌ {uploaded_file_data['error']}")

def render_generation_options(app):
    st.header("🎯 Choose What to Generate")
    if UPLOADED_FILE_DATA in st.session_state:
        metadata = st.session_state[UPLOADED_FILE_DATA].get('metadata', {})
        st.info(f"📄 Ready to process: **{metadata.get('filename', 'Your file')}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="action-button">
            <h3>🃏 Smart Flashcards</h3>
            <p>Generate interactive flashcards with Gemini AI</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Generate Flashcards Only", key="gen_flashcards", use_container_width=True, type="primary"):
            st.session_state[GENERATION_CHOICE] = "flashcards_only"
            st.session_state[CURRENT_STAGE] = 3
            st.rerun()
    with col2:
        st.markdown("""
        <div class="action-button">
            <h3>📄 AI Summary</h3>
            <p>Create summaries with Azure Language Services</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Generate Summary Only", key="gen_summary", use_container_width=True):
            st.session_state[GENERATION_CHOICE] = "summary_only"
            st.session_state[CURRENT_STAGE] = 3
            st.rerun()
    st.markdown("### 🌟 Recommended")
    st.markdown("""
    <div class="action-button">
        <h3>🎯 Complete Study Package</h3>
        <p>Generate both flashcards and summaries</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Generate Everything", key="gen_complete", use_container_width=True, type="primary"):
        st.session_state[GENERATION_CHOICE] = "complete_package"
        st.session_state[CURRENT_STAGE] = 3
        st.rerun()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Upload", key="gen_back", use_container_width=True):
            st.session_state[CURRENT_STAGE] = 1
            st.rerun()

def render_processing_stage(app):
    generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
    if generation_choice == "flashcards_only":
        st.header("🃏 Generating Flashcards")
    elif generation_choice == "summary_only":
        st.header("📄 Creating Summary")
    else:
        st.header("🔍 Creating Study Package")
    if not st.session_state[PROCESSING_RESULTS]:
        app.execute_processing()
    else:
        app.show_results()

def show_results(app):
    generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
    st.success("✅ Generation completed!")
    if generation_choice == "flashcards_only":
        st.markdown(f"### 🎉 Generated {len(st.session_state[FLASHCARDS])} flashcards!")
        st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to view your flashcards")
    elif generation_choice == "summary_only":
        language_result = st.session_state[PROCESSING_RESULTS].get('language_result', {})
        summary_data = language_result.get('summary', {})
        summary_count = len([k for k, v in summary_data.items() if v])
        st.markdown(f"### 📄 Generated {summary_count} AI summaries!")
        st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to view your summaries")
    else:
        language_result = st.session_state[PROCESSING_RESULTS].get('language_result', {})
        summary_data = language_result.get('summary', {})
        summary_count = len([k for k, v in summary_data.items() if v])
        st.markdown("### 🌟 Complete study package created!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🃏 Flashcards", len(st.session_state[FLASHCARDS]))
        with col2:
            st.metric("📄 AI Summaries", f"{summary_count} Types")
        st.info("👆 Use the **ACCESS YOUR STUDY MATERIALS** button above to explore everything!")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Generate Something Else", key="result_back", use_container_width=True):
            st.session_state[PROCESSING_RESULTS] = {}
            st.session_state[FLASHCARDS] = []
            st.session_state[CURRENT_STAGE] = 2
            st.rerun()
    with col2:
        if st.button("🔄 Start Over", key="result_restart", use_container_width=True):
            app.reset_session()

def render_study_mode(app):
    generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
    view_mode = st.session_state.get(VIEW_MODE, 'study')
    app.render_navigation_bar()
    if view_mode == "browse":
        app.render_flashcard_browser()
    elif view_mode == "summary":
        app.render_summary_viewer()
    elif view_mode == "concepts":
        app.render_concepts_viewer()
    else:
        if generation_choice == "summary_only":
            app.render_summary_study()
        else:
            app.render_flashcard_study()

def render_navigation_bar(app):
    generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
    st.markdown("""
    <div class="nav-bar">
        <h4 style="margin: 0; color: #1e293b;">🧭 Navigation</h4>
        <p style="margin: 0.5rem 0 0 0; color: #64748b;">Switch between different views</p>
    </div>
    """, unsafe_allow_html=True)
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
    if len(nav_options) > 0:
        cols = st.columns(len(nav_options))
        for i, (label, mode) in enumerate(nav_options):
            with cols[i]:
                if st.button(label, key=f"nav_{mode}", use_container_width=True):
                    st.session_state[VIEW_MODE] = mode
                    st.rerun()
    st.markdown("---")

def render_flashcard_browser(app):
    st.header("🃏 Browse Your Flashcards")
    if not st.session_state[FLASHCARDS]:
        st.warning("No flashcards available")
        return
    st.info(f"📊 **{len(st.session_state[FLASHCARDS])} flashcards** generated from your content")
    for i, card in enumerate(st.session_state[FLASHCARDS], 1):
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
    st.markdown("### 🚀 Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Start Studying Now", key="browser_study", type="primary", use_container_width=True):
            st.session_state[VIEW_MODE] = "study"
            st.rerun()
    with col2:
        if st.button("⬅️ Back to Main", key="browser_back", use_container_width=True):
            st.session_state[CURRENT_STAGE] = 1
            st.rerun()

def render_summary_viewer(app):
    st.header("📄 AI-Generated Summary")
    if 'language_result' not in st.session_state[PROCESSING_RESULTS]:
        st.warning("No summary available")
        return
    language_result = st.session_state[PROCESSING_RESULTS]['language_result']
    summary_data = language_result.get('summary', {})
    if summary_data:
        st.markdown("### 🎯 Choose Your Summary Style")
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
    key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
    if key_phrases:
        st.markdown("### 🔑 Key Concepts from Your Content")
        st.markdown("*These concepts were automatically identified by Azure AI*")
        concepts_html = ""
        for phrase in key_phrases[:20]:
            concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
        st.markdown(concepts_html, unsafe_allow_html=True)
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
    st.markdown("### 🚀 What's Next?")
    col1, col2, col3 = st.columns(3)
    with col1:
        generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
        if generation_choice in ["flashcards_only", "complete_package"]:
            if st.button("🃏 View Flashcards", key="summary_flashcards", use_container_width=True):
                st.session_state[VIEW_MODE] = "browse"
                st.rerun()
    with col2:
        if generation_choice in ["flashcards_only", "complete_package"]:
            if st.button("🎯 Start Studying", key="summary_study", type="primary", use_container_width=True):
                st.session_state[VIEW_MODE] = "study"
                st.rerun()
    with col3:
        if st.button("⬅️ Back to Main", key="summary_back", use_container_width=True):
            st.session_state[CURRENT_STAGE] = 1
            st.rerun()

def render_concepts_viewer(app):
    st.header("🔑 Key Concepts Analysis")
    if 'language_result' not in st.session_state[PROCESSING_RESULTS]:
        st.warning("No concept analysis available")
        return
    language_result = st.session_state[PROCESSING_RESULTS]['language_result']
    key_phrases = language_result.get('key_phrases', {}).get('azure_key_phrases', [])
    if key_phrases:
        st.markdown("### 🎯 Important Concepts Identified")
        st.markdown("*These concepts were automatically extracted using Azure AI Language Services*")
        concepts_html = ""
        for phrase in key_phrases:
            concepts_html += f'<span class="key-concept-tag">{phrase}</span> '
        st.markdown(concepts_html, unsafe_allow_html=True)
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
    st.markdown("### 🚀 Continue Your Study Journey")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 View Full Summary", key="concepts_summary", type="primary", use_container_width=True):
            st.session_state[VIEW_MODE] = "summary"
            st.rerun()
    with col2:
        if st.button("⬅️ Back to Main", key="concepts_back", use_container_width=True):
            st.session_state[CURRENT_STAGE] = 1
            st.rerun()

def render_summary_study(app):
    st.header("📄 Study Your AI Summary")
    if 'language_result' not in st.session_state[PROCESSING_RESULTS]:
        st.warning("No summary available")
        return
    app.render_summary_viewer()

def render_flashcard_study(app):
    st.header("🃏 Interactive Flashcard Study")
    if not st.session_state[FLASHCARDS]:
        st.warning("No flashcards available")
        return
    total_cards = len(st.session_state[FLASHCARDS])
    current_idx = st.session_state[CURRENT_CARD]
    current_card = st.session_state[FLASHCARDS][current_idx]
    progress = (current_idx + 1) / total_cards
    st.progress(progress)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📊 Progress: {current_idx + 1} of {total_cards} cards**")
    with col2:
        if st.session_state[STUDY_STATS]['total'] > 0:
            accuracy = (st.session_state[STUDY_STATS]['correct'] / st.session_state[STUDY_STATS]['total']) * 100
            st.markdown(f"**🎯 Accuracy: {accuracy:.1f}%**")
    if not st.session_state[SHOW_ANSWER]:
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
                st.session_state[SHOW_ANSWER] = True
                st.rerun()
        with col2:
            if st.button("⏭️ Skip Card", key="btn_skip_card", use_container_width=True):
                app.next_card()
    else:
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
        st.markdown("### 🎯 How did you do?")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("❌ Incorrect", key="btn_incorrect", use_container_width=True):
                app.record_answer(False)
        with col2:
            if st.button("✅ Correct", key="btn_correct", use_container_width=True):
                app.record_answer(True)
        with col3:
            if st.button("➡️ Next Card", key="btn_next_card", use_container_width=True):
                app.next_card()
    st.markdown("---")
    st.markdown("### 🎮 Study Controls")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Restart", key="btn_restart_study", use_container_width=True):
            st.session_state[CURRENT_CARD] = 0
            st.session_state[SHOW_ANSWER] = False
            st.session_state[STUDY_STATS] = {'correct': 0, 'incorrect': 0, 'total': 0}
            st.rerun()
    with col2:
        if st.button("🎲 Shuffle", key="btn_shuffle_cards", use_container_width=True):
            random.shuffle(st.session_state[FLASHCARDS])
            st.session_state[CURRENT_CARD] = 0
            st.session_state[SHOW_ANSWER] = False
            st.rerun()
    with col3:
        if st.button("📊 View Stats", key="btn_view_stats", use_container_width=True):
            app.show_detailed_stats()
    with col4:
        generation_choice = st.session_state.get(GENERATION_CHOICE, 'complete_package')
        if generation_choice in ["summary_only", "complete_package"]:
            if st.button("📖 View Summary", key="btn_study_to_summary", use_container_width=True):
                st.session_state[VIEW_MODE] = "summary"
                st.rerun()