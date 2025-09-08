import streamlit as st


def render_results_page():
    """
    Render the training results page UI.
    
    This function creates the UI for displaying training results including
    score progression, training summary, final optimized prompt, improvements
    made, and interaction history.
    
    Returns:
        None: Displays training results if available
    """
    st.header("Training Results")
    
    if st.session_state.training_results:
        results = st.session_state.training_results
        
        # Score progression and summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Score Progression")
            if results['scores']:
                st.line_chart(results['scores'])
                
        with col2:
            st.subheader("🎯 Training Summary")
            st.write(f"**Cycles Completed:** {results['num_cycles']}")
            st.write(f"**Total Interactions:** {len(results['interactions'])}")
            st.write(f"**Total Improvements:** {len(results['improvements'])}")
            
            # Score statistics
            if results['scores']:
                st.write("**Final Score:**", results['scores'][-1])
                st.write("**Best Score:**", max(results['scores']))
                improvement = results['scores'][-1] - results['scores'][0] if len(results['scores']) > 1 else 0
                st.write("**Improvement:**", improvement)
        
        # Final prompt
        st.subheader("🔄 Final Optimized Prompt")
        st.code(results['final_prompt'], language="text", wrap_lines=True)
        
        # Improvements made
        st.subheader("✨ Improvements Made")
        for i, improvement in enumerate(results['improvements'], 1):
            st.write(f"{i}. {improvement}")
        
        # Interaction history
        with st.expander("📝 Interaction History"):
            for i, (user_input, agent_output) in enumerate(results['interactions'], 1):
                st.write(f"**Interaction {i}:**")
                st.write(f"👤 **User:** {user_input}")
                st.write(f"🤖 **Agent:** {agent_output}")
                st.divider()
    else:
        st.info("No training results available yet. Please complete the training process first.")
        
    return st.session_state.training_results is not None