# Agentic Job Search

An AI-powered automated job search pipeline that parses **any resume**, searches **India + US job portals**, scores results by relevance, and emails a ranked daily digest — with built-in **ATS optimization** to help your resume beat applicant tracking systems.

Orchestrated by **n8n** (production-grade) with a **Python CLI** for standalone use.

---

## How It Works

```
Your Resume (MD / PDF / DOCX / TXT)
              │
              ▼
    ┌─────────────────────────────────────────────────────────┐
    │                    n8n Orchestrator                     │
    │                                                         │
    │  [Schedule Trigger]                                     │
    │       ↓                                                 │
    │  [Read Resume File]                                     │
    │       ↓                                                 │
    │  [Claude: Parse Resume → structured profile]            │
    │       ↓                                                 │
    │  [Claude: Auto-generate search queries]                 │
    │       ↓                                                 │
    │  [Loop: Brave Search → India + US portals]              │
    │       ↓                                                 │
    │  [Merge + Deduplicate]                                  │
    │       ↓                                                 │
    │  [Claude: Score & rank (0–65 pts)]                      │
    │       ↓                                                 │
    │  [Claude: ATS analysis — keyword gaps + rewrite]        │
    │       ↓                                                 │
    │  [Format HTML email digest]                             │
    │       ↓                                                 │
    │  [Gmail: Send to recipient]                             │
    └─────────────────────────────────────────────────────────┘
              │
              ▼
    Ranked jobs + ATS report → your inbox, daily
```

---

## Features

| Feature | Details |
|---|---|
| **Truly generic** | Works for any profession — HR, Engineering, Finance, Marketing, etc. Claude reads your resume and auto-determines what to search |
| **Any resume format** | MD, TXT, PDF, DOCX all supported |
| **India + US portals** | Naukri, TimesJobs, iimjobs, Indeed India, Shine + Indeed US, LinkedIn, Glassdoor, ZipRecruiter, Dice |
| **Relevance scoring** | 65-point rubric across skills overlap, experience fit, role match, industry, location, freshness |
| **ATS optimizer** | Identifies missing keywords, suggests placement, projects score improvement |
| **ATS resume rewrite** | Generates a full optimized resume variant at `resume/resume_optimized.md` |
| **n8n orchestration** | Visual workflow editor, scheduling, retries, execution history, error alerting |
| **Python CLI** | Standalone runner — no n8n required |
| **Rich email digest** | Ranked HTML + plain text with scores, match reasons, apply links, ATS report |

---

## Quick Start — n8n (Recommended for Production)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Anthropic API key](https://console.anthropic.com/settings/keys)
- [Brave Search API key](https://brave.com/search/api/) — free tier: 2 000 queries/month
- Gmail account

### 1. Clone
```bash
git clone https://github.com/shubhamsinha89/Agentic-Job-Search.git
cd Agentic-Job-Search
```

### 2. Add your resume
```bash
cp resume/resume_template.md resume/resume.md
# Fill in your actual details — any profession works
```

### 3. Configure search preferences
```bash
cp config/search_config.example.yaml config/search_config.yaml
# Set email recipient, location priorities, industry preferences
```

### 4. Start n8n
```bash
cd n8n/
cp .env.example .env
# Edit .env — add API keys, email, password
docker compose up -d
```

### 5. Import workflow & activate
1. Open **http://localhost:5678** → log in
2. **Workflows → Import from file** → select `n8n/workflow.json`
3. Add **Gmail OAuth** credential: Settings → Credentials → Add
4. Toggle workflow to **Active**

Full setup guide: [n8n/README.md](n8n/README.md)

---

## Quick Start — Python CLI

```bash
pip install -r scripts/requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
export BRAVE_SEARCH_API_KEY=BSA...
export SMTP_USER=you@gmail.com
export SMTP_PASSWORD=your-app-password

# Dry run — print digest to console, no email sent
python src/main.py --dry-run

# Full run — search, score, ATS-optimize, send email
python src/main.py --resume resume/resume.md --config config/search_config.yaml
```

---

## File Structure

```
agentic-job-search/
├── README.md
├── CLAUDE.md                          # Claude Code project notes
├── .gitignore
│
├── src/                               # Python pipeline (standalone)
│   ├── resume_parser.py               # Parse any resume → structured profile dict
│   ├── job_searcher.py                # Search India + US portals via Brave API
│   ├── relevance_scorer.py            # 65-point relevance scoring engine
│   ├── ats_optimizer.py               # ATS gap analysis + resume rewriter
│   ├── email_formatter.py             # Plain text + HTML email builder
│   └── main.py                        # CLI entry point
│
├── n8n/                               # n8n orchestration
│   ├── workflow.json                  # Importable 15-node n8n workflow
│   ├── docker-compose.yml             # One-command local n8n setup
│   ├── .env.example                   # Environment variable template
│   └── README.md                      # n8n setup + troubleshooting guide
│
├── config/
│   ├── search_config.yaml             # Your config (gitignored)
│   └── search_config.example.yaml    # Copy this and edit
│
├── resume/
│   ├── resume.md                      # Your resume (gitignored)
│   ├── resume_optimized.md            # ATS-rewritten output (gitignored)
│   ├── resume_template.md             # Blank template for any profession
│   └── resume_example.md             # Example: Shivam Sinha, HR, 13 yrs
│
├── agent/                             # Claude Code remote agent (legacy mode)
│   ├── prompt_template.md
│   ├── scoring_rubric.md
│   └── generated_prompt.md            # Built by build_prompt.py (gitignored)
│
└── scripts/
    ├── build_prompt.py                # Build Claude remote-agent prompt
    ├── deploy_routine.py              # Deploy to Claude Code Routines
    └── requirements.txt
```

---

## Relevance Scoring — 65 Points

| Dimension | Max | Logic |
|---|---|---|
| Skills overlap | 15 | Keyword intersection: resume skills ∩ job description tokens |
| Role match | 15 | Title similarity against `target_roles` from parsed resume |
| Experience fit | 10 | Candidate years vs required range (exact match = full score) |
| Industry match | 8 | Company industry vs candidate background (from config) |
| Location | 12 | Preference-weighted (configure priority order in `search_config.yaml`) |
| Freshness | 5 | Today = 5 · Last 3 days = 4 · Last 7 = 3 · Last 14 = 2 · Older = 1 |
| **Total** | **65** | |

**Score bands:** 52–65 Excellent · 42–51 Strong · 30–41 Good · < 30 Weak

---

## ATS Optimizer

Each run produces a full ATS report comparing your resume against the top 8 job descriptions:

```
ATS OPTIMIZATION REPORT
══════════════════════════════════════════════════════════════
Current ATS match score : 54/100
Projected score (after) : 83/100

TOP MISSING KEYWORDS TO ADD:
  + HRIS Implementation  →  Skills section
    e.g. "Led HRIS implementation across 3 manufacturing plants"
  + Talent Acquisition   →  Work experience at [Company]
    e.g. "Managed end-to-end talent acquisition for 500+ headcount"
  + Change Management    →  Summary
    e.g. "Drove change management initiatives across multi-site operations"

SECTIONS TO STRENGTHEN:
  • Work Experience: Add quantified metrics (headcount, cost savings, % improvement)
  • Skills: Separate technical tools from soft skills for better ATS parsing

SUGGESTED SUMMARY (ATS-optimized):
  "Results-driven HR leader with 13 years across manufacturing and EPC sectors..."
```

The full ATS-optimized resume is saved to `resume/resume_optimized.md`.

---

## n8n Workflow — 15 Nodes

| # | Node | Type | Purpose |
|---|---|---|---|
| 1 | Daily Schedule | Schedule Trigger | Cron: `0 5 * * *` (9 PM PST) |
| 2 | Load Config | Set | Inject env vars (API keys, email, paths) |
| 3 | Read Resume File | Read/Write File | Load resume.md from mounted volume |
| 4 | Parse Resume | HTTP → Claude API | Extract structured profile JSON |
| 5 | Extract Profile JSON | Code | Parse Claude response, store profile |
| 6 | Generate Queries | HTTP → Claude API | Auto-generate 4 search query templates |
| 7 | Build Portal+Query List | Code | Expand: 4 queries × N portals = task list |
| 8 | Search Brave API | HTTP → Brave | Execute each site-scoped search query |
| 9 | Extract Job Listings | Code | Parse Brave results → normalised job dicts |
| 10 | Merge All Jobs | Merge | Collect all portal results into one stream |
| 11 | Score & Rank | HTTP → Claude API | Score all jobs, return top 20 ranked |
| 12 | Parse Ranked Jobs | Code | Extract ranked list from Claude response |
| 13 | ATS Analysis | HTTP → Claude API | Gap analysis resume vs top 8 JDs |
| 14 | Format Email | Code | Build plain text + HTML email |
| 15 | Send Gmail | Gmail node | Deliver digest to recipient |

---

## Job Portals

### India
| Portal | Best for |
|---|---|
| naukri.com | Widest India coverage |
| timesjobs.com | Manufacturing, plant, engineering |
| iimjobs.com | Senior / leadership roles |
| in.indeed.com | Broad mid-market coverage |
| shine.com | Secondary source |

### United States
| Portal | Best for |
|---|---|
| indeed.com | Widest US coverage |
| linkedin.com/jobs | Professional / senior roles |
| glassdoor.com | Culture-fit + salary transparency |
| ziprecruiter.com | AI-matched roles |
| dice.com | Tech / engineering roles |

---

## Configuration Reference

```yaml
email:
  recipient: "you@gmail.com"
  subject_prefix: "Top 20 Job Matches"

smtp:                     # for Python CLI only (n8n uses Gmail node)
  host: smtp.gmail.com
  port: 465

schedule:
  cron: "0 5 * * *"       # 9 PM PST = 5 AM UTC daily

target_roles:             # override auto-detection if needed
  - "Senior Software Engineer"
  - "Engineering Manager"

locations:                # higher score = higher email rank priority
  - name: "Bangalore"
    keywords: ["Bangalore", "Bengaluru"]
    score: 12
  - name: "Delhi NCR"
    keywords: ["Delhi", "Noida", "Gurgaon"]
    score: 10

industries:
  - name: "Fintech"
    keywords: ["fintech", "payments", "neobank"]
    score: 8

portals:
  naukri:      { enabled: true }
  linkedin:    { enabled: false }   # blocks bots
  indeed_us:   { enabled: true }

results:
  top_n: 20

scoring:
  location_max: 12
  role_match_max: 15
  industry_match_max: 8
  experience_fit_max: 10
  freshness_max: 5
  total_max: 65
```

---

## Privacy

All personal files are **gitignored** by default — they never leave your machine:
- `resume/resume.md`
- `resume/resume_optimized.md`
- `config/search_config.yaml`
- `n8n/.env`

The resume is read at runtime by the n8n Docker container (read-only volume mount) or the Python CLI. It is never committed to git.

---

## Two Modes Compared

| | n8n Mode | Python CLI Mode |
|---|---|---|
| **Best for** | Daily automated runs, monitoring | Local testing, CI/CD, scripting |
| **Scheduling** | Built-in visual cron | OS cron or manual |
| **Visibility** | Node-by-node execution history | Console output |
| **Setup** | Docker + 5 min | pip install + env vars |
| **Customisation** | Drag-and-drop node editor | Edit Python source |

---

## Contributing

PRs welcome. Roadmap ideas:
- Cover letter generator per job
- WhatsApp / Slack notifications
- Application tracker (applied / rejected / interview)
- Duplicate detection across daily digests
- Web UI for resume upload + config

---

## License

MIT