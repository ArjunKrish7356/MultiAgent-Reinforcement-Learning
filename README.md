# Adaptix

🚀 **Live Demo:** https://adaptix.streamlit.app

## What is Adaptix?

Adaptix is a smart system that helps make customer support agents better by automatically improving their responses. It uses three AI agents working together to train and optimize customer support conversations. The system learns from each interaction and gets smarter over time, making your support agents more helpful and effective.

## How to Use It

### 1. Install
Clone the project to your computer:
```bash
git clone https://github.com/ArjunKrish7356/MultiAgent-Reinforcement-Learning.git
cd MultiAgent-Reinforcement-Learning
```

### 2. Run
Start the application:
```bash
streamlit run main.py
```

Open your browser and go to the URL shown in your terminal (usually `http://localhost:8501`).

## How It Works

Adaptix uses three smart agents that work together in a cycle:

1. **Support Agent** - Talks to customers and answers their questions
2. **Evaluator Agent** - Watches the conversation and gives it a score (1-100)
3. **Rewriter Agent** - Makes the support agent better based on the feedback

The system keeps repeating this process, getting better each time. If a change makes things worse, it automatically goes back to the previous version.

## File Structure

- **main.py** - The main file that brings all the UI pages together and runs the app
- **functions.py** - Contains all the core functions for creating agents and running training
- **prompts.py** - Stores the different prompts used by each agent
- **ui/** - Folder containing all the user interface pages:
  - **parameter_page.py** - Page for setting training parameters
  - **agent_setup_page.py** - Page for configuring the agent's behavior
  - **training_page.py** - Page where the actual training happens
  - **results_page.py** - Page showing training results and improvements
  - **test_agent_page.py** - Page for testing your trained agent

## How to Contribute

We welcome contributions! Here's how you can help:

1. Fork this repository
2. Create a new branch for your feature
3. Make your changes and test them
4. Submit a pull request with a clear description
5. Make sure your code is simple and well-commented

## Issues and Suggestions

If you find bugs or have ideas for improvements, please open an issue on GitHub. We'd love to hear from you!

---

**Thank you for using Adaptix!**  
*Made with ❤️ by Arjun*
