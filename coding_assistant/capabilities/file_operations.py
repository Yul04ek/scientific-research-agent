from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets import FunctionToolset

from coding_assistant.deps import AgentDeps


def _path_sandbox(path: str) -> Path:
    return Path("sandbox") / Path(path)


def read_file(path: str) -> str:
    """Read the contents of a file.

    Parameters
    ----------
    path : str
        The relative path to the file within the sandbox.

    Returns
    -------
    str
        The contents of the file as a string, or an error message if the
        file does not exist.
    """
    target = _path_sandbox(path)
    if not target.exists():
        return f"Error: file '{path}' not found in sandbox."
    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it does not exist.

    Parameters
    ----------
    path : str
        The relative path to the file within the sandbox.
    content : str
        The content to write to the file.

    Returns
    -------
    str
        A confirmation message.
    """
    target = _path_sandbox(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"File '{path}' written successfully."


def search_files(pattern: str) -> list[str]:
    """Search for files matching a glob pattern.

    Parameters
    ----------
    pattern : str
        The glob pattern to match files (e.g., "**/*.py", "test_*.py").

    Returns
    -------
    list[str]
        A list of relative file paths matching the pattern.
    """
    sandbox_root = _path_sandbox("")
    matches = sandbox_root.glob(pattern)
    return [str(p.relative_to(sandbox_root)) for p in matches]


def delete_file(path: str) -> str:
    """Delete a file.

    Parameters
    ----------
    path : str
        The relative path to the file within the sandbox.

    Returns
    -------
    str
        A confirmation message, or an error message if the file does not exist.
    """
    target = _path_sandbox(path)
    if not target.exists():
        return f"Error: file '{path}' not found in sandbox."
    target.unlink()
    return f"File '{path}' deleted successfully."


@dataclass
class FileOperations(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(read_file)
        toolset.add_function(write_file)
        toolset.add_function(search_files)
        toolset.add_function(delete_file)
        return toolset

    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDeps],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        # Runs before every tool call; logs which tool the agent invokes.
        # Must return args so execution proceeds with the (possibly edited) arguments.
        ctx.deps.console.log(f"Calling tool: {call.tool_name}")
        return args


