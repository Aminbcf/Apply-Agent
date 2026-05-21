"""Unit tests for ChecklistExtractor (Phase 7)."""

from __future__ import annotations

import pytest

from AI.llm.checklist_extractor import ChecklistExtractor, JobChecklist


@pytest.fixture()
def extractor() -> ChecklistExtractor:
    return ChecklistExtractor()


# ── Happy path ────────────────────────────────────────────────

class TestExtractSkills:
    def test_required_skills_detected(self, extractor: ChecklistExtractor) -> None:
        jd = (
            "Required:\n"
            "  - Python\n"
            "  - Docker\n"
            "  - REST API\n"
            "Preferred:\n"
            "  - Kubernetes\n"
        )
        checklist = extractor.extract(jd)
        skills_lower = [s.lower() for s in checklist.required_skills]
        assert any("python" in s for s in skills_lower)
        assert any("docker" in s for s in skills_lower)

    def test_preferred_skills_not_in_required(self, extractor: ChecklistExtractor) -> None:
        jd = (
            "Required:\n  - Python\n"
            "Nice to have:\n  - Kubernetes\n"
        )
        checklist = extractor.extract(jd)
        preferred_lower = [s.lower() for s in checklist.preferred_skills]
        required_lower = [s.lower() for s in checklist.required_skills]
        # No skill should appear in both lists
        overlap = set(preferred_lower) & set(required_lower)
        assert overlap == set()

    def test_to_dict_serialisation(self, extractor: ChecklistExtractor) -> None:
        jd = "We need Python and machine learning experience."
        checklist = extractor.extract(jd)
        d = checklist.to_dict()
        assert isinstance(d, dict)
        assert "required_skills" in d
        assert "education_level" in d
        assert "min_experience_years" in d


# ── Education extraction ──────────────────────────────────────

class TestExtractEducation:
    def test_bachelor_detected(self, extractor: ChecklistExtractor) -> None:
        jd = "Candidates must hold a bachelor degree in computer science."
        checklist = extractor.extract(jd)
        assert checklist.education_level >= 3  # bachelor tier
        assert "computer science" in checklist.education_field.lower()

    def test_master_outranks_bachelor(self, extractor: ChecklistExtractor) -> None:
        jd = "A Master's or PhD in engineering is required."
        checklist = extractor.extract(jd)
        assert checklist.education_level >= 4

    def test_no_degree_mentioned(self, extractor: ChecklistExtractor) -> None:
        jd = "Strong communication and team spirit required."
        checklist = extractor.extract(jd)
        assert checklist.education_level == 0
        assert checklist.education_field == ""


# ── Experience extraction ─────────────────────────────────────

class TestExtractExperience:
    def test_exact_years(self, extractor: ChecklistExtractor) -> None:
        jd = "We require 5 years of experience in backend development."
        checklist = extractor.extract(jd)
        assert checklist.min_experience_years == 5

    def test_range_years(self, extractor: ChecklistExtractor) -> None:
        jd = "3-7 years of relevant experience preferred."
        checklist = extractor.extract(jd)
        assert checklist.min_experience_years == 3
        assert checklist.max_experience_years == 7

    def test_minimum_keyword(self, extractor: ChecklistExtractor) -> None:
        jd = "Minimum of 2 years in data engineering."
        checklist = extractor.extract(jd)
        assert checklist.min_experience_years == 2

    def test_no_experience_mentioned(self, extractor: ChecklistExtractor) -> None:
        jd = "Looking for enthusiastic candidates."
        checklist = extractor.extract(jd)
        assert checklist.min_experience_years == 0
        assert checklist.max_experience_years is None


# ── Edge cases ────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_string_returns_empty_checklist(self, extractor: ChecklistExtractor) -> None:
        checklist = extractor.extract("")
        assert isinstance(checklist, JobChecklist)
        assert checklist.required_skills == []
        assert checklist.min_experience_years == 0

    def test_whitespace_only_returns_empty_checklist(self, extractor: ChecklistExtractor) -> None:
        checklist = extractor.extract("   \n\t  ")
        assert checklist.required_skills == []

    def test_special_characters_do_not_raise(self, extractor: ChecklistExtractor) -> None:
        jd = "Req: C++, C#, .NET – 3+ years; salary: $120k–$150k @ HQ."
        checklist = extractor.extract(jd)
        # Just verifying no exception is raised and result is valid
        assert isinstance(checklist, JobChecklist)

    def test_very_long_description_handled(self, extractor: ChecklistExtractor) -> None:
        jd = ("Python developer needed. " * 500) + " 5 years experience required."
        checklist = extractor.extract(jd)
        assert checklist.min_experience_years == 5
