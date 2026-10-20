from dataclasses import dataclass
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import ToolDefinition

from coding_assistant.deps import AgentDeps


@dataclass
class ToolLogging(AbstractCapability[Any]):
    # Same hook as in FileOperations, but separate, so every tool call is logged once.

    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDeps],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        shown = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in args.items())
        ctx.deps.console.log(f"Calling tool: {call.tool_name}({shown})")
        return args
