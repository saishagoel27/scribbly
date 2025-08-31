import streamlit as st
import logging

# Simple logging setup
logging.basicConfig(level=logging.ERROR)

from session_manager import init_session_state, reset_session
import ui_components
from session_keys import CURRENT_STAGE, VIEW_MODE

class ScribblyApp:
    def setup_page_config(self):
        st.set_page_config(
            page_title="🧠 Scribbly - AI Study Helper",
            page_icon="🧠",
            layout="wide"
        )
        
        # Add your CSS styles
        st.markdown("""
        <style>
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: black;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin: 1rem 0;
        }
        .flashcard-back {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: black;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin: 1rem 0;
        }
        .summary-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .key-concept-tag {
            background: #3b82f6;
            color: black;
            padding: 0.3rem 0.8rem;  
            border-radius: 20px;
            margin: 0.2rem;
            display: inline-block;
            font-size: 0.85rem;
        }
        .nav-bar {
            background: #f1f5f9;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .action-button {
            background: #f8fafc;
            border: 2px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    def run(self):
        self.setup_page_config()
        init_session_state()
        
        # Header
        st.markdown("# 🧠 Scribbly - AI Study Helper")
        st.markdown("Transform your notes into interactive flashcards with AI")
        
        # Progress
        ui_components.render_progress_indicator(self)
        
        # Main routing based on your requirements
        stage = st.session_state[CURRENT_STAGE]
        
        if stage == 1:
            # Step 1: Upload notes
            ui_components.render_upload_stage(self)
            
        elif stage == 2: 
            # Step 2: Choose what to generate (summaries, flashcards, or both)
            ui_components.render_generation_options(self)
            
        elif stage == 3:
            # Step 3: Processing (generate content)
            ui_components.render_processing_stage(self)
            
        elif stage == 4:
            # Step 4: Access generated materials
            ui_components.render_navigation_bar(self)
            view_mode = st.session_state.get(VIEW_MODE, "study")
            
            if view_mode == "browse":
                ui_components.render_flashcard_browser(self)
            elif view_mode == "summary":
                ui_components.render_summary_viewer(self)
            elif view_mode == "concepts":
                ui_components.render_concepts_viewer(self)
            else:
                ui_components.render_flashcard_study(self)

    # Required methods for UI components
    def execute_processing(self):
        import workflow
        workflow.execute_processing(self)
    
    def show_results(self):
        ui_components.show_results(self)
    
    def record_answer(self, correct: bool):
        from session_keys import STUDY_STATS
        stats = st.session_state[STUDY_STATS]
        stats['total'] += 1
        stats['correct' if correct else 'incorrect'] += 1
        self.next_card()
    
    def next_card(self):
        from session_keys import CURRENT_CARD, SHOW_ANSWER, FLASHCARDS
        st.session_state[CURRENT_CARD] = (st.session_state[CURRENT_CARD] + 1) % len(st.session_state[FLASHCARDS])
        st.session_state[SHOW_ANSWER] = False
        st.rerun()
    
    def show_detailed_stats(self):
        from session_keys import STUDY_STATS
        stats = st.session_state[STUDY_STATS]
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            st.metric("🎯 Accuracy", f"{accuracy:.1f}%")
    
    def reset_session(self):
        reset_session()

def main():
    app = ScribblyApp()
    app.run()

if __name__ == "__main__":
    main()