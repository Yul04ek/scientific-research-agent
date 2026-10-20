"""Pure metric functions (no model calls), so they can be unit-tested."""

import re

import numpy as np

CITATION = re.compile(r"\[([A-Za-z0-9./_-]+?) (?:p\.(\d+)|abstract)\]")


def first_hit_rank(hits: list[tuple[str, int]], gold: tuple[str, int], level: str) -> int | None:
    """Rank (1-based) of the first hit that matches the gold passage, else None.

    level='paper': same paper.  level='page': same paper AND same page
    (neighbouring chunks overlap, so the exact chunk id is too strict).
    """
    for rank, (paper_id, page) in enumerate(hits, start=1):
        if paper_id == gold[0] and (level == "paper" or page == gold[1]):
            return rank
    return None


def retrieval_scores(ranks: list[int | None], ks: tuple[int, ...] = (1, 3, 6)) -> dict[str, float]:
    n = max(len(ranks), 1)
    scores = {f"hit@{k}": sum(1 for r in ranks if r is not None and r <= k) / n for k in ks}
    scores["MRR"] = sum(1 / r for r in ranks if r is not None) / n
    return {k: round(v, 3) for k, v in scores.items()}


def best_threshold(answerable: list[float], unanswerable: list[float]) -> dict[str, float]:
    """Pick the similarity threshold that best separates 'corpus covers it' from 'corpus does not'.

    Maximises balanced accuracy; also reports AUROC (threshold-free separability).
    """
    if not answerable or not unanswerable:
        return {}
    scores = np.array(answerable + unanswerable)
    labels = np.array([1] * len(answerable) + [0] * len(unanswerable))
    best = (-1.0, 0.0)
    for t in np.unique(scores):
        predicted = scores >= t
        tpr = (predicted & (labels == 1)).sum() / (labels == 1).sum()
        tnr = (~predicted & (labels == 0)).sum() / (labels == 0).sum()
        balanced = (tpr + tnr) / 2
        if balanced > best[0]:
            best = (balanced, float(t))
    # AUROC by rank statistic (probability that a random answerable score beats a random unanswerable one)
    wins = sum((a > u) + 0.5 * (a == u) for a in answerable for u in unanswerable)
    auroc = wins / (len(answerable) * len(unanswerable))
    return {"threshold": round(float(best[1]), 3), "balanced_accuracy": round(float(best[0]), 3), "auroc": round(float(auroc), 3)}


_ARXIV_ID = r"(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z.-]+/\d{7}(?:v\d+)?)"
_ITEM = re.compile(rf"^({_ARXIV_ID})(?:\s+(?:p\.(\d+)|abstract))?$")


def citation_report(answer: str, valid_tags: set[str]) -> dict:
    """Check the citations in an answer against what the tools really returned in this run.

    Accepted forms: [id p.4], [id abstract], [id], and lists such as [id1, id2 p.3].
    A citation with a page must match a returned tag exactly; a citation with only an id
    must belong to a paper that was returned.
    """
    returned_papers = {tag.strip("[]").split()[0] for tag in valid_tags}
    found, valid = [], []
    for group in re.findall(r"\[([^\[\]]+)\]", answer):
        for item in re.split(r"[;,]\s*", group):
            match = _ITEM.match(item.strip())
            if not match:
                continue
            paper_id, page = match.group(1), match.group(2)
            if page:
                tag = f"[{paper_id} p.{page}]"
            elif item.strip().endswith("abstract"):
                tag = f"[{paper_id} abstract]"
            else:
                tag = f"[{paper_id}]"
            found.append(tag)
            if (tag in valid_tags) if (page or tag.endswith("abstract]")) else (paper_id in returned_papers):
                valid.append(tag)
    return {"n_citations": len(found), "n_valid": len(valid), "invalid": sorted(set(found) - set(valid))}
