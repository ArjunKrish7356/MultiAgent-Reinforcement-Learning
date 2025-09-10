import streamlit as st
from prompts import customer_support_prompt


def render_agent_setup_page():
    """
    Render the agent setup page UI.
    
    This function creates the UI for configuring the agent's system prompt.
    Users can choose to use the default customer support prompt or provide
    a custom prompt. The selected prompt is stored in session state.
    
    Returns:
        None: Updates session state with the initial prompt
    """
    st.header("Agent Setup")
    st.subheader("System Prompt")
    
    # Checkbox for using default prompt
    use_default_prompt = st.checkbox("Use default customer support prompt", value=False)
    
    # Information about the system prompt
    st.info("The system prompt defines how your agent behaves. The training will iteratively improve this prompt based on performance feedback.")
            
    if use_default_prompt:
        # Display default prompt
        initial_prompt = customer_support_prompt
        st.code(initial_prompt, language="text")
    else:
        # Custom prompt text area
        initial_prompt = st.text_area(
            "Custom system prompt",
            value=customer_support_prompt,
            height=200,
            help="Enter your custom system prompt here. This will be the starting point for prompt optimization."
        )
    
    # Store the initial prompt in session state
    st.session_state.initial_prompt = initial_prompt
    
    return initial_prompt