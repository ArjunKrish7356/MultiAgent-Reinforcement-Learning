
import json
import os
from agents import validation_agent, prompt_editor_agent

import logfire
logfire.configure(token="")
logfire.instrument_pydantic_ai()

async def run_conversation_workflow(json_file_path="sample_conversation_data.json"):
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build absolute paths for the files
        json_path = os.path.join(script_dir, json_file_path)
        prompt_path = os.path.join(script_dir, 'system_prompt.txt')
        output_path = os.path.join(script_dir, 'new_system_prompt.txt')
        
        with open(json_path, 'r') as file:
            data = json.load(file)
        with open(prompt_path, 'r') as prompt_file:
            system_prompt = prompt_file.read().strip()
        data['system_prompt'] = system_prompt

        # Compose validation input
        validation_input = (
            f"Conversation Log: {json.dumps(data.get('conversation_log', []), indent=2)}\n"
            f"Final Collected Data: {json.dumps(data.get('final_collected_data', {}), indent=2)}"
        )

        validator_response = await validation_agent.run(validation_input)
        validator_output = validator_response.output
        print(validator_output)

        editor_input = (
            f"system_prompt: {system_prompt}\n"
            f"improvement_instructions: {validator_output}"
        )
        edited_prompt = await prompt_editor_agent.run(editor_input)
        edited_output = edited_prompt.output

        print("Validation Results:\n", validator_output)
        print("Prompt Editing Results:\n", edited_output.Improvements)

        # Save new system prompt
        with open(output_path, 'w') as f:
            f.write(edited_output.new_system_prompt)
        print(f"Updated system prompt saved to '{output_path}'")
        print("WORKFLOW COMPLETE")
        return edited_output
    except Exception as e:
        print("Error!!! Details are given below \n")  # Detailed error info
        print(e)           # Print the exception message

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation_workflow())



