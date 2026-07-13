from __future__ import annotations

from app.models.schemas import ATSScoreResponse, JobMatchResponse, SkillGapResponse
from app.services.text_utils import extract_skills


def match_resume_to_job(resume_text: str, job_description: str) -> JobMatchResponse:
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_description))
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)
    match_percent = round((len(matched) / len(job_skills)) * 100) if job_skills else 70
    return JobMatchResponse(
        match_percent=min(100, match_percent),
        matched_skills=matched,
        missing_skills=missing,
        recommended_skills=missing[:8],
        experience_gap="Review years of experience and project depth against the role requirements.",
        explanation=f"Matched {len(matched)} of {len(job_skills)} detected job skill signals.",
    )


def ats_score(resume_text: str, target_role: str, job_description: str = "") -> ATSScoreResponse:
    resume_skills = set(extract_skills(resume_text))
    target_skills = set(extract_skills(f"{target_role} {job_description}"))
    missing = sorted(target_skills - resume_skills)
    present = sorted(resume_skills & target_skills)
    keyword_score = round((len(present) / len(target_skills)) * 70) if target_skills else 45
    formatting_score = 20 if "\t" not in resume_text else 10
    clarity_score = 10 if len(resume_text.split()) > 120 else 5
    return ATSScoreResponse(
        score=min(100, keyword_score + formatting_score + clarity_score),
        keyword_analysis={"present": present, "missing": missing},
        formatting_suggestions=[
            "Use standard headings such as Skills, Experience, Education, Projects.",
            "Avoid images, complex tables, and multi-column layouts.",
            "Add role-specific keywords exactly as they appear in the job description.",
        ],
        missing_keywords=missing,
    )


def skill_gap(current_skills: list[str], target_role: str, job_description: str = "") -> SkillGapResponse:
    current = {skill.lower() for skill in current_skills}
    required = set(extract_skills(f"{target_role} {job_description}"))
    missing = sorted(required - current)
    return SkillGapResponse(
        missing_skills=missing,
        recommended_courses=[f"Complete a practical course on {skill}." for skill in missing[:5]],
        project_ideas=[f"Build and document a portfolio project using {skill}." for skill in missing[:5]],
        certifications=[
            "AWS Cloud Practitioner or Developer Associate",
            "Meta Front-End Developer Certificate",
            "Google Data Analytics or Machine Learning specialization",
        ],
    )

