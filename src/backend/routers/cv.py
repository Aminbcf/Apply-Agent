from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from AI.cv_processor import CVProcessor
from AI.domain_embeddings import DOMAINS, get_embedding_manager

router = APIRouter()

cv_processor = CVProcessor()
embedding_manager = get_embedding_manager()


class CVData(BaseModel):
    """CV data model."""

    name: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    other_info: Optional[Dict[str, Any]] = None


class CVEmbeddingResponse(BaseModel):
    """Response model for CV with embeddings."""

    cv_data: Dict[str, Any]
    best_domain: str
    domain_scores: List[tuple]


@router.get("/domains")
def get_all_domains() -> dict[str, List[str]]:
    """Get all available job domains."""
    return {"domains": DOMAINS}


@router.get("/domain-embeddings")
def get_domain_embeddings() -> dict[str, List[float]]:
    """Get semantic embeddings for all domains."""
    return embedding_manager.get_all_domain_embeddings()


@router.post("/process-cv")
def process_cv(cv: CVData) -> Dict[str, Any]:
    """
    Process a CV and add semantic embeddings.

    Args:
        cv: CV data

    Returns:
        Enriched CV data with embeddings and domain classification
    """
    cv_dict = cv.model_dump(exclude_none=True)
    enriched_cv = cv_processor.process_cv(cv_dict)
    return enriched_cv


@router.post("/classify-cv-domain")
def classify_cv_domain(cv: CVData) -> Dict[str, Any]:
    """
    Classify CV to its best matching domain.

    Args:
        cv: CV data

    Returns:
        Best matching domain and similarity score
    """
    text = cv.summary or ""
    if cv.skills:
        text += " " + " ".join(cv.skills)
    if cv.experience:
        text += " " + cv.experience

    domain, score = embedding_manager.find_best_matching_domain(text)

    return {
        "domain": domain,
        "confidence": score,
    }


@router.post("/cv-domain-scores")
def get_cv_domain_scores(cv: CVData) -> Dict[str, List[tuple]]:
    """
    Get similarity scores for all domains for a given CV.

    Args:
        cv: CV data

    Returns:
        Dictionary with domain names and their similarity scores
    """
    text = cv.summary or ""
    if cv.skills:
        text += " " + " ".join(cv.skills)
    if cv.experience:
        text += " " + cv.experience

    scores = cv_processor.get_domain_similarity_scores(text)

    return {
        "domain_scores": sorted(scores.items(), key=lambda item: item[1], reverse=True)
    }


@router.post("/embed-text")
def embed_text(text: str) -> Dict[str, Any]:
    """
    Generate semantic embedding for arbitrary text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    embedding = embedding_manager.embed_text(text)
    return {
        "text": text,
        "embedding": embedding.tolist(),
        "dimension": len(embedding),
    }


@router.post("/parse-raw-cv")
def parse_raw_cv(raw_cv_text: str) -> Dict[str, Any]:
    """
    Parse raw CV text and convert to structured format with embeddings.

    Handles common CV formats with sections like:
    - Summary/Overview
    - Highlights/Key Skills
    - Experience/Work History
    - Education
    - Skills

    Args:
        raw_cv_text: Raw CV text

    Returns:
        Structured CV data with semantic embeddings and domain classification
    """
    enriched_cv = cv_processor.parse_and_process_raw_cv(raw_cv_text)
    return enriched_cv
