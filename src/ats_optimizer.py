"""
ats_optimizer.py
Analyses the candidate's resume against the top job descriptions
to identify ATS keyword gaps and generate an optimised resume variant.
"""

import json
import os
import re
import anthropic


ATS_ANALYSIS_PROMPT = """You are an expert ATS (Applicant Tracking System) optimizer.

Candidate resume:
{resume_text}

Top job descriptions the candidate wants to target:
{job_descriptions}

Perform a detailed ATS analysis. Return ONLY valid JSON with this schema:
{{
  "ats_score_before": <integer 0-100, current resume ATS match percentage>,
  "ats_score_after": <integer 0-100, projected score after applying suggestions>,
  "missing_keywords": [
    {{
      "keyword": "string",
      "frequency_in_jds": <number of JDs it appears in>,
      "suggested_placement": "Skills section | Work experience at [Company] | Summary",
      "sample_phrase": "example sentence using this keyword naturally"
    }}
  ],
  "present_keywords": ["keywords already in resume that also appear in JDs"],
  "weak_sections": [
    {{
      "section": "string",
      "issue": "string",
      "suggestion": "string"
    }}
  ],
  "action_verbs_to_add": ["list of 5 strong action verbs relevant to these roles"],
  "quantification_gaps": ["bullet points that should include numbers/metrics"],
  "optimized_summary": "rewritten 3-sentence summary optimised for these roles",
  "optimized_skills_section": "rewritten skills section as comma-separated list including missing keywords"
}}"""


FULL_RESUME_REWRITE_PROMPT = """You are an expert resume writer and ATS optimizer.

Original resume:
{resume_text}

ATS analysis findings:
{ats_analysis}

Target job titles: {target_roles}

Rewrite the resume to maximise ATS compatibility while keeping it authentic and human-readable.
Rules:
- Keep all employment history accurate — do not fabricate experience
- Add missing keywords naturally into existing bullet points where they truthfully apply
- Strengthen weak bullet points with metrics where plausible
- Use the suggested optimized summary and skills section
- Format as clean Markdown

Return the complete rewritten resume as Markdown. Nothing else."""


def analyze_ats(
    profile: dict,
    top_jobs: list,
    api_key: str = None,
    max_jobs: int = 8,
) -> dict:
    """
    Analyse resume against top job descriptions and return ATS report.

    Args:
        profile:   Parsed resume profile (must contain _raw_text)
        top_jobs:  Ranked job list (uses top max_jobs)
        api_key:   Anthropic API key

    Returns:
        ATS analysis dict
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
    resume_text = profile.get("_raw_text", "")

    jd_blocks = []
    for i, job in enumerate(top_jobs[:max_jobs], 1):
        block = (
            f"JD {i}: {job.get('title','')} at {job.get('company','')} "
            f"({job.get('location','')})\n"
            f"{job.get('snippet','')} {job.get('description','')}"
        )
        jd_blocks.append(block)

    prompt = ATS_ANALYSIS_PROMPT.format(
        resume_text=resume_text,
        job_descriptions="\n\n".join(jd_blocks),
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def generate_optimized_resume(profile: dict, ats_analysis: dict, api_key: str = None) -> str:
    """
    Generate a full ATS-optimized resume variant as Markdown.

    Args:
        profile:      Parsed resume profile (must contain _raw_text)
        ats_analysis: Output from analyze_ats()
        api_key:      Anthropic API key

    Returns:
        Rewritten resume as Markdown string
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
    resume_text = profile.get("_raw_text", "")
    target_roles = ", ".join(profile.get("target_roles", [])[:4])

    prompt = FULL_RESUME_REWRITE_PROMPT.format(
        resume_text=resume_text,
        ats_analysis=json.dumps(ats_analysis, indent=2),
        target_roles=target_roles,
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def ats_summary_for_email(ats: dict) -> str:
    """Format ATS analysis into a readable email section."""
    score_before = ats.get("ats_score_before", "?")
    score_after = ats.get("ats_score_after", "?")
    missing = ats.get("missing_keywords", [])[:8]
    optimized_summary = ats.get("optimized_summary", "")

    lines = [
        "=" * 60,
        "ATS OPTIMIZATION REPORT",
        "=" * 60,
        f"Current ATS match score : {score_before}/100",
        f"Projected score (after)  : {score_after}/100",
        "",
        "TOP MISSING KEYWORDS TO ADD:",
    ]
    for kw in missing:
        lines.append(
            f"  + {kw['keyword']}  →  {kw['suggested_placement']}"
        )
        if kw.get("sample_phrase"):
            lines.append(f"    e.g. \"{kw['sample_phrase']}\"")

    if ats.get("weak_sections"):
        lines += ["", "SECTIONS TO STRENGTHEN:"]
        for ws in ats["weak_sections"][:3]:
            lines.append(f"  • {ws['section']}: {ws['suggestion']}")

    if optimized_summary:
        lines += ["", "SUGGESTED SUMMARY (ATS-optimized):", f'  "{optimized_summary}"']

    return "\n".join(lines)