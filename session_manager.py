import streamlit as st
from session_keys import (
    CURRENT_STAGE, PROCESSING_RESULTS, FLASHCARDS, STUDY_SETTINGS,
    CURRENT_CARD, SHOW_ANSWER, STUDY_STATS
)

def init_session_state():
    """Initialize session state variables"""
    if CURRENT_STAGE not in st.session_state:
        st.session_state[CURRENT_STAGE] = 1
    if PROCESSING_RESULTS not in st.session_state:
        st.session_state[PROCESSING_RESULTS] = {}
    if FLASHCARDS not in st.session_state:
        st.session_state[FLASHCARDS] = []
    if STUDY_SETTINGS not in st.session_state:
        st.session_state[STUDY_SETTINGS] = {
            'num_flashcards': 20,
            'difficulty': 'Mixed (Recommended)'
        }
    # Initialize flashcard study variables
    if CURRENT_CARD not in st.session_state:
        st.session_state[CURRENT_CARD] = 0
    if SHOW_ANSWER not in st.session_state:
        st.session_state[SHOW_ANSWER] = False
    if STUDY_STATS not in st.session_state:
        st.session_state[STUDY_STATS] = {'correct': 0, 'incorrect': 0, 'total': 0}

def reset_session():
    """Reset session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]