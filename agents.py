from pydantic_ai import Agent
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.models.groq import GroqModel
from pydantic import BaseModel, Field

from prompts import validation_agent_prompt, prompt_editor_system_prompt

Groq_key = ""

model = GroqModel(
    'qwen/qwen3-32b',
    provider=GroqProvider(api_key=Groq_key)
)

## Validation Agent
class Violation(BaseModel):
    rule_code: str = Field(description="The violated rule code")
    reason: str = Field(description="Reason for the violation")

class Validation_Agent_Output(BaseModel):
    confidence_score: int = Field("Score between 1 and 100 calculated accroding to the rules")
    violations: list[Violation] = Field(description="List of violations found")
    improvement_instructions: list[str] = Field(description="Instructions to improve agent behaviour")

validation_agent = Agent(
    model= model,
    system_prompt = validation_agent_prompt,
    output_type = Validation_Agent_Output,
)

## Prompt_Rewriting_Agent
class EditedPromptOutput(BaseModel):
    new_system_prompt: str = Field(description="new version of the input system prompt with only the minimal required edits")
    Improvements: list[str] = Field(description="Changes made and how it will help")

prompt_editor_agent = Agent(
    system_prompt=prompt_editor_system_prompt,
    model=model,
    output_type=EditedPromptOutput
)
