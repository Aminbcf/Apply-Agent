"""Unit tests for MatchScorer (Phase 7).

All tests use hand-crafted embedding vectors so no model is loaded.
"""

from __future__ import annotations

import math
import pytest

from AI.llm.checklist_extractor import JobChecklist
from AI.llm.match_scorer import DimensionScores, MatchScorer


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture()
def scorer() -> MatchScorer:
    return MatchScorer()


def _unit_vec(dim: int, index: int = 0) -> list[float]:
    """Return a unit vector of *dim* dimensions with a 1.0 at *index*."""
    v = [0.0] * dim
    v[index] = 1.0
    return v


def _perfect_embeddings() -> dict:
    """Job and CV vectors are identical → cosine = 1.0."""
    v = _unit_vec(4, 0)
    return {"job_vec": v, "cv_vec": v, "objective_vec": v}


def _zero_overlap_embeddings() -> dict:
    """Job and CV vectors are orthogonal → cosine = 0.0."""
    return {
        "job_vec": _unit_vec(4, 0),
        "cv_vec": _unit_vec(4, 1),
        "objective_vec": _unit_vec(4, 2),
    }


def _empty_checklist() -> JobChecklist:
    return JobChecklist()


def _full_checklist() -> JobChecklist:
    return JobChecklist(
        required_skills=["Python", "Docker"],
        preferred_skills=["Kubernetes"],
        education_level=3,      # bachelor
        education_level_label="Bachelor",
        education_field="computer science",
        min_experience_years=3,
        max_experience_years=None,
        objectives=["build scalable systems"],
    )


def _cv_context_perfect() -> dict:
    """CV that perfectly satisfies the full checklist."""
    return {
        "skills": ["Python", "Docker", "Kubernetes"],
        "education_level": "Bachelor in Computer Science",
        "experience_years": 5,
        "career_objective": "build scalable systems",
        "summary": "Senior Python engineer with Docker and Kubernetes expertise.",
    }


def _cv_context_empty() -> dict:
    return {
        "skills": [],
        "education_level": "",
        "experience_years": 0,
        "career_objective": "",
        "summary": "",
    }


# ── Weight validation ─────────────────────────────────────────

class TestWeightValidation:
    def test_default_weights_sum_to_one(self) -> None:
        assert math.isclose(sum(MatchScorer.WEIGHTS.values()), 1.0, abs_tol=1e-9)

    def test_custom_weights_valid(self) -> None:
        scorer = MatchScorer({"job_match": 0.5, "skill_match": 0.5,
                              "education_match": 0.0, "experience_match": 0.0,
                              "objective_match": 0.0})
        assert scorer is not None

    def test_invalid_weights_raise(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            MatchScorer({"job_match": 0.9, "skill_match": 0.5,
                         "education_match": 0.0, "experience_match": 0.0,
                         "objective_match": 0.0})


# ── Perfect match ─────────────────────────────────────────────

class TestPerfectMatch:
    def test_overall_near_100(self, scorer: MatchScorer) -> None:
        dims = scorer.score(_full_checklist(), _cv_context_perfect(), _perfect_embeddings())
        overall = scorer.overall(dims)
        assert overall >= 90.0, f"Expected ≥90 for perfect match, got {overall}"

    def test_all_dimensions_high(self, scorer: MatchScorer) -> None:
        dims = scorer.score(_full_checklist(), _cv_context_perfect(), _perfect_embeddings())
        assert dims.skill_match >= 90.0
        assert dims.education_match == 100.0
        assert dims.experience_match == 100.0


# ── Zero overlap ──────────────────────────────────────────────

class TestZeroOverlap:
    def test_overall_near_zero(self, scorer: MatchScorer) -> None:
        dims = scorer.score(_full_checklist(), _cv_context_empty(), _zero_overlap_embeddings())
        overall = scorer.overall(dims)
        assert overall <= 30.0, f"Expected ≤30 for zero overlap, got {overall}"

    def test_skill_match_low(self, scorer: MatchScorer) -> None:
        dims = scorer.score(_full_checklist(), _cv_context_empty(), _zero_overlap_embeddings())
        assert dims.skill_match < 10.0

    def test_experience_low(self, scorer: MatchScorer) -> None:
        dims = scorer.score(_full_checklist(), _cv_context_empty(), _zero_overlap_embeddings())
        assert dims.experience_match < 60.0  # 3 years required, 0 provided


# ── Per-dimension isolation ───────────────────────────────────

class TestDimensionIsolation:
    def test_cosine_helper_identical_vectors(self, scorer: MatchScorer) -> None:
        v = [1.0, 0.0, 0.0]
        assert scorer._cosine(v, v) == pytest.approx(1.0)

    def test_cosine_helper_orthogonal_vectors(self, scorer: MatchScorer) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert scorer._cosine(a, b) == pytest.approx(0.0)

    def test_cosine_empty_vector(self, scorer: MatchScorer) -> None:
        assert scorer._cosine([], []) == 0.0

    def test_skill_overlap_full(self, scorer: MatchScorer) -> None:
        # All required + preferred matched
        s = scorer._skill_overlap(["Python", "Docker"], ["K8s"], ["Python", "Docker", "K8s"])
        assert s == pytest.approx(100.0)

    def test_skill_overlap_none(self, scorer: MatchScorer) -> None:
        s = scorer._skill_overlap(["Rust", "Go"], ["WASM"], ["Python"])
        assert s < 10.0

    def test_skill_overlap_empty_requirements(self, scorer: MatchScorer) -> None:
        # Vacuously satisfied → both fractions = 1.0
        s = scorer._skill_overlap([], [], ["Python"])
        assert s == pytest.approx(100.0)

    def test_education_meets_requirement(self, scorer: MatchScorer) -> None:
        assert scorer._education_score(3, 3) == pytest.approx(100.0)

    def test_education_exceeds_requirement(self, scorer: MatchScorer) -> None:
        assert scorer._education_score(3, 5) == pytest.approx(100.0)

    def test_education_below_requirement(self, scorer: MatchScorer) -> None:
        score = scorer._education_score(4, 3)  # has bachelor, needs master
        assert 0.0 < score < 100.0

    def test_education_no_requirement(self, scorer: MatchScorer) -> None:
        assert scorer._education_score(0, 0) == pytest.approx(100.0)

    def test_experience_meets(self, scorer: MatchScorer) -> None:
        assert scorer._experience_score(3, None, 5) == pytest.approx(100.0)

    def test_experience_below(self, scorer: MatchScorer) -> None:
        score = scorer._experience_score(5, None, 2)
        assert score < 60.0

    def test_experience_no_requirement(self, scorer: MatchScorer) -> None:
        assert scorer._experience_score(0, None, 0) == pytest.approx(100.0)

    def test_experience_over_qualified_soft_penalty(self, scorer: MatchScorer) -> None:
        score = scorer._experience_score(2, 4, 10)  # cap is 4, has 10
        assert score >= 80.0  # soft penalty – still employable

    def test_parse_education_level_bachelor(self, scorer: MatchScorer) -> None:
        assert scorer._parse_education_level("Bachelor of Science") == 3

    def test_parse_education_level_phd(self, scorer: MatchScorer) -> None:
        assert scorer._parse_education_level("PhD in Engineering") == 5

    def test_parse_education_level_empty(self, scorer: MatchScorer) -> None:
        assert scorer._parse_education_level("") == 0


# ── Overall score range guard ─────────────────────────────────

class TestOverallBounds:
    def test_overall_never_exceeds_100(self, scorer: MatchScorer) -> None:
        dims = DimensionScores(
            job_match=100, skill_match=100,
            education_match=100, experience_match=100, objective_match=100,
        )
        assert scorer.overall(dims) <= 100.0

    def test_overall_never_below_0(self, scorer: MatchScorer) -> None:
        dims = DimensionScores()  # all zeros
        assert scorer.overall(dims) >= 0.0

    def test_to_dict_contains_all_keys(self) -> None:
        dims = DimensionScores(job_match=10, skill_match=20, education_match=30,
                               experience_match=40, objective_match=50)
        d = dims.to_dict()
        for key in ("job_match", "skill_match", "education_match",
                    "experience_match", "objective_match"):
            assert key in d
