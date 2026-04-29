"""
job_searcher.py
Searches India + US job portals via Brave Search API.
Uses Claude to auto-generate search queries from the parsed resume profile.
"""

import os
import time
from typing import Optional
import anthropic
import requests


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

INDIA_PORTALS = [
    {"name": "naukri",     "site": "naukri.com"},
    {"name": "timesjobs",  "site": "timesjobs.com"},
    {"name": "iimjobs",    "site": "iimjobs.com"},
    {"name": "indeed_in",  "site": "in.indeed.com"},
    {"name": "shine",      "site": "shine.com"},
]

US_PORTALS = [
    {"name": "indeed_us",  "site": "indeed.com"},
    {"name": "linkedin",   "site": "linkedin.com/jobs"},
    {"name": "glassdoor",  "site": "glassdoor.com/job-listing"},
    {"name": "ziprecruiter", "site": "ziprecruiter.com"},
    {"name": "dice",       "site": "dice.com"},
]

QUERY_PROMPT = """You are a job search strategist. Given the candidate profile below, generate search queries to find matching jobs.

Candidate profile:
- Profession: {profession_category}
- Seniority: {seniority_level}
- Total experience: {total_experience_years} years
- Target roles: {target_roles}
- Top skills: {top_skills}
- Industries: {industries}

Generate exactly 4 search query TEMPLATES (no site: prefix — that will be added automatically).
Each query should be targeted and use quotes for exact phrases.
Return ONLY a JSON array of 4 strings, nothing else.

Example output format:
["\"Senior Software Engineer\" Python AWS", "\"Backend Engineer\" microservices India", ...]"""


def generate_queries(profile: dict, api_key: str = None) -> list:
    """Use Claude to generate job-search queries tailored to the profile."""
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
    prompt = QUERY_PROMPT.format(
        profession_category=profile.get("profession_category", ""),
        seniority_level=profile.get("seniority_level", ""),
        total_experience_years=profile.get("total_experience_years", ""),
        target_roles=", ".join(profile.get("target_roles", [])[:5]),
        top_skills=", ".join(profile.get("top_skills", [])[:8]),
        industries=", ".join(profile.get("industries", [])[:4]),
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    import json, re
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _brave_search(query: str, brave_api_key: str, count: int = 10) -> list:
    """Call Brave Search API and return raw result list."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": brave_api_key,
    }
    params = {"q": query, "count": count, "search_lang": "en"}
    try:
        resp = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("web", {}).get("results", [])
    except Exception as e:
        print(f"  [warn] Brave search failed for '{query}': {e}")
        return []


def _parse_brave_result(result: dict, portal: str, country: str) -> dict:
    """Normalise a Brave search result into a job dict."""
    title = result.get("title", "")
    url = result.get("url", "")
    snippet = result.get("description", "")

    # Try to extract company from title patterns like "Title at Company | Portal"
    company = ""
    import re
    m = re.search(r" at ([^|–\-]+)", title)
    if m:
        company = m.group(1).strip()

    # Extract location hints from snippet
    location_hints = re.findall(
        r"\b(Mumbai|Delhi|NCR|Bangalore|Bengaluru|Chennai|Hyderabad|Pune|Kolkata|"
        r"Noida|Gurgaon|Patna|Bihar|Rajasthan|Jharkhand|"
        r"New York|San Francisco|Seattle|Austin|Chicago|Boston|Remote)\b",
        snippet, re.IGNORECASE
    )
    location = location_hints[0] if location_hints else ""

    # Extract experience requirement
    exp_match = re.search(r"(\d+[\-–]\d+|\d+\+?)\s*(?:years?|yrs?)", snippet, re.IGNORECASE)
    experience_required = exp_match.group(0) if exp_match else ""

    # Extract posting date
    date_match = re.search(
        r"(\d+\s+(?:day|hour|week|month)s?\s+ago|today|just\s+posted|\d{1,2}\s+\w+\s+\d{4})",
        snippet, re.IGNORECASE
    )
    posted_date = date_match.group(0) if date_match else ""

    return {
        "title": title,
        "company": company,
        "location": location,
        "experience_required": experience_required,
        "posted_date": posted_date,
        "snippet": snippet,
        "url": url,
        "portal": portal,
        "country": country,
    }


def search_portal(
    query_template: str,
    portal: dict,
    country: str,
    brave_api_key: str,
    results_per_query: int = 10,
    delay: float = 0.5,
) -> list:
    """Search a single portal with one query template."""
    site = portal["site"]
    full_query = f"site:{site} {query_template}"
    raw = _brave_search(full_query, brave_api_key, count=results_per_query)
    time.sleep(delay)
    return [_parse_brave_result(r, portal["name"], country) for r in raw]


def search_all(
    profile: dict,
    config: dict,
    brave_api_key: str = None,
    anthropic_api_key: str = None,
) -> list:
    """
    Search all enabled portals (India + US) and return combined raw job list.

    Args:
        profile:          Parsed resume profile dict
        config:           search_config.yaml as dict
        brave_api_key:    Brave Search API key (falls back to BRAVE_SEARCH_API_KEY env)
        anthropic_api_key: Anthropic API key for query generation

    Returns:
        List of raw job dicts
    """
    brave_key = brave_api_key or os.environ.get("BRAVE_SEARCH_API_KEY", "")
    if not brave_key:
        raise ValueError("BRAVE_SEARCH_API_KEY not set")

    print("Generating search queries from resume profile...")
    queries = generate_queries(profile, api_key=anthropic_api_key)
    print(f"  Generated {len(queries)} queries: {queries}")

    portals_cfg = config.get("portals", {})
    india_portals = [
        p for p in INDIA_PORTALS
        if portals_cfg.get(p["name"], {}).get("enabled", True)
    ]
    us_portals = [
        p for p in US_PORTALS
        if portals_cfg.get(p["name"], {}).get("enabled", True)
    ]

    results = []
    total = len(queries) * (len(india_portals) + len(us_portals))
    done = 0

    for query in queries:
        for portal in india_portals:
            print(f"  [{done+1}/{total}] Searching {portal['name']} (India): {query[:60]}...")
            results.extend(search_portal(query, portal, "India", brave_key))
            done += 1

        for portal in us_portals:
            print(f"  [{done+1}/{total}] Searching {portal['name']} (US): {query[:60]}...")
            results.extend(search_portal(query, portal, "US", brave_key))
            done += 1

    print(f"Total raw results: {len(results)}")
    return results