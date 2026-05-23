"""Tests for the RAG retrieval helpers in rag_service.py.

All tests use in-memory SQLite and mocked filesystem — no real network or GPU.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# ── retrieve_example_files ────────────────────────────────────────────────────

class TestRetrieveExampleFiles:
    def test_returns_dict_with_expected_keys(self, tmp_path, monkeypatch):
        """Function returns a dict with cv_examples, cover_letter_instructions."""
        from AI.llm.rag_service import retrieve_example_files

        # Patch the directory paths
        fake_cv_dir = tmp_path / "CV-Examples"
        fake_cv_dir.mkdir()
        fake_cl_dir = tmp_path / "Cover-letter-Examples"
        fake_cl_dir.mkdir()

        sample_cv = {"cv_examples": [{"domain": "IT", "summary": "Test CV"}]}
        (fake_cv_dir / "cv_examples.json").write_text(json.dumps(sample_cv))
        (fake_cl_dir / "Instructions.md").write_text("# Instructions\nDo this.")

        import AI.llm.rag_service as rag_mod
        monkeypatch.setattr(rag_mod, "_CV_EXAMPLES_DIR", fake_cv_dir)
        monkeypatch.setattr(rag_mod, "_CL_EXAMPLES_DIR", fake_cl_dir)

        result = retrieve_example_files()
        assert "cv_examples" in result
        assert "cover_letter_instructions" in result
        assert "IT" in result["cv_examples"]
        assert "Instructions" in result["cover_letter_instructions"]

    def test_handles_missing_files_gracefully(self, tmp_path, monkeypatch):
        """No exception raised when example files are absent."""
        from AI.llm.rag_service import retrieve_example_files

        import AI.llm.rag_service as rag_mod
        monkeypatch.setattr(rag_mod, "_CV_EXAMPLES_DIR", tmp_path / "nonexistent")
        monkeypatch.setattr(rag_mod, "_CL_EXAMPLES_DIR", tmp_path / "nonexistent2")

        result = retrieve_example_files()
        assert result["cv_examples"] == ""
        assert result["cover_letter_instructions"] == ""


# ── retrieve_cv_context ───────────────────────────────────────────────────────

class TestRetrieveCvContext:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_profile(self):
        """Returns empty dict when no UserProfile exists in the DB."""
        from AI.llm.rag_service import retrieve_cv_context

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_cv_context(mock_db)
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_profile_fields(self):
        """Returns a dict with all profile fields when profile exists."""
        from AI.llm.rag_service import retrieve_cv_context

        mock_profile = MagicMock()
        mock_profile.full_name = "Alice"
        mock_profile.email = "alice@example.com"
        mock_profile.phone = "+1234"
        mock_profile.location = "Paris"
        mock_profile.career_goals = "ML Engineer"
        mock_profile.skills = {"technical": ["Python", "PyTorch"]}
        mock_profile.education = [{"degree": "MSc", "institution": "Sorbonne"}]
        mock_profile.experience = [{"role": "Data Scientist"}, {"role": "ML Intern"}]
        mock_profile.projects = []
        mock_profile.certifications = []
        mock_profile.languages = []
        mock_profile.achievements = []
        mock_profile.raw_cv_text = "Raw CV text"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_profile
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_cv_context(mock_db)
        assert result["name"] == "Alice"
        assert "Python" in result["skills"]
        assert "PyTorch" in result["skills"]
        assert result["experience_years"] == 4  # 2 entries × 2 heuristic
        assert "MSc" in result["education_level"]


# ── retrieve_job_context ──────────────────────────────────────────────────────

class TestRetrieveJobContext:
    @pytest.mark.asyncio
    async def test_returns_empty_for_invalid_uuid(self):
        from AI.llm.rag_service import retrieve_job_context

        mock_db = AsyncMock()
        result = await retrieve_job_context(mock_db, "not-a-uuid")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_when_job_not_found(self):
        from AI.llm.rag_service import retrieve_job_context

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        import uuid
        job_id = str(uuid.uuid4())
        result = await retrieve_job_context(mock_db, job_id)
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_job_fields(self):
        from AI.llm.rag_service import retrieve_job_context
        import uuid

        mock_job = MagicMock()
        mock_job.id = uuid.uuid4()
        mock_job.job_title = "AI Engineer"
        mock_job.company_name = "Acme Corp"
        mock_job.job_description = "Build AI systems"
        mock_job.extracted_requirements = {"required_skills": ["Python"]}
        mock_job.dimension_scores = {"job_match": 85.0}
        mock_job.match_score = 78.5

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_job_context(mock_db, str(mock_job.id))
        assert result["title"] == "AI Engineer"
        assert result["company"] == "Acme Corp"
        import math
        assert math.isclose(result["match_score"], 78.5)


# ── retrieve_few_shot_examples ────────────────────────────────────────────────

class TestRetrieveFewShotExamples:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_accepted_jobs(self):
        from AI.llm.rag_service import retrieve_few_shot_examples

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_few_shot_examples(mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_snippets_for_accepted_jobs(self):
        from AI.llm.rag_service import retrieve_few_shot_examples
        import uuid

        mock_job = MagicMock()
        mock_job.id = uuid.uuid4()
        mock_job.job_title = "Backend Developer"
        mock_job.company_name = "TechCo"
        mock_job.cv_text = "A" * 1000  # long text
        mock_job.cover_letter_text = "B" * 1000

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_few_shot_examples(mock_db, max_chars=100)
        assert len(result) == 1
        assert result[0]["title"] == "Backend Developer"
        assert len(result[0]["cv_text_snippet"]) <= 100

    @pytest.mark.asyncio
    async def test_skips_jobs_with_no_text(self):
        from AI.llm.rag_service import retrieve_few_shot_examples
        import uuid

        mock_job = MagicMock()
        mock_job.id = uuid.uuid4()
        mock_job.job_title = "No text job"
        mock_job.company_name = "Corp"
        mock_job.cv_text = ""
        mock_job.cover_letter_text = None

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await retrieve_few_shot_examples(mock_db)
        # Job with no text should be excluded
        assert result == []
