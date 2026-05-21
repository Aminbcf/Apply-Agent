import abc
from typing import List

class EmbeddingAdapter(abc.ABC):
    """Abstract base class for embedding models."""

    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors for the given texts."""
        raise NotImplementedError

# Simple placeholder implementation using sentence-transformers (if available)
class SentenceTransformerAdapter(EmbeddingAdapter):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError("sentence_transformers package is required for SentenceTransformerAdapter") from e
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()
