#!/usr/bin/env python3
"""
main.py
Standalone CLI runner for the Agentic Job Search pipeline.
Runs the full pipeline: parse → search → score → ATS → email.

Usage:
  python src/main.py
  python src/main.py --resume resume/resume.md --config config/search_config.yaml
  python src/main.py --dry-run   # skip email, print digest to console
"""

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env from project root if it exists
try:
    from dotenv import load_dotenv
    _env = ROOT / ".env"
    if _env.exists():
        load_dotenv(_env)
        print(f"  Loaded env from {_env}")
except ImportError:
    pass

from src.resume_parser import parse_resume, profile_summary_line
from src.job_searcher import search_all
from src.relevance_scorer import score_and_rank
from src.ats_optimizer import analyze_ats, generate_optimized_resume, ats_summary_for_email
from src.email_formatter import format_plain_text, format_html


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        print(f"Config not found: {config_path}")
        print("Copy config/search_config.example.yaml → config/search_config.yaml")
        sys.exit(1)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def send_email(
    to: str,
    subject: str,
    plain_text: str,
    html: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())


def run(
    resume_path: str,
    config_path: str,
    dry_run: bool = False,
    save_optimized_resume: bool = True,
):
    config = load_config(config_path)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    brave_key = os.environ.get("BRAVE_SEARCH_API_KEY", "")

    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    if not brave_key:
        print("ERROR: BRAVE_SEARCH_API_KEY environment variable not set.")
        sys.exit(1)

    # ── 1. Parse resume ────────────────────────────────────────────────────
    print("\n[1/5] Parsing resume...")
    profile = parse_resume(resume_path, api_key=anthropic_key)
    print(f"  Name      : {profile.get('name')}")
    print(f"  Profession: {profile.get('profession_category')}")
    print(f"  Experience: {profile.get('total_experience_years')} years")
    print(f"  Targets   : {', '.join(profile.get('target_roles', [])[:3])}")

    # ── 2. Search jobs ─────────────────────────────────────────────────────
    print("\n[2/5] Searching India + US job portals...")
    raw_jobs = search_all(profile, config, brave_api_key=brave_key, anthropic_api_key=anthropic_key)

    # ── 3. Score & rank ────────────────────────────────────────────────────
    print("\n[3/5] Scoring and ranking jobs...")
    top_n = config.get("results", {}).get("top_n", 20)
    ranked = score_and_rank(raw_jobs, profile, config, top_n=top_n)
    print(f"  Top {len(ranked)} jobs selected from {len(raw_jobs)} raw results")
    if ranked:
        print(f"  Best match: {ranked[0].get('title')} at {ranked[0].get('company')} "
              f"({ranked[0].get('relevance_pct')}%)")

    # ── 4. ATS analysis ────────────────────────────────────────────────────
    print("\n[4/5] Running ATS analysis...")
    ats = analyze_ats(profile, ranked, api_key=anthropic_key)
    print(f"  ATS score before: {ats.get('ats_score_before')}/100")
    print(f"  ATS score after : {ats.get('ats_score_after')}/100")
    print(f"  Missing keywords: {len(ats.get('missing_keywords', []))}")

    if save_optimized_resume:
        print("  Generating optimised resume...")
        optimized = generate_optimized_resume(profile, ats, api_key=anthropic_key)
        out_path = ROOT / "resume" / "resume_optimized.md"
        out_path.write_text(optimized, encoding="utf-8")
        print(f"  Saved to: {out_path}")

    # ── 5. Email ───────────────────────────────────────────────────────────
    from datetime import datetime
    today = datetime.utcnow().strftime("%d %b %Y")
    subject = f"{config['email'].get('subject_prefix','Top Jobs')} – {today}"
    ats_text = ats_summary_for_email(ats)
    plain = format_plain_text(profile, ranked, ats_text, config)
    html = format_html(profile, ranked, ats_text, config)

    if dry_run:
        print("\n[5/5] DRY RUN — printing digest to console (no email sent)\n")
        print(plain)
        return

    print(f"\n[5/5] Sending email to {config['email']['recipient']}...")
    smtp_cfg = config.get("smtp", {})
    send_email(
        to=config["email"]["recipient"],
        subject=subject,
        plain_text=plain,
        html=html,
        smtp_host=smtp_cfg.get("host", "smtp.gmail.com"),
        smtp_port=smtp_cfg.get("port", 465),
        smtp_user=smtp_cfg.get("user") or os.environ.get("SMTP_USER", ""),
        smtp_password=smtp_cfg.get("password") or os.environ.get("SMTP_PASSWORD", ""),
    )
    print("  Email sent successfully.")
    print("\nDone.")


def main():
    parser = argparse.ArgumentParser(description="Agentic Job Search — standalone runner")
    parser.add_argument(
        "--resume",
        default=str(ROOT / "resume" / "resume.md"),
        help="Path to resume file (MD/TXT/PDF/DOCX)",
    )
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "search_config.yaml"),
        help="Path to search_config.yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print digest to console without sending email",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip generating the optimised resume file",
    )
    args = parser.parse_args()
    run(
        resume_path=args.resume,
        config_path=args.config,
        dry_run=args.dry_run,
        save_optimized_resume=not args.no_optimize,
    )


if __name__ == "__main__":
    main()