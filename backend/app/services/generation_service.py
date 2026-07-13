from __future__ import annotations

from app.models.schemas import CareerGuidanceResponse, CoverLetterRequest, CoverLetterResponse, InterviewRequest, InterviewResponse


def generate_cover_letter(request: CoverLetterRequest) -> CoverLetterResponse:
    skills = ", ".join(request.profile.skills[:6]) or "relevant technical skills"
    project = request.profile.projects[0] if request.profile.projects else "hands-on project work"
    letter = (
        f"Dear {request.company} Hiring Team,\n\n"
        f"I am excited to apply for the {request.job_title} role. My background includes {skills}, "
        f"and I have demonstrated these skills through {project}.\n\n"
        f"Your role interests me because it focuses on {request.job_description[:220].strip()}. "
        "I would bring a practical, learning-oriented engineering mindset and a strong focus on delivering useful results.\n\n"
        "Thank you for your time and consideration.\n\n"
        f"Sincerely,\n{request.profile.name}"
    )
    return CoverLetterResponse(cover_letter=letter)


def career_guidance(current_role: str, target_role: str, skills: list[str], experience_years: float) -> CareerGuidanceResponse:
    return CareerGuidanceResponse(
        roadmap=[
            f"Clarify the exact {target_role} job family and collect 10 target job descriptions.",
            "Build two portfolio projects that map directly to recurring job requirements.",
            "Prepare resume bullets with metrics, project links, and ATS keywords.",
            "Practice role-specific interviews weekly with feedback.",
        ],
        certifications=["AWS Cloud Practitioner", "Meta Front-End Developer", "Oracle Java Foundations", "Google Professional ML Engineer"],
        interview_plan=["DSA fundamentals", "System design basics", "Project deep dive", "Behavioral STAR stories"],
        salary_insights=f"For {target_role}, salary depends heavily on location, company size, and {experience_years:g} years of experience.",
        growth_suggestions=[
            "Track applications and interview feedback.",
            "Focus on one primary stack for 8-12 weeks.",
            "Publish project writeups and GitHub READMEs.",
        ],
    )


def interview_prep(request: InterviewRequest) -> InterviewResponse:
    skills = request.skills or ["data structures", "system design", "project experience"]
    feedback = None
    if request.answer:
        feedback = "Good start. Improve by adding a concrete example, tradeoff, result, and what you learned."
    return InterviewResponse(
        technical_questions=[f"Explain a project where you used {skill}." for skill in skills[:5]],
        hr_questions=[
            "Tell me about yourself.",
            "Describe a challenge you solved.",
            "Why are you interested in this role?",
        ],
        company_questions=[
            f"What do you know about {request.company or 'this company'}?",
            "How would you contribute in your first 90 days?",
        ],
        feedback=feedback,
    )

