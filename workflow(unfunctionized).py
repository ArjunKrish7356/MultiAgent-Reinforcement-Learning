import logfire
import dotenv
import os
from pydantic_ai.agent import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from pydantic import BaseModel, Field

from prompts import customer_support_prompt, evaluator_prompt, rewriter_prompt
import json
from datetime import datetime
from pathlib import Path

dotenv.load_dotenv()
groq_key = os.getenv("GROQ_KEY")
logfire_token = os.getenv("LOGFIRE_TOKEN")


logfire.configure(token=logfire_token)
logfire.instrument_pydantic_ai()

model = GroqModel(
    'qwen/qwen3-32b', provider=GroqProvider(api_key=groq_key)
)


user_prompt = input("Enter your custom prompt (or press Enter to use default): ").strip()
agent1_old_prompt = ''
agent1_new_prompt = user_prompt if user_prompt else customer_support_prompt

class EvaluatorOutput(BaseModel):
    improvement_instr: list[str] = Field("Improvement instructions from the agent")
    score: int = Field("Score between 1 to 100 about how well the agent has performed according to the metrics")

# Ask for custom evaluation criteria
custom_criteria = input("Enter additional evaluation criteria (or press Enter to use default): ").strip()

# Build the evaluator prompt with optional custom criteria
evaluator_system_prompt = evaluator_prompt
if custom_criteria:
    evaluator_system_prompt += f"\n\nAdditional Custom Criteria:\n{custom_criteria}"

evaluator_agent = Agent(
    system_prompt=evaluator_system_prompt,
    model=model,
    output_type=EvaluatorOutput
)

class rewriterOutput(BaseModel):
    new_prompt: str = Field("updated system prompt")
    improvements: list[str] = Field("What improvements where made.")

rewriter_agent = Agent(
    system_prompt=rewriter_prompt,
    output_type=rewriterOutput,
    model=model
)

scores = []

# Ask user for number of RL cycles
num_cycles = input("Enter number of RL cycles to run (or press Enter for default 5): ").strip()
try:
    num_cycles = int(num_cycles) if num_cycles else 5
except ValueError:
    num_cycles = 5
    print("Invalid input, using default 5 cycles.")

# This loop is the no of iterations of our whole system
for i in range(num_cycles):
    log_file = Path("interactions.json")
    log_file.write_text("[]", encoding="utf-8")

    # Make new instance of customer support agent to apply the new prompt changes
    customer_support_agent = Agent(
    model=model,
    system_prompt=agent1_new_prompt,
    output_type=str,
    )

    # agent1 runs and collects chatlog from user
    for j in range(2):
        user_ip = input("Enter your query: ")
        
        agent1_response = customer_support_agent.run_sync(user_ip)
        print(agent1_response.output)

        try:
            data = json.loads(log_file.read_text())
        except Exception:
            data = []

        data.append({
            "user_input": user_ip,
            "agent_output": agent1_response.output,
        })

        log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    
    # agent2 runs
    agent2_response = evaluator_agent.run_sync(
            log_file.read_text()
        )
    
    scores.append(agent2_response.output.score)
    if len(scores) > 1 and scores[-1] < scores[-2]:
        scores.pop()
        print(f"FAIL : backtracked because of lower score.")
        agent1_new_prompt = agent1_old_prompt
        continue

    
    # agent3 runs
    agent3_response = rewriter_agent.run_sync(
        f"""
        old_prompt: {agent1_new_prompt} \n\n
        improvement_instructions: {agent2_response.output.improvement_instr}
        """
    )

    # append new prompt to new_prompt.json
    new_prompt_text = agent3_response.output.new_prompt
    agent1_old_prompt = agent1_new_prompt
    agent1_new_prompt = new_prompt_text
    improvements = getattr(agent3_response.output, "improvements", None)
    entry = {
        "new_prompt": new_prompt_text,
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
    
    if len(scores) >= 2:
        print(f"SUCCESS: Score has been improved from {scores[-2]} to {scores[-1]}.")
    else:
        print(f"SUCCESS: Score is {scores[-1]}.")
