"""Retrieval-Augmented Generation service for Apply-Agent.

This module is the single entry-point for all generation scenarios (CV,
cover letter, job match).  It wires together:

1. Async retrieval helpers that pull context from SQLite and disk.
2. :func:`~AI.llm.llm_interface.build_rag_prompt` for prompt assembly.
3. The active :class:`~AI.llm.llm_interface.LLMAdapter` from ``model_registry``.

Usage::

    service = RAGService(db=session)
    response = await service.generate(session_id="abc", scenario="cv", job_id="<uuid>")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding_service import EmbeddingAdapter, SentenceTransformerAdapter
from .history_cache import HistoryCache
from .llm_interface import LLMAdapter, build_rag_prompt

logger = logging.getLogger(__name__)

# ── Disk-based example file locations ────────────────────────────────────────

_AI_DIR = Path(__file__).parent.parent          # src/backend/AI/
_CV_EXAMPLES_DIR = _AI_DIR / "CV-Examples"
_CL_EXAMPLES_DIR = _AI_DIR / "Cover-letter-Examples"


# ── Retrieval helpers (all async, DB-backed) ──────────────────────────────────


def _flatten_skills(profile_skills) -> List[str]:
    skills_flat: List[str] = []
    if profile_skills and isinstance(profile_skills, dict):
        for v in profile_skills.values():
            if isinstance(v, list):
                skills_flat.extend(str(s) for s in v)
    return skills_flat

async def retrieve_cv_context(db: AsyncSession) -> dict:
    """Pull the full user profile from SQLite and return it as a structured dict.

    Returns a dict with all fields needed to build a CV or cover letter prompt.
    If no profile exists, returns an empty dict so generation degrades gracefully.
    """
    from models.user_profile import UserProfile  # noqa: PLC0415

    result = await db.execute(select(UserProfile))
    profile = result.scalars().first()

    if profile is None:
        logger.warning("retrieve_cv_context: no UserProfile found in DB")
        return {}

    skills_flat = _flatten_skills(profile.skills)

    education_entries = profile.education if isinstance(profile.education, list) else []
    experience_entries = profile.experience if isinstance(profile.experience, list) else []
    experience_years = len(experience_entries) * 2  # simple heuristic

    return {
        "name": profile.full_name or "",
        "email": profile.email or "",
        "phone": profile.phone or "",
        "location": profile.location or "",
        "career_goals": profile.career_goals or "",
        "skills": skills_flat,
        "education": education_entries,
        "experience": experience_entries,
        "projects": profile.projects if isinstance(profile.projects, list) else [],
        "certifications": profile.certifications if isinstance(profile.certifications, list) else [],
        "languages": profile.languages if isinstance(profile.languages, list) else [],
        "achievements": profile.achievements if isinstance(profile.achievements, list) else [],
        "raw_cv_text": (profile.raw_cv_text or "")[:3000],  # cap to avoid prompt overflow
        "experience_years": experience_years,
        "education_level": " ".join(
            f"{e.get('degree', '')} {e.get('institution', '')}".strip()
            for e in education_entries
            if isinstance(e, dict)
        )[:500],
    }


async def retrieve_job_context(db: AsyncSession, job_id: str) -> dict:
    """Pull a JobApplication record from SQLite and return it as a structured dict.

    Parameters
    ----------
    db:
        Active async SQLAlchemy session.
    job_id:
        UUID string of the job application to retrieve.
    """
    import uuid  # noqa: PLC0415
    from models.job_application import JobApplication  # noqa: PLC0415

    try:
        job_uuid = uuid.UUID(job_id)
    except (ValueError, AttributeError):
        logger.warning("retrieve_job_context: invalid job_id '%s'", job_id)
        return {}

    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_uuid)
    )
    job = result.scalar_one_or_none()
    if job is None:
        return {}

    return {
        "job_id": str(job.id),
        "title": job.job_title or "",
        "company": job.company_name or "",
        "description": job.job_description or "",
        "extracted_requirements": job.extracted_requirements or {},
        "dimension_scores": job.dimension_scores or {},
        "match_score": job.match_score,
    }


async def retrieve_few_shot_examples(
    db: AsyncSession,
    limit: int = 3,
    max_chars: int = 800,
) -> List[dict]:
    """Return recent accepted/confirmed jobs as few-shot generation examples.

    Parameters
    ----------
    db:
        Active async SQLAlchemy session.
    limit:
        Maximum number of examples to return.
    max_chars:
        Maximum characters of CV/cover-letter text per example (to avoid
        prompt overflow).
    """
    from models.job_application import JobApplication  # noqa: PLC0415
    from sqlalchemy import or_  # noqa: PLC0415

    result = await db.execute(
        select(JobApplication)
        .where(
            or_(
                JobApplication.workflow_status == "accepted",
                JobApplication.workflow_status == "confirmed",
            )
        )
        .order_by(JobApplication.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()

    examples = []
    for i, job in enumerate(jobs):
        cv_snippet = (job.cv_text or "")[:max_chars]
        cl_snippet = (job.cover_letter_text or "")[:max_chars]
        if not cv_snippet and not cl_snippet:
            continue
        examples.append(
            {
                "source_id": f"past_application_{i + 1}",
                "title": job.job_title or "",
                "company": job.company_name or "",
                "cv_text_snippet": cv_snippet,
                "cover_letter_snippet": cl_snippet,
            }
        )

    logger.info("retrieve_few_shot_examples: found %d accepted examples", len(examples))
    return examples


def retrieve_example_files(max_chars: int = 800) -> dict:
    """Read reference CV and cover-letter example files from disk.

    Returns a dict with keys:
    - ``"cv_examples"``              – stringified JSON from cv_examples.json
    - ``"cover_letter_instructions"`` – text from Instructions.md
    - ``"cover_letter_examples"``    – empty string (no separate examples file yet)
    """
    result: dict = {
        "cv_examples": "",
        "cover_letter_instructions": "",
        "cover_letter_examples": "",
    }

    # CV examples JSON
    cv_json_path = _CV_EXAMPLES_DIR / "cv_examples.json"
    if cv_json_path.is_file():
        try:
            data = json.loads(cv_json_path.read_text(encoding="utf-8"))
            # Return a condensed version to avoid prompt bloat
            condensed = [
                {
                    "domain": ex.get("domain"),
                    "summary": ex.get("summary"),
                    "skills": ex.get("skills", [])[:6],
                    "experience": (ex.get("experience", ""))[:max_chars],
                    "education": ex.get("education", ""),
                }
                for ex in data.get("cv_examples", [])
            ]
            result["cv_examples"] = json.dumps(condensed, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load CV examples JSON")

    # Cover-letter instructions
    cl_instr_path = _CL_EXAMPLES_DIR / "Instructions.md"
    if cl_instr_path.is_file():
        try:
            text = cl_instr_path.read_text(encoding="utf-8")
            # Keep only the most relevant sections to save tokens and avoid prompt contamination.
            result["cover_letter_instructions"] = _extract_cover_letter_guidance(text)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load cover letter instructions")

    return result

def _extract_cover_letter_guidance(text: str, max_chars: int = 1800) -> str:
    """Keep only the operational cover-letter rules and drop example-heavy sections."""
    if not text:
        return ""

    allowed_headings = {
        "System Role",
        "Preflight (always run before generation)",
        "Retrieval & Context Handling",
        "Citation Rules",
        "Metadata Extraction Schema (JSON)",
        "Prompt Templates",
        "Formatting & Style Constraints",
        "Testing & Validation Checklist (run after generation)",
        "Operational notes for RAG integrators",
    }

    kept_lines: list[str] = []
    keep_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            keep_block = heading in allowed_headings
            if keep_block:
                kept_lines.append(line)
            continue

        if keep_block:
            if "Example JSON" in stripped or "Example generation rule" in stripped:
                break
            kept_lines.append(line)

    compact = "\n".join(kept_lines).strip()
    if not compact:
        return text[:max_chars]
    return compact[:max_chars]


# ── RAGService ────────────────────────────────────────────────────────────────


class RAGService:
    """Orchestrate retrieval and generation for all scenarios.

    Parameters
    ----------
    db:
        Active async SQLAlchemy session (optional — required for DB retrieval).
    embedding_adapter:
        Optional custom embedding adapter; falls back to
        :class:`SentenceTransformerAdapter`.
    llm:
        Optional custom LLM adapter; falls back to the singleton from
        ``model_registry`` at call time.
    cache:
        Optional :class:`HistoryCache` for conversation history.
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        embedding_adapter: Optional[EmbeddingAdapter] = None,
        llm: Optional[LLMAdapter] = None,
        cache: Optional[HistoryCache] = None,
    ) -> None:
        self.db = db
        self.embedding_adapter = embedding_adapter or SentenceTransformerAdapter()
        self._llm_override = llm
        self.cache = cache or HistoryCache()

    # ── LLM accessor (lazy, uses registry singleton by default) ──────────────

    @property
    def llm(self) -> LLMAdapter:
        if self._llm_override is not None:
            return self._llm_override
        import model_registry  # noqa: PLC0415
        return model_registry.get_llm()

    # ── Public interface ──────────────────────────────────────────────────────

    async def generate(
        self,
        session_id: str,
        scenario: str,
        user_query: str = "",
        job_id: Optional[str] = None,
    ) -> str:
        """Generate a response for *scenario* using full RAG context.

        Parameters
        ----------
        session_id:
            Used to store message history in :class:`HistoryCache`.
        scenario:
            One of ``"cv"``, ``"cover_letter"``, ``"job_match"``.
        user_query:
            Optional free-text query from the user (appended to prompt if present).
        job_id:
            UUID of the target :class:`~models.job_application.JobApplication`.
            When provided, job context is injected into the prompt.
        """
        from config import settings  # noqa: PLC0415

        # Record user turn
        if user_query:
            self.cache.add_message(session_id, "user", user_query)

        # Retrieve context
        cv_context: dict = {}
        job_context: dict = {}
        few_shot: List[dict] = []

        if self.db is not None:
            cv_context = await retrieve_cv_context(self.db)
            if job_id:
                job_context = await retrieve_job_context(self.db, job_id)
            few_shot = await retrieve_few_shot_examples(
                self.db,
                limit=settings.rag_few_shot_limit,
                max_chars=settings.rag_example_max_chars,
            )

        example_files = retrieve_example_files(max_chars=settings.rag_example_max_chars)

        # Build prompt
        prompt = build_rag_prompt(
            scenario=scenario,
            cv_context=cv_context,
            job_context=job_context,
            few_shot_examples=few_shot,
            example_files=example_files,
        )
        if user_query:
            prompt += f"\n\nUser: {user_query}"

        # Generate
        response = self.llm.generate(prompt)

        # Record assistant turn
        self.cache.add_message(session_id, "assistant", response)
        return response

    async def evaluate_job(
        self,
        job_data: dict,
        session_id: str,
        db: AsyncSession,
    ) -> dict:
        """Delegate job evaluation to :class:`~AI.llm.job_match_service.JobMatchService`.

        This thin wrapper keeps :class:`RAGService` as the single entry-point
        for all RAG scenarios while the heavy lifting lives in
        :class:`~AI.llm.job_match_service.JobMatchService`.
        """
        from .job_match_service import JobMatchService  # noqa: PLC0415

        service = JobMatchService(
            db=db,
            embedding_adapter=self.embedding_adapter,
            cache=self.cache,
        )
        result = await service.evaluate_job(
            title=job_data["title"],
            company=job_data["company"],
            description=job_data["description"],
            session_id=session_id,
        )
        return result.model_dump()
