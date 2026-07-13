from __future__ import annotations

import re

from app.models.schemas import ResumeAnalysisResponse, ResumeProfile
from app.services.text_utils import extract_skills


def parse_resume_text(resume_text: str) -> ResumeProfile:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    name = lines[0] if lines else "Candidate"
    email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", resume_text)
    phone_match = re.search(r"(?:\+?\d[\d\s-]{8,}\d)", resume_text)
    return ResumeProfile(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        skills=extract_skills(resume_text),
        experience=_section_lines(lines, ["experience", "work"]),
        education=_section_lines(lines, ["education", "degree"]),
        certifications=_section_lines(lines, ["certification", "certificate"]),
        projects=_section_lines(lines, ["project", "portfolio"]),
        raw_text=resume_text,
    )


def analyze_resume(resume_text: str) -> ResumeAnalysisResponse:
    profile = parse_resume_text(resume_text)
    suggestions = [
        "Add measurable impact to each experience bullet using numbers, scale, or outcome.",
        "Mirror important keywords from the target job description naturally in your skills and projects.",
        "Keep formatting simple: clear headings, consistent dates, and no tables for ATS-sensitive resumes.",
    ]
    if len(profile.skills) < 8:
        suggestions.append("Add a dedicated technical skills section with tools, languages, frameworks, and databases.")
    return ResumeAnalysisResponse(
        profile=profile,
        summary=f"Parsed {profile.name}'s resume with {len(profile.skills)} detected skill(s).",
        improvement_suggestions=suggestions,
    )


def _section_lines(lines: list[str], markers: list[str]) -> list[str]:
    return [line for line in lines if any(marker in line.lower() for marker in markers)][:6]

