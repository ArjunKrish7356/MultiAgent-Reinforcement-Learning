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

customer_support_agent = Agent(
    model=model,
    system_prompt=customer_support_prompt,
    output_type=str,
)

class EvaluatorOutput(BaseModel):
    improvement_instr: list[str] = Field("Improvement instructions from the agent")
    score: int = Field("Score between 1 to 100 about how well the agent has performed according to the metrics")

evaluator_agent = Agent(
    system_prompt=evaluator_prompt,
    model=model,
    output_type=EvaluatorOutput
)

_log_file = Path("interactions.json")
if not _log_file.exists():
    _log_file.write_text("[]")

while True:
    user_ip = input("Enter your query: ")
    if user_ip == 'q':
        break

    agent1_response = customer_support_agent.run_sync(user_ip)
    print(agent1_response.output)

    try:
        _data = json.loads(_log_file.read_text())
    except Exception:
        _data = []

    _data.append({
        "user_input": user_ip,
        "agent_output": agent1_response.output,
    })

    _log_file.write_text(json.dumps(_data, ensure_ascii=False, indent=2))

agent2_response = evaluator_agent.run_sync(
    _log_file.read_text()
)

print(agent2_response.output)

class rewriterOutput(BaseModel):
    new_prompt: str = Field("updated system prompt")
    improvements: list[str] = Field("What improvements where made.")

rewriter_agent = Agent(
    system_prompt=rewriter_prompt,
    output_type=rewriterOutput,
    model=model
)

agent3_response = rewriter_agent.run_sync(
    f"""
    old_prompt: {customer_support_prompt} \n\n
    improvement_instructions: {agent2_response.output.improvement_instr}
    """
)

new_prompt_text = agent3_response.output.new_prompt
_new_prompt_file = Path("new_prompt.txt")
_new_prompt_file.write_text(new_prompt_text, encoding="utf-8")
print(agent3_response.output.improvements)
print(f"Wrote new prompt to {_new_prompt_file.resolve()}")



