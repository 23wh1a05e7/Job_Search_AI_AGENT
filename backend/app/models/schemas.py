from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class ResumeProfile(BaseModel):
    name: str = "Candidate"
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    experience: list[str] = []
    education: list[str] = []
    certifications: list[str] = []
    projects: list[str] = []
    raw_text: str = ""


class JobSearchRequest(BaseModel):
    role: str
    location: str = "Remote"
    salary: str | None = None
    work_mode: str = "remote"
    skills: list[str] = []


class JobResult(BaseModel):
    id: str
    title: str
    company: str
    location: str
    source: str
    url: str
    posted_at: str | None = None
    description: str
    skills: list[str] = []
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    location_match: bool = False
    location_match_type: str = "exact"
    score: int = 0
    match_reason: str = ""


class ResumeAnalysisRequest(BaseModel):
    resume_text: str


class ResumeAnalysisResponse(BaseModel):
    profile: ResumeProfile
    summary: str
    improvement_suggestions: list[str]


class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str


class JobMatchResponse(BaseModel):
    match_percent: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommended_skills: list[str]
    experience_gap: str
    explanation: str


class ATSScoreRequest(BaseModel):
    resume_text: str
    target_role: str
    job_description: str = ""


class ATSScoreResponse(BaseModel):
    score: int
    keyword_analysis: dict[str, list[str]]
    formatting_suggestions: list[str]
    missing_keywords: list[str]


class CoverLetterRequest(BaseModel):
    profile: ResumeProfile
    job_title: str
    company: str
    job_description: str


class CoverLetterResponse(BaseModel):
    cover_letter: str
    export_formats: list[str] = ["pdf", "docx"]


class CareerGuidanceRequest(BaseModel):
    current_role: str
    target_role: str
    skills: list[str]
    experience_years: float = 0


class CareerGuidanceResponse(BaseModel):
    roadmap: list[str]
    certifications: list[str]
    interview_plan: list[str]
    salary_insights: str
    growth_suggestions: list[str]


class SkillGapRequest(BaseModel):
    current_skills: list[str]
    target_role: str
    job_description: str = ""


class SkillGapResponse(BaseModel):
    missing_skills: list[str]
    recommended_courses: list[str]
    project_ideas: list[str]
    certifications: list[str]


class InterviewRequest(BaseModel):
    role: str
    company: str | None = None
    skills: list[str] = []
    answer: str | None = None


class InterviewResponse(BaseModel):
    technical_questions: list[str]
    hr_questions: list[str]
    company_questions: list[str]
    feedback: str | None = None


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    status: str = Field(pattern="^(Applied|Interview Scheduled|Rejected|Offered)$")
    url: HttpUrl | None = None
