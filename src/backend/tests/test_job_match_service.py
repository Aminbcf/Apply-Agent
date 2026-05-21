"""Unit tests for JobMatchService (Phase 7).

All external dependencies (embedding adapter, LLM, DB, LatexRenderer) are
mocked so tests are fast, deterministic, and offline.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from AI.llm.checklist_extractor import JobChecklist
from AI.llm.match_scorer import DimensionScores
from schemas.job_schemas import JobEvaluationOut


# ── Helpers ───────────────────────────────────────────────────

def _make_dim_scores(**kwargs) -> DimensionScores:
    defaults = dict(
        job_match=80.0, skill_match=70.0,
        education_match=100.0, experience_match=90.0, objective_match=60.0,
    )
    defaults.update(kwargs)
    return DimensionScores(**defaults)


def _unit_vec(n: int = 4) -> list[float]:
    return [1.0] + [0.0] * (n - 1)


def _make_service(db=None):
    """Create a JobMatchService with all dependencies mocked."""
    from AI.llm.job_match_service import JobMatchService

    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [_unit_vec(), _unit_vec()]

    mock_llm = MagicMock()
    mock_llm.generate.return_value = r"\documentclass{article}\begin{document}Test\end{document}"

    mock_cache = MagicMock()
    mock_cache.get_messages.return_value = []
    mock_cache.clear = MagicMock()

    mock_renderer = MagicMock()
    fake_pdf = Path("/tmp/fake.pdf")
    mock_renderer.render.return_value = fake_pdf

    # SQLAlchemy AsyncSession: add() is sync, commit()/refresh() are async
    mock_db = db or AsyncMock()
    mock_db.add = MagicMock()   # sync method – must NOT be a coroutine

    service = JobMatchService(
        db=mock_db,
        embedding_adapter=mock_embedding,
        llm=mock_llm,
        cache=mock_cache,
        renderer=mock_renderer,
    )
    return service, mock_embedding, mock_llm, mock_cache, mock_renderer, mock_db



# ── evaluate_job ──────────────────────────────────────────────

class TestEvaluateJob:
    @pytest.mark.asyncio
    async def test_returns_evaluation_out(self) -> None:
        service, *_ = _make_service()

        with patch.object(service.scorer, "score", return_value=_make_dim_scores()):
            with patch.object(service.scorer, "overall", return_value=80.5):
                result = await service.evaluate_job(
                    title="Senior Python Dev",
                    company="Acme Corp",
                    description="5 years Python. Docker required.",
                    session_id="sess-1",
                )

        assert isinstance(result, JobEvaluationOut)
        assert result.overall_score == 80.5
        assert result.processing is True
        assert result.cv_pdf_url is None

    @pytest.mark.asyncio
    async def test_persists_to_db(self) -> None:
        service, _, _, _, _, mock_db = _make_service()

        with patch.object(service.scorer, "score", return_value=_make_dim_scores()):
            with patch.object(service.scorer, "overall", return_value=75.0):
                await service.evaluate_job(
                    title="ML Engineer",
                    company="DataCo",
                    description="PyTorch, 3 years experience.",
                    session_id="sess-2",
                )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_dimension_scores_stored(self) -> None:
        service, *_ = _make_service()
        dims = _make_dim_scores(skill_match=55.0)

        with patch.object(service.scorer, "score", return_value=dims):
            with patch.object(service.scorer, "overall", return_value=70.0):
                result = await service.evaluate_job(
                    title="Backend Dev",
                    company="Corp",
                    description="Java Spring Boot 2 years.",
                    session_id="sess-3",
                )

        assert result.dimension_scores.skill_match == pytest.approx(55.0)


# ── generate_documents ────────────────────────────────────────

class TestGenerateDocuments:
    @pytest.mark.asyncio
    async def test_llm_called_twice(self) -> None:
        """generate_documents must call llm.generate once for CV and once for cover letter."""
        service, _, mock_llm, _, _, _ = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.job_description = "Python, Docker, 3 years."
        fake_job.processing = True

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.generate_documents(fake_job.id)

        assert mock_llm.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_renderer_called_twice(self) -> None:
        service, _, _, _, mock_renderer, _ = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.job_description = "Python dev role."
        fake_job.processing = True

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.generate_documents(fake_job.id)

        assert mock_renderer.render.call_count == 2

    @pytest.mark.asyncio
    async def test_processing_cleared_on_success(self) -> None:
        service, *_ = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.job_description = "Python."
        fake_job.processing = True

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.generate_documents(fake_job.id)

        assert fake_job.processing is False

    @pytest.mark.asyncio
    async def test_processing_cleared_on_render_failure(self) -> None:
        """Even when rendering fails, processing must be set to False."""
        from utils.latex_renderer import LatexRenderError

        service, _, _, _, mock_renderer, _ = _make_service()
        mock_renderer.render.side_effect = LatexRenderError("pdflatex failed")

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.job_description = "Python."
        fake_job.processing = True

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.generate_documents(fake_job.id)  # must not raise

        assert fake_job.processing is False

    @pytest.mark.asyncio
    async def test_missing_job_is_handled_gracefully(self) -> None:
        service, *_ = _make_service()

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=None):
            # Should complete without raising
            await service.generate_documents("non-existent-id")


# ── update_workflow_status ────────────────────────────────────

class TestUpdateWorkflowStatus:
    @pytest.mark.asyncio
    async def test_status_updated_to_accepted(self) -> None:
        service, _, _, _, _, mock_db = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.workflow_status = "pending"

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            result = await service.update_workflow_status(fake_job.id, "accepted")

        assert result.workflow_status == "accepted"

    @pytest.mark.asyncio
    async def test_rejection_clears_cache(self) -> None:
        service, _, _, mock_cache, _, _ = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.workflow_status = "pending"

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.update_workflow_status(fake_job.id, "rejected", session_id="sess-x")

        mock_cache.clear.assert_called_once_with("sess-x")

    @pytest.mark.asyncio
    async def test_acceptance_does_not_clear_cache(self) -> None:
        service, _, _, mock_cache, _, _ = _make_service()

        fake_job = MagicMock()
        fake_job.id = str(uuid.uuid4())
        fake_job.workflow_status = "pending"

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=fake_job):
            await service.update_workflow_status(fake_job.id, "accepted", session_id="sess-y")

        mock_cache.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_job_returns_none(self) -> None:
        service, *_ = _make_service()

        with patch.object(service, "_get_job", new_callable=AsyncMock, return_value=None):
            result = await service.update_workflow_status("missing-id", "accepted")

        assert result is None
