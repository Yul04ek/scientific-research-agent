from dataclasses import dataclass
from typing import Any

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

from coding_assistant.research.clustering import cluster_papers, format_clusters


def corpus_overview(n_clusters: int | None = None) -> str:
    """Group the collected papers into topic clusters (unsupervised KMeans on
    abstract embeddings) and describe each cluster by its key terms and example
    papers. Use it for questions like "what sub-topics does this literature
    have?" or to pick papers from different schools of thought when looking for
    conflicting evidence.

    Parameters
    ----------
    n_clusters : int | None
        Number of clusters. Leave empty to choose it automatically by silhouette score.

    Returns
    -------
    str
        Cluster sizes, key terms, example papers, and a validation against arXiv categories.
    """
    return format_clusters(cluster_papers(n_clusters))


@dataclass
class CorpusAnalysis(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(corpus_overview)
        return toolset
