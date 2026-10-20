from dataclasses import dataclass
from typing import Any

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

from coding_assistant.research import corpus
from coding_assistant.research.retrieval import Index, format_hits


def list_papers() -> str:
    """List every paper in the corpus with its id, year, arXiv category and title.
    Call this first to see what the corpus covers.

    Returns
    -------
    str
        One line per paper, or a note that the corpus is empty.
    """
    meta = corpus.load_meta()
    if not meta:
        return "The corpus is empty. Use collect_papers first."
    return "\n".join(
        f"{pid} | {info.get('published', '')[:4]} | {info.get('category', '')} | {info.get('title', '')}"
        for pid, info in meta.items()
    )


def retrieve_evidence(query: str, k: int = 6, paper_id: str | None = None) -> str:
    """Find the passages in the collected papers that best match a question
    (text, tables and abstracts). Results are limited to 2 passages per paper so
    that different papers can speak. Every passage starts with a citation tag
    like [2301.00001v1 p.4] that you must copy when you use the passage.

    Parameters
    ----------
    query : str
        A short, specific query in plain words: no quotes, no OR/AND, no formulas (the search is semantic).
    k : int
        Number of passages to return (1-12).
    paper_id : str | None
        Restrict the search to one paper (use an id from list_papers).

    Returns
    -------
    str
        Passages with citation tags and similarity scores. A line starting with
        WEAK_EVIDENCE or NO_EVIDENCE means the corpus probably does not answer
        the question.
    """
    index = Index.load()
    hits = index.search(query, k=max(1, min(k, 12)), paper_id=paper_id)
    return format_hits(hits, corpus.load_meta())


@dataclass
class PaperRetrieval(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(list_papers)
        toolset.add_function(retrieve_evidence)
        return toolset
