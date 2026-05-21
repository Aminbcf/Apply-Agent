"""Pure deterministic scorer for the Apply-Agent job-match scenario.

:class:`MatchScorer` receives pre-computed embedding vectors and a parsed
:class:`~AI.llm.checklist_extractor.JobChecklist`, then returns a
:class:`DimensionScores` instance plus an overall weighted score.

No LLM calls are made here – all computation is numerical, making the
module fully unit-testable without mocks.

Usage::

    from AI.llm.match_scorer import MatchScorer
    from AI.llm.checklist_extractor import JobChecklist

    scorer = MatchScorer()
    dims = scorer.score(job_checklist, cv_context, embeddings)
    overall = scorer.overall(dims)     # 0.0 – 100.0
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DimensionScores:
    """Per-dimension scores in the range 0–100."""

    job_match: float = 0.0
    skill_match: float = 0.0
    education_match: float = 0.0
    experience_match: float = 0.0
    objective_match: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "job_match": round(self.job_match, 2),
            "skill_match": round(self.skill_match, 2),
            "education_match": round(self.education_match, 2),
            "experience_match": round(self.experience_match, 2),
            "objective_match": round(self.objective_match, 2),
        }


# ── Education level mapping ────────────────────────────────────
# Mirror the tiers from ChecklistExtractor so we can compare apples-to-apples.
_EDU_LEVEL: Dict[str, int] = {
    "high school": 0,
    "certificate": 1,
    "diploma": 1,
    "associate": 2,
    "bachelor": 3,
    "bsc": 3,
    "b.sc": 3,
    "b.s.": 3,
    "master": 4,
    "msc": 4,
    "mba": 4,
    "phd": 5,
    "doctorate": 5,
    "doctor": 5,
}


class MatchScorer:
    """Compute multi-dimensional job-match scores.

    Weights must sum to 1.0.  They can be overridden at construction time.
    """

    #: Default dimension weights
    WEIGHTS: Dict[str, float] = {
        "job_match": 0.20,
        "skill_match": 0.30,
        "education_match": 0.15,
        "experience_match": 0.20,
        "objective_match": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        w = weights or self.WEIGHTS
        total = sum(w.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"Dimension weights must sum to 1.0, got {total:.4f}")
        self._weights = w

    # ── Public interface ──────────────────────────────────────

    def score(
        self,
        job_checklist,           # JobChecklist
        cv_context: dict,        # parsed CV fields from DB / user profile
        embeddings: dict,        # pre-computed embedding vectors
    ) -> DimensionScores:
        """Compute all five dimension scores and return them.

        Parameters
        ----------
        job_checklist:
            A :class:`~AI.llm.checklist_extractor.JobChecklist` extracted from
            the job description.
        cv_context:
            Dictionary of CV fields, expected keys:
            ``skills``, ``education_level``, ``experience_years``,
            ``career_objective`` (string), ``summary`` (string).
        embeddings:
            Dictionary with pre-computed vectors:
            ``job_vec``, ``cv_vec``, ``objective_vec``.
        """
        job_vec: List[float] = embeddings.get("job_vec", [])
        cv_vec: List[float] = embeddings.get("cv_vec", [])
        objective_vec: List[float] = embeddings.get("objective_vec", [])

        # 1. Overall semantic similarity
        jm = self._cosine(job_vec, cv_vec) * 100.0 if job_vec and cv_vec else 0.0

        # 2. Skill checklist overlap
        sm = self._skill_overlap(
            required=job_checklist.required_skills,
            preferred=job_checklist.preferred_skills,
            candidate=cv_context.get("skills", []),
        )

        # 3. Education level match
        em = self._education_score(
            required_level=job_checklist.education_level,
            candidate_level=self._parse_education_level(cv_context.get("education_level", "")),
        )

        # 4. Experience years match
        xm = self._experience_score(
            required_min=job_checklist.min_experience_years,
            required_max=job_checklist.max_experience_years,
            candidate_years=cv_context.get("experience_years", 0),
        )

        # 5. Objective / career goal alignment
        om = 0.0
        if objective_vec and job_vec:
            om = self._cosine(job_vec, objective_vec) * 100.0

        dims = DimensionScores(
            job_match=round(min(jm, 100.0), 2),
            skill_match=round(min(sm, 100.0), 2),
            education_match=round(min(em, 100.0), 2),
            experience_match=round(min(xm, 100.0), 2),
            objective_match=round(min(om, 100.0), 2),
        )
        logger.debug("DimensionScores: %s", dims)
        return dims

    def overall(self, dims: DimensionScores) -> float:
        """Compute the weighted overall score (0–100).

        Parameters
        ----------
        dims:
            A :class:`DimensionScores` instance returned by :meth:`score`.
        """
        total = (
            dims.job_match * self._weights["job_match"]
            + dims.skill_match * self._weights["skill_match"]
            + dims.education_match * self._weights["education_match"]
            + dims.experience_match * self._weights["experience_match"]
            + dims.objective_match * self._weights["objective_match"]
        )
        return round(min(max(total, 0.0), 100.0), 2)

    # ── Private helpers ───────────────────────────────────────

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors, returned in [0, 1]."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        raw = dot / (norm_a * norm_b)
        # Clamp to [0, 1] – negative cosine means opposite direction, treat as 0
        return max(0.0, min(raw, 1.0))

    @staticmethod
    def _skill_overlap(
        required: List[str],
        preferred: List[str],
        candidate: List[str],
    ) -> float:
        """Score based on how many required/preferred skills the candidate has.

        Required skills contribute 70 % of the score; preferred contribute 30 %.
        Each sub-score is the fraction of matched items × 100.
        """
        candidate_lower = {s.lower().strip() for s in candidate}

        def _fraction(target: List[str]) -> float:
            if not target:
                return 1.0  # vacuously satisfied
            matched = sum(1 for s in target if s.lower().strip() in candidate_lower)
            return matched / len(target)

        req_score = _fraction(required) * 70.0
        pref_score = _fraction(preferred) * 30.0
        return req_score + pref_score

    @staticmethod
    def _education_score(required_level: int, candidate_level: int) -> float:
        """Compare education tier levels.

        Candidate meets or exceeds requirement → 100.
        Each tier below knocks off 25 points (floor at 0).
        """
        if required_level == 0:
            return 100.0
        delta = candidate_level - required_level
        if delta >= 0:
            return 100.0
        return max(0.0, 100.0 + delta * 25.0)

    @staticmethod
    def _experience_score(
        required_min: int,
        required_max: Optional[int],
        candidate_years: int,
    ) -> float:
        """Score experience years against the job requirement.

        - At or above the minimum (or within range) → 100.
        - Each year below minimum subtracts 15 points (floor 0).
        - Being far above the max loses up to 20 points (over-qualified penalty).
        """
        if required_min == 0 and required_max is None:
            return 100.0

        # Below minimum
        if candidate_years < required_min:
            shortfall = required_min - candidate_years
            return max(0.0, 100.0 - shortfall * 15.0)

        # Within or above range
        if required_max is not None and candidate_years > required_max:
            excess = candidate_years - required_max
            return max(80.0, 100.0 - excess * 5.0)  # soft over-qualification penalty

        return 100.0

    @staticmethod
    def _parse_education_level(level_str: str) -> int:
        """Map a human-readable education label to a numeric tier."""
        if not level_str:
            return 0
        level_lower = level_str.lower().strip()
        for keyword, tier in sorted(_EDU_LEVEL.items(), key=lambda x: -x[1]):
            if keyword in level_lower:
                return tier
        return 0
