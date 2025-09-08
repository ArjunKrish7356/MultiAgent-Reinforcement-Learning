import streamlit as st
import json
from pathlib import Path
from functions import (
    initialize_environment, 
    create_model, 
    create_agents,
    create_customer_support_agent,
    initialize_interaction_log
)


def render_training_page():
    """
    Render the training page UI.
    
    This function creates the UI for the interactive training cycles.
    It handles the step-by-step training process including query collection,
    agent responses, evaluation, and prompt optimization.
    
    Returns:
        None: Updates session state with training progress
    """
    st.header("Training")

    # Create the log file only once (don't overwrite on every rerun)
    log_file = Path("interactions.json")
    if not log_file.exists():
        log_file.write_text("[]", encoding="utf-8")

    run_interactive_cycle()


def run_interactive_cycle():
    """Handle the interactive training cycle UI."""
    if 'interactive_training_state' not in st.session_state:
        return st.error("RL parameters have not been set yet. Please configure the training parameters above and click the Confirm Changes button to proceed.")
    
    state = st.session_state.interactive_training_state
    st.subheader(f"🔄 Cycle {state['current_cycle']}/{state['total_cycles']}")

    if state['scores']:
        st.info(f"📊 Previous score: {state['scores'][-1]}")
    
    # Initialize current cycle data if not exists
    if 'current_cycle_queries' not in state:
        state['current_cycle_queries'] = []
        state['current_cycle_responses'] = []
        state['current_query_index'] = 0
    
    # Check if we're in the middle of collecting queries
    if state['current_query_index'] < state['queries_per_cycle']:
        # Show progress within the cycle
        st.write(f"**Query {state['current_query_index'] + 1} of {state['queries_per_cycle']} for this cycle:**")
        
        # Show previous interactions in this cycle
        if state['current_cycle_queries']:
            with st.expander(f"📝 Previous interactions in this cycle ({len(state['current_cycle_queries'])})", expanded=True):
                for i, (query, response) in enumerate(zip(state['current_cycle_queries'], state['current_cycle_responses'])):
                    st.write(f"**Query {i + 1}:** {query}")
                    st.write(f"**Agent Response:** {response}")
                    st.divider()
        
        # Get current query
        current_query = st.text_input(
            f"Enter your query:",
            key=f"current_query_{state['current_cycle']}_{state['current_query_index']}",
            placeholder="Type your question or request for the agent..."
        )
        
        if st.button("▶️ Send Query", type="primary", disabled=not current_query.strip()):
            if current_query.strip():
                process_single_query(current_query)
    else:
        # All queries for this cycle are collected, show cycle completion
        st.success(f"✅ Completed all {state['queries_per_cycle']} queries for cycle {state['current_cycle']}")
        
        # Show all interactions for this cycle
        with st.expander("📝 All interactions in this cycle", expanded=True):
            for i, (query, response) in enumerate(zip(state['current_cycle_queries'], state['current_cycle_responses'])):
                st.write(f"**Query {i + 1}:** {query}")
                st.write(f"**Agent Response:** {response}")
                st.divider()
            
        if st.button("🔄 Evaluate & Continue", type="primary"):
            complete_cycle_and_evaluate()


def process_single_query(query):
    """Process a single query and get agent response."""
    state = st.session_state.interactive_training_state
    
    try:
        # Initialize environment and create agent
        groq_key, _ = initialize_environment()
        model = create_model(groq_key)
        agent = create_customer_support_agent(model, state['current_prompt'])
        
        # Get agent response
        with st.spinner("🤖 Agent is thinking..."):
            response = agent.run_sync(query)
            agent_response = response.output
        
        # Store the interaction
        state['current_cycle_queries'].append(query)
        state['current_cycle_responses'].append(agent_response)
        state['current_query_index'] += 1
        
        # Show the response
        st.success("✅ Agent responded!")
        with st.expander("🤖 Agent Response", expanded=True):
            st.write(agent_response)
        
        # Log the interaction for evaluation
        log_interaction_to_file(query, agent_response)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error processing query: {e}")


def log_interaction_to_file(user_input, agent_output):
    """Log interaction to the JSON file for evaluation."""
    log_file = Path("interactions.json")
    
    try:
        if log_file.exists():
            data = json.loads(log_file.read_text())
        else:
            data = []
    except Exception:
        data = []
    
    data.append({
        "user_input": user_input,
        "agent_output": agent_output,
    })
    
    log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def complete_cycle_and_evaluate():
    """Complete the current cycle by running evaluation and prompt rewriting."""
    state = st.session_state.interactive_training_state
    
    try:
        with st.spinner("🔄 Evaluating performance and updating prompt..."):
            # Initialize agents
            groq_key, _ = initialize_environment()
            model = create_model(groq_key)
            evaluator_agent, rewriter_agent = create_agents(model, state['custom_criteria'])
            
            # Read interaction log for evaluation
            log_file = Path("interactions.json")
            if log_file.exists():
                log_content = log_file.read_text()
                
                # Evaluate performance
                evaluation = evaluator_agent.run_sync(log_content).output
                
                # Rewrite prompt
                rewrite_response = rewriter_agent.run_sync(
                    f"old_prompt: {state['current_prompt']}\n\nimprovement_instructions: {evaluation.improvement_instr}"
                )
                
                # Store results
                new_score = evaluation.score
                new_prompt = rewrite_response.output.new_prompt
                improvements = rewrite_response.output.improvements
                
                # Update state
                state['scores'].append(new_score)
                state['all_interactions'].extend(list(zip(state['current_cycle_queries'], state['current_cycle_responses'])))
                state['all_improvements'].extend(improvements)
                
                # Check for improvement (backtrack if score decreased)
                if len(state['scores']) > 1 and state['scores'][-1] < state['scores'][-2]:
                    st.warning(f"⚠️ Score decreased from {state['scores'][-2]} to {state['scores'][-1]}. Keeping previous prompt.")
                    state['scores'].pop()  # Remove the bad score
                else:
                    state['current_prompt'] = new_prompt
                    st.success(f"🎉 Score: {new_score}. Prompt updated!")
                
                # Save current cycle results for display
                st.session_state.current_cycle_results = {
                    'score': new_score,
                    'improvements': improvements,
                    'interactions': list(zip(state['current_cycle_queries'], state['current_cycle_responses']))
                }
                
                # Move to next cycle
                if state['current_cycle'] < state['total_cycles']:
                    state['current_cycle'] += 1
                    # Reset cycle data
                    state['current_cycle_queries'] = []
                    state['current_cycle_responses'] = []
                    state['current_query_index'] = 0
                    initialize_interaction_log()
                    st.success(f"✅ Moving to cycle {state['current_cycle']}")
                else:
                    # Training complete
                    complete_interactive_training()
                    return
                
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error during evaluation: {e}")


def complete_interactive_training():
    """Complete interactive training and save final results."""
    state = st.session_state.interactive_training_state
    
    # Create final results
    final_results = {
        'final_prompt': state['current_prompt'],
        'scores': state['scores'],
        'interactions': state['all_interactions'],
        'improvements': state['all_improvements'],
        'num_cycles': len(state['scores'])  # Actual cycles completed
    }
    
    st.session_state.training_results = final_results
    st.session_state.interactive_training_state['active'] = False
    
    st.success("🎉 Interactive training completed!")
    st.balloons()
    
    # Clear current cycle results
    if hasattr(st.session_state, 'current_cycle_results'):
        del st.session_state.current_cycle_results