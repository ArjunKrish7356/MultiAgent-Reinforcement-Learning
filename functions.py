import logfire
import dotenv
import os
from pydantic_ai.agent import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple, Optional
import streamlit as st

from prompts import customer_support_prompt, evaluator_prompt, rewriter_prompt
import json
from datetime import datetime
from pathlib import Path


class EvaluatorOutput(BaseModel):
    improvement_instr: list[str] = Field("Improvement instructions from the agent")
    score: int = Field("Score between 1 to 100 about how well the agent has performed according to the metrics")


class RewriterOutput(BaseModel):
    new_prompt: str = Field("updated system prompt")
    improvements: list[str] = Field("What improvements where made.")


def initialize_environment() -> Tuple[str, str]:
    """Initialize environment variables and return API keys."""
    dotenv.load_dotenv()
    groq_key = os.getenv("GROQ_KEY")
    logfire_token = os.getenv("LOGFIRE_TOKEN")

    if not groq_key:
        groq_key = st.secrets['GROQ_KEY']
        logfire_token = st.secrets['LOGFIRE_TOKEN']
    
    if logfire_token:
        logfire.configure(token=logfire_token)
        logfire.instrument_pydantic_ai()
    
    return groq_key, logfire_token


def create_model(groq_key: str) -> GroqModel:
    """Create and return a GroqModel instance."""
    return GroqModel(
        'qwen/qwen3-32b', provider=GroqProvider(api_key=groq_key)
    )


def create_agents(model: GroqModel, custom_criteria: str = "") -> Tuple[Agent, Agent]:
    """Create and return evaluator and rewriter agents."""
    evaluator_system_prompt = evaluator_prompt
    if custom_criteria:
        evaluator_system_prompt += f"\n\nAdditional Custom Criteria:\n{custom_criteria}"

    evaluator_agent = Agent(
        system_prompt=evaluator_system_prompt,
        model=model,
        output_type=EvaluatorOutput
    )

    rewriter_agent = Agent(
        system_prompt=rewriter_prompt,
        output_type=RewriterOutput,
        model=model
    )
    
    return evaluator_agent, rewriter_agent


def create_customer_support_agent(model: GroqModel, system_prompt: str) -> Agent:
    """Create a customer support agent with the given system prompt."""
    return Agent(
        model=model,
        system_prompt=system_prompt,
        output_type=str,
    )


def initialize_interaction_log() -> Path:
    """Initialize and return the interaction log file path."""
    log_file = Path("interactions.json")
    log_file.write_text("[]", encoding="utf-8")
    return log_file


def log_interaction(log_file: Path, user_input: str, agent_output: str) -> None:
    """Log a user interaction to the JSON file."""
    try:
        data = json.loads(log_file.read_text())
    except Exception:
        data = []

    data.append({
        "user_input": user_input,
        "agent_output": agent_output,
    })

    log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def evaluate_performance(evaluator_agent: Agent, log_content: str) -> EvaluatorOutput:
    """Evaluate the agent's performance using the evaluator agent."""
    response = evaluator_agent.run_sync(log_content)
    return response.output


def rewrite_prompt(rewriter_agent: Agent, old_prompt: str, improvement_instructions: List[str]) -> RewriterOutput:
    """Rewrite the prompt using the rewriter agent."""
    prompt_text = f"""
    old_prompt: {old_prompt} \n\n
    improvement_instructions: {improvement_instructions}
    """
    response = rewriter_agent.run_sync(prompt_text)
    return response.output


def save_new_prompt(new_prompt: str, improvements: List[str]) -> None:
    """Save the new prompt and improvements to new_prompt.json."""
    entry = {
        "new_prompt": new_prompt,
        "improvements": improvements,
    }

    json_file = Path("new_prompt.json")
    try:
        existing = json.loads(json_file.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            existing = [existing]
    except Exception:
        existing = []

    existing.append(entry)
    json_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


def run_customer_interaction(agent: Agent, user_queries: List[str]) -> List[Tuple[str, str]]:
    """Run customer interactions and return the conversation log."""
    interactions = []
    log_file = initialize_interaction_log()
    
    for query in user_queries:
        response = agent.run_sync(query)
        agent_output = response.output
        interactions.append((query, agent_output))
        log_interaction(log_file, query, agent_output)
    
    return interactions


def run_rl_cycle(
    initial_prompt: str,
    custom_criteria: str,
    user_queries: List[str],
    evaluator_agent: Agent,
    rewriter_agent: Agent,
    model: GroqModel
) -> Tuple[str, int, List[str], List[Tuple[str, str]]]:
    """
    Run a single RL cycle and return results.
    
    Returns:
        - Updated prompt
        - Score
        - Improvements made
        - Interaction log
    """
    # Create customer support agent with current prompt
    customer_agent = create_customer_support_agent(model, initial_prompt)
    
    # Run customer interactions
    interactions = run_customer_interaction(customer_agent, user_queries)
    
    # Read the log file for evaluation
    log_file = Path("interactions.json")
    log_content = log_file.read_text()
    
    # Evaluate performance
    evaluation = evaluate_performance(evaluator_agent, log_content)
    
    # Rewrite prompt based on evaluation
    rewritten = rewrite_prompt(rewriter_agent, initial_prompt, evaluation.improvement_instr)
    
    # Save the new prompt
    save_new_prompt(rewritten.new_prompt, rewritten.improvements)
    
    return rewritten.new_prompt, evaluation.score, rewritten.improvements, interactions


def run_full_rl_training(
    initial_prompt: str = None,
    custom_criteria: str = "",
    num_cycles: int = 5,
    queries_per_cycle: int = 2,
    user_queries_callback=None
) -> Dict[str, Any]:
    """
    Run the full reinforcement learning training process.
    
    Args:
        initial_prompt: Starting prompt (uses default if None)
        custom_criteria: Additional evaluation criteria
        num_cycles: Number of RL cycles to run
        queries_per_cycle: Number of user queries per cycle
        user_queries_callback: Function to get user queries (for Streamlit)
    
    Returns:
        Dictionary containing training results
    """
    # Initialize environment and models
    groq_key, logfire_token = initialize_environment()
    model = create_model(groq_key)
    
    # Set initial prompt
    if initial_prompt is None:
        initial_prompt = customer_support_prompt
    
    # Create agents
    evaluator_agent, rewriter_agent = create_agents(model, custom_criteria)
    
    # Training variables
    current_prompt = initial_prompt
    previous_prompt = ""
    scores = []
    all_interactions = []
    all_improvements = []
    
    for i in range(num_cycles):
        print(f"Starting RL Cycle {i + 1}/{num_cycles}")
        
        # Get user queries for this cycle
        if user_queries_callback:
            user_queries = user_queries_callback(i + 1, queries_per_cycle)
        else:
            # Fallback for non-interactive mode
            user_queries = [f"Default query {j+1} for cycle {i+1}" for j in range(queries_per_cycle)]
        
        # Run RL cycle
        new_prompt, score, improvements, interactions = run_rl_cycle(
            current_prompt, custom_criteria, user_queries,
            evaluator_agent, rewriter_agent, model
        )
        
        # Store results
        scores.append(score)
        all_interactions.extend(interactions)
        all_improvements.extend(improvements)
        
        # Check if score improved (backtrack if not)
        if len(scores) > 1 and scores[-1] < scores[-2]:
            scores.pop()
            print(f"FAIL: Backtracked because of lower score.")
            current_prompt = previous_prompt
            continue
        
        # Update prompts
        previous_prompt = current_prompt
        current_prompt = new_prompt
        
        # Print progress
        if len(scores) >= 2:
            print(f"SUCCESS: Score improved from {scores[-2]} to {scores[-1]}.")
        else:
            print(f"SUCCESS: Score is {scores[-1]}.")
    
    return {
        "final_prompt": current_prompt,
        "scores": scores,
        "interactions": all_interactions,
        "improvements": all_improvements,
        "num_cycles": num_cycles
    }


# Keep the original main execution for backward compatibility
if __name__ == "__main__":
    user_prompt = input("Enter your custom prompt (or press Enter to use default): ").strip()
    agent1_new_prompt = user_prompt if user_prompt else customer_support_prompt

    custom_criteria = input("Enter additional evaluation criteria (or press Enter to use default): ").strip()

    num_cycles = input("Enter number of RL cycles to run (or press Enter for default 5): ").strip()
    try:
        num_cycles = int(num_cycles) if num_cycles else 5
    except ValueError:
        num_cycles = 5
        print("Invalid input, using default 5 cycles.")

    def get_user_queries(cycle_num, queries_per_cycle):
        queries = []
        for j in range(queries_per_cycle):
            query = input(f"Cycle {cycle_num}, Query {j+1}: Enter your query: ")
            queries.append(query)
        return queries

    results = run_full_rl_training(
        initial_prompt=agent1_new_prompt,
        custom_criteria=custom_criteria,
        num_cycles=num_cycles,
        queries_per_cycle=2,
        user_queries_callback=get_user_queries
    )
    
    print("\n=== Training Complete ===")
    print(f"Final Score: {results['scores'][-1] if results['scores'] else 'N/A'}")
    print(f"Score History: {results['scores']}")
