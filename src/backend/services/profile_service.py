from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from AI.raw_cv_parser import parse_raw_cv
from config import settings
from models.user_profile import UserProfile
from models.user_profile_version import UserProfileVersion
from schemas.profile import ProfileSchema


@dataclass(frozen=True)
class ParsedCvProfilePatch:
    experience: list[Any]
    education: list[Any]
    skills: dict[str, Any]


class ProfileService:
    """Business logic for profile persistence and CV parsing."""

    async def get_profile(self, db: AsyncSession) -> UserProfile | None:
        result = await db.execute(select(UserProfile))
        return result.scalars().first()

    def to_schema(self, profile: UserProfile | None) -> ProfileSchema:
        if not profile:
            return ProfileSchema()

        return ProfileSchema(
            full_name=profile.full_name,
            email=profile.email,
            phone=profile.phone,
            location=profile.location,
            experience=profile.experience or [],
            education=profile.education or [],
            projects=profile.projects or [],
            skills=profile.skills or {},
            certifications=profile.certifications or [],
            languages=profile.languages or [],
            achievements=profile.achievements or [],
            career_goals=profile.career_goals,
        )

    async def upsert_profile(
        self, db: AsyncSession, data: ProfileSchema
    ) -> ProfileSchema:
        profile = await self.get_profile(db)

        if not profile:
            profile = UserProfile()
            db.add(profile)
            await db.flush()

        self._apply_schema(profile, data)
        await self._create_version(db, profile, data)

        await db.commit()
        await db.refresh(profile)
        return self.to_schema(profile)

    async def apply_cv_upload(
        self, db: AsyncSession, uploaded_file: UploadFile
    ) -> ProfileSchema:
        text = await self._extract_text_from_upload(uploaded_file)
        parsed_raw_dict = parse_raw_cv(text)

        patch = self._build_patch_from_parsed_cv(parsed_raw_dict)

        existing_profile = await self.get_profile(db)
        if not existing_profile:
            existing_profile = UserProfile()
            db.add(existing_profile)
            await db.flush()

        existing_profile.raw_cv_text = text
        existing_profile.parsed_cv_json = parsed_raw_dict

        merged = self._merge_patch_into_profile(existing_profile, patch)
        await self._create_version(db, existing_profile, merged)

        await db.commit()
        await db.refresh(existing_profile)
        return self.to_schema(existing_profile)

    def _apply_schema(
        self, profile: UserProfile, data: ProfileSchema
    ) -> None:
        profile.full_name = data.full_name
        profile.email = data.email
        profile.phone = data.phone
        profile.location = data.location

        profile.experience = data.experience
        profile.education = data.education
        profile.projects = data.projects
        profile.skills = data.skills
        profile.certifications = data.certifications
        profile.languages = data.languages
        profile.achievements = data.achievements
        profile.career_goals = data.career_goals

    async def _create_version(
        self, db: AsyncSession, profile: UserProfile, data: ProfileSchema
    ) -> None:
        snapshot = data.model_dump()
        version = UserProfileVersion(
            user_profile_id=profile.id, snapshot=snapshot
        )
        db.add(version)

    async def _extract_text_from_upload(
        self, uploaded_file: UploadFile
    ) -> str:
        filename = uploaded_file.filename or ""
        suffix = Path(filename).suffix.lower()

        content = await self._read_upload_with_limit(
            uploaded_file, max_bytes=settings.cv_upload_max_bytes
        )

        if suffix == ".txt":
            return content.decode("utf-8", errors="replace")
        if suffix == ".pdf":
            return self._extract_pdf_text(content)
        if suffix == ".docx":
            return self._extract_docx_text(content)

        raise ValueError(
            "Unsupported file type. Please upload a PDF, DOCX, or TXT CV."
        )

    async def _read_upload_with_limit(
        self, uploaded_file: UploadFile, *, max_bytes: int
    ) -> bytes:
        if max_bytes <= 0:
            raise ValueError("Invalid upload size limit configuration.")

        chunks: list[bytes] = []
        bytes_read = 0
        chunk_size = 1024 * 1024

        while True:
            chunk = await uploaded_file.read(chunk_size)
            if not chunk:
                break

            bytes_read += len(chunk)
            if bytes_read > max_bytes:
                raise ValueError(
                    f"Upload too large. Max size is {max_bytes} bytes."
                )
            chunks.append(chunk)

        return b"".join(chunks)

    def _extract_pdf_text(self, content: bytes) -> str:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        try:
            reader = PdfReader(BytesIO(content))
            if getattr(reader, "is_encrypted", False):
                raise ValueError(
                    "Encrypted PDFs are not supported. "
                    "Please upload an unencrypted PDF."
                )

            pages_text: list[str] = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            return "\n".join(pages_text).strip()
        except (PdfReadError, ValueError) as exc:
            raise ValueError(
                "Invalid PDF file. Please upload a valid PDF CV."
            ) from exc

    def _extract_docx_text(self, content: bytes) -> str:
        from zipfile import BadZipFile

        from docx import Document
        from docx.opc.exceptions import PackageNotFoundError

        try:
            doc = Document(BytesIO(content))
        except (BadZipFile, PackageNotFoundError, ValueError) as exc:
            raise ValueError(
                "Invalid DOCX file. Please upload a valid DOCX CV."
            ) from exc

        return "\n".join(p.text for p in doc.paragraphs if p.text).strip()

    def _parse_cv_to_patch(self, cv_text: str) -> ParsedCvProfilePatch:
        parsed = parse_raw_cv(cv_text)

        return self._build_patch_from_parsed_cv(parsed)

    def _build_patch_from_parsed_cv(
        self, parsed_raw_dict: dict[str, Any]
    ) -> ParsedCvProfilePatch:
        experience = parsed_raw_dict.get("experience") or []
        education = parsed_raw_dict.get("education") or []
        skills_list = parsed_raw_dict.get("skills") or []
        skills: dict[str, Any] = (
            {"general": skills_list} if skills_list else {}
        )
        return ParsedCvProfilePatch(
            experience=experience, education=education, skills=skills
        )

    def _merge_patch_into_profile(
        self, profile: UserProfile, patch: ParsedCvProfilePatch
    ) -> ProfileSchema:
        current = self.to_schema(profile)

        merged_skills = dict(current.skills)
        for key, value in patch.skills.items():
            merged_skills[key] = value

        merged_payload = current.model_dump()
        if patch.experience:
            merged_payload["experience"] = patch.experience
        if patch.education:
            merged_payload["education"] = patch.education
        merged_payload["skills"] = merged_skills

        merged = ProfileSchema(**merged_payload)

        self._apply_schema(profile, merged)
        return merged
