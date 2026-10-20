import os
from dataclasses import dataclass
from typing import Any

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

from coding_assistant.research import arxiv_client, corpus
from coding_assistant.research.indexer import build_index


def search_arxiv(query: str, max_results: int = 10, sort_by: str = "relevance") -> str:
    """Search arXiv for papers WITHOUT downloading them. Use it to look around
    before deciding what to collect.

    Parameters
    ----------
    query : str
        arXiv search syntax, e.g. 'all:"conformal prediction" AND all:coverage'
        or 'ti:"mixed models"'. Plain words also work.
    max_results : int
        How many papers to list (1-30).
    sort_by : str
        "relevance" (default), "submittedDate" (newest first) or "lastUpdatedDate".

    Returns
    -------
    str
        One line per paper: id, year, category, title.
    """
    try:
        papers = arxiv_client.search(query, max_results=min(max_results, 30), sort_by=sort_by)
    except Exception as error:  # noqa: BLE001 - network problems must not crash the agent
        return f"ERROR: arXiv search failed ({error}). Try again or use papers already in the corpus."
    if not papers:
        return "No papers found. Try broader or different keywords."
    in_corpus = set(corpus.load_meta())
    return "\n".join(
        f"{p['paper_id']} | {p['published'][:4]} | {p['category']} | {p['title']}"
        + (" | already in corpus" if p["paper_id"] in in_corpus else "")
        for p in papers
    )


def collect_papers(query: str, max_results: int = 8) -> str:
    """Search arXiv, download the PDFs of the results, and add them to the
    searchable corpus (text, tables and figure captions are indexed).
    Papers already in the corpus are skipped. This can take several minutes, and it changes
    the corpus for good, so use it only as the skill instructs.

    Parameters
    ----------
    query : str
        arXiv search syntax or plain words describing the topic.
    max_results : int
        Number of papers to add (1-15).

    Returns
    -------
    str
        A summary of what was added and what failed.
    """
    if os.getenv("FREEZE_CORPUS") == "1":  # set by the evaluation, so every run uses the same papers
        return "Collecting is switched off in this run: the corpus is fixed. Answer from the papers already in the corpus."
    try:
        papers = arxiv_client.search(query, max_results=min(max_results, 15))
    except Exception as error:  # noqa: BLE001
        return f"ERROR: arXiv search failed ({error})."
    meta = corpus.load_meta()
    added, failed = [], []
    for paper in papers:
        pid = paper["paper_id"]
        if pid in meta:
            continue
        meta[pid] = paper
        try:
            arxiv_client.download_pdf(pid)
            added.append(f"{pid} {paper['title'][:80]}")
        except Exception as error:  # noqa: BLE001
            failed.append(f"{pid}: PDF download failed ({error}); abstract only")
    corpus.save_meta(meta)
    report = build_index(meta)
    lines = [f"Added {len(added)} papers; corpus now has {len(meta)} papers and {report['total_chunks']} chunks."]
    lines += [f"+ {a}" for a in added]
    lines += failed + report["problems"]
    return "\n".join(lines)


@dataclass
class LiteratureSearch(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(search_arxiv)
        toolset.add_function(collect_papers)
        return toolset
