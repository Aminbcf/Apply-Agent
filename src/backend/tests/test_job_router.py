"""Integration tests for the job router (Phase 7).

Uses the same in-memory SQLite + ASGI-transport pattern as the existing
test_database_and_routes.py.  All LLM / embedding / pdflatex calls are
mocked so tests run offline and fast.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_db
from main import app
from models.job_application import JobApplication

# ── Async mark ────────────────────────────────────────────────
pytestmark = pytest.mark.anyio

# ── In-memory DB setup ────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
test_session_factory = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    from models.user_profile import UserProfile  # Ensure UserProfile is registered
    from models.job_application import JobApplication # Ensure JobApplication is registered
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with test_session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        yield ac


# ── Shared mock patch helper ───────────────────────────────────

def _mock_job_match_service(overall_score: float = 78.5):
    """Patch JobMatchService so no model or subprocess is invoked."""
    mock_result = MagicMock()
    mock_result.job_id = uuid.uuid4()
    mock_result.overall_score = overall_score
    mock_result.dimension_scores = MagicMock(
        job_match=70.0, skill_match=80.0,
        education_match=90.0, experience_match=75.0, objective_match=60.0,
    )
    mock_result.workflow_status = "pending"
    mock_result.processing = True
    mock_result.cv_pdf_url = None
    mock_result.cover_letter_pdf_url = None
    mock_result.model_dump.return_value = {
        "job_id": str(mock_result.job_id),
        "overall_score": overall_score,
        "dimension_scores": {
            "job_match": 70.0, "skill_match": 80.0,
            "education_match": 90.0, "experience_match": 75.0, "objective_match": 60.0,
        },
        "workflow_status": "pending",
        "processing": True,
        "cv_pdf_url": None,
        "cover_letter_pdf_url": None,
    }
    return mock_result


# ── POST /jobs/evaluate ───────────────────────────────────────

class TestEvaluateEndpoint:
    # Removed test_returns_202_with_scores as requested

    async def test_missing_fields_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/jobs/evaluate",
            json={"title": "Dev"},   # missing company, description, session_id
        )
        assert resp.status_code == 422

    async def test_short_description_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/jobs/evaluate",
            json={
                "title": "Dev",
                "company": "Corp",
                "description": "Hi",
                "session_id": "s1",
            },
        )
        assert resp.status_code == 422


# ── GET /jobs ───────────────────────────────────────────────────

class TestListJobsEndpoint:
    async def _insert_jobs(self) -> list[uuid.UUID]:
        jids = [uuid.uuid4(), uuid.uuid4()]
        async with test_session_factory() as session:
            for jid in jids:
                job = JobApplication(
                    id=jid,
                    company_name=f"Company {jid}",
                    job_title="Dev",
                    job_description="Python.",
                    processing=False,
                    workflow_status="pending",
                )
                session.add(job)
            await session.commit()
        return jids

    async def test_list_jobs_returns_200(self, client: AsyncClient) -> None:
        await self._insert_jobs()
        resp = await client.get("/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert "job_id" in data[0]
        assert "company_name" in data[0]


# ── GET /jobs/{job_id}/status ─────────────────────────────────

class TestStatusEndpoint:
    async def _insert_job(self, job_id: uuid.UUID, processing: bool = False) -> None:
        async with test_session_factory() as session:
            job = JobApplication(
                id=job_id,
                company_name="Corp",
                job_title="Dev",
                job_description="Python.",
                processing=processing,
                workflow_status="pending",
            )
            session.add(job)
            await session.commit()

    async def test_returns_processing_flag(self, client: AsyncClient) -> None:
        jid = uuid.uuid4()
        await self._insert_job(jid, processing=True)

        resp = await client.get(f"/jobs/{jid}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["processing"] is True
        assert data["workflow_status"] == "pending"

    async def test_not_found_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get(f"/jobs/{uuid.uuid4()}/status")
        assert resp.status_code == 404


# ── GET /jobs/{job_id}/download ───────────────────────────────

class TestDownloadEndpoint:
    async def _insert_job_with_pdf(self, job_id: uuid.UUID, tmp_path: Path) -> Path:
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        async with test_session_factory() as session:
            job = JobApplication(
                id=job_id,
                company_name="Corp",
                job_title="Dev",
                job_description="Python.",
                cv_pdf_path=str(pdf),
                workflow_status="accepted",
            )
            session.add(job)
            await session.commit()
        return pdf

    async def test_cv_pdf_200(self, client: AsyncClient, tmp_path: Path) -> None:
        jid = uuid.uuid4()
        await self._insert_job_with_pdf(jid, tmp_path)
        resp = await client.get(f"/jobs/{jid}/download?file_type=cv")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    async def test_missing_pdf_returns_404(self, client: AsyncClient) -> None:
        jid = uuid.uuid4()
        async with test_session_factory() as session:
            job = JobApplication(
                id=jid,
                company_name="Corp",
                job_title="Dev",
                job_description="Python.",
                workflow_status="pending",
            )
            session.add(job)
            await session.commit()

        resp = await client.get(f"/jobs/{jid}/download?file_type=cv")
        assert resp.status_code == 404

    async def test_latex_source_returned(self, client: AsyncClient) -> None:
        jid = uuid.uuid4()
        async with test_session_factory() as session:
            job = JobApplication(
                id=jid,
                company_name="Corp",
                job_title="Dev",
                job_description="Python.",
                cv_latex=r"\documentclass{article}\begin{document}Test\end{document}",
                workflow_status="accepted",
            )
            session.add(job)
            await session.commit()

        resp = await client.get(f"/jobs/{jid}/download?file_type=cv_latex")
        assert resp.status_code == 200
        assert "latex" in resp.json()


# ── PATCH /jobs/{job_id}/status ───────────────────────────────

class TestWorkflowStatusEndpoint:
    async def _insert_job(self, job_id: uuid.UUID) -> None:
        async with test_session_factory() as session:
            job = JobApplication(
                id=job_id,
                company_name="Corp",
                job_title="Dev",
                job_description="Python.",
                workflow_status="pending",
            )
            session.add(job)
            await session.commit()

    # Removed test_accept_updates_status and test_reject_clears_cache as requested

    async def test_invalid_status_returns_422(self, client: AsyncClient) -> None:
        jid = uuid.uuid4()
        await self._insert_job(jid)
        resp = await client.patch(
            f"/jobs/{jid}/status",
            json={"status": "flying"},   # not a valid literal
        )
        assert resp.status_code == 422


# ── PATCH /jobs/{job_id}/latex ────────────────────────────────

class TestLatexUpdateEndpoint:
    pass
    # Removed test_saves_cv_latex as requested

# ── POST /jobs/{job_id}/regenerate ────────────────────────────

class TestRegenerateEndpoint:
    # Removed test_returns_202_and_queues_task as requested

    async def test_unknown_job_returns_404(self, client: AsyncClient) -> None:
        # Even for a missing job we still need a valid body
        resp = await client.post(
            f"/jobs/{uuid.uuid4()}/regenerate",
            json={"doc_type": "cv"},
        )
        assert resp.status_code == 404
