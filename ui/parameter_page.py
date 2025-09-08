import streamlit as st


def initialize_state(num_cycles, queries_per_cycle, custom_criteria):
    """Initialize the interactive training state in session state."""
    st.session_state.interactive_training_state = {
        'active': True,
        'current_cycle': 1,
        'total_cycles': num_cycles,
        'queries_per_cycle': queries_per_cycle,
        'custom_criteria': custom_criteria,
        'current_prompt': st.session_state.initial_prompt,
        'scores': [],
        'all_interactions': [],
        'all_improvements': [],
        'current_cycle_queries': [],
        'current_cycle_responses': [],
        'current_query_index': 0
    }


def render_parameter_page():
    """
    Render the parameter setting page UI.
    
    This function creates the UI for setting training parameters and evaluation criteria.
    It handles user input for number of RL cycles, queries per cycle, and custom criteria,
    and provides a confirmation button to initialize the training state.
    
    Returns:
        None: Updates session state when parameters are confirmed
    """
    # Create two columns for parameters
    param_col1, param_col2 = st.columns(2)

    # Training parameters
    with param_col1:
        st.subheader("Training Parameters")
        num_cycles = st.number_input(
            "Number of RL cycles", 
            min_value=1, 
            max_value=20, 
            value=5,
            help="Number of reinforcement learning cycles to run"
        )
        queries_per_cycle = st.number_input(
            "Queries per cycle", 
            min_value=1, 
            max_value=10, 
            value=2,
            help="Number of queries to process in each RL cycle"
        )
        
    # Custom criteria
    with param_col2:
        st.subheader("Evaluation Criteria")
        custom_criteria = st.text_area(
            "Additional evaluation criteria (optional)",
            placeholder="Enter custom evaluation criteria...",
            height=100,
            help="Specify additional criteria for evaluating agent performance"
        )
        
        # Confirmation button
        if st.button("Confirm Changes", type="primary"):
            initialize_state(num_cycles, queries_per_cycle, custom_criteria)
            st.success("✅ Parameters confirmed! Training configuration updated.")
            st.rerun()
