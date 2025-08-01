import streamlit as st

def init_session_state():
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

def reset_session():
    """Reset session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()