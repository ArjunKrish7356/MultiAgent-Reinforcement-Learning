import streamlit as st
from functions import (
    initialize_environment,
    create_model,
    create_customer_support_agent
)


def render_test_agent_page():
    """
    Render the test agent page UI.
    
    This function creates the UI for testing the trained agent through
    a chat interface. Users can interact with their trained agent
    using the final optimized prompt.
    
    Returns:
        None: Displays chat interface if training results are available
    """
    st.header("Test Your Trained Agent")
    
    if st.session_state.training_results:
        final_prompt = st.session_state.training_results['final_prompt']
        
        st.subheader("🤖 Chat with your trained agent")
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask your trained agent something..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get agent response
            try:
                groq_key, _ = initialize_environment()
                model = create_model(groq_key)
                agent = create_customer_support_agent(model, final_prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = agent.run_sync(prompt)
                        agent_response = response.output
                        st.write(agent_response)
                
                # Add agent response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
                
            except Exception as e:
                st.error(f"Error getting agent response: {e}")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.info("No trained agent available yet. Please complete the training process first to test your agent.")
        
    return st.session_state.training_results is not None