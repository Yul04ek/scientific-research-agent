import base64
import os
from dataclasses import dataclass
from typing import Any

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

from coding_assistant.research import corpus
from coding_assistant.research.llm import chat


def list_figures(paper_id: str | None = None, query: str | None = None) -> str:
    """List figures (number, page, caption) found in the papers. Use it to find
    a figure before inspecting it.

    Parameters
    ----------
    paper_id : str | None
        Only this paper. Leave empty for all papers.
    query : str | None
        Keep only figures whose caption contains one of these words.

    Returns
    -------
    str
        One line per figure.
    """
    figures = corpus.load_figures()
    words = [w.lower() for w in (query or "").split()]
    lines = []
    for pid, items in figures.items():
        if paper_id and pid != paper_id:
            continue
        for item in items:
            caption = item["caption"]
            if words and not any(w in caption.lower() for w in words):
                continue
            lines.append(f"{pid} | {item['figure']} | page {item['page']} | {caption[:160]}")
    return "\n".join(lines[:40]) or "No matching figures found."


def inspect_figure(paper_id: str, figure: str, question: str) -> str:
    """Look at a figure (or table) of a paper with a vision model and answer a
    question about it, e.g. "what is on the x and y axes?" or "which method has
    the highest value?". The whole page is shown to the model because many
    figures are vector graphics that cannot be cut out reliably.

    Parameters
    ----------
    paper_id : str
        Paper id from list_papers.
    figure : str
        Label such as "Figure 2" (see list_figures), or "page 7" to look at a page directly.
    question : str
        What you want to know about the figure.

    Returns
    -------
    str
        The vision model's answer, prefixed with the citation tag of the page.
    """
    # 1) find the page
    page_number = None
    if figure.lower().startswith("page"):
        digits = "".join(ch for ch in figure if ch.isdigit())
        page_number = int(digits) if digits else None
    else:
        for item in corpus.load_figures().get(paper_id, []):
            if item["figure"].lower() == figure.lower():
                page_number = item["page"]
    if page_number is None:
        return f"Figure '{figure}' not found for {paper_id}. Call list_figures first."

    # 2) render the page to a PNG (cached on disk)
    pdf_path = corpus.papers_dir() / f"{corpus.safe_id(paper_id)}.pdf"
    if not pdf_path.exists():
        return f"No PDF for {paper_id}; cannot look at its figures."
    image_path = corpus.pages_dir() / f"{corpus.safe_id(paper_id)}_p{page_number}.png"
    if not image_path.exists():
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            pdf.pages[page_number - 1].to_image(resolution=110).original.save(image_path)
    encoded = base64.b64encode(image_path.read_bytes()).decode()

    # 3) ask the vision model (same Gemini key, OpenAI-compatible endpoint)
    from openai import OpenAI

    client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])
    try:
        response = chat(
            client,
            model=os.getenv("VISION_MODEL", os.environ["MODEL_NAME"]),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"This is page {page_number} of a scientific paper. Look at {figure} and answer: {question}\n"
                                "Describe only what is visible. If the page does not show what is asked, say so."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
                    ],
                }
            ],
        )
    except Exception as error:  # noqa: BLE001
        return f"ERROR: the vision model call failed ({error})."
    return f"[{paper_id} p.{page_number}] {response.choices[0].message.content}"


@dataclass
class FigureInspection(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(list_figures)
        toolset.add_function(inspect_figure)
        return toolset
