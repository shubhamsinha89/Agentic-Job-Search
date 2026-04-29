# n8n Setup Guide

n8n is the production-grade workflow orchestrator for Agentic Job Search.
It provides a visual editor, scheduling, error handling, retries, and execution history.

## Architecture

```
[Schedule Trigger]
       ↓
[Read Resume File]
       ↓
[Parse Resume → Claude API]  →  structured profile JSON
       ↓
[Generate Search Queries → Claude API]  →  targeted query strings
       ↓
[Loop: Search Each Portal → Brave Search API]  →  raw job listings
       ↓
[Merge + Deduplicate]
       ↓
[Score & Rank → Claude API]  →  top 20 scored jobs
       ↓
[ATS Analysis → Claude API]  →  keyword gaps + suggestions
       ↓
[Format Email HTML]
       ↓
[Send via Gmail Node]
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com/settings/keys)
- Brave Search API key (free tier) — [brave.com/search/api](https://brave.com/search/api/)
- Gmail account for sending email

## Quick Start

### 1. Set up environment
```bash
cd n8n/
cp .env.example .env
# Edit .env — fill in your API keys, email, password
```

### 2. Add your resume
```bash
# Make sure resume/resume.md exists (see ../resume/resume_template.md)
```

### 3. Start n8n
```bash
docker compose up -d
```

### 4. Open n8n
Visit http://localhost:5678 and log in with your N8N_USER / N8N_PASSWORD.

### 5. Import the workflow
1. Go to **Workflows** → **Import from file**
2. Select `n8n/workflow.json`
3. Click **Import**

### 6. Configure credentials in n8n
n8n stores credentials securely. Set these up once:

| Credential | Type | Where used |
|---|---|---|
| Anthropic API | HTTP Request Header | Parse Resume, Score Jobs, ATS Analysis |
| Brave Search API | HTTP Request Header | Job search calls |
| Gmail OAuth | Gmail node | Send email |

To add credentials: **Settings** → **Credentials** → **Add Credential**

### 7. Activate the workflow
Toggle the workflow to **Active** — it will run on the configured schedule.

### 8. Test manually
Click **Execute Workflow** to trigger a one-off run and see results.

## Environment Variables in Workflow

The workflow reads API keys directly from n8n environment variables (set in docker-compose.yml):
- `ANTHROPIC_API_KEY`
- `BRAVE_SEARCH_API_KEY`
- `EMAIL_RECIPIENT`
- `RESUME_FILE_PATH`

These are passed to HTTP Request nodes via expressions like `{{ $env.ANTHROPIC_API_KEY }}`.

## Monitoring

- **Execution history**: Workflows → click workflow → Executions tab
- **Error alerts**: Settings → Workflows → Error workflow (set up an error notification)
- **Logs**: `docker compose logs -f n8n`

## Deploying to Cloud (optional)

For always-on scheduling, deploy n8n to:
- **Railway**: one-click deploy, free tier available
- **Render**: free tier, persistent storage
- **DigitalOcean Droplet**: $6/month, full control

Update `N8N_HOST` in `.env` to your server's domain/IP.

## Updating the Resume or Config

After changing `resume/resume.md` or `config/search_config.yaml`:
1. The n8n workflow reads the resume file at runtime — no redeploy needed
2. Config changes that affect scoring/portals require updating the workflow's Code nodes

## Troubleshooting

| Issue | Fix |
|---|---|
| "Brave API 401" | Check BRAVE_SEARCH_API_KEY in .env |
| "Claude API error" | Check ANTHROPIC_API_KEY, check account credits |
| Gmail not sending | Re-authorise Gmail OAuth credential in n8n |
| Workflow stuck | Check execution logs for which node failed |
| No jobs found | Brave free tier exhausted (2000/month) — check usage |