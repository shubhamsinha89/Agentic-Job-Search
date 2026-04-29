"""
email_formatter.py
Builds the daily job digest email (plain text + HTML).
"""

from datetime import datetime


def _score_bar(score: int, max_score: int = 65) -> str:
    filled = round((score / max_score) * 10)
    return "█" * filled + "░" * (10 - filled)


def format_plain_text(
    profile: dict,
    ranked_jobs: list,
    ats_summary: str,
    config: dict,
) -> str:
    today = datetime.utcnow().strftime("%d %b %Y")
    top_n = config.get("results", {}).get("top_n", 20)
    candidate_name = profile.get("name", "there")
    profession = profile.get("profession_category", "")
    exp = profile.get("total_experience_years", "?")
    roles = " | ".join(profile.get("target_roles", [])[:3])
    skills = " | ".join(profile.get("top_skills", [])[:4])

    lines = [
        f"Hi {candidate_name},",
        "",
        f"Here are your top {min(top_n, len(ranked_jobs))} job matches for {today}.",
        f"Profile: {exp} yrs | {profession} | {roles}",
        f"Skills:  {skills}",
        "",
        "=" * 60,
        "JOB MATCHES",
        "=" * 60,
    ]

    for i, job in enumerate(ranked_jobs[:top_n], 1):
        score = job.get("total_score", 0)
        pct = job.get("relevance_pct", 0)
        bd = job.get("score_breakdown", {})
        country_flag = "🇮🇳" if job.get("country") == "India" else "🇺🇸"

        lines += [
            "",
            f"RANK {i} {country_flag}  |  Score: {score}/65  ({pct}%)  {_score_bar(score)}",
            f"Title   : {job.get('title', 'N/A')}",
            f"Company : {job.get('company', 'N/A')}",
            f"Location: {job.get('location', 'N/A')}",
            f"Exp Req : {job.get('experience_required', 'Not specified')}",
            f"Posted  : {job.get('posted_date', 'Unknown')}",
            f"Portal  : {job.get('portal', 'N/A')}",
            f"Scores  : Skills {bd.get('skills',0)} | Exp {bd.get('experience',0)} | "
            f"Role {bd.get('role',0)} | Industry {bd.get('industry',0)} | "
            f"Location {bd.get('location',0)} | Fresh {bd.get('freshness',0)}",
            f"Apply   : {job.get('url', 'N/A')}",
            "-" * 60,
        ]

    lines += [
        "",
        ats_summary,
        "",
        "=" * 60,
        f"Searches covered: India (Naukri, TimesJobs, iimjobs, Indeed India, Shine) + "
        f"US (Indeed, LinkedIn, Glassdoor, ZipRecruiter, Dice)",
        "This is an automated daily digest powered by Agentic Job Search.",
        "https://github.com/shubhamsinha89/Agentic-Job-Search",
    ]

    return "\n".join(lines)


def format_html(
    profile: dict,
    ranked_jobs: list,
    ats_summary: str,
    config: dict,
) -> str:
    today = datetime.utcnow().strftime("%d %b %Y")
    top_n = config.get("results", {}).get("top_n", 20)
    candidate_name = profile.get("name", "there")
    profession = profile.get("profession_category", "")
    exp = profile.get("total_experience_years", "?")
    roles = " | ".join(profile.get("target_roles", [])[:3])

    def pct_color(pct):
        if pct >= 80:
            return "#22c55e"
        if pct >= 60:
            return "#f59e0b"
        return "#ef4444"

    job_rows = []
    for i, job in enumerate(ranked_jobs[:top_n], 1):
        score = job.get("total_score", 0)
        pct = job.get("relevance_pct", 0)
        flag = "🇮🇳" if job.get("country") == "India" else "🇺🇸"
        color = pct_color(pct)
        job_rows.append(f"""
        <tr style="border-bottom:1px solid #e5e7eb">
          <td style="padding:12px;font-weight:600;color:#1f2937">{i}. {flag}</td>
          <td style="padding:12px">
            <strong><a href="{job.get('url','#')}" style="color:#2563eb;text-decoration:none">{job.get('title','N/A')}</a></strong><br>
            <span style="color:#6b7280">{job.get('company','N/A')} · {job.get('location','N/A')}</span><br>
            <span style="font-size:12px;color:#9ca3af">{job.get('portal','').capitalize()} · {job.get('posted_date','')}</span>
          </td>
          <td style="padding:12px;text-align:center">
            <span style="background:{color};color:white;padding:4px 10px;border-radius:12px;font-weight:700;font-size:14px">{pct}%</span><br>
            <span style="font-size:11px;color:#9ca3af">{score}/65 pts</span>
          </td>
          <td style="padding:12px;font-size:12px;color:#6b7280">{job.get('experience_required','N/A')}</td>
        </tr>""")

    ats_html = ats_summary.replace("\n", "<br>").replace("=", "")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#1f2937">
  <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:24px;border-radius:12px;color:white;margin-bottom:24px">
    <h1 style="margin:0 0 8px 0;font-size:22px">Your Daily Job Digest</h1>
    <p style="margin:0;opacity:0.9">{today} · {candidate_name} · {exp} yrs · {profession}</p>
    <p style="margin:4px 0 0 0;opacity:0.8;font-size:14px">{roles}</p>
  </div>

  <h2 style="color:#1f2937;border-bottom:2px solid #e5e7eb;padding-bottom:8px">
    Top {min(top_n, len(ranked_jobs))} Matches
  </h2>

  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <thead>
      <tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb">
        <th style="padding:10px;text-align:left;color:#6b7280;font-weight:600">#</th>
        <th style="padding:10px;text-align:left;color:#6b7280;font-weight:600">Role</th>
        <th style="padding:10px;text-align:center;color:#6b7280;font-weight:600">Match</th>
        <th style="padding:10px;text-align:left;color:#6b7280;font-weight:600">Exp Req</th>
      </tr>
    </thead>
    <tbody>{"".join(job_rows)}</tbody>
  </table>

  <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:20px;margin-top:24px">
    <h2 style="margin:0 0 12px 0;color:#92400e;font-size:16px">ATS Optimization Report</h2>
    <div style="font-size:13px;color:#78350f;line-height:1.6">{ats_html}</div>
  </div>

  <p style="font-size:12px;color:#9ca3af;margin-top:24px;text-align:center">
    Powered by <a href="https://github.com/shubhamsinha89/Agentic-Job-Search" style="color:#2563eb">Agentic Job Search</a>
    · India (Naukri · TimesJobs · iimjobs · Indeed · Shine) + US (Indeed · LinkedIn · Glassdoor · ZipRecruiter · Dice)
  </p>
</body>
</html>"""