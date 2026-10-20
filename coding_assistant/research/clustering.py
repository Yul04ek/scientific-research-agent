# Groups the papers by topic (the machine learning part).
# 1. Embed the abstracts.  2. KMeans, k chosen by silhouette score.
# 3. Compare the clusters with the arXiv categories (NMI / ARI); the categories
#    are not used for the clustering, only for checking it.
# 4. Name each cluster by its top TF-IDF words.

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score

from coding_assistant.research import corpus
from coding_assistant.research.embeddings import embed


def cluster_papers(n_clusters: int | None = None, k_range: tuple[int, int] = (2, 8), seed: int = 0) -> dict:
    meta = corpus.load_meta()
    ids = [pid for pid, info in meta.items() if info.get("abstract")]
    if len(ids) < 4:
        return {"error": f"Need at least 4 papers with abstracts, have {len(ids)}."}

    texts = [f"{meta[pid]['title']}. {meta[pid]['abstract']}" for pid in ids]
    vectors = embed(texts)

    # pick k by silhouette score (unless k is given)
    silhouettes: dict[int, float] = {}
    if n_clusters is None:
        upper = min(k_range[1], len(ids) - 1)
        for k in range(k_range[0], upper + 1):
            labels_k = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(vectors)
            if len(set(labels_k)) > 1:
                silhouettes[k] = float(silhouette_score(vectors, labels_k, metric="cosine"))
        n_clusters = max(silhouettes, key=silhouettes.get) if silhouettes else 2
    n_clusters = max(2, min(n_clusters, len(ids) - 1))

    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=seed).fit_predict(vectors)

    # Top terms per cluster via TF-IDF of the concatenated abstracts.
    cluster_docs = [" ".join(t for t, lab in zip(texts, labels) if lab == c) for c in range(n_clusters)]
    tfidf = TfidfVectorizer(stop_words="english", max_features=4000, ngram_range=(1, 2), sublinear_tf=True)
    matrix = tfidf.fit_transform(cluster_docs)
    vocabulary = np.array(tfidf.get_feature_names_out())

    clusters = []
    for c in range(n_clusters):
        members = [i for i, lab in enumerate(labels) if lab == c]
        centroid = vectors[members].mean(axis=0)
        closest = sorted(members, key=lambda i: -float(vectors[i] @ centroid))[:3]
        top_terms = vocabulary[np.argsort(-matrix[c].toarray()[0])[:6]].tolist()
        clusters.append(
            {
                "cluster": c,
                "size": len(members),
                "top_terms": top_terms,
                "example_papers": [{"paper_id": ids[i], "title": meta[ids[i]]["title"]} for i in closest],
                "paper_ids": [ids[i] for i in members],
            }
        )

    # check against arXiv categories
    categories = [meta[pid].get("category", "") for pid in ids]
    validation = None
    if len(set(categories)) > 1 and all(categories):
        validation = {
            "nmi_vs_arxiv_category": round(float(normalized_mutual_info_score(categories, labels)), 3),
            "ari_vs_arxiv_category": round(float(adjusted_rand_score(categories, labels)), 3),
            "categories_seen": sorted(set(categories)),
        }

    return {
        "n_papers": len(ids),
        "n_clusters": int(n_clusters),
        "silhouette_by_k": {k: round(v, 3) for k, v in silhouettes.items()},
        "silhouette_chosen": round(silhouettes.get(n_clusters, float(silhouette_score(vectors, labels, metric="cosine"))), 3),
        "validation": validation,
        "clusters": clusters,
    }


def format_clusters(result: dict) -> str:
    if "error" in result:
        return result["error"]
    lines = [
        f"{result['n_papers']} papers grouped into {result['n_clusters']} topic clusters "
        f"(silhouette {result['silhouette_chosen']})."
    ]
    if result["validation"]:
        v = result["validation"]
        lines.append(
            f"Check against arXiv categories {v['categories_seen']}: NMI {v['nmi_vs_arxiv_category']}, "
            f"ARI {v['ari_vs_arxiv_category']} (1 = perfect agreement, 0 = no better than chance)."
        )
    for c in result["clusters"]:
        examples = "; ".join(f"{p['paper_id']} {p['title'][:70]}" for p in c["example_papers"])
        lines.append(f"- Cluster {c['cluster']} ({c['size']} papers), key terms: {', '.join(c['top_terms'])}. E.g. {examples}")
    return "\n".join(lines)
