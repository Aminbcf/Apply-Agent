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
        import os
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            if "client has been closed" in str(e) or "getaddrinfo" in str(e) or "Max retries exceeded" in str(e):
                print(f"Network error loading {model_name}, attempting offline mode...")
                os.environ["HF_HUB_OFFLINE"] = "1"
                self.model = SentenceTransformer(model_name, local_files_only=True)
            else:
                raise

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()
