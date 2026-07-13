from __future__ import annotations

import re
from html.parser import HTMLParser


# The application deliberately uses a small, transparent skills catalogue instead
# of an opaque model.  Keys are the labels returned to the user; values include
# common resume and job-posting spellings for the same skill.
SKILL_ALIASES = {
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node", "node.js", "nodejs"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "spring": ["spring framework", "spring"],
    "spring boot": ["spring boot"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo db", "mongo"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud platform", "google cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git"],
    "github": ["github"],
    "rest api": ["rest api", "restful api", "restful services"],
    "graphql": ["graphql"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "tailwind css": ["tailwind", "tailwind css"],
    "data structures": ["data structures"],
    "algorithms": ["algorithms"],
    "system design": ["system design"],
    "testing": ["testing", "unit testing", "pytest", "jest"],
    "machine learning": ["machine learning", "ml"],
    "data analysis": ["data analysis", "data analytics"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "linux": ["linux"],
    "ci/cd": ["ci/cd", "ci cd", "continuous integration"],
    "figma": ["figma"],
}


class HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_html(html: str) -> str:
    parser = HTMLTextParser()
    parser.feed(html)
    return clean_text(parser.text())


def extract_skills(text: str) -> list[str]:
    normalized = text.lower().replace("_", " ")
    detected: set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        if any(_contains_phrase(normalized, alias) for alias in aliases):
            detected.add(skill)
    return sorted(detected)


def normalize_skill(skill: str) -> str:
    """Return the catalogue label for a user-entered skill when one exists."""
    normalized = clean_text(skill.lower())
    for canonical, aliases in SKILL_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            return canonical
    return normalized


def _contains_phrase(text: str, phrase: str) -> bool:
    # Word boundaries avoid false positives such as matching "java" in
    # "javascript" or matching "git" in "digital".
    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def summarize(text: str, limit: int = 260) -> str:
    compact = clean_text(text)
    return compact if len(compact) <= limit else compact[:limit].rstrip() + "..."
