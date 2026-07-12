"""
Wraps the sentence-transformers embedding model.
This is the "Vector Embeddings" piece of the project: it turns job
descriptions and resume text into dense numeric vectors that capture
semantic meaning, so that "Python backend developer" and "Django REST
API engineer" end up close together in vector space even though they
share few exact words.
"""

from functools import lru_cache
from sentence_transformers import SentenceTransformer
from src import config


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads the embedding model once and caches it (models are slow to
    load, so we don't want to reload it on every call).
    """
    return SentenceTransformer(config.EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list:
    """Embed a single piece of text into a vector (list of floats)."""
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_texts(texts: list) -> list:
    """Embed a batch of texts at once (more efficient than one-by-one)."""
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
