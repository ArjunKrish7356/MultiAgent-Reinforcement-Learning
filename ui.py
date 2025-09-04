import streamlit as st
import json
from pathlib import Path
from workflow import (
    run_full_rl_training, 
    initialize_environment, 
    create_model, 
    create_agents,
    run_rl_cycle,
    create_customer_support_agent
)
from prompts import customer_support_prompt

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

def main():
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
    param_col1, param_col2 = st.columns(2)

    # Training parameters
    with param_col1:
        st.subheader("Training Parameters")
        num_cycles = st.number_input("Number of RL cycles", min_value=1, max_value=20, value=5)
        queries_per_cycle = st.number_input("Queries per cycle", min_value=1, max_value=10, value=2)
        
    # Custom criteria
    with param_col2:
        st.subheader("Evaluation Criteria")
        custom_criteria = st.text_area(
            "Additional evaluation criteria (optional)",
            placeholder="Enter custom evaluation criteria...",
            height=100
        )
        if st.button("Confirm Changes"):
            initialize_state(num_cycles, queries_per_cycle, custom_criteria)
    
    st.header("Agent Setup")
    st.subheader("System Prompt")
    use_default_prompt = st.checkbox("Use default customer support prompt", value=False)
    st.info("The system prompt defines how your agent behaves. The RL training will iteratively improve this prompt based on performance feedback.")
            
    if use_default_prompt:
                initial_prompt = customer_support_prompt
                st.code(initial_prompt, language="text")
    else:
                initial_prompt = st.text_area(
                    "Custom system prompt",
                    value=customer_support_prompt,
                    height=200
                )
    st.session_state.initial_prompt = initial_prompt
    st.header("Training")


        # Create the log file only once (don't overwrite on every rerun)
    log_file = Path("interactions.json")
    if not log_file.exists():
            log_file.write_text("[]", encoding="utf-8")

    run_interactive_cycle()

    st.header("Training Results")
    if st.session_state.training_results:
            results = st.session_state.training_results
        # Score progression
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
                st.write("**Final Score:**", results['scores'][-1])
                st.write("**Best Score:**", max(results['scores']))
                st.write("**Improvement:**", results['scores'][-1] - results['scores'][0] if len(results['scores']) > 1 else 0)
            
            # Final prompt
            st.subheader("🔄 Final Optimized Prompt")
            st.code(results['final_prompt'], language="text",wrap_lines=True)
            
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
    
def initialize_state(num_cycles, queries_per_cycle, custom_criteria):
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

def run_interactive_cycle():
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
            with st.expander(f"📝 Previous interactions in this cycle ({len(state['current_cycle_queries'])})",expanded=True):
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
    


if __name__ == '__main__':
    main()
