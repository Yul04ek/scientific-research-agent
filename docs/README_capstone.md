![AI Agent Yu helping a scientist](IMG_0488.png)


# AI Agent Yu

AI Agent Yu is a small coding assistant built during the Agentic AI 
masterclass by the appliedAI Institute.

The goal of this project is to learn how to build an **agentic coding 
assistant** from scratch using **Python** and **Pydantic AI**.

I designed it specifically for non-programmer researchers — 
biologists, psychologists, economists — who use Python for their 
scientific or analytical work but aren't professional developers.

The agent runs in the terminal and offers several built-in skills, so 
it can help with writing code, step-by-step explanations, error 
explanations, plotting, and project structuring — all through simple 
conversation. Skills follow a two-level architecture: a router file 
(`SKILL.md`) plus a `references/` subfolder for more detailed, 
narrowly scoped topics.

The agent also offers the user a choice of request complexity, or 
decides on its own if the user doesn't choose — letting it work deeper 
for a more detailed, precise answer, or faster to save tokens.

## What this project demonstrates

- A conversational agent that keeps context across multiple turns.
- Tool-calling to work with files (read, write, search).
- Execution hooks for logging what the agent is doing.
- Dynamic control of reasoning effort (simple vs complex tasks).
- Loading extra "skills" from Markdown files (flat or two-level 
  architecture) to extend the assistant.

## Project structure

- `coding_assistant/main.py` – entry point, interactive loop for the assistant.
- `coding_assistant/utils.py` – helper functions (console, config, etc.).
- `coding_assistant/deps.py` – dependency container for the agent (e.g. console).
- `coding_assistant/capabilities/` – capabilities and tools:
  - `file_operations.py` – tools for reading/writing files.
  - `reasoning_effort.py` – adjusts reasoning level based on the prompt.
  - `skills.py` – loads and exposes external skills.

## Setup

You can use any Python environment manager (conda, venv, etc.). Example with conda:

```bash
conda create -n agentic-ai python=3.12 -y
conda activate agentic-ai
```

Install dependencies:

```bash
python -m pip install "pydantic-ai[openai]" openai rich python-frontmatter
```

## Configuration

Create a `.env` file in the project root with your OpenAI-compatible credentials:

```
BASE_URL=https://openrouter.ai/api/v1
API_KEY=sk-...
MODEL_NAME=your-model-name
```

## Run

```bash
python -m coding_assistant.main
```

You can now chat with the agent from your terminal.

## Why this project exists

This repository is part of my THRIVE portfolio: it shows that I can set up a local Python environment, use an LLM framework, and design a simple but extensible agent that works on my own machine.
