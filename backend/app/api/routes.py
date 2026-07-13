from __future__ import annotations

from io import BytesIO
from urllib.parse import quote_plus

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader

from app.models.schemas import (
    ATSScoreRequest,
    CareerGuidanceRequest,
    CoverLetterRequest,
    InterviewRequest,
    JobMatchRequest,
    JobSearchRequest,
    ResumeAnalysisRequest,
    SkillGapRequest,
)
from app.services.generation_service import career_guidance, generate_cover_letter, interview_prep
from app.services.job_service import JobFeedUnavailable, search_live_jobs
from app.services.matching_service import ats_score, match_resume_to_job, skill_gap
from app.services.resume_service import analyze_resume


router = APIRouter()


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "resume"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if suffix == "pdf":
        try:
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="This PDF could not be read. Upload a text-based PDF or a .txt resume.") from exc
    elif suffix == "txt":
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Upload a PDF or TXT resume.")
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="No readable resume text was found in this file.")
    analysis = analyze_resume(text)
    return {"filename": filename, "text": text, **analysis.model_dump()}


@router.post("/analyze-resume")
def analyze_resume_endpoint(request: ResumeAnalysisRequest):
    return analyze_resume(request.resume_text)


@router.post("/search-jobs")
def search_jobs_endpoint(request: JobSearchRequest):
    try:
        return {
            "jobs": search_live_jobs(request),
            "search_links": _location_search_links(request.role, request.location),
        }
    except JobFeedUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _location_search_links(role: str, location: str) -> list[dict[str, str]]:
    """Links remain useful when free feeds have no listing for a specific city."""
    role_query = quote_plus(role.strip())
    location_query = quote_plus(location.strip())
    role_slug = "-".join(role.lower().split())
    location_slug = "-".join(location.lower().split())
    return [
        {"name": "Naukri", "url": f"https://www.naukri.com/{role_slug}-jobs-in-{location_slug}"},
        {"name": "LinkedIn Jobs", "url": f"https://www.linkedin.com/jobs/search/?keywords={role_query}&location={location_query}"},
        {"name": "Indeed", "url": f"https://in.indeed.com/jobs?q={role_query}&l={location_query}"},
    ]


@router.post("/job-match")
def job_match_endpoint(request: JobMatchRequest):
    return match_resume_to_job(request.resume_text, request.job_description)


@router.post("/ats-score")
def ats_score_endpoint(request: ATSScoreRequest):
    return ats_score(request.resume_text, request.target_role, request.job_description)


@router.post("/generate-cover-letter")
def cover_letter_endpoint(request: CoverLetterRequest):
    return generate_cover_letter(request)


@router.post("/career-guidance")
def career_guidance_endpoint(request: CareerGuidanceRequest):
    return career_guidance(request.current_role, request.target_role, request.skills, request.experience_years)


@router.post("/skill-gap-analysis")
def skill_gap_endpoint(request: SkillGapRequest):
    return skill_gap(request.current_skills, request.target_role, request.job_description)


@router.post("/interview-session")
def interview_session_endpoint(request: InterviewRequest):
    return interview_prep(request)


@router.get("/recommendations")
def recommendations(query: str = "software developer"):
    return {
        "query": query,
        "next_steps": [
            "Search roles that match your strongest skills.",
            "Compare your resume with one selected job description.",
            "Tailor your resume keywords before applying.",
        ],
        "note": "Recommendations use simple keyword matching and templates; no external AI model is required.",
    }
