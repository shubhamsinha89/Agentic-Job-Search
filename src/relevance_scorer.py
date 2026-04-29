"""
relevance_scorer.py
Computes a relevance score (0–65) for each job against the candidate's profile.

Scoring breakdown:
  Skills overlap     0–15  (keyword match between resume skills and job snippet)
  Experience fit     0–10  (how well candidate's years fit the job's requirement)
  Role match         0–15  (title similarity)
  Industry match     0–10  (from config preferences)
  Location score     0–10  (from config preferences)
  Freshness          0– 5  (posting recency)
  ─────────────────────────
  Total              0–65
"""

import re
from datetime import datetime, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> set:
    """Lower-case, remove punctuation, split into words."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return set(text.split())


def _extract_years_range(text: str) -> Optional[tuple]:
    """Extract (min, max) years from strings like '10-15 years', '12+ years'."""
    text = text.lower()
    m = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*(?:year|yr)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*\+\s*(?:year|yr)", text)
    if m:
        return int(m.group(1)), int(m.group(1)) + 5
    m = re.search(r"(\d+)\s*(?:year|yr)", text)
    if m:
        v = int(m.group(1))
        return max(0, v - 2), v + 2
    return None


def _parse_posted_date(date_str: str) -> Optional[datetime]:
    """Best-effort parse of posting date strings."""
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    now = datetime.utcnow()
    if "today" in date_str or "just" in date_str or "hour" in date_str:
        return now
    m = re.search(r"(\d+)\s*day", date_str)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r"(\d+)\s*week", date_str)
    if m:
        return now - timedelta(weeks=int(m.group(1)))
    m = re.search(r"(\d+)\s*month", date_str)
    if m:
        return now - timedelta(days=30 * int(m.group(1)))
    for fmt in ("%d %b %Y", "%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Scoring dimensions
# ---------------------------------------------------------------------------

def _score_skills(profile: dict, job: dict) -> int:
    """Skills overlap: matched skills / total profile skills * 15."""
    resume_skills = _normalise(" ".join(profile.get("top_skills", [])))
    resume_keywords = _normalise(" ".join(profile.get("keywords", [])))
    resume_tokens = resume_skills | resume_keywords

    job_text = _normalise(
        f"{job.get('title','')} {job.get('snippet','')} {job.get('description','')}"
    )
    matched = resume_tokens & job_text
    if not resume_tokens:
        return 5
    ratio = min(len(matched) / max(len(resume_tokens) * 0.3, 1), 1.0)
    return round(ratio * 15)


def _score_experience(profile: dict, job: dict) -> int:
    """Experience fit: how well candidate years fit job requirement."""
    candidate_years = profile.get("total_experience_years", 0)
    job_text = f"{job.get('snippet','')} {job.get('description','')} {job.get('experience_required','')}"
    req = _extract_years_range(job_text)
    if not req:
        return 5  # unspecified → neutral
    lo, hi = req
    if lo <= candidate_years <= hi:
        return 10
    gap = min(abs(candidate_years - lo), abs(candidate_years - hi))
    if gap <= 2:
        return 7
    if gap <= 4:
        return 4
    return 1


def _score_role(profile: dict, job: dict) -> int:
    """Role match: title keywords vs target roles."""
    target_tokens = _normalise(" ".join(profile.get("target_roles", [])))
    job_title_tokens = _normalise(job.get("title", ""))
    matched = target_tokens & job_title_tokens
    if not target_tokens:
        return 8
    ratio = min(len(matched) / max(len(job_title_tokens), 1), 1.0)
    return round(ratio * 15)


def _score_industry(profile: dict, job: dict, config: dict) -> int:
    """Industry match from config preferences."""
    industries_cfg = config.get("industries", [])
    if not industries_cfg:
        return 5
    job_text = (
        f"{job.get('company','')} {job.get('snippet','')} {job.get('description','')}".lower()
    )
    for ind in sorted(industries_cfg, key=lambda x: x.get("score", 0), reverse=True):
        for kw in ind.get("keywords", []):
            if kw.lower() in job_text:
                return min(ind.get("score", 5), 10)
    return 2


def _score_location(profile: dict, job: dict, config: dict) -> int:
    """Location preference from config."""
    locations_cfg = config.get("locations", [])
    if not locations_cfg:
        return 5
    job_location = job.get("location", "").lower()
    for loc in sorted(locations_cfg, key=lambda x: x.get("score", 0), reverse=True):
        for kw in loc.get("keywords", []):
            if kw.lower() in job_location:
                return min(loc.get("score", 2), 10)
    return 2


def _score_freshness(job: dict) -> int:
    """Recency of job posting."""
    posted = _parse_posted_date(job.get("posted_date", ""))
    if not posted:
        return 2
    age_days = (datetime.utcnow() - posted).days
    if age_days <= 1:
        return 5
    if age_days <= 3:
        return 4
    if age_days <= 7:
        return 3
    if age_days <= 14:
        return 2
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_job(job: dict, profile: dict, config: dict) -> dict:
    """
    Score a single job against the candidate profile.

    Returns the job dict enriched with:
      score_breakdown: dict of each dimension score
      total_score: int (0–65)
      relevance_pct: float (0–100)
    """
    breakdown = {
        "skills":     _score_skills(profile, job),
        "experience": _score_experience(profile, job),
        "role":       _score_role(profile, job),
        "industry":   _score_industry(profile, job, config),
        "location":   _score_location(profile, job, config),
        "freshness":  _score_freshness(job),
    }
    total = sum(breakdown.values())
    return {
        **job,
        "score_breakdown": breakdown,
        "total_score": total,
        "relevance_pct": round((total / 65) * 100, 1),
    }


def score_and_rank(jobs: list, profile: dict, config: dict, top_n: int = 20) -> list:
    """Score all jobs, deduplicate, return top_n sorted by total_score."""
    scored = [score_job(j, profile, config) for j in jobs]

    # Deduplicate by (title, company) — keep highest score
    seen = {}
    for job in scored:
        key = (job.get("title", "").lower(), job.get("company", "").lower())
        if key not in seen or job["total_score"] > seen[key]["total_score"]:
            seen[key] = job

    ranked = sorted(seen.values(), key=lambda x: x["total_score"], reverse=True)
    return ranked[:top_n]