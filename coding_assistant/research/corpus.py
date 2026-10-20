# Where the papers and the index are stored (one folder, DATA_DIR, default "data/").
#
#   data/papers/*.pdf     downloaded PDFs
#   data/meta.json        title, authors, abstract, category of each paper
#   data/chunks.jsonl     the text pieces we search in
#   data/embeddings.npy   one vector per chunk
#   data/figures.json     figure captions and page numbers
#   data/pages/*.png      page images, made only when the agent asks for a figure

import json
import os
from pathlib import Path


def data_dir() -> Path:
    path = Path(os.getenv("DATA_DIR", "data"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def papers_dir() -> Path:
    path = data_dir() / "papers"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pages_dir() -> Path:
    path = data_dir() / "pages"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------- metadata

def load_meta() -> dict[str, dict]:
    path = data_dir() / "meta.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_meta(meta: dict[str, dict]) -> None:
    path = data_dir() / "meta.json"
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ chunks

def load_chunks() -> list[dict]:
    path = data_dir() / "chunks.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_chunks(chunks: list[dict]) -> None:
    path = data_dir() / "chunks.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


# -------------------------------------------------------------------- figures

def load_figures() -> dict[str, list[dict]]:
    path = data_dir() / "figures.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_figures(figures: dict[str, list[dict]]) -> None:
    path = data_dir() / "figures.json"
    path.write_text(json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_id(paper_id: str) -> str:
    """arXiv ids like 'cs/0112017' or '2301.00001v2' -> a safe file name stem."""
    return paper_id.replace("/", "_")


def remove_papers(paper_ids: list[str]) -> int:
    """Delete papers from the corpus: metadata, chunks, vectors, figures and PDFs.
    Chunks of the papers that stay keep their order (chunk ids are renumbered)."""
    import numpy as np

    drop = set(paper_ids)
    meta = load_meta()
    for pid in drop:
        meta.pop(pid, None)
    save_meta(meta)

    chunks = load_chunks()
    keep = [i for i, c in enumerate(chunks) if c["paper_id"] not in drop]
    vectors_path = data_dir() / "embeddings.npy"
    if vectors_path.exists() and chunks:
        vectors = np.load(vectors_path)
        if len(vectors) == len(chunks):
            np.save(vectors_path, vectors[keep])
    save_chunks([dict(chunks[i], chunk_id=n) for n, i in enumerate(keep)])

    figures = load_figures()
    for pid in drop:
        figures.pop(pid, None)
        (papers_dir() / f"{safe_id(pid)}.pdf").unlink(missing_ok=True)
    save_figures(figures)
    return len(drop)
