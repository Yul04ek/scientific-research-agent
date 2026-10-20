# Search in the chunks: dense (cosine) + BM25, combined with Reciprocal Rank Fusion.
# Dense search finds similar meaning, BM25 finds exact words (method names, symbols).
# At most 2 chunks per paper in the results, so that other papers are also visible.
# If the best similarity is below the threshold, the tool says WEAK_EVIDENCE.
# The threshold is set with EVIDENCE_THRESHOLD and checked in eval/run_eval.py.

import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np

from coding_assistant.research import corpus
from coding_assistant.research.embeddings import embed

_TOKEN = re.compile(r"[A-Za-z0-9_]+")
_STOP = frozenset(
    "a an the of and or to in on for with by is are was were be been this that these those it its as at from we our can "
    "which than then also such not but if into over under between using use used".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in (w.lower() for w in _TOKEN.findall(text)) if t not in _STOP and len(t) > 1]


def weak_threshold() -> float:
    return float(os.getenv("EVIDENCE_THRESHOLD", "0.45"))


@dataclass
class Hit:
    chunk: dict
    dense: float  # cosine similarity
    bm25: float
    fused: float


class Index:
    """In-memory view of the stored corpus. Cheap to rebuild, so tools just call `load()`."""

    def __init__(self, chunks: list[dict], vectors: np.ndarray):
        self.chunks = chunks
        self.vectors = vectors
        self._tokens = [tokenize(c["text"]) for c in chunks]
        self._doc_freq: Counter = Counter()
        for tokens in self._tokens:
            self._doc_freq.update(set(tokens))
        self._avg_len = (sum(len(t) for t in self._tokens) / len(self._tokens)) if self._tokens else 1.0

    @classmethod
    def load(cls) -> "Index":
        chunks = corpus.load_chunks()
        path = corpus.data_dir() / "embeddings.npy"
        if not chunks or not path.exists():
            return cls([], np.zeros((0, 1), dtype=np.float32))
        return cls(chunks, np.load(path))

    def __len__(self) -> int:
        return len(self.chunks)

    # ---------------------------------------------------------------- scores
    def _bm25(self, query_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        n_docs = len(self._tokens)
        scores = np.zeros(n_docs, dtype=np.float32)
        for term in set(query_tokens):
            df = self._doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            for i, tokens in enumerate(self._tokens):
                tf = tokens.count(term)
                if tf:
                    denom = tf + k1 * (1 - b + b * len(tokens) / self._avg_len)
                    scores[i] += idf * tf * (k1 + 1) / denom
        return scores

    def search(
        self,
        query: str,
        k: int = 6,
        paper_id: str | None = None,
        max_per_paper: int = 2,
        mode: str = "hybrid",
    ) -> list[Hit]:
        """mode: 'hybrid' (default), 'dense' or 'bm25' - the other two exist for the evaluation."""
        if not self.chunks:
            return []
        dense = self.vectors @ embed([query], is_query=True)[0]
        sparse = self._bm25(tokenize(query))

        allowed = np.ones(len(self.chunks), dtype=bool)
        if paper_id:
            allowed = np.array([c["paper_id"] == paper_id for c in self.chunks])
            if not allowed.any():
                return []

        # Reciprocal Rank Fusion: score = sum 1 / (60 + rank) over the two rankings.
        fused = np.zeros(len(self.chunks), dtype=np.float32)
        rankings = {"dense": [dense], "bm25": [sparse], "hybrid": [dense, sparse]}[mode]
        for scores in rankings:
            masked = np.where(allowed, scores, -np.inf)
            order = np.argsort(-masked)
            for rank, idx in enumerate(order[: 200]):
                if allowed[idx]:
                    fused[idx] += 1.0 / (60 + rank)

        hits: list[Hit] = []
        per_paper: dict[str, int] = defaultdict(int)
        for idx in np.argsort(-fused):
            if not allowed[idx] or fused[idx] == 0:
                continue
            pid = self.chunks[idx]["paper_id"]
            if per_paper[pid] >= max_per_paper:
                continue
            per_paper[pid] += 1
            hits.append(Hit(self.chunks[idx], float(dense[idx]), float(sparse[idx]), float(fused[idx])))
            if len(hits) >= k:
                break
        return hits


def format_hits(hits: list[Hit], meta: dict[str, dict]) -> str:
    """Render hits as text for the agent, with citation tags and a weak-evidence warning."""
    if not hits:
        return "NO_EVIDENCE: the corpus is empty or nothing matched. Collect papers first or say the evidence is missing."
    best = max(h.dense for h in hits)
    lines = []
    if best < weak_threshold():
        lines.append(
            f"WEAK_EVIDENCE: best similarity {best:.2f} is below {weak_threshold():.2f}. "
            "The corpus probably does not cover this question; say so instead of guessing."
        )
    for hit in hits:
        c = hit.chunk
        info = meta.get(c["paper_id"], {})
        tag = f"[{c['paper_id']} p.{c['page']}]" if c["page"] else f"[{c['paper_id']} abstract]"
        lines.append(
            f"{tag} ({c['kind']}, similarity {hit.dense:.2f}) {info.get('title', '')} ({info.get('published', '')[:4]})\n{c['text']}"
        )
    return "\n\n".join(lines)
