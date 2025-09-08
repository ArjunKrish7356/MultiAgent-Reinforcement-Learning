import streamlit as st
from functions import initialize_environment,initialize_interaction_log

# Import all page modules
from ui.parameter_page import render_parameter_page
from ui.agent_setup_page import render_agent_setup_page
from ui.training_page import render_training_page
from ui.results_page import render_results_page
from ui.test_agent_page import render_test_agent_page


def main():
    """
    Main function that orchestrates the multi-page RL training interface.
    

    This function sets up the page configuration, initializes session state,
    checks environment configuration, and renders all the UI pages in sequence.
    Each page is rendered as a function that returns its content.
    
    Returns:
        None: Runs the complete Streamlit application
    """
    # Page configuration
    st.set_page_config(
        page_title="RL Agent Training Interface",
        page_icon="🤖",
        layout="wide"
    )

    # Initialize session state
    if 'training_results' not in st.session_state:
        st.session_state.training_results = None
    if 'current_cycle' not in st.session_state:
        st.session_state.current_cycle = 0
    if 'user_queries' not in st.session_state:
        st.session_state.user_queries = {}

    # Main title
    st.title("🤖 Multi-Agent Reinforcement Learning Training")
    st.markdown("Train your customer support agent using reinforcement learning!")

    # Environment check
    try:
        groq_key, logfire_token = initialize_environment()
        if groq_key:
            st.success("✅ Environment configured")
        else:
            st.error("❌ GROQ_KEY not found")
            return
    except Exception as e:
        st.error(f"❌ Environment error: {e}")
        return

    # Render all pages in sequence
    initialize_interaction_log()
    render_parameter_page()
    render_agent_setup_page()
    render_training_page()
    render_results_page()
    render_test_agent_page()


if __name__ == '__main__':
    main()