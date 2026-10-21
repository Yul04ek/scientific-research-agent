# Research agent: same structure as main.py (provider -> model -> Agent -> loop),
# but with research tools and Gemini as the model.
# Terminal:  python -m coding_assistant.research_agent
# Colab:     agent = build_agent(); await ask(agent, "question")

import asyncio
import os

from pydantic_ai import Agent
from openai import AsyncOpenAI
from pydantic_ai.exceptions import ModelHTTPError

try:  # connection problems and timeouts (ModelHTTPError is a special case of it)
    from pydantic_ai.exceptions import ModelAPIError
except ImportError:
    ModelAPIError = ModelHTTPError
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.console import Console
from rich.markdown import Markdown

from coding_assistant.capabilities.corpus_analysis import CorpusAnalysis
from coding_assistant.capabilities.figure_inspection import FigureInspection
from coding_assistant.capabilities.literature_search import LiteratureSearch
from coding_assistant.capabilities.paper_retrieval import PaperRetrieval
from coding_assistant.capabilities.python_analysis import PythonAnalysis
from coding_assistant.capabilities.reasoning_effort import ReasoningEffort
from coding_assistant.capabilities.skills import Skills
from coding_assistant.capabilities.tool_logging import ToolLogging
from coding_assistant.deps import AgentDeps
from coding_assistant.utils import get_env

try:  # limit on model requests per question, so the agent cannot loop for ever
    from pydantic_ai.usage import UsageLimits
except ImportError:  # older/newer versions: run without the limit
    UsageLimits = None

SKILLS_DIR = "skills_research"

_INSTRUCTIONS = (
    "You are a scientific research assistant. You answer questions using evidence from a corpus of "
    "arXiv papers that you can extend yourself.\n"
    "* Decide yourself which tools you need; do not follow a fixed order.\n"
    "* Check with list_papers what the corpus covers. Collect papers with collect_papers only if the corpus is empty "
    "or the user asks you to. If a question is outside the topic of the corpus, say so and offer to collect papers; "
    "do not change the corpus on your own.\n"
    "* Every factual claim from the literature needs a citation tag copied from retrieve_evidence, "
    "like [2301.00001v1 p.4]. Never invent a citation.\n"
    "* If the evidence is missing or weak, say so; do not fill the gap from memory.\n"
    "* If papers disagree, present both sides instead of choosing silently.\n"
    "* Keep answers short and structured.\n"
    "* Use the available tools.\n"
)


def build_agent(console: Console | None = None) -> Agent[AgentDeps]:
    # A request that gets no answer for MODEL_TIMEOUT seconds is cancelled (and tried again in ask()).
    client = AsyncOpenAI(
        base_url=get_env("BASE_URL"),
        api_key=get_env("API_KEY"),
        timeout=float(os.getenv("MODEL_TIMEOUT", "90")),
        max_retries=1,
    )
    provider = OpenAIProvider(openai_client=client)
    # Gemini speaks the Chat Completions dialect (not the Responses API used in the course).
    model = OpenAIChatModel(model_name=get_env("MODEL_NAME"), provider=provider)

    return Agent[AgentDeps](
        model=model,
        instructions=_INSTRUCTIONS,
        capabilities=[
            LiteratureSearch(),
            PaperRetrieval(),
            CorpusAnalysis(),
            FigureInspection(),
            PythonAnalysis(),
            # Manual @low / @high only: no extra classification call, to stay inside free-tier limits.
            # Set auto_classify=True (and pass base_url/api_key/model_name) to bring the classifier back.
            ReasoningEffort(auto_classify=False),
            Skills(skills_dir=SKILLS_DIR),
            ToolLogging(),
        ],
        deps_type=AgentDeps,
    )


async def ask(
    agent: Agent[AgentDeps],
    question: str,
    console: Console | None = None,
    message_history: list[ModelMessage] | None = None,
    retries: int = 4,
):
    """Run one question. Waits and retries on a short rate limit (429).
    Stops at once if the DAILY free quota is used up, and stops the agent after
    MAX_MODEL_REQUESTS model calls (default 12) so one question cannot use the whole quota."""
    console = console or Console()
    deps = AgentDeps(console=console)
    extra = {}
    if UsageLimits is not None:
        extra["usage_limits"] = UsageLimits(request_limit=int(os.getenv("MAX_MODEL_REQUESTS", "12")))
    for attempt in range(retries + 1):
        try:
            return await agent.run(question, message_history=message_history, deps=deps, **extra)
        except ModelHTTPError as error:
            if error.status_code == 429 and "PerDay" in str(error.body):
                console.log("Daily free quota of this model is used up. Choose another MODEL_NAME or try tomorrow.")
                raise
            # 429 = rate limit, 5xx = Google server is overloaded (temporary): wait and try again
            if error.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 20 * (attempt + 1)
                console.log(f"Model answered {error.status_code}, waiting {wait} s ...")
                await asyncio.sleep(wait)
                continue
            raise
        except ModelAPIError as error:
            # no answer at all (timeout, connection lost): wait and try again
            if attempt < retries:
                wait = 10 * (attempt + 1)
                console.log(f"No answer from the model ({type(error).__name__}), waiting {wait} s ...")
                await asyncio.sleep(wait)
                continue
            raise


async def run_agent() -> None:
    console = Console()
    console.print("Research assistant ready. Type a question and press Enter twice to send it. Type exit to stop. Tip: @low / @high set reasoning effort.\n")
    agent = build_agent(console)
    history: list[ModelMessage] | None = None
    while True:
        first = console.input(">> ")
        if first.strip().lower() in ("exit", "quit"):
            break
        if not first:
            continue
        lines = [first]
        while (line := console.input("... ")) != "":
            lines.append(line)
        result = await ask(agent, "\n".join(lines), console, history)
        console.print(Markdown(result.output))
        history = result.all_messages()


def main() -> None:
    try:
        asyncio.run(run_agent())
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
