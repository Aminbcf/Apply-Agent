"""Checklist extractor for the Apply-Agent job-match scenario.

Parses a raw job description into a structured :class:`JobChecklist` using a
combination of regex patterns and curated keyword lists.  An optional LLM
fallback path is provided for ambiguous items but is disabled by default so
unit tests remain fast and deterministic.

Usage::

    from AI.llm.checklist_extractor import ChecklistExtractor

    extractor = ChecklistExtractor()
    checklist = extractor.extract(job_description)
    print(checklist.required_skills)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Keyword / pattern libraries ───────────────────────────────

# Common degree-level keywords mapped to a numeric tier (higher = more senior)
_DEGREE_LEVELS: dict[str, int] = {
    "phd": 5,
    "doctorate": 5,
    "doctor": 5,
    "master": 4,
    "msc": 4,
    "mba": 4,
    "bachelor": 3,
    "bsc": 3,
    "b.sc": 3,
    "b.s.": 3,
    "associate": 2,
    "diploma": 1,
    "certificate": 1,
    "high school": 0,
}

# Common technical and soft-skill terms to look for in job descriptions
_SKILL_PATTERNS: list[str] = [
    # Programming languages
    r"\bpython\b", r"\bjava(?:script)?\b", r"\btypescript\b", r"\bc\+\+\b",
    r"\bc#\b", r"\brust\b", r"\bgo(?:lang)?\b", r"\bkotlin\b", r"\bswift\b",
    r"\bscala\b", r"\br\b", r"\bmatlab\b", r"\bsql\b", r"\bbash\b",
    # Frameworks & tools
    r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bdjango\b", r"\bfastapi\b",
    r"\bflask\b", r"\bspring\b", r"\bdocker\b", r"\bkubernetes\b", r"\bterraform\b",
    r"\bansible\b", r"\bgit\b", r"\bjenkins\b", r"\bgithub actions\b",
    # Data / ML
    r"\bpandas\b", r"\bnumpy\b", r"\bpytorch\b", r"\btensorflow\b",
    r"\bscikit[\-\s]learn\b", r"\bhugging\s?face\b", r"\bllm\b",
    r"\bmachine learning\b", r"\bdeep learning\b", r"\bdata science\b",
    r"\bmlops\b", r"\brag\b",
    # Cloud & infra
    r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bci/?cd\b", r"\bmicroservices\b",
    r"\brest(?:ful)?\s?api\b", r"\bgraphql\b",
    # Soft skills
    r"\bcommunication\b", r"\bteamwork\b", r"\bproblem[\s\-]solv\w+\b",
    r"\bleadership\b", r"\bcollaboration\b", r"\bagile\b", r"\bscrum\b",
]

# Patterns to extract years-of-experience requirements
_EXPERIENCE_PATTERNS: list[str] = [
    r"(\d+)\+?\s*years?\s+of\s+experience",
    r"(\d+)\+?\s*years?\s+experience",
    r"minimum\s+(?:of\s+)?(\d+)\s+years?",
    r"at\s+least\s+(\d+)\s+years?",
    r"(\d+)[\-–](\d+)\s+years?",
]

# Career objective / goal signals
_OBJECTIVE_PATTERNS: list[str] = [
    r"passionate\s+about\s+(.{10,60}?)(?:\.|,|\n)",
    r"looking\s+for\s+(?:a\s+)?(?:candidate|professional)\s+who\s+(.{10,80}?)(?:\.|,|\n)",
    r"driven\s+by\s+(.{10,60}?)(?:\.|,|\n)",
    r"mission[\s\-]+(?:is|:)\s+(.{10,80}?)(?:\.|,|\n)",
    r"join\s+(?:our|the)\s+(?:team|mission)\s+(?:to|and)\s+(.{10,80}?)(?:\.|,|\n)",
]


@dataclass
class JobChecklist:
    """Structured representation of a job description's requirements."""

    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    education_level: int = 0          # numeric tier (see _DEGREE_LEVELS)
    education_level_label: str = ""   # human-readable label
    education_field: str = ""         # e.g. "computer science"
    min_experience_years: int = 0
    max_experience_years: Optional[int] = None
    objectives: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise for storage in the DB dimension_scores JSON column."""
        return {
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "education_level": self.education_level,
            "education_level_label": self.education_level_label,
            "education_field": self.education_field,
            "min_experience_years": self.min_experience_years,
            "max_experience_years": self.max_experience_years,
            "objectives": self.objectives,
        }


class ChecklistExtractor:
    """Extract a :class:`JobChecklist` from a raw job-description string.

    The extraction is intentionally deterministic (regex + keyword matching)
    so it can be unit-tested without any model calls.
    """

    def extract(self, job_description: str) -> JobChecklist:
        """Parse *job_description* and return a populated :class:`JobChecklist`.

        Parameters
        ----------
        job_description:
            Raw text of the job posting.  May be empty – the method degrades
            gracefully and returns an empty checklist in that case.
        """
        if not job_description or not job_description.strip():
            logger.debug("ChecklistExtractor received empty description; returning empty checklist.")
            return JobChecklist()

        text = job_description.lower()

        return JobChecklist(
            required_skills=self._extract_skills(text, job_description),
            preferred_skills=self._extract_preferred_skills(text, job_description),
            **self._extract_education(text),
            **self._extract_experience(text),
            objectives=self._extract_objectives(text),
        )

    # ── Private extraction helpers ────────────────────────────

    def _extract_skills(self, text: str, original: str) -> list[str]:
        """Return skills found in the 'required' section (or anywhere if no section split)."""
        required_block = self._get_section(text, ["required", "must have", "qualifications"])
        search_text = required_block if required_block else text
        return self._match_skills(search_text, original)

    def _extract_preferred_skills(self, text: str, original: str) -> list[str]:
        """Return skills found in the 'preferred / nice-to-have' section."""
        preferred_block = self._get_section(
            text, ["preferred", "nice to have", "nice-to-have", "bonus", "plus"]
        )
        if not preferred_block:
            return []
        all_skills = self._match_skills(preferred_block, original)
        required = set(self._extract_skills(text, original))
        # Avoid duplicating skills already listed as required
        return [s for s in all_skills if s not in required]

    def _match_skills(self, text: str, original: str) -> list[str]:
        """Run all skill patterns against *text*, return deduplicated matches."""
        found: list[str] = []
        for pattern in _SKILL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Use the canonical lowercase form from the pattern
                skill = re.sub(r"[\\b^]", "", pattern).strip(r"\b").replace(r"\b", "")
                # Recover the actual matched substring from original for display
                original_match = re.search(pattern, original, re.IGNORECASE)
                if original_match:
                    skill = original_match.group(0).strip()
                if skill and skill not in found:
                    found.append(skill)
        return found

    def _extract_education(self, text: str) -> dict:
        """Return ``education_level``, ``education_level_label``, and ``education_field``."""
        level = 0
        label = ""
        field_name = ""

        for keyword, tier in sorted(_DEGREE_LEVELS.items(), key=lambda x: -x[1]):
            if keyword in text:
                level = tier
                label = keyword.title()
                break

        # Try to extract field of study (e.g. "computer science", "engineering")
        field_match = re.search(
            r"(?:degree|bachelor|master|phd|doctor)\s+in\s+([\w\s]{3,40}?)(?:\s+or|\s+and|\s*[,.\n])",
            text,
            re.IGNORECASE,
        )
        if field_match:
            field_name = field_match.group(1).strip().lower()

        return {
            "education_level": level,
            "education_level_label": label,
            "education_field": field_name,
        }

    def _extract_experience(self, text: str) -> dict:
        """Return ``min_experience_years`` and ``max_experience_years``."""
        min_years = 0
        max_years: Optional[int] = None

        for pattern in _EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    # Range pattern: e.g. "3-5 years"
                    min_years = int(groups[0])
                    max_years = int(groups[1])
                else:
                    min_years = int(groups[0])
                break

        return {"min_experience_years": min_years, "max_experience_years": max_years}

    def _extract_objectives(self, text: str) -> list[str]:
        """Return mission / objective phrases from the description."""
        objectives: list[str] = []
        for pattern in _OBJECTIVE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = match.group(1).strip().rstrip(".,;")
                if phrase and phrase not in objectives:
                    objectives.append(phrase)
        return objectives

    @staticmethod
    def _get_section(text: str, headings: list[str]) -> str:
        """Extract a sub-block of text that falls under one of *headings*."""
        # Build a pattern that matches a heading followed by content up to the next heading.
        # NOTE: plain string concat is used here to avoid brace-escaping conflicts between
        # f-string interpolation and regex quantifiers like {0,1500}.
        heading_re = "|".join(re.escape(h) for h in headings)
        section_pattern = (
            r"(?:" + heading_re + r")[:\s]*\n"
            r"([\s\S]{0,1500}?)"
            r"(?:\n[A-Z][^\n]{0,60}:\n|\Z)"
        )
        match = re.search(section_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

