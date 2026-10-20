# PDF -> chunks (text, tables, abstract) + figure captions -> embeddings.
#
# * Chunks are about 220 words with 40 words overlap and keep their page number,
#   so answers can cite [paper_id p.N].
# * Tables are saved as extra chunks in Markdown.
# * Figures: only the caption is searchable. The page image is made later,
#   when the agent wants to look at a figure.
# * The abstract is always indexed, even if the PDF cannot be read.

import re
from pathlib import Path

import numpy as np

from coding_assistant.research import corpus
from coding_assistant.research.embeddings import embed

CHUNK_WORDS = 220
OVERLAP_WORDS = 40
MAX_PAGES = 40  # references and appendices rarely help, and parsing is slow

_CAPTION = re.compile(r"^\s*(Figure|Fig\.)\s*(\d+)\s*[.:|]\s*(.+)", re.IGNORECASE)


def split_words(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    """Sliding window over words. Short texts give exactly one chunk."""
    words = text.split()
    if not words:
        return []
    if len(words) <= size:
        return [" ".join(words)]
    step = size - overlap
    pieces = []
    for start in range(0, len(words), step):
        piece = words[start : start + size]
        if len(piece) < overlap + 10 and pieces:  # tiny tail: already covered by overlap
            break
        pieces.append(" ".join(piece))
    return pieces


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [[(cell or "").replace("\n", " ").strip() for cell in row] for row in table if row]
    rows = [r for r in rows if any(r)]
    if len(rows) < 2:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def parse_pdf(pdf_path: Path, paper_id: str) -> tuple[list[dict], list[dict]]:
    """Return (chunks, figures) for one PDF. Never raises on a bad page."""
    import pdfplumber

    chunks: list[dict] = []
    figures: list[dict] = []
    seen_figures: set[str] = set()

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages[:MAX_PAGES], start=1):
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001 - one broken page must not stop the paper
                text = ""

            # Figure captions: "Figure 3: ..." at the start of a line.
            for line in text.splitlines():
                match = _CAPTION.match(line)
                if match:
                    label = f"Figure {match.group(2)}"
                    if label not in seen_figures:
                        seen_figures.add(label)
                        figures.append({"figure": label, "page": page_number, "caption": match.group(3).strip()})

            for piece in split_words(text):
                chunks.append({"paper_id": paper_id, "page": page_number, "kind": "text", "text": piece})

            try:
                for table in page.extract_tables():
                    markdown = _table_to_markdown(table)
                    if markdown:
                        chunks.append({"paper_id": paper_id, "page": page_number, "kind": "table", "text": markdown})
            except Exception:  # noqa: BLE001
                pass

    return chunks, figures


def build_index(meta: dict[str, dict], reuse_existing: bool = True) -> dict:
    """(Re)build chunks.jsonl, figures.json and embeddings.npy for every paper in meta.

    Papers that are already indexed keep their chunks and embeddings; only new
    papers are parsed and embedded.
    """
    old_chunks = corpus.load_chunks() if reuse_existing else []
    old_vectors_path = corpus.data_dir() / "embeddings.npy"
    old_vectors = np.load(old_vectors_path) if (reuse_existing and old_vectors_path.exists() and old_chunks) else None
    if old_vectors is not None and len(old_vectors) != len(old_chunks):
        old_chunks, old_vectors = [], None  # inconsistent state: start over

    figures = corpus.load_figures() if reuse_existing else {}
    indexed = {c["paper_id"] for c in old_chunks}

    new_chunks: list[dict] = []
    problems: list[str] = []
    for paper_id, info in meta.items():
        if paper_id in indexed:
            continue
        # abstract first
        abstract = info.get("abstract", "")
        if abstract:
            new_chunks.append({"paper_id": paper_id, "page": 0, "kind": "abstract", "text": f"{info.get('title', '')}. {abstract}"})
        # then the full text, if the PDF is there
        pdf_path = corpus.papers_dir() / f"{corpus.safe_id(paper_id)}.pdf"
        if pdf_path.exists():
            try:
                chunks, paper_figures = parse_pdf(pdf_path, paper_id)
                new_chunks.extend(chunks)
                figures[paper_id] = paper_figures
            except Exception as error:  # noqa: BLE001
                problems.append(f"{paper_id}: PDF could not be parsed ({error}); only the abstract is indexed")
        else:
            problems.append(f"{paper_id}: no PDF downloaded; only the abstract is indexed")

    if new_chunks:
        new_vectors = embed([c["text"] for c in new_chunks])
        all_chunks = old_chunks + new_chunks
        all_vectors = new_vectors if old_vectors is None else np.vstack([old_vectors, new_vectors])
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_id"] = i
        corpus.save_chunks(all_chunks)
        np.save(old_vectors_path, all_vectors)
        corpus.save_figures(figures)
    else:
        all_chunks = old_chunks

    return {
        "papers": len(meta),
        "new_chunks": len(new_chunks),
        "total_chunks": len(all_chunks),
        "problems": problems,
    }
