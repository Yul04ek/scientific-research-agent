# Small arXiv helper: search and PDF download (standard library only).
# arXiv asks for max. one request per 3 seconds, so every call waits a bit.

import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from coding_assistant.research.corpus import papers_dir, safe_id

_API = "https://export.arxiv.org/api/query"
_NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_last_call = 0.0


def _throttle(min_interval: float = 3.0) -> None:
    global _last_call
    wait = min_interval - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def _get(url: str, timeout: int = 60) -> bytes:
    _throttle()
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-yu/0.1 (research demo)"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def short_id(abs_url: str) -> str:
    """'http://arxiv.org/abs/2301.00001v2' -> '2301.00001v2'."""
    return abs_url.rsplit("/abs/", 1)[-1]


def parse_feed(xml_bytes: bytes) -> list[dict]:
    """Turn an arXiv Atom response into a list of paper dictionaries."""
    root = ET.fromstring(xml_bytes)
    papers = []
    for entry in root.findall("a:entry", _NS):
        abs_url = _clean(entry.findtext("a:id", namespaces=_NS))
        if "/abs/" not in abs_url:  # error entries have no abs url
            continue
        primary = entry.find("arxiv:primary_category", _NS)
        papers.append(
            {
                "paper_id": short_id(abs_url),
                "title": _clean(entry.findtext("a:title", namespaces=_NS)),
                "authors": [_clean(a.findtext("a:name", namespaces=_NS)) for a in entry.findall("a:author", _NS)],
                "abstract": _clean(entry.findtext("a:summary", namespaces=_NS)),
                "published": _clean(entry.findtext("a:published", namespaces=_NS))[:10],
                "category": primary.get("term") if primary is not None else "",
                "url": abs_url,
            }
        )
    return papers


def search(query: str, max_results: int = 10, sort_by: str = "relevance") -> list[dict]:
    """Search arXiv. `query` uses arXiv syntax, e.g. 'all:"conformal prediction"'."""
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max(1, min(max_results, 50)),
        "sortBy": sort_by,  # relevance | submittedDate | lastUpdatedDate
        "sortOrder": "descending",
    }
    url = f"{_API}?{urllib.parse.urlencode(params)}"
    return parse_feed(_get(url))


def download_pdf(paper_id: str) -> Path:
    """Download the PDF of a paper into data/papers/. Skips files that exist."""
    target = papers_dir() / f"{safe_id(paper_id)}.pdf"
    if target.exists() and target.stat().st_size > 0:
        return target
    pdf_bytes = _get(f"https://arxiv.org/pdf/{paper_id}", timeout=120)
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError(f"arXiv did not return a PDF for {paper_id}")
    target.write_bytes(pdf_bytes)
    return target
