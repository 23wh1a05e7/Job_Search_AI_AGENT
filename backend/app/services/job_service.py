from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from dotenv import load_dotenv
from app.models.schemas import JobResult, JobSearchRequest
from app.services.text_utils import extract_skills, normalize_skill, strip_html, summarize


load_dotenv()


class JobFeedUnavailable(Exception):
    """Raised only when neither live job source can be reached."""


def search_live_jobs(request: JobSearchRequest) -> list[JobResult]:
    """Retrieve, location-filter, and rank live listings against resume skills."""
    # Query both sources: non-local results from one source must not hide a
    # valid role from the other source.
    jobs = _adzuna_jobs(request) + _remotive_jobs(request) + _muse_jobs(request) + _arbeitnow_jobs(request)
    if not jobs:
        raise JobFeedUnavailable("Live job sources are unavailable right now. Please try again in a few minutes.")
    matching_jobs = [
        job for job in jobs
        if job.location_match and _matches_requested_role(request.role, job.title, job.description)
    ]
    if matching_jobs:
        return sorted(matching_jobs, key=lambda job: job.score, reverse=True)[:25]

    # A city search should not silently turn into a different city search. If
    # no job explicitly lists the requested city, show only remote roles that
    # are clearly eligible for the user's country or worldwide.
    remote_jobs = [
        job for job in jobs
        if _is_remote_fallback_for(request.location, job.location)
        and _matches_requested_role(request.role, job.title, job.description)
    ]
    return [
        job.model_copy(update={
            "location_match_type": "remote_fallback",
            "match_reason": (
                f"No live role explicitly listed in {request.location}; showing an eligible remote role. "
                f"{job.match_reason}"
            ),
        })
        for job in sorted(remote_jobs, key=lambda job: job.score, reverse=True)[:25]
    ]


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "JobMate/1.0 (personal job search)"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _remotive_jobs(request: JobSearchRequest) -> list[JobResult]:
    # Skills are used for ranking, not as API search terms: combining them made searches too narrow.
    query = urllib.parse.quote(request.role.strip())
    payload = _fetch_json(f"https://remotive.com/api/remote-jobs?search={query}")
    return [_normalize_remotive(job, request) for job in payload.get("jobs", [])]


def _adzuna_jobs(request: JobSearchRequest) -> list[JobResult]:
    """Fetch direct India listings when the optional Adzuna credentials exist."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []
    query = urllib.parse.urlencode({
        "app_id": app_id,
        "app_key": app_key,
        "what": request.role,
        "where": request.location,
        "results_per_page": 25,
        "content-type": "application/json",
    })
    payload = _fetch_json(f"https://api.adzuna.com/v1/api/jobs/in/search/1?{query}")
    return [_normalize_adzuna(job, request) for job in payload.get("results", [])]


def _muse_jobs(request: JobSearchRequest) -> list[JobResult]:
    # A second public source makes searches resilient when Remotive is temporarily unavailable.
    query = urllib.parse.urlencode({"page": 1, "descending": "true"})
    payload = _fetch_json(f"https://www.themuse.com/api/public/jobs?{query}")
    return [_normalize_muse(job, request) for job in payload.get("results", [])]


def _arbeitnow_jobs(request: JobSearchRequest) -> list[JobResult]:
    """Public job-board feed used when either primary feed is incomplete."""
    payload = _fetch_json("https://www.arbeitnow.com/api/job-board-api")
    return [_normalize_arbeitnow(job, request) for job in payload.get("data", [])]


def _normalize_remotive(job: dict, request: JobSearchRequest) -> JobResult:
    text = strip_html(job.get("description", ""))
    skills = sorted(set([str(tag).lower() for tag in job.get("tags", [])] + extract_skills(text)))
    return _job_result(
        request=request,
        job_id=str(job.get("id", "")),
        title=job.get("title", "Untitled role"),
        company=job.get("company_name", "Unknown company"),
        location=job.get("candidate_required_location", "Remote"),
        source="Remotive",
        url=job.get("url", ""),
        posted_at=job.get("publication_date"),
        description=text,
        skills=skills,
    )


def _normalize_adzuna(job: dict, request: JobSearchRequest) -> JobResult:
    description = strip_html(job.get("description", ""))
    company = (job.get("company") or {}).get("display_name", "Unknown company")
    location = (job.get("location") or {}).get("display_name", "Location not listed")
    category = (job.get("category") or {}).get("label", "")
    skills = extract_skills(f"{job.get('title', '')} {description} {category}")
    return _job_result(
        request=request,
        job_id=str(job.get("id", job.get("redirect_url", ""))),
        title=job.get("title", "Untitled role"),
        company=company,
        location=location,
        source="Adzuna",
        url=job.get("redirect_url", ""),
        posted_at=job.get("created"),
        description=description,
        skills=skills,
    )


def _normalize_muse(job: dict, request: JobSearchRequest) -> JobResult:
    contents = strip_html(job.get("contents", ""))
    categories = [category.get("name", "") for category in job.get("categories", [])]
    skills = sorted(set(extract_skills(f"{job.get('name', '')} {contents} {' '.join(categories)}")))
    locations = ", ".join(location.get("name", "") for location in job.get("locations", []) if location.get("name")) or "Location not listed"
    company = (job.get("company") or {}).get("name", "Unknown company")
    return _job_result(
        request=request,
        job_id=str(job.get("id", "")),
        title=job.get("name", "Untitled role"),
        company=company,
        location=locations,
        source="The Muse",
        url=job.get("refs", {}).get("landing_page", ""),
        posted_at=job.get("publication_date"),
        description=contents,
        skills=skills,
    )


def _normalize_arbeitnow(job: dict, request: JobSearchRequest) -> JobResult:
    description = strip_html(job.get("description", ""))
    tags = [str(tag).lower() for tag in job.get("tags", [])]
    skills = sorted(set(tags + extract_skills(f"{job.get('title', '')} {description}")))
    base_location = job.get("location") or "Location not listed"
    location = f"{base_location} (Remote)" if job.get("remote") and "remote" not in base_location.lower() else base_location
    return _job_result(
        request=request,
        job_id=job.get("slug") or job.get("url", ""),
        title=job.get("title", "Untitled role"),
        company=job.get("company_name", "Unknown company"),
        location=location,
        source="Arbeitnow",
        url=job.get("url", ""),
        posted_at=job.get("created_at"),
        description=description,
        skills=skills,
    )


def _job_result(*, request: JobSearchRequest, job_id: str, title: str, company: str, location: str, source: str, url: str, posted_at: str | None, description: str, skills: list[str]) -> JobResult:
    requested_skills = {normalize_skill(skill) for skill in request.skills if skill.strip()}
    matched = sorted(requested_skills & set(skills))
    missing = sorted(set(skills) - requested_skills)
    role_score = _role_score(request.role, title, description)
    location_match = _location_matches(request.location, location, request.work_mode)
    skill_score = min(45, round((len(matched) / len(skills)) * 45)) if skills else 0
    score = min(100, 20 + role_score + skill_score + _recency_score(posted_at))
    location_note = "matches your location" if location_match else "does not match your location"
    reason = f"{location_note.title()}. Role relevance: {role_score}/35. Matched skills: {', '.join(matched) or 'none detected'}."
    return JobResult(
        id=job_id,
        title=title,
        company=company,
        location=location,
        source=source,
        url=url,
        posted_at=str(posted_at) if posted_at is not None else None,
        description=summarize(description),
        skills=skills[:20],
        matched_skills=matched,
        missing_skills=missing[:12],
        location_match=location_match,
        score=score,
        match_reason=reason,
    )


def _location_matches(requested_location: str, job_location: str, work_mode: str) -> bool:
    """Use only explicit location text; never label a city request as a match by accident."""
    requested = requested_location.strip().lower()
    listed = job_location.strip().lower()
    if not requested or requested in {"remote", "anywhere", "worldwide"}:
        return any(marker in listed for marker in {"remote", "worldwide", "anywhere"})

    requested_words = [word for word in requested.replace(",", " ").split() if len(word) > 2]
    if requested in listed or (requested_words and all(word in listed for word in requested_words)):
        return True
    # Country-level remote eligibility is useful for a user searching a city in
    # that country (for example, Hyderabad / India), but generic global remote
    # roles are not shown as local listings.
    countries = {"india": ["india"], "united states": ["united states", "usa"], "uk": ["uk", "united kingdom"]}
    for country, markers in countries.items():
        if country in requested and any(marker in listed for marker in markers):
            return True
    return False


def _is_remote_fallback_for(requested_location: str, job_location: str) -> bool:
    listed = job_location.lower()
    if "worldwide" in listed or "anywhere" in listed:
        return True
    requested = requested_location.lower()
    india_cities = {
        "hyderabad", "bengaluru", "bangalore", "chennai", "mumbai", "pune",
        "delhi", "noida", "gurugram", "gurgaon", "kolkata", "ahmedabad", "kochi",
    }
    if any(city in requested for city in india_cities):
        return "remote" in listed and "india" in listed
    return False


def _role_score(role: str, title: str, description: str) -> int:
    role_words = {word for word in role.lower().replace("/", " ").split() if len(word) > 2 and word not in {"the", "and", "for", "job"}}
    title_lower = title.lower()
    text = f"{title_lower} {description.lower()}"
    exact = role.strip().lower() in title_lower
    title_hits = sum(word in title_lower for word in role_words)
    text_hits = sum(word in text for word in role_words)
    # A small, explicit synonym list handles common title variations without an AI model.
    synonym_bonus = 8 if ({"developer", "engineer", "sde"} & role_words and any(word in title_lower for word in {"developer", "engineer", "sde"})) else 0
    return min(35, (20 if exact else 0) + title_hits * 7 + text_hits * 2 + synonym_bonus)


def _matches_requested_role(role: str, title: str, description: str) -> bool:
    """Keep generic developer terms flexible but require stated specialty terms."""
    generic_words = {"developer", "engineer", "software", "job", "role", "specialist", "manager"}
    role_words = {
        word for word in role.lower().replace("/", " ").split()
        if len(word) > 2 and word not in {"the", "and", "for", *generic_words}
    }
    title_text = title.lower()
    if role_words:
        return all(word in title_text for word in role_words)
    return _role_score(role, title, description) >= 10


def _recency_score(posted_at: str | int | float | None) -> int:
    if not posted_at:
        return 0
    try:
        if isinstance(posted_at, (int, float)):
            value = datetime.fromtimestamp(posted_at, tz=timezone.utc)
        else:
            value = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - value).days
        return 8 if days <= 3 else 4 if days <= 14 else 0
    except (TypeError, ValueError):
        return 0
