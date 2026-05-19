"""
Domain-based semantic embeddings for CV categorization.
Uses sentence-transformers to generate embeddings for predefined domains.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Tuple
import json

# Domains from Kaggle dataset
DOMAINS = [
    'HR', 'DESIGNER', 'INFORMATION-TECHNOLOGY', 'TEACHER', 'ADVOCATE',
    'BUSINESS-DEVELOPMENT', 'HEALTHCARE', 'FITNESS', 'AGRICULTURE',
    'BPO', 'SALES', 'CONSULTANT', 'DIGITAL-MEDIA', 'AUTOMOBILE',
    'CHEF', 'FINANCE', 'APPAREL', 'ENGINEERING', 'ACCOUNTANT',
    'CONSTRUCTION', 'PUBLIC-RELATIONS', 'BANKING', 'ARTS', 'AVIATION'
]


class DomainEmbeddingManager:
    """Manages semantic embeddings for job domains."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding manager with a pre-trained model.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                       'all-MiniLM-L6-v2' is lightweight and fast.
                       'all-mpnet-base-v2' is more accurate but slower.
        """
        self.model = SentenceTransformer(model_name)
        self.domain_embeddings: Dict[str, np.ndarray] = {}
        self.domains = DOMAINS
        self._generate_domain_embeddings()
    
    def _generate_domain_embeddings(self) -> None:
        """Generate embeddings for all domains."""
        domain_texts = [
            f"A professional working in {domain} field"
            for domain in self.domains
        ]
        embeddings = self.model.encode(domain_texts, convert_to_numpy=True)
        
        for domain, embedding in zip(self.domains, embeddings):
            self.domain_embeddings[domain] = embedding
    
    def get_domain_embedding(self, domain: str) -> np.ndarray:
        """Get embedding for a specific domain."""
        return self.domain_embeddings.get(domain)
    
    def get_all_domain_embeddings(self) -> Dict[str, List[float]]:
        """
        Get all domain embeddings as a dictionary.
        
        Returns:
            Dictionary mapping domain names to their embedding vectors (as lists).
        """
        return {
            domain: embedding.tolist()
            for domain, embedding in self.domain_embeddings.items()
        }
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for arbitrary text (e.g., CV content).
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def find_best_matching_domain(self, text: str) -> Tuple[str, float]:
        """
        Find the best matching domain for a given text.
        
        Args:
            text: Text to classify (e.g., CV summary)
            
        Returns:
            Tuple of (domain_name, similarity_score)
        """
        text_embedding = self.embed_text(text)
        
        max_similarity = -1
        best_domain = None
        
        for domain, domain_embedding in self.domain_embeddings.items():
            # Compute cosine similarity
            similarity = np.dot(text_embedding, domain_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(domain_embedding)
            )
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_domain = domain
        
        return best_domain, float(max_similarity)
    
    def find_top_matching_domains(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find top-k matching domains for a given text.
        
        Args:
            text: Text to classify
            top_k: Number of top domains to return
            
        Returns:
            List of (domain_name, similarity_score) tuples, sorted by similarity descending
        """
        text_embedding = self.embed_text(text)
        similarities = []
        
        for domain, domain_embedding in self.domain_embeddings.items():
            similarity = np.dot(text_embedding, domain_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(domain_embedding)
            )
            similarities.append((domain, float(similarity)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def embed_cv(self, cv_data: Dict) -> Dict:
        """
        Add semantic embeddings to CV data.
        
        Args:
            cv_data: Dictionary containing CV information
                    Expected keys: 'summary', 'skills', 'experience', etc.
        
        Returns:
            Updated cv_data with added 'embeddings' field
        """
        cv_copy = cv_data.copy()
        
        # Generate composite text from CV sections
        cv_text_parts = []
        if 'summary' in cv_data:
            cv_text_parts.append(cv_data['summary'])
        if 'skills' in cv_data:
            cv_text_parts.append(' '.join(cv_data['skills']) if isinstance(cv_data['skills'], list) else cv_data['skills'])
        if 'experience' in cv_data:
            cv_text_parts.append(str(cv_data['experience']))
        
        composite_text = ' '.join(cv_text_parts)
        
        # Generate embeddings
        cv_copy['embeddings'] = {
            'vector': self.embed_text(composite_text).tolist(),
            'best_domain': self.find_best_matching_domain(composite_text)[0],
            'domain_scores': self.find_top_matching_domains(composite_text, top_k=5)
        }
        
        return cv_copy


# Singleton instance for easy access
_embedding_manager = None

def get_embedding_manager() -> DomainEmbeddingManager:
    """Get or create the singleton embedding manager."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = DomainEmbeddingManager()
    return _embedding_manager
