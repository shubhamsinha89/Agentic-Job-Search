# Agentic Job Search

An AI-powered automated job search agent built with [Claude Code](https://claude.ai/code) that runs daily, searches major job portals, scores results against your resume, and emails you the top matches — hands-free.

## How It Works

```
Your Resume + Config
        │
        ▼
  build_prompt.py        ← Generates personalised agent prompt
        │
        ▼
  deploy_routine.py      ← Deploys as a Claude remote agent routine
        │
        ▼
  Runs every night       ← Searches portals, scores jobs, sends email
        │
        ▼
  Top 20 jobs → Gmail
```

Every night at your configured time, the agent:
1. Reads your resume profile and target preferences
2. Runs targeted searches across major job portals
3. Scores every result on a 45-point rubric (location + role + industry + experience + freshness)
4. De-duplicates across portals
5. Emails the top 20 best-matched jobs directly to your inbox

---

## Quick Start

### Prerequisites
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Gmail MCP connector set up at [claude.ai/customize/connectors](https://claude.ai/customize/connectors)
- Python 3.8+

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/agentic-job-search.git
cd agentic-job-search
```

### 2. Install dependencies
```bash
pip install -r scripts/requirements.txt
```

### 3. Add your resume
```bash
cp resume/resume_template.md resume/resume.md
# Edit resume/resume.md with your actual details
```

### 4. Configure search preferences
```bash
cp config/search_config.example.yaml config/search_config.yaml
# Edit config/search_config.yaml — set email, locations, portals, schedule
```

### 5. Build your agent prompt
```bash
python scripts/build_prompt.py
# Outputs: agent/generated_prompt.md
```

### 6. Deploy the routine
```bash
# Open Claude Code and run:
/schedule
# Then paste the contents of agent/generated_prompt.md when prompted
```

Or use the automated deploy script (requires Claude Code CLI in PATH):
```bash
python scripts/deploy_routine.py
```

---

## File Structure

```
agentic-job-search/
├── README.md
├── CLAUDE.md                        # Claude Code instructions
├── .gitignore
├── config/
│   ├── search_config.yaml           # Your config (gitignored)
│   └── search_config.example.yaml  # Template to copy
├── resume/
│   ├── resume.md                    # Your resume (gitignored)
│   ├── resume_template.md           # Blank template
│   └── resume_example.md           # Example (Shivam Sinha - HR professional)
├── agent/
│   ├── prompt_template.md           # Agent prompt with {{placeholders}}
│   ├── scoring_rubric.md            # Scoring criteria documentation
│   └── generated_prompt.md          # Output of build_prompt.py (gitignored)
├── scripts/
│   ├── build_prompt.py              # Builds final prompt from resume + config
│   ├── deploy_routine.py            # Creates/updates Claude remote routine
│   └── requirements.txt
└── .claude/
    └── skills/
        └── job-search.md            # Claude Code skill definition
```

---

## Customisation

### Changing target locations
Edit `config/search_config.yaml`:
```yaml
locations:
  - name: "Mumbai"
    keywords: ["Mumbai", "Navi Mumbai", "Thane"]
    score: 12
  - name: "Bangalore"
    keywords: ["Bangalore", "Bengaluru"]
    score: 10
```

### Changing job portals
```yaml
portals:
  - name: naukri
    site: naukri.com
    enabled: true
  - name: linkedin
    site: linkedin.com/jobs
    enabled: false   # LinkedIn blocks bots — use with caution
```

### Changing schedule
9 PM PST = `0 5 * * *` UTC. Use [crontab.guru](https://crontab.guru) to generate your expression.

### Adjusting scoring weights
```yaml
scoring:
  location_max: 12
  role_match_max: 15
  industry_match_max: 8
  experience_fit_max: 5
  freshness_max: 5
```

---

## Supported Job Portals (India)

| Portal | Site | Notes |
|---|---|---|
| Naukri | naukri.com | Best coverage, works well |
| TimesJobs | timesjobs.com | Good for manufacturing/plant roles |
| iimjobs | iimjobs.com | Best for senior roles |
| Indeed India | in.indeed.com | Broad coverage |
| Shine | shine.com | Good secondary source |
| Foundit | foundit.in | Formerly Monster India |
| LinkedIn | linkedin.com/jobs | Rate-limited — use sparingly |

---

## Email Output Format

Each daily digest looks like:

```
Subject: Top 20 Job Matches – 27 Apr 2026

Hi [Name],

Here are your top 20 job matches for 27 Apr 2026.
Profile: 13 yrs | Plant HR | Labour Laws | SAP Payroll

---
RANK 1 | Score: 42/45
Title: Senior Manager – Plant HR
Company: Tata Chemicals Ltd
Industry: Chemicals / Fertilizers
Location: Patna, Bihar
Experience: 12–15 years
Posted: Today
Match reason: Plant HR in Bihar, Chemicals industry, 12-15 yrs required
Apply: https://naukri.com/...
---
...
```

---

## Architecture

This project uses **Claude Code remote agents** (CCR — Claude Code Routines):
- No server required — runs on Anthropic's cloud infrastructure
- Triggered daily via cron schedule
- Uses Gmail MCP connector for email delivery
- Fully stateless — each run is independent

---

## Privacy

- `resume/resume.md` and `config/search_config.yaml` are **gitignored by default** — your personal info stays local
- The resume is embedded into the agent prompt at deploy time
- Only the prompt template and example files are committed to git

---

## Contributing

PRs welcome. Ideas:
- Add WhatsApp/Slack notification support
- Add more job portals (Internshala, Apna, Instahyre)
- Add duplicate detection across daily digests
- Build a web UI for configuration

---

## License

MIT