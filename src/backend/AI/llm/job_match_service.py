"""Job-match orchestration service for the Apply-Agent (Phase 7).

:class:`JobMatchService` ties together:

1. :class:`~AI.llm.checklist_extractor.ChecklistExtractor` – rule-based NLP
2. :class:`~AI.llm.embedding_service.EmbeddingAdapter` – sentence vectors
3. :class:`~AI.llm.match_scorer.MatchScorer` – deterministic scoring
4. :class:`~AI.llm.llm_interface.QwenAdapter` – LaTeX generation
5. :class:`~utils.latex_renderer.LatexRenderer` – PDF compilation
6. SQLAlchemy async session – persistence

Usage::

    service = JobMatchService(db=session)
    result = await service.evaluate_job(job_offer, session_id="abc")
    # PDF generation continues in the background; poll /jobs/{id}/status
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from AI.llm.checklist_extractor import ChecklistExtractor
from AI.llm.embedding_service import EmbeddingAdapter, SentenceTransformerAdapter
from AI.llm.history_cache import HistoryCache
from AI.llm.llm_interface import QwenAdapter, build_prompt
from AI.llm.match_scorer import DimensionScores, MatchScorer
from config import settings
from models.job_application import JobApplication
from schemas.job_schemas import JobEvaluationOut
from schemas.job_schemas import DimensionScores as DimensionScoresSchema
from utils.latex_renderer import LatexRenderer, LatexRenderError

logger = logging.getLogger(__name__)


class JobMatchService:
    """Orchestrate job evaluation, LaTeX generation, and persistence.

    Parameters
    ----------
    db:
        An active :class:`AsyncSession` (injected via FastAPI ``Depends``).
    embedding_adapter:
        Optional custom embedding adapter; falls back to
        :class:`SentenceTransformerAdapter` if *None*.
    llm:
        Optional custom LLM adapter; falls back to :class:`QwenAdapter`.
    cache:
        Optional :class:`HistoryCache`; used to clear session on rejection.
    renderer:
        Optional :class:`LatexRenderer`; constructed from ``settings`` if *None*.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_adapter: Optional[EmbeddingAdapter] = None,
        llm: Optional[QwenAdapter] = None,
        cache: Optional[HistoryCache] = None,
        renderer: Optional[LatexRenderer] = None,
    ) -> None:
        self.db = db
        self.embedding = embedding_adapter or SentenceTransformerAdapter()
        self.llm = llm or QwenAdapter()
        self.cache = cache or HistoryCache()
        self.renderer = renderer or LatexRenderer(
            output_dir=settings.latex_output_dir,
            timeout=settings.pdflatex_timeout_seconds,
        )
        self.extractor = ChecklistExtractor()
        self.scorer = MatchScorer()

    # ── Public interface ──────────────────────────────────────

    async def evaluate_job(
        self,
        title: str,
        company: str,
        description: str,
        session_id: str,
    ) -> JobEvaluationOut:
        """Evaluate a job offer and persist a new :class:`JobApplication` record.

        Steps:

        1. Extract checklist from job description (deterministic NLP).
        2. Embed job description + CV/cover-letter context.
        3. Compute all five dimension scores and the overall score.
        4. Persist the record (``processing=True``).
        5. **Caller is responsible for enqueueing** :meth:`generate_documents`
           as a background task so PDF compilation does not block the response.

        Returns
        -------
        :class:`~schemas.job_schemas.JobEvaluationOut`
            Immediate response – PDF URLs are ``None`` until the background
            task completes.
        """
        # 1 — Extract checklist
        checklist = self.extractor.extract(description)

        # 2 — Embed
        cv_context = self._build_cv_context(session_id)
        embeddings = self._compute_embeddings(description, cv_context)

        # 3 — Score
        dims: DimensionScores = self.scorer.score(checklist, cv_context, embeddings)
        overall = self.scorer.overall(dims)

        # 4 — Persist
        job = JobApplication(
            id=uuid.uuid4(),
            company_name=company,
            job_title=title,
            job_description=description,
            match_score=overall,
            dimension_scores=dims.to_dict(),
            extracted_requirements=checklist.to_dict(),
            workflow_status="pending",
            processing=True,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        logger.info(
            "JobApplication %s created: overall_score=%.1f%%",
            job.id,
            overall,
        )

        return JobEvaluationOut(
            job_id=job.id,
            overall_score=overall,
            dimension_scores=DimensionScoresSchema(**dims.to_dict()),
            workflow_status=job.workflow_status,
            processing=True,
            cv_pdf_url=None,
            cover_letter_pdf_url=None,
        )

    async def generate_documents(self, job_id: str) -> None:
        """Background task: generate LaTeX then compile PDFs.

        Sets ``processing=False`` when done (or on failure, logs the error
        and still clears the flag so the frontend stops polling).
        """
        job = await self._get_job(job_id)
        if job is None:
            logger.error("generate_documents: job %s not found", job_id)
            return

        try:
            # Build prompts
            cv_prompt = build_prompt("cv", job.job_description)
            cl_prompt = build_prompt("cover_letter", job.job_description)

            # Generate LaTeX via the fine-tuned Qwen model
            cv_latex = self.llm.generate(cv_prompt)
            cl_latex = self.llm.generate(cl_prompt)

            # Compile to PDF
            cv_pdf: Path = self.renderer.render(cv_latex, str(job.id), "cv")
            cl_pdf: Path = self.renderer.render(cl_latex, str(job.id), "cover")

            # Persist
            job.cv_latex = cv_latex
            job.cover_letter_latex = cl_latex
            job.cv_pdf_path = str(cv_pdf)
            job.cover_letter_pdf_path = str(cl_pdf)

        except LatexRenderError as exc:
            logger.exception("PDF render failed for job %s: %s", job_id, exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error in generate_documents for job %s: %s", job_id, exc)
        finally:
            # Always clear the processing flag
            job.processing = False
            attributes.flag_modified(job, "dimension_scores")
            await self.db.commit()

    async def update_workflow_status(
        self, job_id: str, status: str, session_id: Optional[str] = None
    ) -> Optional[JobApplication]:
        """Update workflow status; clear session cache on rejection.

        Parameters
        ----------
        job_id:
            UUID string of the target :class:`JobApplication`.
        status:
            One of ``"pending"``, ``"accepted"``, ``"rejected"``.
        session_id:
            If *status* is ``"rejected"`` and this is provided, the
            corresponding RAG history cache is cleared.
        """
        job = await self._get_job(job_id)
        if job is None:
            return None

        job.workflow_status = status

        if status == "rejected" and session_id:
            self.cache.clear(session_id)
            logger.info("History cache cleared for session %s (job rejected)", session_id)

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update_latex(
        self, job_id: str, doc_type: str, latex_source: str
    ) -> Optional[JobApplication]:
        """Persist user-edited LaTeX source without re-rendering."""
        job = await self._get_job(job_id)
        if job is None:
            return None

        if doc_type == "cv":
            job.cv_latex = latex_source
        else:
            job.cover_letter_latex = latex_source

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def regenerate_pdf(self, job_id: str, doc_type: str) -> None:
        """Re-compile the stored LaTeX source to a fresh PDF.

        Intended to be called as a background task after a user edits the
        LaTeX source and clicks the "Re-generate" button.
        """
        job = await self._get_job(job_id)
        if job is None:
            return

        latex = job.cv_latex if doc_type == "cv" else job.cover_letter_latex
        if not latex:
            logger.warning("No LaTeX source found for job %s doc_type=%s", job_id, doc_type)
            return

        job.processing = True
        await self.db.commit()

        try:
            pdf_path = self.renderer.render(latex, str(job.id), doc_type)
            if doc_type == "cv":
                job.cv_pdf_path = str(pdf_path)
            else:
                job.cover_letter_pdf_path = str(pdf_path)
        except LatexRenderError as exc:
            logger.exception("Re-render failed for job %s doc_type=%s: %s", job_id, doc_type, exc)
        finally:
            job.processing = False
            await self.db.commit()

    # ── Internal helpers ──────────────────────────────────────

    async def _get_job(self, job_id: str) -> Optional[JobApplication]:
        from uuid import UUID as PyUUID  # noqa: PLC0415
        try:
            job_uuid = PyUUID(job_id)
        except (ValueError, AttributeError):
            return None
        result = await self.db.execute(
            select(JobApplication).where(JobApplication.id == job_uuid)
        )
        return result.scalar_one_or_none()

    def _build_cv_context(self, session_id: str) -> dict:
        """Build a simplified CV context dict from the history cache.

        In the current implementation the cache stores conversation messages.
        Future work can extend this to pull structured profile data from the DB.
        """
        messages = self.cache.get_messages(session_id)
        full_text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        )
        return {
            "skills": [],           # Extended in future via UserProfile model
            "education_level": "",  # Extended in future via UserProfile model
            "experience_years": 0,  # Extended in future via UserProfile model
            "career_objective": "",
            "summary": full_text[:2000],  # Truncate to avoid embedding dim explosion
        }

    def _compute_embeddings(self, job_description: str, cv_context: dict) -> dict:
        """Embed job description and CV summary for cosine scoring."""
        texts = [job_description, cv_context.get("summary", "")]
        objective = cv_context.get("career_objective", "")
        if objective:
            texts.append(objective)

        vectors = self.embedding.embed([t for t in texts if t])
        result: dict = {}
        if len(vectors) >= 1:
            result["job_vec"] = vectors[0]
        if len(vectors) >= 2:
            result["cv_vec"] = vectors[1]
        if len(vectors) >= 3:
            result["objective_vec"] = vectors[2]
        return result
