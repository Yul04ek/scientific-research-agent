# Turns text into vectors. Backend is chosen with EMBED_BACKEND:
#   local  - sentence-transformers on the Colab machine (default, no API quota)
#   gemini - Gemini embeddings through the OpenAI-compatible endpoint
#   hash   - simple hashing, no download, only used for offline tests
# All vectors are normalised, so cosine similarity is just a dot product.

import os

import numpy as np

_LOCAL_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
_cache: dict[str, object] = {}


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (matrix / norms).astype(np.float32)


def _embed_local(texts: list[str], is_query: bool) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    if "local" not in _cache:
        _cache["local"] = SentenceTransformer(_LOCAL_MODEL)
    model = _cache["local"]
    # bge models work better when queries carry this instruction prefix.
    if is_query and "bge" in _LOCAL_MODEL:
        texts = ["Represent this sentence for searching relevant passages: " + t for t in texts]
    return np.asarray(model.encode(texts, batch_size=32, show_progress_bar=False))  # type: ignore[attr-defined]


def _embed_gemini(texts: list[str], is_query: bool) -> np.ndarray:
    from openai import OpenAI

    client = OpenAI(
        base_url=os.getenv("BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        api_key=os.environ["API_KEY"],
    )
    model = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 64):
        response = client.embeddings.create(model=model, input=texts[start : start + 64])
        vectors.extend(item.embedding for item in response.data)
    return np.asarray(vectors)


def _embed_hash(texts: list[str], is_query: bool) -> np.ndarray:
    from sklearn.feature_extraction.text import HashingVectorizer

    vectorizer = HashingVectorizer(n_features=1024, alternate_sign=False, norm=None, ngram_range=(1, 2))
    return vectorizer.transform(texts).toarray()


def embed(texts: list[str], is_query: bool = False) -> np.ndarray:
    backend = os.getenv("EMBED_BACKEND", "local").lower()
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    if backend == "local":
        matrix = _embed_local(texts, is_query)
    elif backend == "gemini":
        matrix = _embed_gemini(texts, is_query)
    elif backend == "hash":
        matrix = _embed_hash(texts, is_query)
    else:
        raise ValueError(f"Unknown EMBED_BACKEND '{backend}' (use local, gemini or hash)")
    return _normalise(matrix)
