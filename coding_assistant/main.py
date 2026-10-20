import asyncio

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.console import Console
from rich.markdown import Markdown

from coding_assistant.capabilities.file_operations import FileOperations
from coding_assistant.capabilities.reasoning_effort import ReasoningEffort
from coding_assistant.capabilities.skills import Skills
from coding_assistant.deps import AgentDeps
from coding_assistant.utils import get_env

_INSTRUCTIONS = (
    "You are a Python coding agent.\n"
    "* Write clear, correct, and minimal Python code.\n"
    "* Follow the user's instructions exactly, do not add extra features.\n"
    "* Prefer the standard library over external dependencies unless explicitly specified.\n"
    "* Explore the project structure before planning or implementing.\n"
    "* If requirements are unclear, ask a concise clarification question.\n"
    "* Provide a brief summary of your implementation.\n"
    "* Use the available tools.\n"
)


async def run_agent() -> None:
    console = Console()
    console.print("Coding assistant ready. Type your request:\n"
            "Tip: add @high in your request for deeper reasoning on complex tasks, "
           " or @low for faster output on simple ones."
    )
    
    provider = OpenAIProvider(
    base_url=get_env("BASE_URL"),
    api_key=get_env("API_KEY"),
    )

    model = OpenAIResponsesModel(
        model_name=get_env("MODEL_NAME"),
        provider=provider,
    )

    agent = Agent[AgentDeps](
        model=model,
        instructions=_INSTRUCTIONS,
        capabilities=[
            FileOperations(),
            ReasoningEffort(base_url=get_env("BASE_URL"),
                            api_key=get_env("API_KEY"),
                            model_name=get_env("MODEL_NAME"),
            ),
            Skills(),
        ],
        deps_type=AgentDeps,
    )

    deps = AgentDeps(console=console)
    def _read_multiline_prompt() -> str:
        """Read user input across multiple lines until an empty line signals 'send'."""
        first_line = console.input(">> ")

        # Empty first line — nothing to send, loop will just ask again.
        if first_line == "":
            return ""

        lines = [first_line]

        while True:
            line = console.input("... ")
            if line == "":
                break
            lines.append(line)

        return "\n".join(lines)


    message_history: list[ModelMessage] | None = None

    while True:
        user_prompt = _read_multiline_prompt()
        if not user_prompt:
            continue

        result = await agent.run(
            user_prompt, message_history=message_history, deps=deps
        )
        console.print(Markdown(result.output))

        message_history = result.all_messages()
    

def main() -> None:
    try:
        asyncio.run(run_agent())
    except (EOFError, KeyboardInterrupt):
        pass
        
if __name__ == "__main__":
    main()
