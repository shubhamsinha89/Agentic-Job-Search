"""
resume_parser.py
Parses any resume format (MD, TXT, PDF, DOCX) using Claude API.
Returns a structured profile dict used by all other modules.
"""

import json
import os
import re
from pathlib import Path

from src.llm_client import complete_json, provider_info


PARSE_PROMPT = """You are a resume parser. Extract all information from the resume below into a structured JSON object.

Return ONLY valid JSON with this exact schema:
{{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "total_experience_years": number,
  "current_role": "string",
  "current_company": "string",
  "target_roles": ["list of 5-8 specific job titles this person should target"],
  "top_skills": ["list of top 15 hard skills, tools, technologies, certifications"],
  "soft_skills": ["list of top 5 soft skills"],
  "industries": ["industries the person has worked in"],
  "keywords": ["30 most important ATS keywords from this resume"],
  "education": [{{"degree": "string", "institution": "string", "year": number}}],
  "employment_history": [
    {{
      "title": "string",
      "company": "string",
      "industry": "string",
      "start_date": "string",
      "end_date": "string",
      "duration_months": number,
      "key_achievements": ["list of 3 key achievements or responsibilities"]
    }}
  ],
  "languages": ["list of languages"],
  "certifications": ["list of certifications if any"],
  "summary": "2-3 sentence professional summary",
  "seniority_level": "Junior | Mid | Senior | Lead | Director | VP | C-Suite",
  "profession_category": "e.g. Human Resources | Software Engineering | Finance | Marketing | etc."
}}

Resume:
{resume_text}"""


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise ImportError("Install python-docx:  pip install python-docx")


def _read_pdf(path: Path) -> str:
    try:
        import pdfplumber
        text = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
        return "\n".join(text)
    except ImportError:
        raise ImportError("Install pdfplumber:  pip install pdfplumber")


def read_resume_file(file_path: str) -> str:
    """Read resume from any supported format and return raw text."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {file_path}")

    ext = path.suffix.lower()
    readers = {
        ".md": _read_txt,
        ".txt": _read_txt,
        ".docx": _read_docx,
        ".pdf": _read_pdf,
    }
    reader = readers.get(ext)
    if not reader:
        raise ValueError(f"Unsupported format: {ext}. Supported: {list(readers)}")

    return reader(path)


def parse_resume(file_path: str, api_key: str = None) -> dict:
    """
    Parse a resume file and return a structured profile dict.

    Args:
        file_path: Path to resume (MD / TXT / DOCX / PDF)
        api_key:   Unused — provider is set via LLM_PROVIDER env var

    Returns:
        Structured profile dict
    """
    raw_text = read_resume_file(file_path)
    print(f"  LLM provider : {provider_info()}")

    profile = complete_json(PARSE_PROMPT.format(resume_text=raw_text), max_tokens=2048)
    profile["_raw_text"] = raw_text  # keep original for ATS analysis
    return profile


def profile_summary_line(profile: dict) -> str:
    """One-line summary for email headers."""
    exp = profile.get("total_experience_years", "?")
    roles = " | ".join(profile.get("target_roles", [])[:3])
    skills = " | ".join(profile.get("top_skills", [])[:3])
    return f"{exp} yrs | {roles} | {skills}"