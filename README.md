# MultiAgent-Reinforcement-Learning

This repository implements a multi-agent system designed for iterative improvement of support agent prompts using reinforcement learning (RL). The system features three primary agents that work together in a loop to continually refine and optimize the support agent's behavior.

## System Architecture

### Agents

1. **Support Agent**
   - Engages in conversations with technicians.
   - Provides support and answers queries based on its current system prompt.

2. **Fault Detection & Scoring Agent**
   - Monitors the conversation between the Support Agent and the technician.
   - Identifies faults, issues, or areas for improvement in the conversation.
   - Assigns a score to the interaction, highlighting specific faults and suggesting improvements.

3. **Prompt Rewriting Agent**
   - Receives improvement instructions from the Fault Detection & Scoring Agent.
   - Updates the system prompt for the Support Agent based on these instructions.
   - Ensures that prompt changes are aimed at improving overall support quality.

### Workflow Loop

The three agents operate in a continuous loop:

1. The Support Agent interacts with the technician.
2. The Fault Detection & Scoring Agent analyzes the conversation and provides feedback.
3. The Prompt Rewriting Agent updates the Support Agent's prompt.
4. The process repeats, allowing for ongoing improvement.

## Next Phase: Reinforcement Learning

In future development, reinforcement learning will be introduced to:

- Make the Prompt Rewriting Agent more robust.
- Allow the system to backtrack if changes to the prompt do not lead to improved support performance.
- Optimize prompt updates based on reward signals from conversation scores.

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/ArjunKrish7356/MultiAgent-Reinforcement-Learning.git
